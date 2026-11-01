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
_last_call_at: Dict[str, float] = {}


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


async def _wait_for_rate_limit(model: str, min_interval_s: float) -> None:
    """Allow at most one call per min_interval_s to each model (quotas are per model)."""
    async with _rate_lock:
        wait = _last_call_at.get(model, 0.0) + min_interval_s - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)
        _last_call_at[model] = time.monotonic()


async def identify_foods(
    image_base64: str,
    mime_type: str,
    base_ingredients: List[str],
    cooking_methods: List[str],
    fat_media: List[str],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Ask Gemini what foods are in the image.

    Returns {'is_food': bool, 'items': [...], 'model': <model that answered>}.
    Tries config model first, then each fallback model when one is rate-limited (429)
    or keeps failing.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise FoodVisionError("Food scanner is not configured (GEMINI_API_KEY missing).", 503)

    gemini = config["gemini"]
    models = [gemini["model"]] + list(gemini.get("fallback_models", []))
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
    rate_limited = 0

    async with httpx.AsyncClient(timeout=gemini["request_timeout_s"]) as client:
        for model in models:
            url = f"{gemini['endpoint']}/{model}:generateContent"
            for attempt in range(max_retries):
                await _wait_for_rate_limit(model, gemini["min_seconds_between_calls"])
                try:
                    response = await client.post(url, headers=headers, json=payload)

                    # Free-tier quotas are per model and often daily: retrying the
                    # same model will not help, so move on to the next one
                    if response.status_code == 429:
                        logger.warning(f"Gemini model {model} is rate-limited (HTTP 429)")
                        rate_limited += 1
                        break

                    # Bad request / bad key will not get better on retry
                    if 400 <= response.status_code < 500:
                        logger.error(f"Gemini rejected request: HTTP {response.status_code}")
                        raise FoodVisionError(
                            f"The food recognition service rejected the request (HTTP {response.status_code}).",
                            502,
                        )

                    response.raise_for_status()
                    data = response.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    result = json.loads(text)
                    result["model"] = model
                    return result
                except (httpx.RequestError, httpx.HTTPStatusError, json.JSONDecodeError, KeyError, IndexError) as e:
                    logger.warning(f"Gemini {model} attempt {attempt + 1} failed: {type(e).__name__}")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                        await asyncio.sleep(delay)

    if rate_limited == len(models):
        raise FoodVisionError(
            "The free food-recognition limit is used up for now. Please try again later "
            "or search for the dish manually.",
            429,
        )
    raise FoodVisionError(
        "The food recognition service is not responding. Please try again "
        "or search for the dish manually.",
        502,
    )
