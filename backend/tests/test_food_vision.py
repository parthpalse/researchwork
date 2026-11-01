import json
import httpx
import pytest
from src.llm import food_vision
from src.llm.food_vision import build_response_schema, identify_foods, FoodVisionError, OTHER_INGREDIENT

CONFIG = {
    "gemini": {
        "model": "gemini-test",
        "endpoint": "https://example.test/v1beta/models",
        "request_timeout_s": 5,
        "max_retries": 3,
        "base_backoff_s": 0.0,
        "min_seconds_between_calls": 0.0,
        "temperature": 0.1,
        "thinking_budget": 0,
    }
}

GEMINI_RESULT = {"is_food": True, "items": [{"name": "Roti", "confidence": 0.9, "components": [
    {"base_ingredient": "Wheat Atta (Whole)", "cooking_method": "Griddled (Tava)",
     "fat_medium": "No Added Fat", "grams": 40}]}]}


def _gemini_body(result):
    return {"candidates": [{"content": {"parts": [{"text": json.dumps(result)}]}}]}


@pytest.fixture
def mock_gemini(monkeypatch):
    """Route identify_foods' HTTP calls to a handler; returns the list of requests seen."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    seen = []
    responses = []

    def handler(request: httpx.Request):
        seen.append(request)
        return responses.pop(0)

    real_client = httpx.AsyncClient

    def fake_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(food_vision.httpx, "AsyncClient", fake_client)
    return seen, responses


def _call():
    return identify_foods("aGVsbG8=", "image/jpeg", ["Wheat Atta (Whole)"],
                          ["Griddled (Tava)"], ["No Added Fat"], CONFIG)


def test_schema_restricts_values_to_dataset_lists():
    schema = build_response_schema(["Toor Dal", "Potato"], ["Boiled"], ["Ghee"])
    component = schema["properties"]["items"]["items"]["properties"]["components"]["items"]
    assert component["properties"]["base_ingredient"]["enum"] == ["Potato", "Toor Dal", OTHER_INGREDIENT]
    assert component["properties"]["cooking_method"]["enum"] == ["Boiled"]
    assert component["properties"]["fat_medium"]["enum"] == ["Ghee"]


@pytest.mark.anyio
async def test_missing_key_raises_503(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(FoodVisionError) as err:
        await _call()
    assert err.value.status_code == 503


@pytest.mark.anyio
async def test_success_sends_key_in_header_and_parses_json(mock_gemini):
    seen, responses = mock_gemini
    responses.append(httpx.Response(200, json=_gemini_body(GEMINI_RESULT)))
    result = await _call()
    assert result == GEMINI_RESULT
    assert seen[0].headers["x-goog-api-key"] == "test-key"
    assert "key=" not in str(seen[0].url)  # key never in the URL (would leak into logs)
    assert str(seen[0].url).endswith("/gemini-test:generateContent")


@pytest.mark.anyio
async def test_retries_on_server_error_then_succeeds(mock_gemini):
    seen, responses = mock_gemini
    responses.extend([
        httpx.Response(503, json={}),
        httpx.Response(429, json={}),
        httpx.Response(200, json=_gemini_body(GEMINI_RESULT)),
    ])
    assert await _call() == GEMINI_RESULT
    assert len(seen) == 3


@pytest.mark.anyio
async def test_gives_up_after_max_retries(mock_gemini):
    seen, responses = mock_gemini
    responses.extend([httpx.Response(500, json={}) for _ in range(3)])
    with pytest.raises(FoodVisionError) as err:
        await _call()
    assert err.value.status_code == 502
    assert len(seen) == 3


@pytest.mark.anyio
async def test_client_error_is_not_retried(mock_gemini):
    seen, responses = mock_gemini
    responses.append(httpx.Response(400, json={"error": "bad image"}))
    with pytest.raises(FoodVisionError):
        await _call()
    assert len(seen) == 1
