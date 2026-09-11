import pytest
from src.engine.dietary import calculate_nutrient_summary, get_dietary_fuzzy_inputs

def test_calculate_nutrient_summary():
    meals = [
        {"dish_id": "IND-001", "servings": 2.0, "serving_size_g": 100.0},
        {"dish_id": "IND-002", "servings": 1.0, "serving_size_g": 50.0},
    ]
    dish_lookup = {
        "IND-001": {
            "energy_kcal": 200.0,
            "protein_g": 5.0,
            "carbohydrate_g": 30.0,
            "sugars_g": 2.0,
            "iron_mg": 2.0,
            "glycemic_index": 60.0,
            "nova_group": 1
        },
        "IND-002": {
            "energy_kcal": 100.0,
            "protein_g": 4.0,
            "carbohydrate_g": 10.0,
            "sugars_g": 5.0,
            "iron_mg": 1.0,
            "glycemic_index": 40.0,
            "nova_group": 3
        }
    }

    summary = calculate_nutrient_summary(meals, dish_lookup)
    # IND-001 factor = 2.0 * (100/100) = 2.0
    # IND-002 factor = 1.0 * (50/100) = 0.5
    expected_energy = 200.0 * 2.0 + 100.0 * 0.5 # 450.0
    expected_protein = 5.0 * 2.0 + 4.0 * 0.5 # 12.0

    assert summary["total_energy_kcal"] == pytest.approx(expected_energy)
    assert summary["total_protein_g"] == pytest.approx(expected_protein)
    assert summary["avg_glycemic_index"] > 0
    assert 1 in summary["nova_breakdown"]

def test_get_dietary_fuzzy_inputs():
    rda_config = {
        "age_groups": {
            "age_4_6": [48, 72]
        },
        "rda_values": {
            "age_4_6": {
                "protein": 16.0,
                "iron": 11.0
            }
        }
    }
    summary = {
        "total_protein_g": 8.0, # 50% of RDA
        "total_iron_mg": 11.0,  # 100% of RDA
        "total_sugar_g": 30.0,
        "avg_glycemic_index": 65.0,
        "nova_breakdown": {1: 80.0, 3: 20.0}
    }
    inputs = get_dietary_fuzzy_inputs(summary, child_age_months=60, rda_config=rda_config)
    assert inputs["protein_pct_rda"] == pytest.approx(50.0)
    assert inputs["iron_pct_rda"] == pytest.approx(100.0)
    assert inputs["sugar_g"] == pytest.approx(30.0)
