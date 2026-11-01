import json
import types
import pytest
from src.llm import explainer

TRACE = {"final_risk_level": "Low", "rules_fired": [{"rule_id": "R3"}]}
REPLY = {"parent_message": "Lovely progress!", "suggested_next_step": "Add a fruit at lunch.",
         "clinician_note": "R3 fired: normal WHZ and MUAC."}


class FakeClient:
    """Stands in for anthropic.AsyncAnthropic; records the request it receives."""
    last_request = None
    response = None
    error = None

    def __init__(self, **kwargs):
        self.init_kwargs = kwargs
        self.messages = self

    async def create(self, **request):
        FakeClient.last_request = request
        if FakeClient.error:
            raise FakeClient.error
        return FakeClient.response

    async def close(self):
        pass


def _response(text, stop_reason="end_turn"):
    return types.SimpleNamespace(
        stop_reason=stop_reason,
        content=[types.SimpleNamespace(type="text", text=text)],
    )


@pytest.fixture
def fake_claude(monkeypatch):
    monkeypatch.setenv("CLAUDE_API_KEY", "test-key")
    monkeypatch.setattr(explainer.anthropic, "AsyncAnthropic", FakeClient)
    FakeClient.last_request = None
    FakeClient.error = None
    return FakeClient


@pytest.mark.anyio
async def test_no_key_uses_fallback(monkeypatch):
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)
    result = await explainer.explain_trace(TRACE)
    assert "Fallback" in result["clinician_note"]


@pytest.mark.anyio
async def test_success_uses_current_model_and_json_schema(fake_claude):
    fake_claude.response = _response(json.dumps(REPLY))
    result = await explainer.explain_trace(TRACE)
    assert result == REPLY
    request = fake_claude.last_request
    assert request["model"] == "claude-haiku-5-5"
    assert request["output_config"]["format"]["type"] == "json_schema"
    assert "temperature" not in request  # sampling params are rejected by current models


@pytest.mark.anyio
async def test_refusal_uses_fallback(fake_claude):
    fake_claude.response = _response("", stop_reason="refusal")
    result = await explainer.explain_trace(TRACE)
    assert "Fallback" in result["clinician_note"]


@pytest.mark.anyio
async def test_api_error_uses_fallback(fake_claude):
    import httpx2
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    fake_claude.error = explainer.anthropic.APIConnectionError(request=request)
    result = await explainer.explain_trace(TRACE)
    assert "Fallback" in result["clinician_note"]
