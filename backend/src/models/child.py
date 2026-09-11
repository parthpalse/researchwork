"""
Pydantic models for Child data.
"""
from enum import Enum
import datetime
from typing import Literal, List
from pydantic import BaseModel, Field


class GrowthTrend(str, Enum):
    """Enumeration of possible growth trends."""
    improving = "improving"
    stable = "stable"
    declining = "declining"


class WeightReading(BaseModel):
    """A historical weight reading."""
    date: datetime.date = Field(..., description="Date of the reading")
    weight_kg: float = Field(..., description="Weight in kilograms")
    
    model_config = {"from_attributes": True}


class ChildInput(BaseModel):
    """Input data for a child assessment."""
    child_id: str = Field(..., description="Unique identifier for the child")
    age_months: int = Field(..., ge=48, le=120, description="Age in months (4-10 years)")
    sex: Literal['M', 'F'] = Field(..., description="Biological sex")
    weight_kg: float = Field(..., gt=0, description="Current weight in kilograms")
    height_cm: float = Field(..., gt=0, description="Current height in centimeters")
    muac_cm: float = Field(..., gt=0, description="Mid-upper arm circumference in centimeters")
    growth_trend: GrowthTrend = Field(..., description="Recent growth trend")
    recent_weight_history: List[WeightReading] = Field(default_factory=list, description="Recent weight readings")

    model_config = {"from_attributes": True}


class ChildRecord(ChildInput):
    """A persistent child record including calculated fields."""
    weight_for_height_z: float = Field(..., description="Calculated weight-for-height Z-score")
    muac_risk_band: str = Field(..., description="Categorized MUAC risk band")
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), description="Record creation timestamp")
    
    model_config = {"from_attributes": True}
