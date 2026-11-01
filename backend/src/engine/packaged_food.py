"""
Packaged Food Module.

Validates barcodes and converts an Open Food Facts product into the same per-100 g
row format as the Indian Dishes dataset, so packaged foods can be logged, summed
and alerted on exactly like home-cooked dishes.
"""
from typing import Dict, Any, Optional, List


def normalize_barcode(raw: str, config: Dict[str, Any]) -> Optional[str]:
    """Return the barcode as digits only, or None if it is not a plausible EAN/UPC."""
    digits = "".join(ch for ch in (raw or "") if ch.isdigit())
    bounds = config["barcode"]
    if not (bounds["min_digits"] <= len(digits) <= bounds["max_digits"]):
        return None
    if len(digits) != len((raw or "").strip().replace(" ", "").replace("-", "")):
        return None  # letters or other symbols mixed in
    return digits


def _num(nutriments: Dict[str, Any], key: str) -> Optional[float]:
    value = nutriments.get(key)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _grams_to_mg(value: Optional[float]) -> float:
    return round(value * 1000.0, 2) if value is not None else 0.0


def map_allergens(tags: List[str], tag_map: Dict[str, str]) -> List[str]:
    """Map Open Food Facts tags (e.g. 'en:milk') to our allergen group names."""
    return sorted({tag_map[t] for t in tags or [] if t in tag_map})


def normalize_off_product(
    product: Dict[str, Any],
    barcode: str,
    config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Convert an OFF 'product' object to a dish-like row. None if it has no calorie data."""
    n = product.get("nutriments") or {}
    energy = _num(n, "energy-kcal_100g")
    if energy is None and _num(n, "energy_100g") is not None:
        energy = _num(n, "energy_100g") / 4.184  # kJ -> kcal
    if energy is None:
        return None

    # Sodium is reported in grams; fall back to salt (salt = sodium x 2.5)
    sodium_g = _num(n, "sodium_100g")
    if sodium_g is None and _num(n, "salt_100g") is not None:
        sodium_g = _num(n, "salt_100g") / 2.5

    sugars = _num(n, "sugars_100g")
    added = _num(n, "added-sugars_100g")
    if added is None and config["treat_unknown_sugar_as_added"]:
        added = sugars

    name = (product.get("product_name") or "").strip() or f"Packaged product {barcode}"
    brand = (product.get("brands") or "").split(",")[0].strip()
    if brand and brand.lower() not in name.lower():
        name = f"{name} ({brand})"

    serving = _num(product, "serving_quantity")
    nova = product.get("nova_group") or config["default_nova_group"]

    return {
        "record_id": f"OFF-{barcode}",
        "barcode": barcode,
        "dish_name": name,
        "category": config["default_category"],
        "energy_kcal": round(energy, 1),
        "protein_g": _num(n, "proteins_100g") or 0.0,
        "total_fat_g": _num(n, "fat_100g") or 0.0,
        "carbohydrate_g": _num(n, "carbohydrates_100g") or 0.0,
        "dietary_fiber_g": _num(n, "fiber_100g") or 0.0,
        "sugars_g": sugars or 0.0,
        "added_sugars_g": added,
        "calcium_mg": _grams_to_mg(_num(n, "calcium_100g")),
        "iron_mg": _grams_to_mg(_num(n, "iron_100g")),
        "zinc_mg": _grams_to_mg(_num(n, "zinc_100g")),
        "sodium_mg": _grams_to_mg(sodium_g),
        "vitamin_c_mg": _grams_to_mg(_num(n, "vitamin-c_100g")),
        "thiamin_mg": _grams_to_mg(_num(n, "vitamin-b1_100g")),
        "folate_mcg": round((_num(n, "folates_100g") or 0.0) * 1_000_000, 1),
        "glycemic_index": None,
        "nova_group": int(nova),
        "serving_g": serving if serving and serving > 0 else float(config["default_serving_g"]),
        "allergens": map_allergens(product.get("allergens_tags"), config["allergen_tags"]),
    }
