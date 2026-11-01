import pytest
from src.engine.food_alerts import meal_totals, age_group_for, find_allergens, build_alerts

RDA_CONFIG = {
    "age_groups": {"age_4_6": [48, 72], "age_7_9": [73, 108]},
    "rda_values": {
        "age_4_6": {"protein": 16.0, "sugar": 25.0},
        "age_7_9": {"protein": 23.0, "sugar": 30.0},
    },
    "daily_upper_limits": {
        "age_4_6": {"sodium_mg": 1500},
        "age_7_9": {"sodium_mg": 1500},
    },
}

SCANNER_CONFIG = {
    "alerts": {
        "meal_share_of_day": 0.33,
        "low_protein_ratio": 0.5,
        "added_sugar_ingredients": ["Sugar (White)", "Jaggery (Gur)"],
        "allergens": {
            "Milk": ["Paneer", "Ghee"],
            "Peanuts": ["Peanuts (Groundnut, Raw)", "Groundnut Oil"],
        },
    }
}

PANEER = {"base_ingredient": "Paneer", "fat_medium": "Ghee", "energy_kcal": 300.0,
          "protein_g": 18.0, "total_fat_g": 22.0, "carbohydrate_g": 4.0,
          "dietary_fiber_g": 0.0, "sugars_g": 2.0, "sodium_mg": 40.0}
JALEBI = {"base_ingredient": "Refined Flour (Maida)", "fat_medium": "Refined Oil",
          "energy_kcal": 400.0, "protein_g": 2.0, "total_fat_g": 15.0, "carbohydrate_g": 60.0,
          "dietary_fiber_g": 0.5, "sugars_g": 5.0, "sodium_mg": 900.0}
SUGAR = {"base_ingredient": "Sugar (White)", "fat_medium": "No Added Fat", "energy_kcal": 380.0,
         "protein_g": 0.0, "total_fat_g": 0.0, "carbohydrate_g": 95.0, "dietary_fiber_g": 0.0,
         "sugars_g": 95.0, "sodium_mg": 0.0}
MILK = {"base_ingredient": "Milk (Cow)", "fat_medium": "No Added Fat", "energy_kcal": 67.0,
        "protein_g": 3.2, "total_fat_g": 4.1, "carbohydrate_g": 4.4, "dietary_fiber_g": 0.0,
        "sugars_g": 4.4, "sodium_mg": 44.0}
ADDED = SCANNER_CONFIG["alerts"]["added_sugar_ingredients"]


def test_meal_totals_scales_by_grams():
    totals = meal_totals([{"dish": PANEER, "grams": 50}, {"dish": JALEBI, "grams": 100}])
    assert totals["energy_kcal"] == pytest.approx(150.0 + 400.0)
    assert totals["protein_g"] == pytest.approx(9.0 + 2.0)
    assert totals["sugar_g"] == pytest.approx(1.0 + 5.0)
    assert totals["sodium_mg"] == pytest.approx(20.0 + 900.0)


def test_meal_totals_added_sugar_only_from_sugar_ingredients():
    totals = meal_totals([{"dish": MILK, "grams": 200}, {"dish": SUGAR, "grams": 10}], ADDED)
    assert totals["sugar_g"] == pytest.approx(8.8 + 9.5)
    assert totals["added_sugar_g"] == pytest.approx(9.5)


def test_meal_totals_skips_unmatched():
    totals = meal_totals([{"dish": None, "grams": 100}])
    assert totals["energy_kcal"] == 0.0


def test_age_group_for():
    assert age_group_for(60, RDA_CONFIG) == "age_4_6"
    assert age_group_for(90, RDA_CONFIG) == "age_7_9"
    assert age_group_for(None, RDA_CONFIG) == "age_4_6"  # unknown age -> youngest
    assert age_group_for(400, RDA_CONFIG) == "age_4_6"


def test_find_allergens_checks_ingredient_and_fat():
    found = find_allergens([{"dish": PANEER, "grams": 50}], SCANNER_CONFIG["alerts"]["allergens"])
    assert found == {"Milk": ["Ghee", "Paneer"]}


def test_build_alerts_high_sugar_and_sodium():
    parts = [{"dish": JALEBI, "grams": 100}, {"dish": SUGAR, "grams": 20}]
    alerts = build_alerts(meal_totals(parts, ADDED), parts, 60, RDA_CONFIG, SCANNER_CONFIG)
    types = {a["type"] for a in alerts}
    assert "high_sugar" in types       # 19 g added > 25 * 0.33
    assert "high_sodium" in types      # 900 mg > 1500 * 0.33
    assert "low_protein" in types      # 2 g < 16 * 0.33 * 0.5
    assert "allergen" not in types


def test_natural_sugar_does_not_trigger_sugar_alert():
    parts = [{"dish": MILK, "grams": 250}]  # 11 g natural milk sugar, no added sugar
    alerts = build_alerts(meal_totals(parts, ADDED), parts, 60, RDA_CONFIG, SCANNER_CONFIG)
    assert not any(a["type"] == "high_sugar" for a in alerts)


def test_build_alerts_balanced_meal_only_allergen():
    parts = [{"dish": PANEER, "grams": 50}]
    alerts = build_alerts(meal_totals(parts, ADDED), parts, 60, RDA_CONFIG, SCANNER_CONFIG)
    assert [a["type"] for a in alerts] == ["allergen"]
    assert alerts[0]["allergen"] == "Milk"


def test_build_alerts_uses_age_specific_limits():
    # 9 g added sugar: above a third of 25 g (8.25) but below a third of 30 g (9.9)
    parts = [{"dish": PANEER, "grams": 50}, {"dish": SUGAR, "grams": 100 * 9.0 / 95.0}]
    young = build_alerts(meal_totals(parts, ADDED), parts, 60, RDA_CONFIG, SCANNER_CONFIG)
    older = build_alerts(meal_totals(parts, ADDED), parts, 90, RDA_CONFIG, SCANNER_CONFIG)
    assert any(a["type"] == "high_sugar" for a in young)
    assert not any(a["type"] == "high_sugar" for a in older)
