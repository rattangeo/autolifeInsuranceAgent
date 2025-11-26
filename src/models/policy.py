"""
Data models for insurance policies.
"""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class CoverageType(str, Enum):
    """Types of insurance coverage."""
    # Auto
    AUTO_COLLISION = "auto_collision"
    AUTO_COMPREHENSIVE = "auto_comprehensive"
    AUTO_LIABILITY = "auto_liability"
    
    # Home
    HOME_PROPERTY = "home_property"
    HOME_THEFT = "home_theft"
    HOME_NATURAL_DISASTER = "home_natural_disaster"
    HOME_LIABILITY = "home_liability"
    
    # Health
    HEALTH_EMERGENCY = "health_emergency"
    HEALTH_HOSPITALIZATION = "health_hospitalization"
    HEALTH_PRESCRIPTION = "health_prescription"
    HEALTH_PREVENTIVE = "health_preventive"
    
    # Life
    LIFE_TERM = "life_term"
    LIFE_WHOLE = "life_whole"


class PolicyStatus(str, Enum):
    """Policy status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class Coverage(BaseModel):
    """Individual coverage details."""
    coverage_type: CoverageType = Field(description="Type of coverage")
    coverage_limit: float = Field(description="Maximum coverage amount")
    deductible: float = Field(description="Deductible amount")
    description: str = Field(description="Coverage description")


class Policy(BaseModel):
    """Insurance policy definition."""
    policy_number: str = Field(description="Unique policy identifier")
    policy_type: str = Field(description="Type of policy (auto, home, health, life)")
    policyholder: str = Field(description="Name of policyholder")
    status: PolicyStatus = Field(description="Current policy status")
    effective_date: datetime = Field(description="Policy start date")
    expiry_date: datetime = Field(description="Policy end date")
    coverages: List[Coverage] = Field(description="List of coverages included")
    annual_premium: float = Field(description="Annual premium amount")
    
    def is_active(self) -> bool:
        """Check if policy is currently active."""
        now = datetime.now()
        return (
            self.status == PolicyStatus.ACTIVE
            and self.effective_date <= now <= self.expiry_date
        )
    
    def get_coverage(self, coverage_type: CoverageType) -> Optional[Coverage]:
        """Get specific coverage if exists."""
        for coverage in self.coverages:
            if coverage.coverage_type == coverage_type:
                return coverage
        return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "policy_number": self.policy_number,
            "policy_type": self.policy_type,
            "policyholder": self.policyholder,
            "status": self.status.value,
            "effective_date": self.effective_date.isoformat(),
            "expiry_date": self.expiry_date.isoformat(),
            "coverages": [
                {
                    "type": c.coverage_type.value,
                    "limit": c.coverage_limit,
                    "deductible": c.deductible,
                    "description": c.description
                }
                for c in self.coverages
            ],
            "annual_premium": self.annual_premium
        }
