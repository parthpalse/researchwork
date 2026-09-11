"""
Dietary Risk and Nutrient Aggregation Module.

Aggregates nutritional intake from meal entries (dishes from the Indian Dishes dataset),
calculates key metrics (total energy, protein, sugars, iron, weighted Glycemic Index, NOVA breakdown),
and evaluates nutrient gaps / excess against ICMR 2020 RDA for children ages 4-10.
"""
from typing import Dict, List, Any, Optional
import math


def calculate_nutrient_summary(
    meals: List[Dict[str, Any]],
    dish_lookup: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """Calculate aggregated daily nutrients from consumed dishes.

    Args:
        meals: List of dicts with keys 'dish_id', 'servings' (float), 'serving_size_g' (float, default 100g)
        dish_lookup: Dict mapping dish_id -> dish record dict with nutrient values per 100g

    Returns:
        Aggregated nutrient summary dictionary matching NutrientSummary model.
    """
    totals = {
        "total_energy_kcal": 0.0,
        "total_protein_g": 0.0,
        "total_fat_g": 0.0,
        "total_carbs_g": 0.0,
        "total_fiber_g": 0.0,
        "total_sugar_g": 0.0,
        "total_calcium_mg": 0.0,
        "total_iron_mg": 0.0,
        "total_zinc_mg": 0.0,
        "total_vitamin_c_mg": 0.0,
        "total_thiamin_mg": 0.0,
        "total_folate_mcg": 0.0,
        "avg_glycemic_index": 0.0,
        "nova_breakdown": {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
    }

    if not meals:
        return totals

    total_weight_g = 0.0
    total_carb_weighted_gi = 0.0
    total_carbs_for_gi = 0.0
    nova_counts: Dict[int, float] = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
    total_servings = 0.0

    for meal in meals:
        dish_id = meal.get("dish_id")
        servings = float(meal.get("servings", 1.0))
        serving_size_g = float(meal.get("serving_size_g", 100.0))
        dish = dish_lookup.get(dish_id)

        if not dish:
            continue

        # Proportion of 100g standard portion
        factor = servings * (serving_size_g / 100.0)
        total_weight_g += servings * serving_size_g
        total_servings += servings

        totals["total_energy_kcal"] += float(dish.get("energy_kcal", 0.0) or 0.0) * factor
        totals["total_protein_g"] += float(dish.get("protein_g", 0.0) or 0.0) * factor
        totals["total_fat_g"] += float(dish.get("total_fat_g", 0.0) or 0.0) * factor
        totals["total_carbs_g"] += float(dish.get("carbohydrate_g", 0.0) or 0.0) * factor
        totals["total_fiber_g"] += float(dish.get("dietary_fiber_g", 0.0) or 0.0) * factor
        totals["total_sugar_g"] += float(dish.get("sugars_g", 0.0) or 0.0) * factor
        totals["total_calcium_mg"] += float(dish.get("calcium_mg", 0.0) or 0.0) * factor
        totals["total_iron_mg"] += float(dish.get("iron_mg", 0.0) or 0.0) * factor
        totals["total_zinc_mg"] += float(dish.get("zinc_mg", 0.0) or 0.0) * factor
        totals["total_vitamin_c_mg"] += float(dish.get("vitamin_c_mg", 0.0) or 0.0) * factor
        totals["total_thiamin_mg"] += float(dish.get("thiamin_mg", 0.0) or 0.0) * factor
        totals["total_folate_mcg"] += float(dish.get("folate_mcg", 0.0) or 0.0) * factor

        carbs = float(dish.get("carbohydrate_g", 0.0) or 0.0) * factor
        gi = float(dish.get("glycemic_index", 0.0) or 0.0)
        if carbs > 0 and gi > 0:
            total_carb_weighted_gi += gi * carbs
            total_carbs_for_gi += carbs

        nova = int(dish.get("nova_group", 1) or 1)
        nova_counts[nova] = nova_counts.get(nova, 0.0) + servings

    # Weighted Glycemic Index by carbohydrate contribution
    if total_carbs_for_gi > 0:
        totals["avg_glycemic_index"] = round(total_carb_weighted_gi / total_carbs_for_gi, 1)
    else:
        totals["avg_glycemic_index"] = 0.0

    # Percentage breakdown of meals in each NOVA group
    if total_servings > 0:
        totals["nova_breakdown"] = {
            k: round((count / total_servings) * 100.0, 1)
            for k, count in nova_counts.items()
        }

    # Round all scalar sums for clean readability
    for k in [
        "total_energy_kcal", "total_protein_g", "total_fat_g", "total_carbs_g",
        "total_fiber_g", "total_sugar_g", "total_calcium_mg", "total_iron_mg",
        "total_zinc_mg", "total_vitamin_c_mg", "total_thiamin_mg", "total_folate_mcg"
    ]:
        totals[k] = round(totals[k], 2)

    return totals


def get_dietary_fuzzy_inputs(
    nutrient_summary: Dict[str, Any],
    child_age_months: int,
    rda_config: Dict[str, Any]
) -> Dict[str, float]:
    """Convert aggregated nutrient summary into raw numeric inputs ready for fuzzification.

    Returns dict suitable for fuzzy set evaluation:
        protein_pct_rda, iron_pct_rda, sugar_g, gi_score, nova_score
    """
    # Determine age group
    age_group = "age_4_6"
    for group, bounds in rda_config.get("age_groups", {}).items():
        if bounds[0] <= child_age_months <= bounds[1]:
            age_group = group
            break

    rda_vals = rda_config.get("rda_values", {}).get(age_group, {})
    protein_rda = rda_vals.get("protein", 16.0)
    iron_rda = rda_vals.get("iron", 11.0)

    total_protein = nutrient_summary.get("total_protein_g", 0.0)
    total_iron = nutrient_summary.get("total_iron_mg", 0.0)
    total_sugar = nutrient_summary.get("total_sugar_g", 0.0)
    avg_gi = nutrient_summary.get("avg_glycemic_index", 50.0)

    # Average NOVA score weighted by breakdown
    nova_breakdown = nutrient_summary.get("nova_breakdown", {})
    weighted_nova = 1.0
    if nova_breakdown:
        total_pct = sum(nova_breakdown.values())
        if total_pct > 0:
            weighted_nova = sum(group * pct for group, pct in nova_breakdown.items()) / total_pct

    protein_pct = (total_protein / protein_rda) * 100.0 if protein_rda > 0 else 0.0
    iron_pct = (total_iron / iron_rda) * 100.0 if iron_rda > 0 else 0.0

    return {
        "protein": total_protein,
        "protein_pct_rda": round(protein_pct, 1),
        "iron": total_iron,
        "iron_pct_rda": round(iron_pct, 1),
        "sugar_g": round(total_sugar, 1),
        "gi_score": round(avg_gi, 1),
        "nova_score": round(weighted_nova, 2),
        "nova_breakdown": {str(k): v for k, v in nova_breakdown.items()}
    }
