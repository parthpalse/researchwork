import pytest
from src.engine.packaged_food import normalize_barcode, map_allergens, normalize_off_product
from src.engine.food_alerts import meal_totals, find_allergens

CONFIG = {
    "barcode": {"min_digits": 8, "max_digits": 14},
    "default_category": "Packaged Food",
    "default_serving_g": 30,
    "default_nova_group": 4,
    "treat_unknown_sugar_as_added": True,
    "allergen_tags": {"en:milk": "Milk", "en:gluten": "Gluten (wheat/barley)"},
}

# Shape taken from a real Open Food Facts response (Maggi noodles, trimmed)
MAGGI = {
    "product_name": "Masala Noodles",
    "brands": "Maggi,Nestle",
    "nova_group": 4,
    "serving_quantity": 70,
    "allergens_tags": ["en:gluten", "en:unknown-tag"],
    "nutriments": {
        "energy-kcal_100g": 437, "proteins_100g": 10.4, "fat_100g": 15.7,
        "carbohydrates_100g": 44.5, "fiber_100g": 3.9, "sugars_100g": 2.5,
        "added-sugars_100g": 0, "sodium_100g": 1.2, "calcium_100g": 0.1535, "iron_100g": 0.0037,
    },
}


def test_normalize_barcode():
    assert normalize_barcode("8901058851298", CONFIG) == "8901058851298"
    assert normalize_barcode(" 8901-0588 51298 ", CONFIG) == "8901058851298"
    assert normalize_barcode("1234", CONFIG) is None
    assert normalize_barcode("89010588ABC98", CONFIG) is None
    assert normalize_barcode("", CONFIG) is None


def test_map_allergens_ignores_unknown_tags():
    assert map_allergens(["en:gluten", "en:xyz", "en:milk"], CONFIG["allergen_tags"]) == [
        "Gluten (wheat/barley)", "Milk"]


def test_normalize_off_product_units_and_fields():
    p = normalize_off_product(MAGGI, "8901058851298", CONFIG)
    assert p["record_id"] == "OFF-8901058851298"
    assert p["dish_name"] == "Masala Noodles (Maggi)"
    assert p["energy_kcal"] == 437
    assert p["sodium_mg"] == pytest.approx(1200.0)      # grams -> mg
    assert p["calcium_mg"] == pytest.approx(153.5)
    assert p["added_sugars_g"] == 0.0                   # label says 0 added sugar
    assert p["serving_g"] == 70
    assert p["nova_group"] == 4
    assert p["allergens"] == ["Gluten (wheat/barley)"]


def test_normalize_uses_salt_and_kj_when_missing():
    product = {"product_name": "Biscuit", "nutriments": {
        "energy_100g": 2092, "salt_100g": 1.0, "sugars_100g": 25.0}}
    p = normalize_off_product(product, "12345678", CONFIG)
    assert p["energy_kcal"] == pytest.approx(500.0, abs=0.1)
    assert p["sodium_mg"] == pytest.approx(400.0)       # salt / 2.5
    assert p["added_sugars_g"] == 25.0                  # unknown -> treated as added
    assert p["serving_g"] == 30                         # default serving
    assert p["nova_group"] == 4                         # default NOVA


def test_normalize_without_calories_returns_none():
    assert normalize_off_product({"product_name": "X", "nutriments": {}}, "12345678", CONFIG) is None


def test_packaged_rows_work_with_meal_totals_and_allergens():
    p = normalize_off_product(dict(MAGGI, nutriments={**MAGGI["nutriments"], "added-sugars_100g": 10}),
                              "8901058851298", CONFIG)
    parts = [{"dish": p, "grams": 70}]
    totals = meal_totals(parts, ["Sugar (White)"])
    assert totals["added_sugar_g"] == pytest.approx(7.0)
    assert totals["sodium_mg"] == pytest.approx(840.0)
    assert find_allergens(parts, {}) == {"Gluten (wheat/barley)": ["Masala Noodles (Maggi)"]}
