from typing import Dict, List

def triangular_mf(x: float, a: float, b: float, c: float) -> float:
    """Triangular membership function. a=left foot, b=peak, c=right foot.
    Returns membership degree [0, 1]."""
    if x <= a or x >= c:
        return 0.0
    if a == b:
        if x <= b:
            return 1.0
        return (c - x) / (c - b)
    if b == c:
        if x >= b:
            return 1.0
        return (x - a) / (b - a)
    if x <= b:
        return (x - a) / (b - a)
    return (c - x) / (c - b)

def trapezoidal_mf(x: float, a: float, b: float, c: float, d: float) -> float:
    """Trapezoidal membership function. a=left foot, b=left shoulder, c=right shoulder, d=right foot."""
    if x <= a or x >= d:
        return 0.0
    if x >= b and x <= c:
        return 1.0
    if x < b:
        if a == b: return 1.0
        return (x - a) / (b - a)
    # x > c
    if c == d: return 1.0
    return (d - x) / (d - c)

def left_shoulder_mf(x: float, a: float, b: float) -> float:
    """Left shoulder membership function. 1.0 at <=a, linear to 0 at b."""
    if x <= a:
        return 1.0
    if x >= b:
        return 0.0
    return (b - x) / (b - a)

def right_shoulder_mf(x: float, a: float, b: float) -> float:
    """Right shoulder membership function. 0.0 at <=a, linear to 1.0 at >=b."""
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    return (x - a) / (b - a)

def fuzzify_value(value: float, fuzzy_sets: Dict[str, Dict]) -> Dict[str, float]:
    """Fuzzify a single numeric value against configured fuzzy sets.
    Each fuzzy set in the config has 'type' (triangular/trapezoidal/left_shoulder/right_shoulder)
    and 'params' (list of floats).
    Returns dict of {set_name: membership_degree}, only including non-zero memberships."""
    memberships = {}
    for set_name, set_config in fuzzy_sets.items():
        mf_type = set_config.get("type")
        params = set_config.get("params", [])
        
        val = 0.0
        if mf_type == "triangular" and len(params) == 3:
            val = triangular_mf(value, *params)
        elif mf_type == "trapezoidal" and len(params) == 4:
            val = trapezoidal_mf(value, *params)
        elif mf_type == "left_shoulder" and len(params) == 2:
            val = left_shoulder_mf(value, *params)
        elif mf_type == "right_shoulder" and len(params) == 2:
            val = right_shoulder_mf(value, *params)
            
        if val > 0:
            memberships[set_name] = val
            
    return memberships

def fuzzify_categorical(value: str, category_map: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """Fuzzify a categorical value (like growth_trend) using direct mapping.
    E.g., 'declining' -> {'declining': 1.0, 'stable': 0.0, 'improving': 0.0}"""
    if value in category_map:
        return {k: v for k, v in category_map[value].items() if v > 0}
    return {}

def fuzzify_child_inputs(weight_for_height_z: float, muac_cm: float, growth_trend: str, config: Dict) -> Dict[str, Dict[str, float]]:
    """Fuzzify all anthropometric inputs. Returns dict of {field_name: {set: membership}}."""
    result = {}
    fuzzy_sets_config = config.get("fuzzy_sets", {})
    
    if "weight_for_height_z" in fuzzy_sets_config:
        result["weight_for_height_z"] = fuzzify_value(weight_for_height_z, fuzzy_sets_config["weight_for_height_z"])
        
    if "muac_cm" in fuzzy_sets_config:
        result["muac_cm"] = fuzzify_value(muac_cm, fuzzy_sets_config["muac_cm"])
        
    categorical_sets_config = config.get("categorical_sets", {})
    if "growth_trend" in categorical_sets_config:
        result["growth_trend"] = fuzzify_categorical(growth_trend, categorical_sets_config["growth_trend"])
        
    return result

def fuzzify_dietary_inputs(nutrient_summary: Dict, child_age_months: int, config: Dict, rda_config: Dict) -> Dict[str, Dict[str, float]]:
    """Fuzzify dietary inputs (protein %RDA, sugar, iron %RDA, GI, NOVA).
    Computes %RDA from nutrient_summary and rda_config for the child's age group."""
    result = {}
    
    # Determine age group for RDA lookup
    age_group = "age_4_6"
    for group, bounds in rda_config.get("age_groups", {}).items():
        if bounds[0] <= child_age_months <= bounds[1]:
            age_group = group
            break
            
    rda_values = rda_config.get("rda_values", {}).get(age_group, {})
    fuzzy_sets_config = config.get("fuzzy_sets", {})
    
    # Check protein %RDA
    protein_val = nutrient_summary.get("protein", nutrient_summary.get("total_protein_g", None))
    if protein_val is not None:
        protein_rda = rda_values.get("protein", 16.0)
        pct_rda = (float(protein_val) / protein_rda) * 100.0 if protein_rda > 0 else 0.0
        if "protein_pct_rda" in fuzzy_sets_config:
            result["protein_pct_rda"] = fuzzify_value(pct_rda, fuzzy_sets_config["protein_pct_rda"])

    # Check iron %RDA
    iron_val = nutrient_summary.get("iron", nutrient_summary.get("total_iron_mg", None))
    if iron_val is not None:
        iron_rda = rda_values.get("iron", 11.0)
        pct_rda = (float(iron_val) / iron_rda) * 100.0 if iron_rda > 0 else 0.0
        if "iron_pct_rda" in fuzzy_sets_config:
            result["iron_pct_rda"] = fuzzify_value(pct_rda, fuzzy_sets_config["iron_pct_rda"])
                
    # Fuzzify sugar
    sugar_val = nutrient_summary.get("sugar_g", nutrient_summary.get("total_sugar_g", None))
    if sugar_val is not None and "sugar_g" in fuzzy_sets_config:
        result["sugar_g"] = fuzzify_value(float(sugar_val), fuzzy_sets_config["sugar_g"])

    # Fuzzify GI
    gi_val = nutrient_summary.get("gi_score", nutrient_summary.get("avg_glycemic_index", None))
    if gi_val is not None and "gi_score" in fuzzy_sets_config:
        result["gi_score"] = fuzzify_value(float(gi_val), fuzzy_sets_config["gi_score"])

    # Fuzzify NOVA
    nova_val = nutrient_summary.get("nova_score", None)
    if nova_val is None and "nova_breakdown" in nutrient_summary:
        bd = nutrient_summary["nova_breakdown"]
        tot = sum(bd.values()) if isinstance(bd, dict) else 0
        if tot > 0:
            nova_val = sum(float(k) * float(v) for k, v in bd.items()) / tot
    if nova_val is not None and "nova_score" in fuzzy_sets_config:
        result["nova_score"] = fuzzify_value(float(nova_val), fuzzy_sets_config["nova_score"])
            
    return result

