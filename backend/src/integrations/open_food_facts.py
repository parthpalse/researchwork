import time
import httpx
import asyncio
import random
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

PRODUCT_FIELDS = "code,product_name,brands,nutriments,allergens_tags,serving_quantity,nova_group"

_rate_lock = asyncio.Lock()
_last_call_at = 0.0


class OpenFoodFactsError(Exception):
    """Raised when Open Food Facts cannot be reached. status_code is the HTTP code to return."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


async def _wait_for_rate_limit(min_interval_s: float) -> None:
    global _last_call_at
    async with _rate_lock:
        wait = _last_call_at + min_interval_s - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)
        _last_call_at = time.monotonic()


async def fetch_product(barcode: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return the OFF 'product' object for a barcode, or None if OFF does not know it."""
    off = config["open_food_facts"]
    url = f"{off['endpoint']}/{barcode}.json"
    headers = {"User-Agent": off["user_agent"]}
    params = {"fields": PRODUCT_FIELDS}

    max_retries = off["max_retries"]
    base_delay = off["base_backoff_s"]

    async with httpx.AsyncClient(timeout=off["request_timeout_s"]) as client:
        for attempt in range(max_retries):
            await _wait_for_rate_limit(off["min_seconds_between_calls"])
            try:
                response = await client.get(url, headers=headers, params=params)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                data = response.json()
                if data.get("status") == 0 or not data.get("product"):
                    return None
                return data["product"]
            except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
                logger.warning(f"Open Food Facts attempt {attempt + 1} failed: {type(e).__name__}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    await asyncio.sleep(delay)

    raise OpenFoodFactsError(
        "The packaged food database is not responding. Please try again later.", 502
    )
