import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


def _child(child_id):
    return {"child_id": child_id, "age_months": 72, "sex": "F", "weight_kg": 19.0,
            "height_cm": 112.0, "muac_cm": 14.2, "growth_trend": "stable"}


async def _client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.anyio
async def test_unknown_child_is_404():
    async with await _client() as ac:
        res = await ac.get(f"/api/child/NOPE-{uuid.uuid4().hex[:8]}")
    assert res.status_code == 404


@pytest.mark.anyio
async def test_save_child_validates_input():
    async with await _client() as ac:
        res = await ac.post("/api/child", json={**_child("CH-BAD"), "age_months": 10})
    assert res.status_code == 422


@pytest.mark.anyio
async def test_save_then_update_child():
    child_id = f"CH-T{uuid.uuid4().hex[:6]}"
    async with await _client() as ac:
        assert (await ac.post("/api/child", json=_child(child_id))).status_code == 200
        assert (await ac.post("/api/child", json={**_child(child_id), "weight_kg": 20.5})).status_code == 200
        res = await ac.get(f"/api/child/{child_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["child"]["weight_kg"] == 20.5
    assert data["latest_assessment"] is None
    assert data["meal_logs"] == []


@pytest.mark.anyio
async def test_overview_has_meals_and_latest_assessment():
    """Step 1 details -> step 2 meals -> assessment; parent/clinician can load it all back."""
    child_id = f"CH-T{uuid.uuid4().hex[:6]}"
    async with await _client() as ac:
        await ac.post("/api/child", json=_child(child_id))
        meal = await ac.post("/api/meal-log", json={"child_id": child_id, "meals": [
            {"dish_id": "IND-000001", "dish_name": "Bajra (Boiled)", "servings": 1, "serving_size_g": 120}]})
        assert meal.status_code == 200
        summary = meal.json()["nutrient_summary"]
        assessed = await ac.post("/api/assess", json={"child": _child(child_id), "nutrient_summary": summary})
        assert assessed.status_code == 200

        res = await ac.get(f"/api/child/{child_id}")
    data = res.json()
    assert data["latest_assessment"]["trace_id"] == assessed.json()["trace_id"]
    assert data["latest_assessment"]["trace"]["dietary_risk"] is not None
    assert "parent_message" in data["latest_assessment"]["explanation"]
    assert len(data["meal_logs"]) == 1
    assert data["meal_logs"][0]["meals"][0]["dish_name"] == "Bajra (Boiled)"
    assert data["meal_logs"][0]["nutrient_summary"]["total_energy_kcal"] > 0
