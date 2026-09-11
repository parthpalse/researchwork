import os
import json
import httpx
import asyncio
import random
import logging

logger = logging.getLogger(__name__)

from src.llm.prompts import SYSTEM_PROMPT

async def explain_trace(trace: dict) -> dict:
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        return _fallback_explanation(trace)
        
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 512,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": f"Here is the trace:\n{json.dumps(trace)}"}
        ]
    }

    max_retries = 3
    base_delay = 1.0

    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(max_retries):
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["content"][0]["text"]
                return json.loads(content)
            except (httpx.RequestError, httpx.HTTPStatusError, json.JSONDecodeError) as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error("All attempts failed, using fallback.")
                    return _fallback_explanation(trace)
                
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                await asyncio.sleep(delay)

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
