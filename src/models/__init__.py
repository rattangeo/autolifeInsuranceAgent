"""Models package."""

from .claim import (
    Claim,
    ClaimInformation,
    ClaimType,
    ClaimStatus,
    PolicyCoverageCheck,
    FraudAssessment,
    FraudRiskLevel,
    ClaimRecommendation
)
from .policy import Policy, Coverage, CoverageType, PolicyStatus

__all__ = [
    'Claim',
    'ClaimInformation',
    'ClaimType',
    'ClaimStatus',
    'PolicyCoverageCheck',
    'FraudAssessment',
    'FraudRiskLevel',
    'ClaimRecommendation',
    'Policy',
    'Coverage',
    'CoverageType',
    'PolicyStatus'
]
