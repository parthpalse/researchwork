import pytest
import yaml
from pathlib import Path
from src.engine.trace_builder import build_trace

CONFIG_DIR = Path(__file__).parent.parent / "config"

@pytest.fixture
def configs():
    with open(CONFIG_DIR / "thresholds.yaml", "r", encoding="utf-8") as f:
        thresholds_cfg = yaml.safe_load(f)
    with open(CONFIG_DIR / "rda_children.yaml", "r", encoding="utf-8") as f:
        rda_cfg = yaml.safe_load(f)
    return thresholds_cfg, rda_cfg

def test_build_trace_healthy_child(configs):
    thresholds_cfg, rda_cfg = configs
    child_input = {
        "child_id": "CH-001",
        "age_months": 60,
        "sex": "M",
        "height_cm": 110.0,
        "weight_kg": 18.7,  # normal weight for 110cm
        "muac_cm": 14.5,    # normal MUAC
        "growth_trend": "stable"
    }

    trace = build_trace(child_input, None, thresholds_cfg, rda_cfg)
    assert trace["child_id"] == "CH-001"
    assert "timestamp" in trace
    assert "fuzzification" in trace
    assert "rules_fired" in trace
    assert "combined_confidence" in trace
    assert trace["final_risk_level"] in ["low", "normal"]

def test_build_trace_severe_risk_child(configs):
    thresholds_cfg, rda_cfg = configs
    child_input = {
        "child_id": "CH-002",
        "age_months": 60,
        "sex": "M",
        "height_cm": 100.0,
        "weight_kg": 9.5,   # severely underweight (z < -3)
        "muac_cm": 11.2,    # severe risk MUAC (< 11.5)
        "growth_trend": "declining"
    }

    trace = build_trace(child_input, None, thresholds_cfg, rda_cfg)
    assert trace["final_risk_level"] == "high"
    assert trace["final_confidence"] > 0.5
    # Should have fired R1
    fired_ids = [r["rule_id"] for r in trace["rules_fired"]]
    assert "R1" in fired_ids
