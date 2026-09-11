import pytest
from src.engine.fuzzy import (
    triangular_mf,
    trapezoidal_mf,
    left_shoulder_mf,
    right_shoulder_mf,
    fuzzify_value,
    fuzzify_categorical,
    fuzzify_child_inputs,
    fuzzify_dietary_inputs,
)

def test_triangular_mf():
    # Peak at 0, left -1, right 1
    assert triangular_mf(-2.0, -1.0, 0.0, 1.0) == 0.0
    assert triangular_mf(0.0, -1.0, 0.0, 1.0) == 1.0
    assert triangular_mf(-0.5, -1.0, 0.0, 1.0) == 0.5
    assert triangular_mf(0.5, -1.0, 0.0, 1.0) == 0.5
    assert triangular_mf(2.0, -1.0, 0.0, 1.0) == 0.0

def test_left_shoulder_mf():
    # 1.0 at <= -3, 0 at -2
    assert left_shoulder_mf(-4.0, -3.0, -2.0) == 1.0
    assert left_shoulder_mf(-3.0, -3.0, -2.0) == 1.0
    assert left_shoulder_mf(-2.5, -3.0, -2.0) == 0.5
    assert left_shoulder_mf(-2.0, -3.0, -2.0) == 0.0
    assert left_shoulder_mf(0.0, -3.0, -2.0) == 0.0

def test_right_shoulder_mf():
    # 0 at <= 1.0, 1.0 at >= 2.0
    assert right_shoulder_mf(0.5, 1.0, 2.0) == 0.0
    assert right_shoulder_mf(1.0, 1.0, 2.0) == 0.0
    assert right_shoulder_mf(1.5, 1.0, 2.0) == 0.5
    assert right_shoulder_mf(2.0, 1.0, 2.0) == 1.0
    assert right_shoulder_mf(3.0, 1.0, 2.0) == 1.0

def test_fuzzify_value_anthropometric():
    fuzzy_sets = {
        "severely_low": {"type": "left_shoulder", "params": [-3.0, -2.0]},
        "low": {"type": "triangular", "params": [-3.0, -2.5, -1.0]},
        "normal": {"type": "triangular", "params": [-1.0, 0.0, 1.0]},
    }
    # Test at z = -2.3 (should have severely_low and low)
    res = fuzzify_value(-2.3, fuzzy_sets)
    assert "severely_low" in res
    assert "low" in res
    assert res["severely_low"] == pytest.approx(0.3, abs=0.01) # (-2 - (-2.3)) / (-2 - (-3)) = 0.3/1.0 = 0.3
    assert "normal" not in res

def test_fuzzify_categorical():
    category_map = {
        "declining": {"declining": 1.0, "stable": 0.0, "improving": 0.0},
        "stable": {"declining": 0.0, "stable": 1.0, "improving": 0.0},
    }
    res = fuzzify_categorical("declining", category_map)
    assert res == {"declining": 1.0}
