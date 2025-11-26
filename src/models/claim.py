"""
Data models for insurance claims.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ClaimType(str, Enum):
    """Types of insurance claims."""
    AUTO = "auto"
    HOME = "home"
    HEALTH = "health"
    LIFE = "life"


class ClaimStatus(str, Enum):
    """Claim processing status."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    NEEDS_REVIEW = "needs_review"


class FraudRiskLevel(str, Enum):
    """Fraud risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ClaimInformation(BaseModel):
    """Structured claim information extracted from claim text."""
    policy_number: str = Field(description="Insurance policy number")
    claim_type: ClaimType = Field(description="Type of insurance claim")
    incident_date: datetime = Field(description="Date of incident")
    claim_amount: float = Field(description="Claimed amount in dollars", gt=0)
    description: str = Field(description="Description of the incident")
    claimant_name: Optional[str] = Field(default=None, description="Name of claimant")
    location: Optional[str] = Field(default=None, description="Location of incident")
    
    @field_validator('claim_amount')
    @classmethod
    def validate_amount(cls, v: float) -> float:
        """Ensure claim amount is positive and reasonable."""
        if v <= 0:
            raise ValueError("Claim amount must be positive")
        if v > 10_000_000:
            raise ValueError("Claim amount exceeds maximum allowed")
        return round(v, 2)


class PolicyCoverageCheck(BaseModel):
    """Results of policy coverage validation."""
    is_valid: bool = Field(description="Whether policy is valid and active")
    coverage_type: str = Field(description="Type of coverage")
    coverage_limit: float = Field(description="Maximum coverage amount")
    deductible: float = Field(description="Policy deductible amount")
    is_covered: bool = Field(description="Whether claim type is covered")
    reason: str = Field(description="Explanation of coverage decision")
    policy_expiry: Optional[datetime] = Field(default=None, description="Policy expiration date")


class FraudAssessment(BaseModel):
    """Fraud risk assessment results."""
    risk_level: FraudRiskLevel = Field(description="Overall risk level")
    risk_score: float = Field(description="Risk score from 0-100", ge=0, le=100)
    indicators: List[str] = Field(description="List of fraud indicators found")
    recommendation: str = Field(description="Recommendation based on assessment")
    requires_investigation: bool = Field(description="Whether manual investigation needed")


class ClaimRecommendation(BaseModel):
    """Final claim processing recommendation."""
    status: ClaimStatus = Field(description="Recommended claim status")
    approved_amount: float = Field(description="Approved amount (0 if denied)", ge=0)
    reasoning: str = Field(description="Detailed reasoning for decision")
    confidence: float = Field(description="Confidence in decision (0-1)", ge=0, le=1)
    next_steps: List[str] = Field(description="Recommended next steps")
    processed_at: datetime = Field(default_factory=datetime.now)


class Claim(BaseModel):
    """Complete claim with all processing results."""
    raw_claim_text: str = Field(description="Original claim submission text")
    information: Optional[ClaimInformation] = None
    coverage_check: Optional[PolicyCoverageCheck] = None
    fraud_assessment: Optional[FraudAssessment] = None
    recommendation: Optional[ClaimRecommendation] = None
    processing_log: List[str] = Field(default_factory=list, description="Agent reasoning log")
    
    def add_log(self, message: str) -> None:
        """Add entry to processing log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.processing_log.append(f"[{timestamp}] {message}")
    
    def to_report(self) -> Dict[str, Any]:
        """Generate human-readable report."""
        return {
            "claim_summary": {
                "policy": self.information.policy_number if self.information else "N/A",
                "type": self.information.claim_type.value if self.information else "N/A",
                "amount": f"${self.information.claim_amount:,.2f}" if self.information else "N/A",
            },
            "decision": {
                "status": self.recommendation.status.value if self.recommendation else "pending",
                "approved_amount": f"${self.recommendation.approved_amount:,.2f}" if self.recommendation else "$0.00",
                "confidence": f"{self.recommendation.confidence * 100:.0f}%" if self.recommendation else "N/A",
            },
            "reasoning": self.recommendation.reasoning if self.recommendation else "Processing...",
            "fraud_risk": self.fraud_assessment.risk_level.value if self.fraud_assessment else "N/A",
            "next_steps": self.recommendation.next_steps if self.recommendation else [],
        }
