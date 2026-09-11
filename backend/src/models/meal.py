"""
Pydantic models for Meal tracking and Nutritional Summaries.
"""
from pydantic import BaseModel, Field
import datetime
from typing import List, Dict


class MealEntry(BaseModel):
    """A single logged meal item/dish."""
    dish_id: str = Field(..., description="Unique identifier for the dish")
    dish_name: str = Field(..., description="Name of the dish")
    servings: float = Field(1.0, description="Number of servings consumed")
    serving_size_g: float = Field(100.0, description="Weight of one serving in grams")
    
    model_config = {"from_attributes": True}


class MealLog(BaseModel):
    """A daily log of meals for a child."""
    child_id: str = Field(..., description="Child identifier")
    date: datetime.date = Field(..., description="Date of the meal log")
    meals: List[MealEntry] = Field(default_factory=list, description="Meals consumed on this date")
    
    model_config = {"from_attributes": True}


class NutrientSummary(BaseModel):
    """Aggregated nutritional summary."""
    total_energy_kcal: float = Field(0.0, description="Total energy in kcal")
    total_protein_g: float = Field(0.0, description="Total protein in grams")
    total_fat_g: float = Field(0.0, description="Total fat in grams")
    total_carbs_g: float = Field(0.0, description="Total carbohydrates in grams")
    total_fiber_g: float = Field(0.0, description="Total dietary fiber in grams")
    total_sugar_g: float = Field(0.0, description="Total sugar in grams")
    total_calcium_mg: float = Field(0.0, description="Total calcium in milligrams")
    total_iron_mg: float = Field(0.0, description="Total iron in milligrams")
    total_zinc_mg: float = Field(0.0, description="Total zinc in milligrams")
    total_vitamin_c_mg: float = Field(0.0, description="Total vitamin C in milligrams")
    total_thiamin_mg: float = Field(0.0, description="Total thiamin in milligrams")
    total_folate_mcg: float = Field(0.0, description="Total folate in micrograms")
    avg_glycemic_index: float = Field(0.0, description="Average Glycemic Index")
    nova_breakdown: Dict[int, float] = Field(default_factory=dict, description="Percentage of meals in each NOVA group (1-4)")
    
    model_config = {"from_attributes": True}
