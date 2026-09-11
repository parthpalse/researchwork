import pytest
from src.engine.rules import Rule, fire_rules, combine_conclusions, determine_final_risk

def test_fire_rules_single_and_multi():
    rules = [
        Rule(
            rule_id="R1",
            antecedents=[("weight_for_height_z", "severely_low"), ("muac_cm", "severe_risk")],
            conclusion_category="risk",
            conclusion_level="high",
            expert_cf=0.9
        ),
        Rule(
            rule_id="R2",
            antecedents=[("weight_for_height_z", "low"), ("growth_trend", "declining")],
            conclusion_category="risk",
            conclusion_level="moderate",
            expert_cf=0.7
        )
    ]

    fuzzified = {
        "weight_for_height_z": {"severely_low": 0.6, "low": 0.4},
        "muac_cm": {"severe_risk": 0.5},
        "growth_trend": {"declining": 1.0}
    }

    fired = fire_rules(fuzzified, rules)
    assert len(fired) == 2

    # R1: min(0.6, 0.5) * 0.9 = 0.5 * 0.9 = 0.45
    r1 = next(r for r in fired if r["rule_id"] == "R1")
    assert r1["strength"] == pytest.approx(0.45)

    # R2: min(0.4, 1.0) * 0.7 = 0.4 * 0.7 = 0.28
    r2 = next(r for r in fired if r["rule_id"] == "R2")
    assert r2["strength"] == pytest.approx(0.28)

def test_combine_conclusions_mycin():
    # CF_combined = CF1 + CF2 * (1 - CF1)
    fired_rules = [
        {
            "rule_id": "R1",
            "conclusion_category": "risk",
            "conclusion_level": "high",
            "strength": 0.54,
            "expert_cf": 0.9
        },
        {
            "rule_id": "R4",
            "conclusion_category": "risk",
            "conclusion_level": "high",
            "strength": 0.40,
            "expert_cf": 0.75
        }
    ]

    combined = combine_conclusions(fired_rules)
    expected_high = 0.54 + 0.40 * (1.0 - 0.54) # 0.54 + 0.184 = 0.724
    assert combined["risk"]["high"] == pytest.approx(expected_high, abs=1e-4)

def test_determine_final_risk():
    combined = {
        "risk": {
            "high": 0.72,
            "moderate": 0.4
        }
    }
    level, conf = determine_final_risk(combined)
    assert level == "high"
    assert conf == pytest.approx(0.72)
