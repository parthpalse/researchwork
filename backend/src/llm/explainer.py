import os
import json
import logging

import anthropic

logger = logging.getLogger(__name__)

from src.llm.prompts import SYSTEM_PROMPT

EXPLAINER_MODEL = "claude-haiku-5-5"

# Structured output: the API guarantees the reply is JSON matching this schema
EXPLANATION_SCHEMA = {
    "type": "object",
    "properties": {
        "parent_message": {"type": "string"},
        "suggested_next_step": {"type": "string"},
        "clinician_note": {"type": "string"},
    },
    "required": ["parent_message", "suggested_next_step", "clinician_note"],
    "additionalProperties": False,
}


async def explain_trace(trace: dict) -> dict:
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        return _fallback_explanation(trace)

    # The SDK retries connection errors, 429 and 5xx with exponential backoff + jitter
    client = anthropic.AsyncAnthropic(api_key=api_key, timeout=30.0, max_retries=3)

    try:
        response = await client.messages.create(
            model=EXPLAINER_MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": f"Here is the trace:\n{json.dumps(trace)}"}
            ],
            output_config={
                "effort": "low",
                "format": {"type": "json_schema", "schema": EXPLANATION_SCHEMA},
            },
        )
    except anthropic.APIStatusError as e:
        logger.error(f"Claude API error (HTTP {e.status_code}), using fallback.")
        return _fallback_explanation(trace)
    except anthropic.APIConnectionError as e:
        logger.error(f"Claude API unreachable ({type(e).__name__}), using fallback.")
        return _fallback_explanation(trace)
    finally:
        await client.close()

    if response.stop_reason != "end_turn":
        logger.warning(f"Claude stopped with '{response.stop_reason}', using fallback.")
        return _fallback_explanation(trace)

    text = next((b.text for b in response.content if b.type == "text"), None)
    try:
        return json.loads(text) if text else _fallback_explanation(trace)
    except json.JSONDecodeError:
        logger.error("Claude returned invalid JSON, using fallback.")
        return _fallback_explanation(trace)

def _fallback_explanation(trace: dict) -> dict:
    risk = trace.get("final_risk_level", "Unknown")
    rules = trace.get("rules_fired", [])
    rule_ids = [r.get("rule_id") for r in rules]

    msg = "We've noticed some areas where the child's nutrition could use a little extra attention."
    if risk == "Low":
        msg = "Everything looks to be on a great track! Keep up the good work."

    return {
        "parent_message": msg,
        "suggested_next_step": "Try incorporating one extra serving of vegetables today.",
        "clinician_note": f"Fallback explanation used. Rules fired: {rule_ids}"
    }
