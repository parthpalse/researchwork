import httpx
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.api import packaged
from src.integrations import open_food_facts
from src.integrations.open_food_facts import fetch_product, OpenFoodFactsError

OFF_CONFIG = {"open_food_facts": {
    "endpoint": "https://example.test/api/v2/product", "user_agent": "Test/1.0",
    "request_timeout_s": 5, "max_retries": 3, "base_backoff_s": 0.0, "min_seconds_between_calls": 0.0}}

RAW = {"product_name": "Glucose Biscuits", "brands": "TestBrand", "serving_quantity": 25,
       "allergens_tags": ["en:gluten", "en:milk"],
       "nutriments": {"energy-kcal_100g": 450, "proteins_100g": 7, "fat_100g": 14,
                      "carbohydrates_100g": 75, "sugars_100g": 30, "sodium_100g": 0.3}}


@pytest.fixture
def off_http(monkeypatch):
    """Route fetch_product's HTTP calls to queued responses; returns (requests_seen, responses)."""
    seen, responses = [], []

    def handler(request):
        seen.append(request)
        return responses.pop(0)

    real_client = httpx.AsyncClient
    monkeypatch.setattr(open_food_facts.httpx, "AsyncClient",
                        lambda *a, **kw: real_client(*a, **{**kw, "transport": httpx.MockTransport(handler)}))
    return seen, responses


@pytest.mark.anyio
async def test_fetch_product_sends_user_agent_and_returns_product(off_http):
    seen, responses = off_http
    responses.append(httpx.Response(200, json={"status": 1, "product": RAW}))
    assert await fetch_product("8901234567890", OFF_CONFIG) == RAW
    assert seen[0].headers["user-agent"] == "Test/1.0"
    assert "/8901234567890.json" in str(seen[0].url)


@pytest.mark.anyio
async def test_fetch_product_not_found(off_http):
    _, responses = off_http
    responses.append(httpx.Response(200, json={"status": 0, "status_verbose": "product not found"}))
    assert await fetch_product("8901234567890", OFF_CONFIG) is None


@pytest.mark.anyio
async def test_fetch_product_retries_then_raises(off_http):
    seen, responses = off_http
    responses.extend([httpx.Response(503) for _ in range(3)])
    with pytest.raises(OpenFoodFactsError):
        await fetch_product("8901234567890", OFF_CONFIG)
    assert len(seen) == 3


@pytest.fixture
def lookup(monkeypatch):
    """Mock the cache table and OFF; returns state to control them."""
    state = {"cached": None, "raw": RAW, "saved": [], "fetches": 0}

    async def fake_cached(barcode, cache_days):
        return state["cached"]

    async def fake_save(product, source):
        state["saved"].append(product)
        return {**product, "source": source, "fetched_at": "2026-11-02T00:00:00+00:00"}

    async def fake_fetch(barcode, config):
        state["fetches"] += 1
        return state["raw"]

    monkeypatch.setattr(packaged, "get_cached_product", fake_cached)
    monkeypatch.setattr(packaged, "save_product", fake_save)
    monkeypatch.setattr(packaged, "fetch_product", fake_fetch)
    return state


async def _get(path):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        return await ac.get(path)


@pytest.mark.anyio
async def test_lookup_fetches_saves_and_alerts(lookup):
    res = await _get("/api/packaged/8901234567890?age_months=60")
    assert res.status_code == 200
    data = res.json()
    assert data["cached"] is False
    assert data["product"]["record_id"] == "OFF-8901234567890"
    assert data["product"]["source"] == "openfoodfacts"
    assert data["serving_totals"]["added_sugar_g"] == pytest.approx(7.5)  # 25 g x 30 %
    types = {a["type"] for a in data["alerts"]}
    assert "allergen" in types
    assert "low_protein" not in types   # suppressed for a single packaged serving
    assert len(lookup["saved"]) == 1


@pytest.mark.anyio
async def test_lookup_uses_cache_without_fetching(lookup):
    lookup["cached"] = {**lookup_product(), "source": "openfoodfacts", "fetched_at": "2026-11-01T00:00:00+00:00"}
    res = await _get("/api/packaged/8901234567890")
    assert res.status_code == 200
    assert res.json()["cached"] is True
    assert lookup["fetches"] == 0


@pytest.mark.anyio
async def test_lookup_invalid_and_unknown_barcodes(lookup):
    assert (await _get("/api/packaged/12ab")).status_code == 422
    lookup["raw"] = None
    res = await _get("/api/packaged/8901234567890")
    assert res.status_code == 404
    assert "Open Food Facts" in res.json()["detail"]


def lookup_product():
    from src.engine.packaged_food import normalize_off_product
    cfg = packaged._load_configs()[0]
    return normalize_off_product(RAW, "8901234567890", cfg)
