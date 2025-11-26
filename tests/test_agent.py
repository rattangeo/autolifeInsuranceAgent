"""Tests for Claims Processing Agent."""

import pytest
import json
from pathlib import Path
from datetime import datetime

from src.models import (
    ClaimInformation, ClaimType, ClaimStatus, 
    FraudRiskLevel, PolicyStatus, Policy
)
from src.agent.tools import ClaimsTools


@pytest.fixture
def policies_path():
    """Get path to test policies."""
    return Path(__file__).parent.parent / "src" / "data" / "policies.json"


@pytest.fixture
def claims_tools(policies_path):
    """Create ClaimsTools instance."""
    return ClaimsTools(policies_path)


def test_extract_claim_information(claims_tools):
    """Test claim information extraction."""
    claim_text = """
    I was in a car accident on November 20, 2025. 
    My policy number is POL-AUTO-001. 
    The repair costs are estimated at $5,000.
    """
    
    result = claims_tools.extract_claim_information(claim_text)
    data = json.loads(result)
    
    assert data['policy_number'] == 'POL-AUTO-001'
    assert data['claim_type'] == 'auto'
    assert data['claim_amount'] == 5000.0
    assert 'incident_date' in data


def test_check_policy_coverage_valid(claims_tools):
    """Test policy coverage check for valid policy."""
    result = claims_tools.check_policy_coverage(
        policy_number="POL-AUTO-001",
        claim_type="auto",
        claim_amount=5000.0
    )
    
    data = json.loads(result)
    
    assert data['is_valid'] is True
    assert data['is_covered'] is True
    assert data['coverage_limit'] > 0
    assert data['deductible'] >= 0


def test_check_policy_coverage_expired(claims_tools):
    """Test policy coverage check for expired policy."""
    result = claims_tools.check_policy_coverage(
        policy_number="POL-AUTO-005",
        claim_type="auto",
        claim_amount=5000.0
    )
    
    data = json.loads(result)
    
    assert data['is_valid'] is False
    assert data['is_covered'] is False


def test_check_policy_coverage_not_found(claims_tools):
    """Test policy coverage check for non-existent policy."""
    result = claims_tools.check_policy_coverage(
        policy_number="POL-FAKE-999",
        claim_type="auto",
        claim_amount=5000.0
    )
    
    data = json.loads(result)
    
    assert data['is_valid'] is False
    assert 'not found' in data['reason'].lower()


def test_assess_fraud_risk_low(claims_tools):
    """Test fraud assessment for low-risk claim."""
    claim_text = """
    I was in a car accident on November 20, 2025. 
    Police report number PR-2025-123. Two witnesses present.
    My policy number is POL-AUTO-001. Repair estimate: $3,000.
    """
    
    result = claims_tools.assess_fraud_risk(
        claim_text=claim_text,
        claim_amount=3000.0,
        policy_age_days=365
    )
    
    data = json.loads(result)
    
    assert data['risk_level'] == 'low'
    assert data['requires_investigation'] is False


def test_assess_fraud_risk_high(claims_tools):
    """Test fraud assessment for high-risk claim."""
    claim_text = """
    My car was damaged yesterday. Not sure what happened.
    No police report, no witnesses. Need money urgently.
    My cousin's repair shop quoted $15,000. 
    Just got this policy 2 weeks ago.
    """
    
    result = claims_tools.assess_fraud_risk(
        claim_text=claim_text,
        claim_amount=15000.0,
        policy_age_days=14
    )
    
    data = json.loads(result)
    
    assert data['risk_level'] in ['high', 'critical']
    assert data['requires_investigation'] is True
    assert len(data['indicators']) > 0


def test_calculate_approved_amount_covered(claims_tools):
    """Test approved amount calculation for covered claim."""
    result = claims_tools.calculate_approved_amount(
        claim_amount=10000.0,
        coverage_limit=50000.0,
        deductible=500.0,
        is_covered=True
    )
    
    data = json.loads(result)
    
    assert data['approved_amount'] == 9500.0
    assert data['deductible_applied'] == 500.0


def test_calculate_approved_amount_not_covered(claims_tools):
    """Test approved amount calculation for non-covered claim."""
    result = claims_tools.calculate_approved_amount(
        claim_amount=10000.0,
        coverage_limit=50000.0,
        deductible=500.0,
        is_covered=False
    )
    
    data = json.loads(result)
    
    assert data['approved_amount'] == 0.0


def test_calculate_approved_amount_exceeds_limit(claims_tools):
    """Test approved amount when claim exceeds coverage limit."""
    result = claims_tools.calculate_approved_amount(
        claim_amount=60000.0,
        coverage_limit=50000.0,
        deductible=500.0,
        is_covered=True
    )
    
    data = json.loads(result)
    
    assert data['approved_amount'] == 49500.0  # 50000 - 500
    assert data['coverage_limit_applied'] is True


def test_policy_model():
    """Test Policy model."""
    policy_data = {
        "policy_number": "TEST-001",
        "policy_type": "auto",
        "policyholder": "Test User",
        "status": PolicyStatus.ACTIVE,
        "effective_date": datetime(2024, 1, 1),
        "expiry_date": datetime(2025, 12, 31),
        "coverages": [],
        "annual_premium": 1000.0
    }
    
    policy = Policy(**policy_data)
    
    assert policy.policy_number == "TEST-001"
    assert policy.is_active() is True


def test_claim_model():
    """Test Claim model."""
    from src.models import Claim
    
    claim = Claim(raw_claim_text="Test claim")
    claim.add_log("Test log entry")
    
    assert len(claim.processing_log) == 1
    assert "Test log entry" in claim.processing_log[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
