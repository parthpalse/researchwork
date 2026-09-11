import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.mark.anyio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.anyio
async def test_assess_endpoint():
    payload = {
        "child_id": "TEST_CHILD_01",
        "age_months": 60,
        "sex": "M",
        "weight_kg": 18.0,
        "height_cm": 110.0,
        "muac_cm": 14.0,
        "growth_trend": "stable"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/assess", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "trace" in data
    assert "explanation" in data
    assert "trace_id" in data
    assert data["trace"]["child_id"] == "TEST_CHILD_01"
    assert "parent_message" in data["explanation"]
    assert "clinician_note" in data["explanation"]

@pytest.mark.anyio
async def test_history_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/child/TEST_CHILD_01/history")
    assert response.status_code == 200
    history = response.json()
    assert isinstance(history, list)
    assert len(history) > 0

@pytest.mark.anyio
async def test_clinician_override_endpoint():
    # First get trace id from an assessment
    payload = {
        "child_id": "TEST_CHILD_OVERRIDE",
        "age_months": 60,
        "sex": "F",
        "weight_kg": 17.5,
        "height_cm": 110.0,
        "muac_cm": 13.5,
        "growth_trend": "stable"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/assess", json=payload)
        trace_id = res.json()["trace_id"]

        override_payload = {
            "trace_id": trace_id,
            "new_risk_level": "moderate",
            "reason": "Clinician clinical observation: mild edema observed."
        }
        res_override = await ac.post("/api/clinician/override", json=override_payload)
        assert res_override.status_code == 200
        data = res_override.json()
        assert data["clinician_override"] == "moderate"
        assert data["override_reason"] == "Clinician clinical observation: mild edema observed."
