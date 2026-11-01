"""
Pydantic models for the Food Scanner (photo -> dishes -> nutrients -> alerts).
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class IdentifyFoodRequest(BaseModel):
    """A food photo sent by the client. The image is never stored."""
    image_base64: str = Field(..., description="Base64 image (optionally a data: URL)")
    mime_type: str = Field("image/jpeg", description="Image MIME type")
    age_months: Optional[int] = Field(None, ge=0, le=240, description="Child age for age-specific alerts")


class ScanDish(BaseModel):
    """Dataset row (values per 100 g) that a food component was matched to."""
    record_id: str
    dish_name: str
    category: str
    energy_kcal: float
    protein_g: float
    total_fat_g: float
    carbohydrate_g: float
    sugars_g: float
    sodium_mg: float


class FoodComponent(BaseModel):
    """One ingredient of an identified food, as described by the vision model and matched."""
    base_ingredient: str
    cooking_method: str
    fat_medium: str
    grams: float
    matched: bool
    confidence: float
    possible_match: bool
    energy_kcal: float = Field(0.0, description="Energy for this portion (not per 100 g)")
    dish: Optional[ScanDish] = None


class IdentifiedFood(BaseModel):
    """A food item seen in the photo, e.g. 'Aloo Paratha', with its components."""
    name: str
    model_confidence: float
    components: List[FoodComponent]


class MealTotals(BaseModel):
    """Nutrients for the matched portions of one meal."""
    energy_kcal: float
    protein_g: float
    fat_g: float
    carbs_g: float
    fiber_g: float
    sugar_g: float
    added_sugar_g: float = Field(0.0, description="Sugar from added sugar/jaggery only")
    sodium_mg: float


class FoodAlert(BaseModel):
    """A gentle, child-specific nutrition or allergen alert."""
    type: str
    message: str
    value: Optional[float] = None
    meal_limit: Optional[float] = None
    allergen: Optional[str] = None
    sources: Optional[List[str]] = None


class FoodScanResponse(BaseModel):
    """Result of scanning one photo."""
    is_food: bool
    model: str
    latency_ms: int
    items: List[IdentifiedFood]
    unmatched: List[str]
    totals: MealTotals
    alerts: List[FoodAlert]


class ScanSummaryItem(BaseModel):
    dish_id: str
    grams: float = Field(..., gt=0, le=2000)


class ScanSummaryRequest(BaseModel):
    """Recalculate totals/alerts after the parent edits grams or removes items."""
    items: List[ScanSummaryItem]
    age_months: Optional[int] = Field(None, ge=0, le=240)


class ScanSummaryResponse(BaseModel):
    totals: MealTotals
    alerts: List[FoodAlert]


class PackagedProduct(BaseModel):
    """A packaged food from Open Food Facts, in the dish format (values per 100 g)."""
    record_id: str = Field(..., description="'OFF-<barcode>', usable as a meal-log dish_id")
    barcode: str
    dish_name: str
    category: str
    energy_kcal: float
    protein_g: float
    total_fat_g: float
    carbohydrate_g: float
    dietary_fiber_g: float = 0.0
    sugars_g: float = 0.0
    added_sugars_g: Optional[float] = None
    sodium_mg: float = 0.0
    nova_group: int
    serving_g: float
    allergens: List[str]
    source: str
    fetched_at: str


class PackagedProductResponse(BaseModel):
    product: PackagedProduct
    cached: bool
    serving_totals: MealTotals
    alerts: List[FoodAlert]
