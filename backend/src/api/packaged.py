import yaml
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from src.auth.users import get_current_user
from src.db.packaged_products import get_cached_product, save_product
from src.engine.packaged_food import normalize_barcode, normalize_off_product
from src.engine.food_alerts import meal_totals, build_alerts
from src.integrations.open_food_facts import fetch_product, OpenFoodFactsError
from src.models.food_scan import PackagedProductResponse

router = APIRouter(prefix="/api", tags=["packaged-food"], dependencies=[Depends(get_current_user)])

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
PACKAGED_PATH = CONFIG_DIR / "packaged_food.yaml"
SCANNER_PATH = CONFIG_DIR / "food_scanner.yaml"
RDA_PATH = CONFIG_DIR / "rda_children.yaml"
SOURCE = "openfoodfacts"


def _load_configs():
    configs = []
    for path in (PACKAGED_PATH, SCANNER_PATH, RDA_PATH):
        with open(path, "r", encoding="utf-8") as f:
            configs.append(yaml.safe_load(f))
    return configs


@router.get("/packaged/{barcode}", response_model=PackagedProductResponse)
async def lookup_packaged(barcode: str, age_months: Optional[int] = None):
    """Look up a packaged food by barcode (cached, else Open Food Facts) with per-serving alerts."""
    packaged_cfg, scanner_cfg, rda_cfg = _load_configs()

    code = normalize_barcode(barcode, packaged_cfg)
    if code is None:
        raise HTTPException(status_code=422, detail="That does not look like a product barcode (8-14 digits).")

    product = await get_cached_product(code, packaged_cfg["cache_days"])
    cached = product is not None
    if not cached:
        try:
            raw = await fetch_product(code, packaged_cfg)
        except OpenFoodFactsError as e:
            raise HTTPException(status_code=e.status_code, detail=str(e))
        if raw is None:
            raise HTTPException(status_code=404, detail="This product is not in Open Food Facts yet.")
        normalized = normalize_off_product(raw, code, packaged_cfg)
        if normalized is None:
            raise HTTPException(status_code=404, detail="This product has no nutrition information in Open Food Facts.")
        product = await save_product(normalized, SOURCE)

    parts = [{"dish": product, "grams": product["serving_g"]}]
    totals = meal_totals(parts, scanner_cfg["alerts"]["added_sugar_ingredients"])
    alerts = build_alerts(totals, parts, age_months, rda_cfg, scanner_cfg)
    # One packaged snack is not a meal: "low protein" would fire on almost every serving
    alerts = [a for a in alerts if a["type"] != "low_protein"]
    return {
        "product": product,
        "cached": cached,
        "serving_totals": totals,
        "alerts": alerts,
    }
