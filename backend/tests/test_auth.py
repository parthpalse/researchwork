import time
import types
import uuid

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.auth import supabase_token, users
from src.auth.supabase_token import verify_access_token, TokenError
from src.auth.users import CurrentUser, get_current_user, has_valid_clinician_invite

BASE = "https://example-project.supabase.co"
PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())


def _token(**overrides):
    now = int(time.time())
    claims = {"sub": "user-1", "email": "p@test.local", "aud": "authenticated",
              "iss": f"{BASE}/auth/v1", "iat": now, "exp": now + 3600, "user_metadata": {}}
    claims.update(overrides)
    return jwt.encode(claims, PRIVATE_KEY, algorithm="ES256", headers={"kid": "test-key"})


@pytest.fixture
def supabase_keys(monkeypatch):
    """Serve our test public key as if it came from the project's JWKS endpoint."""
    monkeypatch.setenv("SUPABASE_URL", f"{BASE}/rest/v1/")  # REST URL form is accepted too
    fake = types.SimpleNamespace(get_signing_key_from_jwt=lambda t: types.SimpleNamespace(key=PRIVATE_KEY.public_key()))
    monkeypatch.setattr(supabase_token, "_client", lambda base_url: fake)


# --- token verification -------------------------------------------------------

@pytest.mark.anyio
async def test_valid_token_returns_claims(supabase_keys):
    claims = await verify_access_token(_token())
    assert claims["sub"] == "user-1"


@pytest.mark.anyio
@pytest.mark.parametrize("bad", [
    {"exp": int(time.time()) - 10},                       # expired
    {"aud": "anon"},                                      # wrong audience
    {"iss": "https://other-project.supabase.co/auth/v1"},  # another project
])
async def test_bad_tokens_rejected(supabase_keys, bad):
    with pytest.raises(TokenError):
        await verify_access_token(_token(**bad))


@pytest.mark.anyio
async def test_forged_signature_rejected(supabase_keys):
    other_key = ec.generate_private_key(ec.SECP256R1())
    forged = jwt.encode({"sub": "x", "aud": "authenticated", "iss": f"{BASE}/auth/v1",
                         "exp": int(time.time()) + 60}, other_key, algorithm="ES256")
    with pytest.raises(TokenError):
        await verify_access_token(forged)


@pytest.mark.anyio
async def test_missing_supabase_url_fails_closed(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    with pytest.raises(TokenError):
        await verify_access_token(_token())


def test_clinician_invite(monkeypatch):
    monkeypatch.delenv("CLINICIAN_INVITE_CODE", raising=False)
    assert not has_valid_clinician_invite({"clinician_invite_code": "anything"})
    monkeypatch.setenv("CLINICIAN_INVITE_CODE", "secret-123")
    assert has_valid_clinician_invite({"clinician_invite_code": "secret-123"})
    assert not has_valid_clinician_invite({"clinician_invite_code": "wrong"})
    assert not has_valid_clinician_invite({})


# --- real sign-in dependency (no test override) --------------------------------

async def _get(path, headers=None):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        return await ac.get(path, headers=headers or {})


@pytest.mark.anyio
async def test_requests_without_login_are_rejected():
    app.dependency_overrides.pop(get_current_user, None)
    assert (await _get("/api/children")).status_code == 401
    assert (await _get("/api/dishes/categories")).status_code == 401
    assert (await _get("/api/packaged/8901058851298")).status_code == 401
    assert (await _get("/api/health")).status_code == 200
    assert (await _get("/api/config")).status_code == 200


@pytest.mark.anyio
async def test_sign_in_creates_parent_or_clinician_profile(supabase_keys, monkeypatch):
    app.dependency_overrides.pop(get_current_user, None)
    monkeypatch.setenv("CLINICIAN_INVITE_CODE", "secret-123")

    parent_id, clinician_id = f"u-{uuid.uuid4().hex[:6]}", f"u-{uuid.uuid4().hex[:6]}"
    res = await _get("/api/me", {"Authorization": f"Bearer {_token(sub=parent_id)}"})
    assert res.status_code == 200 and res.json()["role"] == "parent"

    token = _token(sub=clinician_id, user_metadata={"clinician_invite_code": "secret-123"})
    res = await _get("/api/me", {"Authorization": f"Bearer {token}"})
    assert res.json()["role"] == "clinician"

    res = await _get("/api/me", {"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401


# --- who can see which child ----------------------------------------------------

PARENT_A = CurrentUser("parent-a", "a@test.local", "parent")
PARENT_B = CurrentUser("parent-b", "b@test.local", "parent")
CLINICIAN = CurrentUser("clin-1", "c@test.local", "clinician")


def _as(user):
    app.dependency_overrides[get_current_user] = lambda: user


async def _call(method, path, json=None):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        return await ac.request(method, path, json=json)


@pytest.mark.anyio
async def test_parents_only_see_their_own_children():
    child_id = f"CH-A{uuid.uuid4().hex[:5]}"
    child = {"child_id": child_id, "age_months": 70, "sex": "M", "weight_kg": 18.0,
             "height_cm": 110.0, "muac_cm": 14.0, "growth_trend": "stable"}

    _as(PARENT_A)
    assert (await _call("POST", "/api/child", child)).status_code == 200
    assert child_id in [c["child_id"] for c in (await _call("GET", "/api/children")).json()]

    _as(PARENT_B)
    assert (await _call("GET", f"/api/child/{child_id}")).status_code == 404
    assert (await _call("GET", f"/api/child/{child_id}/history")).status_code == 404
    assert (await _call("POST", "/api/child", {**child, "weight_kg": 1.0})).status_code == 409
    assert (await _call("POST", "/api/assess", {"child": child})).status_code == 409
    meal = {"child_id": child_id, "meals": [{"dish_id": "X", "dish_name": "X", "servings": 1, "serving_size_g": 10}]}
    assert (await _call("POST", "/api/meal-log", meal)).status_code == 404
    assert child_id not in [c["child_id"] for c in (await _call("GET", "/api/children")).json()]
    assert (await _call("POST", "/api/clinician/override",
                        {"trace_id": 1, "new_risk_level": "high", "reason": "x"})).status_code == 403

    _as(CLINICIAN)
    res = await _call("GET", f"/api/child/{child_id}")
    assert res.status_code == 200
    assert res.json()["child"]["weight_kg"] == 18.0     # parent B's update was refused
    assert child_id in [c["child_id"] for c in (await _call("GET", "/api/children")).json()]
