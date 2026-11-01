import time
import yaml
import base64
import binascii
from pathlib import Path
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException
from src.db.connection import get_db
from src.engine.food_match import build_dish_index, match_food_part
from src.engine.food_alerts import meal_totals, build_alerts
from src.llm.food_vision import identify_foods, FoodVisionError, OTHER_INGREDIENT
from src.models.food_scan import (
    IdentifyFoodRequest, FoodScanResponse, ScanSummaryRequest, ScanSummaryResponse,
)

router = APIRouter(prefix="/api", tags=["food-scanner"])

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
SCANNER_PATH = CONFIG_DIR / "food_scanner.yaml"
RDA_PATH = CONFIG_DIR / "rda_children.yaml"

DISH_COLUMNS = (
    "record_id, base_ingredient, dish_name, category, cooking_method, fat_medium, "
    "energy_kcal, protein_g, total_fat_g, carbohydrate_g, dietary_fiber_g, sugars_g, sodium_mg"
)

# Dish rows are read from the DB once and kept in memory (~20k small rows)
_dish_cache: Dict[str, Any] = {}


def _load_configs():
    with open(SCANNER_PATH, "r", encoding="utf-8") as f:
        scanner_cfg = yaml.safe_load(f)
    with open(RDA_PATH, "r", encoding="utf-8") as f:
        rda_cfg = yaml.safe_load(f)
    return scanner_cfg, rda_cfg


async def get_dish_index() -> Dict[str, Any]:
    """Return {'index', 'by_id', 'base_names', 'methods', 'fats'} built from the dishes table."""
    if _dish_cache:
        return _dish_cache

    async with get_db() as db:
        async with db.execute(f"SELECT {DISH_COLUMNS} FROM dishes") as cursor:
            rows = [dict(r) for r in await cursor.fetchall()]

    if not rows:
        raise HTTPException(status_code=503, detail="Dish database is empty. Restart the server to load it.")

    index = build_dish_index(rows)
    _dish_cache.update({
        "index": index,
        "by_id": {r["record_id"]: r for r in rows},
        "base_names": list(index.keys()),
        "methods": sorted({r["cooking_method"] for r in rows}),
        "fats": sorted({r["fat_medium"] for r in rows if r["fat_medium"]}),
    })
    return _dish_cache


def _decode_image(payload: IdentifyFoodRequest, image_cfg: Dict[str, Any]) -> str:
    """Validate the image and return clean base64 (no data: prefix)."""
    if payload.mime_type not in image_cfg["allowed_mime_types"]:
        raise HTTPException(status_code=415, detail=f"Unsupported image type: {payload.mime_type}")

    data = payload.image_base64
    if data.startswith("data:"):
        data = data.split(",", 1)[-1]

    try:
        raw = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=422, detail="Image is not valid base64.")

    if not raw:
        raise HTTPException(status_code=422, detail="Image is empty.")
    if len(raw) > image_cfg["max_bytes"]:
        raise HTTPException(status_code=413, detail="Image is too large. Please use a smaller photo.")
    return data


def _dish_summary(dish: Dict[str, Any]) -> Dict[str, Any]:
    keys = ("record_id", "dish_name", "category", "energy_kcal", "protein_g",
            "total_fat_g", "carbohydrate_g", "sugars_g", "sodium_mg")
    return {k: dish.get(k) if k in ("record_id", "dish_name", "category") else float(dish.get(k) or 0.0)
            for k in keys}


@router.post("/identify-food", response_model=FoodScanResponse)
async def identify_food(payload: IdentifyFoodRequest):
    """Identify foods in a photo, match them to the dish database and return nutrients + alerts.
    The image is only forwarded to the vision model; it is never saved."""
    started = time.perf_counter()
    scanner_cfg, rda_cfg = _load_configs()
    image_b64 = _decode_image(payload, scanner_cfg["image"])
    dishes = await get_dish_index()

    try:
        vision = await identify_foods(
            image_b64, payload.mime_type, dishes["base_names"],
            dishes["methods"], dishes["fats"], scanner_cfg,
        )
    except FoodVisionError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    items: List[Dict[str, Any]] = []
    unmatched: List[str] = []
    matched_parts: List[Dict[str, Any]] = []

    for item in vision.get("items", []) if vision.get("is_food") else []:
        model_confidence = float(item.get("confidence", 0.0))
        components = []
        for comp in item.get("components", []):
            part = {**comp, "model_confidence": model_confidence}
            if comp.get("base_ingredient") == OTHER_INGREDIENT:
                part["base_ingredient"] = None
            result = match_food_part(part, dishes["index"], scanner_cfg, dishes["base_names"])

            dish = result["dish"]
            components.append({
                "base_ingredient": comp.get("base_ingredient", ""),
                "cooking_method": comp.get("cooking_method", ""),
                "fat_medium": comp.get("fat_medium", ""),
                "grams": result["grams"],
                "matched": result["matched"],
                "confidence": result["confidence"],
                "possible_match": result["possible_match"],
                "energy_kcal": round(float(dish["energy_kcal"]) * result["grams"] / 100.0, 1) if dish else 0.0,
                "dish": _dish_summary(dish) if dish else None,
            })
            if dish:
                matched_parts.append({"dish": dish, "grams": result["grams"]})

        if components and not any(c["matched"] for c in components):
            unmatched.append(item.get("name", "Unknown food"))
        items.append({"name": item.get("name", "Unknown food"),
                      "model_confidence": model_confidence, "components": components})

    totals = meal_totals(matched_parts, scanner_cfg["alerts"]["added_sugar_ingredients"])
    alerts = build_alerts(totals, matched_parts, payload.age_months, rda_cfg, scanner_cfg)

    return {
        "is_food": bool(vision.get("is_food")),
        "model": vision.get("model", scanner_cfg["gemini"]["model"]),
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "items": items,
        "unmatched": unmatched,
        "totals": totals,
        "alerts": alerts,
    }


@router.post("/scan-summary", response_model=ScanSummaryResponse)
async def scan_summary(payload: ScanSummaryRequest):
    """Recalculate totals and alerts for the dishes/grams the parent confirmed."""
    scanner_cfg, rda_cfg = _load_configs()
    dishes = await get_dish_index()

    parts = []
    for item in payload.items:
        dish = dishes["by_id"].get(item.dish_id)
        if dish is None:
            raise HTTPException(status_code=404, detail=f"Unknown dish_id: {item.dish_id}")
        parts.append({"dish": dish, "grams": item.grams})

    totals = meal_totals(parts, scanner_cfg["alerts"]["added_sugar_ingredients"])
    return {"totals": totals, "alerts": build_alerts(totals, parts, payload.age_months, rda_cfg, scanner_cfg)}
