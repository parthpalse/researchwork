import os
import json
import time
import httpx
import asyncio
import random
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

from src.llm.prompts import FOOD_VISION_PROMPT

OTHER_INGREDIENT = "Other"

_rate_lock = asyncio.Lock()
_last_call_at = 0.0


class FoodVisionError(Exception):
    """Raised when the vision model cannot be used. status_code is the HTTP code to return."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def build_response_schema(
    base_ingredients: List[str],
    cooking_methods: List[str],
    fat_media: List[str]
) -> Dict[str, Any]:
    """JSON schema that forces Gemini to choose values from our dataset's own lists."""
    component = {
        "type": "OBJECT",
        "properties": {
            "base_ingredient": {"type": "STRING", "enum": sorted(base_ingredients) + [OTHER_INGREDIENT]},
            "cooking_method": {"type": "STRING", "enum": sorted(cooking_methods)},
            "fat_medium": {"type": "STRING", "enum": sorted(fat_media)},
            "grams": {"type": "NUMBER"},
        },
        "required": ["base_ingredient", "cooking_method", "fat_medium", "grams"],
    }
    item = {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING"},
            "confidence": {"type": "NUMBER"},
            "components": {"type": "ARRAY", "items": component},
        },
        "required": ["name", "confidence", "components"],
    }
    return {
        "type": "OBJECT",
        "properties": {
            "is_food": {"type": "BOOLEAN"},
            "items": {"type": "ARRAY", "items": item},
        },
        "required": ["is_food", "items"],
    }


async def _wait_for_rate_limit(min_interval_s: float) -> None:
    """Allow at most one Gemini call per min_interval_s across the whole app."""
    global _last_call_at
    async with _rate_lock:
        wait = _last_call_at + min_interval_s - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)
        _last_call_at = time.monotonic()


async def identify_foods(
    image_base64: str,
    mime_type: str,
    base_ingredients: List[str],
    cooking_methods: List[str],
    fat_media: List[str],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Ask Gemini what foods are in the image. Returns {'is_food': bool, 'items': [...]}."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise FoodVisionError("Food scanner is not configured (GEMINI_API_KEY missing).", 503)

    gemini = config["gemini"]
    url = f"{gemini['endpoint']}/{gemini['model']}:generateContent"
    headers = {"x-goog-api-key": api_key, "content-type": "application/json"}

    payload = {
        "systemInstruction": {"parts": [{"text": FOOD_VISION_PROMPT}]},
        "contents": [{
            "role": "user",
            "parts": [
                {"inlineData": {"mimeType": mime_type, "data": image_base64}},
                {"text": "Identify the foods in this photo."},
            ],
        }],
        "generationConfig": {
            "temperature": gemini["temperature"],
            "responseMimeType": "application/json",
            "responseSchema": build_response_schema(base_ingredients, cooking_methods, fat_media),
            "thinkingConfig": {"thinkingBudget": gemini["thinking_budget"]},
        },
    }

    max_retries = gemini["max_retries"]
    base_delay = gemini["base_backoff_s"]

    async with httpx.AsyncClient(timeout=gemini["request_timeout_s"]) as client:
        for attempt in range(max_retries):
            await _wait_for_rate_limit(gemini["min_seconds_between_calls"])
            try:
                response = await client.post(url, headers=headers, json=payload)

                # Bad request / bad key will not get better on retry
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    logger.error(f"Gemini rejected request: HTTP {response.status_code}")
                    raise FoodVisionError(
                        f"The food recognition service rejected the request (HTTP {response.status_code}).",
                        502,
                    )

                response.raise_for_status()
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            except (httpx.RequestError, httpx.HTTPStatusError, json.JSONDecodeError, KeyError, IndexError) as e:
                logger.warning(f"Gemini attempt {attempt + 1} failed: {type(e).__name__}")
                if attempt == max_retries - 1:
                    raise FoodVisionError(
                        "The food recognition service is not responding. Please try again "
                        "or search for the dish manually.",
                        502,
                    )

                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                await asyncio.sleep(delay)

    raise FoodVisionError("The food recognition service is not responding.", 502)
