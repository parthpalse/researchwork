import csv
from pathlib import Path

import pytest
from src.engine.food_match import (
    build_dish_index,
    resolve_base_ingredient,
    dish_style,
    clamp_grams,
    match_food_part,
)

CONFIG = {
    "matching": {
        "base_ingredient_min_score": 85,
        "min_confidence": 0.60,
        "default_style": "Home-Style",
        "weights": {"cooking_method": 3.0, "fat_medium": 2.0, "style": 1.0},
        "attribute_weight": 0.4,
        "similar_methods": {"Gravy-Stewed": ["Pressure-Cooked", "Shallow-Fried (Tadka)", "Boiled"]},
        "similar_method_credit": [0.6, 0.4, 0.2],
        "min_grams": 5,
        "max_grams": 600,
        "default_grams": 100,
    }
}

DISHES = [
    {"record_id": "A1", "base_ingredient": "Wheat Atta (Whole)", "cooking_method": "Deep-Fried",
     "fat_medium": "Ghee", "dish_name": "Wheat Atta (Whole) (Deep-Fried in Ghee) [Home-Style]"},
    {"record_id": "A2", "base_ingredient": "Wheat Atta (Whole)", "cooking_method": "Griddled (Tava)",
     "fat_medium": "No Added Fat", "dish_name": "Wheat Atta (Whole) (Griddled) [Rich/Festive]"},
    {"record_id": "A3", "base_ingredient": "Wheat Atta (Whole)", "cooking_method": "Griddled (Tava)",
     "fat_medium": "No Added Fat", "dish_name": "Wheat Atta (Whole) (Griddled) [Home-Style]"},
    {"record_id": "B1", "base_ingredient": "Toor Dal", "cooking_method": "Boiled",
     "fat_medium": "No Added Fat", "dish_name": "Toor Dal (Boiled)"},
]


@pytest.fixture
def index():
    return build_dish_index(DISHES)


def test_build_dish_index_groups_by_ingredient(index):
    assert set(index.keys()) == {"Wheat Atta (Whole)", "Toor Dal"}
    assert len(index["Wheat Atta (Whole)"]) == 3


def test_resolve_base_ingredient_exact_and_fuzzy():
    names = ["Wheat Atta (Whole)", "Toor Dal"]
    assert resolve_base_ingredient("Toor Dal", names, 85) == ("Toor Dal", 100.0)
    name, score = resolve_base_ingredient("wheat atta whole", names, 85)
    assert name == "Wheat Atta (Whole)"
    assert score >= 85


def test_resolve_base_ingredient_unknown_returns_none():
    assert resolve_base_ingredient("Pizza", ["Wheat Atta (Whole)", "Toor Dal"], 85) is None
    assert resolve_base_ingredient("", ["Toor Dal"], 85) is None


def test_dish_style():
    assert dish_style("Paneer (Boiled) [Home-Style]") == "Home-Style"
    assert dish_style("Toor Dal (Boiled)") is None


def test_clamp_grams():
    assert clamp_grams(None, CONFIG) == 100.0
    assert clamp_grams(0, CONFIG) == 100.0
    assert clamp_grams(2, CONFIG) == 5.0
    assert clamp_grams(5000, CONFIG) == 600.0
    assert clamp_grams(80, CONFIG) == 80.0


def test_match_prefers_method_fat_and_default_style(index):
    part = {"base_ingredient": "Wheat Atta (Whole)", "cooking_method": "Griddled (Tava)",
            "fat_medium": "No Added Fat", "grams": 40, "model_confidence": 0.9}
    result = match_food_part(part, index, CONFIG)
    assert result["matched"] is True
    assert result["dish"]["record_id"] == "A3"  # Home-Style beats Rich/Festive
    assert result["grams"] == 40.0
    assert result["confidence"] == pytest.approx(0.9)
    assert result["possible_match"] is False


def test_match_without_method_has_lower_confidence(index):
    full = match_food_part(
        {"base_ingredient": "Wheat Atta (Whole)", "cooking_method": "Griddled (Tava)",
         "fat_medium": "No Added Fat"}, index, CONFIG)
    partial = match_food_part({"base_ingredient": "Wheat Atta (Whole)"}, index, CONFIG)
    assert partial["matched"] is True
    assert partial["confidence"] < full["confidence"]


def test_low_model_confidence_is_possible_match(index):
    result = match_food_part(
        {"base_ingredient": "Toor Dal", "cooking_method": "Boiled",
         "fat_medium": "No Added Fat", "model_confidence": 0.4}, index, CONFIG)
    assert result["matched"] is True
    assert result["possible_match"] is True


def test_missing_method_falls_back_to_similar_not_deep_fried():
    rows = [
        {"record_id": "R1", "base_ingredient": "Rice (Milled)", "cooking_method": "Deep-Fried",
         "fat_medium": "Ghee", "dish_name": "Rice (Milled) (Deep-Fried in Ghee) [Home-Style]"},
        {"record_id": "R2", "base_ingredient": "Rice (Milled)", "cooking_method": "Boiled",
         "fat_medium": "No Added Fat", "dish_name": "Rice (Milled) (Boiled)"},
        {"record_id": "R3", "base_ingredient": "Rice (Milled)", "cooking_method": "Pressure-Cooked",
         "fat_medium": "Ghee", "dish_name": "Rice (Milled) (Pressure-Cooked with Ghee) [Home-Style]"},
    ]
    # Rice has no Gravy-Stewed rows (e.g. biryani rice) -> closest is Pressure-Cooked, not Deep-Fried
    part = {"base_ingredient": "Rice (Milled)", "cooking_method": "Gravy-Stewed", "fat_medium": "Ghee"}
    result = match_food_part(part, build_dish_index(rows), CONFIG)
    assert result["dish"]["record_id"] == "R3"


def test_unknown_ingredient_is_unmatched(index):
    result = match_food_part({"base_ingredient": "Pizza", "grams": 150}, index, CONFIG)
    assert result["matched"] is False
    assert result["dish"] is None
    assert result["grams"] == 150.0


def test_roti_matches_real_dataset():
    csv_path = Path(__file__).parent.parent / "data" / "indian_dishes.csv"
    with open(csv_path, encoding="utf-8") as f:
        dishes = [
            {
                "record_id": r["Record_ID"],
                "base_ingredient": r["Base_Ingredient_Name"],
                "dish_name": r["Dish_Variant_Name"],
                "cooking_method": r["Cooking_Method"],
                "fat_medium": r["Fat_Medium_Used"],
            }
            for r in csv.DictReader(f)
        ]
    index = build_dish_index(dishes)
    assert len(index) == 130

    roti = {"base_ingredient": "Wheat Atta (Whole)", "cooking_method": "Griddled (Tava)",
            "fat_medium": "No Added Fat", "grams": 40}
    result = match_food_part(roti, index, CONFIG)
    assert result["dish"]["base_ingredient"] == "Wheat Atta (Whole)"
    assert result["dish"]["cooking_method"] == "Griddled (Tava)"
    assert result["dish"]["fat_medium"] == "No Added Fat"
