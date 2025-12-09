"""
Agent tools for claims processing.
These are the functions the agent can autonomously call during claim processing.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from semantic_kernel.functions import kernel_function

from ..models import (
    ClaimInformation, ClaimType, PolicyCoverageCheck, 
    FraudAssessment, FraudRiskLevel, ClaimRecommendation, ClaimStatus,
    Policy, CoverageType
)
from ..utils import logger


class ClaimsTools:
    """Collection of tools the agent can use to process claims."""
    
    def __init__(self, policies_path: Path):
        """Initialize tools with policy database."""
        self.policies = self._load_policies(policies_path)
        logger.info(f"Loaded {len(self.policies)} policies from database")
    
    def _load_policies(self, policies_path: Path) -> List[Policy]:
        """Load policies from JSON file."""
        with open(policies_path, 'r') as f:
            data = json.load(f)
        
        policies = []
        for p in data:
            # Convert coverage types to enum
            for coverage in p['coverages']:
                coverage['coverage_type'] = CoverageType(coverage['coverage_type'])
            
            # Parse dates
            p['effective_date'] = datetime.fromisoformat(p['effective_date'])
            p['expiry_date'] = datetime.fromisoformat(p['expiry_date'])
            
            policies.append(Policy(**p))
        
        return policies
    
    def _get_policy(self, policy_number: str) -> Policy | None:
        """Retrieve policy by number."""
        for policy in self.policies:
            if policy.policy_number == policy_number:
                return policy
        return None
    
    @kernel_function(
        name="extract_claim_information",
        description="Extracts structured information from claim text including policy number, claim type, incident date, amount, and description"
    )
    def extract_claim_information(self, claim_text: str) -> str:
        """
        Extract structured claim information from raw text.
        
        Args:
            claim_text: Raw claim submission text
            
        Returns:
            JSON string with extracted claim information
        """
        logger.info("Extracting claim information from text")
        
        # Extract policy number
        policy_match = re.search(r'POL-[A-Z]+-\d+', claim_text, re.IGNORECASE)
        policy_number = policy_match.group(0) if policy_match else "UNKNOWN"
        
        # Determine claim type - prioritize policy number prefix first
        if 'POL-AUTO' in policy_number.upper():
            claim_type = ClaimType.AUTO
        elif 'POL-HOME' in policy_number.upper():
            claim_type = ClaimType.HOME
        elif 'POL-HEALTH' in policy_number.upper():
            claim_type = ClaimType.HEALTH
        # If policy number doesn't indicate type, check content keywords
        elif any(word in claim_text.lower() for word in ['hospital', 'medical', 'health', 'emergency', 'doctor', 'chest pain', 'heart', 'ekg', 'ambulance', 'patient', 'diagnosis']):
            claim_type = ClaimType.HEALTH
        elif any(word in claim_text.lower() for word in ['home', 'house', 'property', 'pipe', 'theft', 'burglary', 'fire', 'water damage']):
            claim_type = ClaimType.HOME
        elif any(word in claim_text.lower() for word in ['car', 'vehicle', 'collision', 'auto', 'driving', 'windshield', 'fender']):
            claim_type = ClaimType.AUTO
        else:
            claim_type = ClaimType.AUTO  # default
        
        # Extract amount
        amounts = re.findall(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', claim_text)
        amounts = [float(a.replace(',', '')) for a in amounts if float(a.replace(',', '')) > 100]
        claim_amount = max(amounts) if amounts else 1000.0
        
        # Extract date
        date_patterns = [
            r'(?:November|Nov)\s+(\d{1,2}),?\s+2025',
            r'(\d{1,2})/(\d{1,2})/2025',
            r'2025-(\d{2})-(\d{2})'
        ]
        
        incident_date = datetime.now()
        for pattern in date_patterns:
            match = re.search(pattern, claim_text, re.IGNORECASE)
            if match:
                if 'November' in pattern or 'Nov' in pattern:
                    day = int(match.group(1))
                    incident_date = datetime(2025, 11, day)
                break
        
        # Extract claimant name (basic heuristic)
        claimant_name = None
        if 'policyholder' in claim_text.lower():
            name_match = re.search(r'policyholder[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)', claim_text)
            if name_match:
                claimant_name = name_match.group(1)
        
        # Create short description
        description = claim_text[:200] + "..." if len(claim_text) > 200 else claim_text
        
        result = {
            "policy_number": policy_number,
            "claim_type": claim_type.value,
            "incident_date": incident_date.isoformat(),
            "claim_amount": claim_amount,
            "description": description,
            "claimant_name": claimant_name
        }
        
        logger.info(f"Extracted: {policy_number}, {claim_type.value}, ${claim_amount:,.2f}")
        return json.dumps(result, indent=2)
    
    @kernel_function(
        name="check_policy_coverage",
        description="Validates if a policy is active and covers the claim type, returns coverage limits and deductibles"
    )
    def check_policy_coverage(self, policy_number: str, claim_type: str, claim_amount: float) -> str:
        """
        Check if policy covers the claim.
        
        Args:
            policy_number: Insurance policy number
            claim_type: Type of claim (auto, home, health, life)
            claim_amount: Claimed amount
            
        Returns:
            JSON string with coverage check results
        """
        logger.info(f"Checking coverage for policy {policy_number}")
        
        policy = self._get_policy(policy_number)
        
        if not policy:
            result = {
                "is_valid": False,
                "coverage_type": "unknown",
                "coverage_limit": 0.0,
                "deductible": 0.0,
                "is_covered": False,
                "reason": f"Policy {policy_number} not found in database"
            }
            logger.warning(f"Policy {policy_number} not found")
            return json.dumps(result, indent=2)
        
        # Check if policy is active
        if not policy.is_active():
            result = {
                "is_valid": False,
                "coverage_type": policy.policy_type,
                "coverage_limit": 0.0,
                "deductible": 0.0,
                "is_covered": False,
                "reason": f"Policy is {policy.status.value}. Expiry date: {policy.expiry_date.date()}",
                "policy_expiry": policy.expiry_date.isoformat()
            }
            logger.warning(f"Policy {policy_number} is not active")
            return json.dumps(result, indent=2)
        
        # Map claim type to coverage type
        coverage_map = {
            "auto": CoverageType.AUTO_COLLISION,
            "home": CoverageType.HOME_PROPERTY,
            "health": CoverageType.HEALTH_EMERGENCY,
        }
        
        coverage_type = coverage_map.get(claim_type, CoverageType.AUTO_COLLISION)
        coverage = policy.get_coverage(coverage_type)
        
        if not coverage:
            result = {
                "is_valid": True,
                "coverage_type": policy.policy_type,
                "coverage_limit": 0.0,
                "deductible": 0.0,
                "is_covered": False,
                "reason": f"Policy does not include {coverage_type.value} coverage"
            }
            logger.info(f"Policy {policy_number} lacks {coverage_type.value} coverage")
            return json.dumps(result, indent=2)
        
        # Check if claim amount exceeds coverage
        is_covered = claim_amount <= coverage.coverage_limit
        reason = "Claim is within coverage limits" if is_covered else f"Claim amount exceeds coverage limit of ${coverage.coverage_limit:,.2f}"
        
        result = {
            "is_valid": True,
            "coverage_type": coverage_type.value,
            "coverage_limit": coverage.coverage_limit,
            "deductible": coverage.deductible,
            "is_covered": is_covered,
            "reason": reason,
            "policy_expiry": policy.expiry_date.isoformat()
        }
        
        logger.info(f"Coverage check complete: {is_covered}")
        return json.dumps(result, indent=2)
    
    @kernel_function(
        name="assess_fraud_risk",
        description="Analyzes claim for fraud indicators and calculates risk score"
    )
    def assess_fraud_risk(self, claim_text: str, claim_amount: float, policy_age_days: int = 365) -> str:
        """
        Assess fraud risk for a claim.
        
        Args:
            claim_text: Original claim text
            claim_amount: Claimed amount
            policy_age_days: Days since policy was issued
            
        Returns:
            JSON string with fraud assessment
        """
        logger.info("Assessing fraud risk")
        
        indicators = []
        risk_score = 0.0
        
        claim_lower = claim_text.lower()
        
        # Check for fraud indicators
        if policy_age_days < 30:
            indicators.append("Policy is very new (less than 30 days)")
            risk_score += 25
        
        if claim_amount > 10000:
            indicators.append("High claim amount (over $10,000)")
            risk_score += 15
        
        if 'urgent' in claim_lower or 'immediately' in claim_lower or 'urgently' in claim_lower:
            indicators.append("Urgency language detected")
            risk_score += 10
        
        if 'no witness' in claim_lower or 'no police report' in claim_lower:
            indicators.append("Lack of documentation or witnesses")
            risk_score += 20
        
        if any(word in claim_lower for word in ['financial difficult', 'need money', 'cash', 'payment today']):
            indicators.append("Financial distress mentioned")
            risk_score += 20
        
        if claim_lower.count('claim') > 3 or 'previous claim' in claim_lower or 'other claim' in claim_lower:
            indicators.append("Multiple recent claims mentioned")
            risk_score += 25
        
        if 'cousin' in claim_lower or 'friend' in claim_lower or 'family' in claim_lower:
            if 'repair' in claim_lower or 'shop' in claim_lower:
                indicators.append("Repair shop has personal connection")
                risk_score += 15
        
        if "not sure" in claim_lower or "don't know" in claim_lower or "not exactly" in claim_lower:
            indicators.append("Vague or inconsistent details")
            risk_score += 10
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = FraudRiskLevel.CRITICAL
            recommendation = "REJECT - High fraud risk, requires immediate investigation"
            requires_investigation = True
        elif risk_score >= 40:
            risk_level = FraudRiskLevel.HIGH
            recommendation = "HOLD - Multiple fraud indicators, manual review required"
            requires_investigation = True
        elif risk_score >= 20:
            risk_level = FraudRiskLevel.MEDIUM
            recommendation = "REVIEW - Some concerns, additional verification recommended"
            requires_investigation = True
        else:
            risk_level = FraudRiskLevel.LOW
            recommendation = "PROCEED - Low fraud risk, normal processing"
            requires_investigation = False
        
        result = {
            "risk_level": risk_level.value,
            "risk_score": min(risk_score, 100.0),
            "indicators": indicators if indicators else ["No significant fraud indicators detected"],
            "recommendation": recommendation,
            "requires_investigation": requires_investigation
        }
        
        logger.info(f"Fraud assessment: {risk_level.value} ({risk_score:.0f}/100)")
        return json.dumps(result, indent=2)
    
    @kernel_function(
        name="calculate_approved_amount",
        description="Calculates the final approved claim amount after applying deductibles and coverage limits"
    )
    def calculate_approved_amount(
        self, 
        claim_amount: float, 
        coverage_limit: float, 
        deductible: float,
        is_covered: bool
    ) -> str:
        """
        Calculate approved amount.
        
        Args:
            claim_amount: Claimed amount
            coverage_limit: Maximum coverage
            deductible: Policy deductible
            is_covered: Whether claim is covered
            
        Returns:
            JSON string with calculation details
        """
        logger.info(f"Calculating approved amount for ${claim_amount:,.2f}")
        
        if not is_covered:
            result = {
                "approved_amount": 0.0,
                "calculation": "Claim not covered by policy",
                "deductible_applied": 0.0,
                "coverage_limit_applied": False
            }
            return json.dumps(result, indent=2)
        
        # Apply coverage limit
        amount_after_limit = min(claim_amount, coverage_limit)
        coverage_limit_applied = claim_amount > coverage_limit
        
        # Apply deductible
        approved_amount = max(0.0, amount_after_limit - deductible)
        
        calculation = f"Claim: ${claim_amount:,.2f}"
        if coverage_limit_applied:
            calculation += f" → Limited to coverage: ${coverage_limit:,.2f}"
        calculation += f" → Minus deductible: ${deductible:,.2f} → Approved: ${approved_amount:,.2f}"
        
        result = {
            "approved_amount": round(approved_amount, 2),
            "calculation": calculation,
            "deductible_applied": deductible,
            "coverage_limit_applied": coverage_limit_applied
        }
        
        logger.info(f"Approved amount: ${approved_amount:,.2f}")
        return json.dumps(result, indent=2)
