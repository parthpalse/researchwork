import pytest
from src.engine.zscore import compute_weight_for_height_z, classify_muac

def test_compute_weight_for_height_z_median():
    # At height 100cm for boys, median M is 13.9507 kg.
    # At weight = 13.9507, z should be very close to 0.0
    z = compute_weight_for_height_z(weight_kg=13.95, height_cm=100.0, sex="M")
    assert z == pytest.approx(0.0, abs=0.1)

def test_compute_weight_for_height_z_underweight():
    # Weight lower than median yields negative z
    z = compute_weight_for_height_z(weight_kg=11.0, height_cm=100.0, sex="M")
    assert z < -1.5

def test_classify_muac():
    assert classify_muac(11.0) == "severe"
    assert classify_muac(11.4) == "severe"
    assert classify_muac(11.5) == "moderate"
    assert classify_muac(12.0) == "moderate"
    assert classify_muac(12.5) == "moderate"
    assert classify_muac(12.6) == "normal"
    assert classify_muac(14.0) == "normal"
