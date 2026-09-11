"""
Pydantic models for Explainability and Rule Tracing.
"""
from pydantic import BaseModel, Field
import datetime
from typing import Dict, List, Optional


class FuzzificationResult(BaseModel):
    """Result of fuzzifying an input variable."""
    field_name: str = Field(..., description="Name of the input field (e.g., 'muac_cm')")
    memberships: Dict[str, float] = Field(..., description="Mapping of fuzzy set names to membership degrees [0, 1]")
    
    model_config = {"from_attributes": True}


class RuleFired(BaseModel):
    """Details of a fuzzy rule that was fired."""
    rule_id: str = Field(..., description="Identifier of the rule (e.g., 'R1')")
    antecedents: Dict[str, str] = Field(..., description="Conditions that triggered the rule")
    strength: float = Field(..., description="Firing strength of the rule based on input memberships")
    expert_cf: float = Field(..., description="Expert Certainty Factor associated with the rule")
    conclusion_category: str = Field(..., description="Risk category concluded by the rule")
    conclusion_level: str = Field(..., description="Specific level of the conclusion")
    
    model_config = {"from_attributes": True}


class CombinedConfidence(BaseModel):
    """Combined confidence scores across different risk categories."""
    high: float = Field(0.0, description="Confidence in high/severe risk")
    moderate: float = Field(0.0, description="Confidence in moderate risk")
    low: float = Field(0.0, description="Confidence in low risk")
    
    model_config = {"from_attributes": True}


class DietaryRisk(BaseModel):
    """Identified dietary risks."""
    nutrient_gaps: List[str] = Field(default_factory=list, description="List of nutrients below adequate levels")
    excess_nutrients: List[str] = Field(default_factory=list, description="List of nutrients above recommended levels")
    nova_breakdown: Dict[str, float] = Field(..., description="Percentage breakdown of diet by NOVA classification")
    avg_glycemic_index: Optional[float] = Field(None, description="Average Glycemic Index of the diet")
    
    model_config = {"from_attributes": True}


class TraceObject(BaseModel):
    """Comprehensive trace of the inference process for explainability."""
    child_id: str = Field(..., description="Child identifier")
    timestamp: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), description="Inference timestamp")
    fuzzification: Dict[str, Dict[str, float]] = Field(..., description="All fuzzification results by field name")
    rules_fired: List[RuleFired] = Field(..., description="List of all rules that fired")
    combined_confidence: CombinedConfidence = Field(..., description="Final combined confidences")
    dietary_risk: Optional[DietaryRisk] = Field(None, description="Dietary risk components if applicable")
    final_risk_level: str = Field(..., description="The ultimate risk determination")
    final_confidence: float = Field(..., description="Confidence in the final risk level")
    
    model_config = {"from_attributes": True}
