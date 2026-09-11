"""
Trace Builder — Orchestrates the full risk assessment pipeline.

Pipeline steps:
  1. Compute WHO z-score from weight/height/sex
  2. Fuzzify anthropometric inputs (z-score, MUAC, growth trend)
  3. Fuzzify dietary inputs if nutrient summary provided
  4. Merge all fuzzified values
  5. Fire rules against merged fuzzification
  6. Combine conclusions using MYCIN CF combination
  7. Determine final risk level
  8. Assemble spec-compliant TraceObject
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .fuzzy import fuzzify_child_inputs, fuzzify_dietary_inputs
from .rules import (
    Rule,
    combine_conclusions,
    determine_final_risk,
    fire_rules,
    load_rules,
)
from .zscore import classify_muac, compute_weight_for_height_z


def build_trace(
    child_input: Dict[str, Any],
    nutrient_summary: Optional[Dict[str, float]],
    config: Dict[str, Any],
    rda_config: Dict[str, Any],
) -> Dict[str, Any]:
    """Full risk assessment pipeline.

    Takes child anthropometric data + optional dietary data, runs the
    complete fuzzy logic pipeline, and returns a spec-compliant TraceObject
    dict ready for storage and LLM explanation.

    Args:
        child_input: Dict with keys from ChildInput model
            (child_id, age_months, sex, weight_kg, height_cm, muac_cm,
             growth_trend, recent_weight_history).
        nutrient_summary: Optional dict with aggregated daily nutrients
            (protein, iron, sugar_g, gi_score, nova_score, etc.).
            If None, only anthropometric risk is assessed.
        config: Loaded thresholds.yaml config dict.
        rda_config: Loaded rda_children.yaml config dict.

    Returns:
        Dict matching the TraceObject schema from the spec:
        {
            child_id, timestamp, fuzzification, rules_fired,
            combined_confidence, dietary_risk, final_risk_level,
            final_confidence
        }
    """
    child_id = child_input.get("child_id", "unknown")
    timestamp = datetime.now(timezone.utc).isoformat()

    # --- Step 1: Compute WHO z-score ---
    zscore_error = None
    try:
        wfh_z = compute_weight_for_height_z(
            weight_kg=child_input["weight_kg"],
            height_cm=child_input["height_cm"],
            sex=child_input["sex"],
        )
    except (ValueError, KeyError) as e:
        wfh_z = 0.0
        zscore_error = str(e)

    muac_cm = child_input.get("muac_cm", 13.0)
    muac_band = classify_muac(muac_cm)
    growth_trend = child_input.get("growth_trend", "stable")

    # --- Step 2: Fuzzify anthropometric inputs ---
    fuzzified_anthro = fuzzify_child_inputs(
        weight_for_height_z=wfh_z,
        muac_cm=muac_cm,
        growth_trend=growth_trend,
        config=config,
    )

    # --- Step 3: Fuzzify dietary inputs (if available) ---
    fuzzified_dietary: Dict[str, Dict[str, float]] = {}
    dietary_risk_info: Optional[Dict[str, Any]] = None

    if nutrient_summary:
        fuzzified_dietary = fuzzify_dietary_inputs(
            nutrient_summary=nutrient_summary,
            child_age_months=child_input.get("age_months", 60),
            config=config,
            rda_config=rda_config,
        )

        # Build dietary risk summary
        nutrient_gaps: List[str] = []
        excess_nutrients: List[str] = []

        for field, memberships in fuzzified_dietary.items():
            if "deficient" in memberships and memberships["deficient"] > 0.5:
                nutrient_gaps.append(field.replace("_pct_rda", ""))
            if "excess" in memberships and memberships.get("excess", 0) > 0.5:
                excess_nutrients.append(field)
            if "high_excess" in memberships and memberships.get("high_excess", 0) > 0.5:
                excess_nutrients.append(field)

        dietary_risk_info = {
            "nutrient_gaps": nutrient_gaps,
            "excess_nutrients": excess_nutrients,
            "nova_breakdown": nutrient_summary.get("nova_breakdown", {}),
            "avg_glycemic_index": nutrient_summary.get("gi_score"),
        }

    # --- Step 4: Merge all fuzzified values ---
    all_fuzzified = {**fuzzified_anthro, **fuzzified_dietary}

    # --- Step 5: Fire rules ---
    rules = load_rules(config)
    fired_rules = fire_rules(all_fuzzified, rules)

    # --- Step 6: Combine conclusions ---
    combined = combine_conclusions(fired_rules)

    # --- Step 7: Determine final risk ---
    if combined:
        final_level, final_confidence = determine_final_risk(combined)
    else:
        # No rules fired — default to low risk
        final_level = "low"
        final_confidence = 0.0

    # Flatten combined into simple {level: cf} across all categories
    combined_flat: Dict[str, float] = {}
    for _category, levels in combined.items():
        for level, cf in levels.items():
            if level in combined_flat:
                # MYCIN combine across categories
                combined_flat[level] = combined_flat[level] + cf * (1 - combined_flat[level])
            else:
                combined_flat[level] = cf

    # --- Step 8: Assemble TraceObject ---
    trace: Dict[str, Any] = {
        "child_id": child_id,
        "timestamp": timestamp,
        "fuzzification": all_fuzzified,
        "rules_fired": [
            {
                "rule_id": r["rule_id"],
                "antecedents": {
                    ant[0]: ant[1] for ant in r["antecedents"]
                } if isinstance(r["antecedents"], list) else r["antecedents"],
                "strength": round(r["strength"], 4),
                "expert_cf": r["expert_cf"],
                "conclusion_category": r["conclusion_category"],
                "conclusion_level": r["conclusion_level"],
            }
            for r in fired_rules
        ],
        "combined_confidence": {
            "high": round(combined_flat.get("high", 0.0), 4),
            "moderate": round(combined_flat.get("moderate", 0.0), 4),
            "low": round(combined_flat.get("low", 0.0), 4),
        },
        "dietary_risk": dietary_risk_info,
        "final_risk_level": final_level,
        "final_confidence": round(final_confidence, 4),
        # Internal metadata (not in spec, but useful for debugging)
        "_metadata": {
            "weight_for_height_z": wfh_z,
            "muac_risk_band": muac_band,
            "zscore_error": zscore_error,
        },
    }

    return trace
