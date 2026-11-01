import base64
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.api import identify
from src.engine.food_match import build_dish_index
from src.llm.food_vision import FoodVisionError

ROWS = [
    {"record_id": "W1", "base_ingredient": "Wheat Atta (Whole)", "dish_name": "Wheat Atta (Whole) (Griddled) [Home-Style]",
     "category": "Cereals/Millets", "cooking_method": "Griddled (Tava)", "fat_medium": "No Added Fat",
     "energy_kcal": 300.0, "protein_g": 10.0, "total_fat_g": 2.0, "carbohydrate_g": 60.0,
     "dietary_fiber_g": 8.0, "sugars_g": 1.0, "sodium_mg": 5.0},
    {"record_id": "S1", "base_ingredient": "Sugar (White)", "dish_name": "Sugar (White) (Raw)",
     "category": "Snacks/Sweets", "cooking_method": "Raw", "fat_medium": "No Added Fat",
     "energy_kcal": 380.0, "protein_g": 0.0, "total_fat_g": 0.0, "carbohydrate_g": 95.0,
     "dietary_fiber_g": 0.0, "sugars_g": 95.0, "sodium_mg": 0.0},
]

IMAGE = base64.b64encode(b"fake-jpeg-bytes").decode()


@pytest.fixture
def scanner(monkeypatch):
    """Mock the dish DB and the Gemini call; returns a dict to set the vision result."""
    index = build_dish_index(ROWS)
    cache = {"index": index, "by_id": {r["record_id"]: r for r in ROWS},
             "base_names": list(index.keys()), "methods": ["Griddled (Tava)", "Raw"], "fats": ["No Added Fat"]}

    async def fake_index():
        return cache

    state = {"result": None, "error": None, "calls": 0}

    async def fake_identify(*args, **kwargs):
        state["calls"] += 1
        if state["error"]:
            raise state["error"]
        return state["result"]

    monkeypatch.setattr(identify, "get_dish_index", fake_index)
    monkeypatch.setattr(identify, "identify_foods", fake_identify)
    return state


async def _post(path, json):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        return await ac.post(path, json=json)


@pytest.mark.anyio
async def test_identify_food_matches_and_alerts(scanner):
    scanner["result"] = {"is_food": True, "items": [
        {"name": "Roti", "confidence": 0.9, "components": [
            {"base_ingredient": "Wheat Atta (Whole)", "cooking_method": "Griddled (Tava)",
             "fat_medium": "No Added Fat", "grams": 40}]},
        {"name": "Kheer sugar", "confidence": 0.8, "components": [
            {"base_ingredient": "Sugar (White)", "cooking_method": "Raw", "fat_medium": "No Added Fat", "grams": 20}]},
        {"name": "Papad", "confidence": 0.7, "components": [
            {"base_ingredient": "Other", "cooking_method": "Raw", "fat_medium": "No Added Fat", "grams": 10}]},
    ]}
    res = await _post("/api/identify-food", {"image_base64": IMAGE, "mime_type": "image/jpeg", "age_months": 60})
    assert res.status_code == 200
    data = res.json()

    assert data["is_food"] is True
    assert data["model"]
    assert data["latency_ms"] >= 0
    roti = data["items"][0]["components"][0]
    assert roti["matched"] is True
    assert roti["dish"]["record_id"] == "W1"
    assert roti["energy_kcal"] == pytest.approx(120.0)
    assert data["unmatched"] == ["Papad"]
    assert data["totals"]["sugar_g"] == pytest.approx(0.4 + 19.0)
    assert "high_sugar" in {a["type"] for a in data["alerts"]}
    assert "allergen" in {a["type"] for a in data["alerts"]}  # wheat -> gluten (real YAML map)


@pytest.mark.anyio
async def test_identify_food_accepts_data_url(scanner):
    scanner["result"] = {"is_food": False, "items": []}
    res = await _post("/api/identify-food", {"image_base64": f"data:image/jpeg;base64,{IMAGE}"})
    assert res.status_code == 200
    assert res.json()["is_food"] is False
    assert res.json()["items"] == []


@pytest.mark.anyio
async def test_identify_food_rejects_bad_type_and_base64(scanner):
    res = await _post("/api/identify-food", {"image_base64": IMAGE, "mime_type": "application/pdf"})
    assert res.status_code == 415
    res = await _post("/api/identify-food", {"image_base64": "not base64!!", "mime_type": "image/jpeg"})
    assert res.status_code == 422
    assert scanner["calls"] == 0  # Gemini never called for invalid input


@pytest.mark.anyio
async def test_identify_food_rejects_large_image(scanner, monkeypatch):
    real_load = identify._load_configs

    def small_limit():
        scanner_cfg, rda_cfg = real_load()
        scanner_cfg["image"]["max_bytes"] = 4
        return scanner_cfg, rda_cfg

    monkeypatch.setattr(identify, "_load_configs", small_limit)
    res = await _post("/api/identify-food", {"image_base64": IMAGE})
    assert res.status_code == 413


@pytest.mark.anyio
async def test_identify_food_reports_vision_errors(scanner):
    scanner["error"] = FoodVisionError("Food scanner is not configured (GEMINI_API_KEY missing).", 503)
    res = await _post("/api/identify-food", {"image_base64": IMAGE})
    assert res.status_code == 503
    assert "GEMINI_API_KEY" in res.json()["detail"]


@pytest.mark.anyio
async def test_scan_summary_recalculates_for_edited_grams(scanner):
    res = await _post("/api/scan-summary", {"items": [{"dish_id": "W1", "grams": 80}], "age_months": 60})
    assert res.status_code == 200
    data = res.json()
    assert data["totals"]["energy_kcal"] == pytest.approx(240.0)
    assert "high_sugar" not in {a["type"] for a in data["alerts"]}


@pytest.mark.anyio
async def test_scan_summary_unknown_dish_is_404(scanner):
    res = await _post("/api/scan-summary", {"items": [{"dish_id": "NOPE", "grams": 50}]})
    assert res.status_code == 404
