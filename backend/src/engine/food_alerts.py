"""
Food Alerts Module.

Turns the matched dishes of one scanned meal into nutrient totals and gentle,
child-specific alerts: high sugar, high sodium, low protein and allergens.
All limits come from rda_children.yaml and food_scanner.yaml.
"""
from typing import Dict, List, Any, Optional

# Dataset column -> meal total key
_NUTRIENT_FIELDS = {
    "energy_kcal": "energy_kcal",
    "protein_g": "protein_g",
    "total_fat_g": "fat_g",
    "carbohydrate_g": "carbs_g",
    "dietary_fiber_g": "fiber_g",
    "sugars_g": "sugar_g",
    "sodium_mg": "sodium_mg",
}


def meal_totals(parts: List[Dict[str, Any]]) -> Dict[str, float]:
    """Sum nutrients of matched parts. Each part: {'dish': row per 100 g, 'grams': float}."""
    totals = {key: 0.0 for key in _NUTRIENT_FIELDS.values()}
    for part in parts:
        dish = part.get("dish")
        if not dish:
            continue
        factor = float(part.get("grams", 0.0)) / 100.0
        for column, key in _NUTRIENT_FIELDS.items():
            totals[key] += float(dish.get(column, 0.0) or 0.0) * factor
    return {key: round(value, 1) for key, value in totals.items()}


def age_group_for(age_months: Optional[int], rda_config: Dict[str, Any]) -> str:
    """Age group key for a child. Unknown age uses the youngest group (most cautious)."""
    groups = rda_config.get("age_groups", {})
    if age_months is not None:
        for group, bounds in groups.items():
            if bounds[0] <= age_months <= bounds[1]:
                return group
    return min(groups, key=lambda g: groups[g][0]) if groups else "age_4_6"


def find_allergens(parts: List[Dict[str, Any]], allergen_map: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Map allergen group -> sorted list of ingredients/fats in the meal that contain it."""
    found: Dict[str, set] = {}
    for part in parts:
        dish = part.get("dish")
        if not dish:
            continue
        sources = {dish.get("base_ingredient"), dish.get("fat_medium")}
        for allergen, members in allergen_map.items():
            hits = sources.intersection(members)
            if hits:
                found.setdefault(allergen, set()).update(hits)
    return {allergen: sorted(hits) for allergen, hits in found.items()}


def build_alerts(
    totals: Dict[str, float],
    parts: List[Dict[str, Any]],
    age_months: Optional[int],
    rda_config: Dict[str, Any],
    scanner_config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Return a list of alerts for one meal, using the child's daily limits."""
    alert_cfg = scanner_config["alerts"]
    share = alert_cfg["meal_share_of_day"]
    group = age_group_for(age_months, rda_config)
    rda = rda_config.get("rda_values", {}).get(group, {})
    upper = rda_config.get("daily_upper_limits", {}).get(group, {})

    alerts: List[Dict[str, Any]] = []

    sugar_limit = rda.get("sugar")
    if sugar_limit and totals["sugar_g"] > sugar_limit * share:
        alerts.append({
            "type": "high_sugar",
            "value": totals["sugar_g"],
            "meal_limit": round(sugar_limit * share, 1),
            "message": (
                f"This meal has about {totals['sugar_g']} g of sugar — more than a third of "
                f"the day's {sugar_limit:g} g limit for this age. Fruit or a smaller sweet "
                f"portion can help balance the day."
            ),
        })

    sodium_limit = upper.get("sodium_mg")
    if sodium_limit and totals["sodium_mg"] > sodium_limit * share:
        alerts.append({
            "type": "high_sodium",
            "value": totals["sodium_mg"],
            "meal_limit": round(sodium_limit * share, 1),
            "message": (
                f"This meal has about {totals['sodium_mg']:g} mg of sodium — more than a third "
                f"of the day's {sodium_limit:g} mg limit for this age. Less salt or pickle in "
                f"the next meal keeps the day on track."
            ),
        })

    protein_rda = rda.get("protein")
    if protein_rda:
        protein_floor = protein_rda * share * alert_cfg["low_protein_ratio"]
        if totals["protein_g"] < protein_floor:
            alerts.append({
                "type": "low_protein",
                "value": totals["protein_g"],
                "meal_limit": round(protein_floor, 1),
                "message": (
                    f"This meal has about {totals['protein_g']} g of protein. Adding dal, curd, "
                    f"paneer, egg or sprouts would help your child grow strong."
                ),
            })

    for allergen, sources in find_allergens(parts, alert_cfg["allergens"]).items():
        alerts.append({
            "type": "allergen",
            "allergen": allergen,
            "sources": sources,
            "message": (
                f"Contains {allergen.lower()} (from {', '.join(sources)}). "
                f"Please skip it if your child is allergic."
            ),
        })

    return alerts
