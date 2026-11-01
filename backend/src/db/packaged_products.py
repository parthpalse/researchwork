"""
Read/write cache of packaged products (Open Food Facts) in the packaged_products table.
Rows come back in the same per-100 g dish format used by the rest of the app.
"""
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from src.db.connection import get_db

_COLUMNS = (
    "record_id", "barcode", "dish_name", "category", "energy_kcal", "protein_g", "total_fat_g",
    "carbohydrate_g", "dietary_fiber_g", "sugars_g", "added_sugars_g", "calcium_mg", "iron_mg",
    "zinc_mg", "sodium_mg", "vitamin_c_mg", "thiamin_mg", "folate_mcg", "glycemic_index",
    "nova_group", "serving_g",
)


def _row_to_product(row) -> Dict[str, Any]:
    product = {key: row[key] for key in _COLUMNS}
    product["allergens"] = json.loads(row["allergens_json"])
    product["source"] = row["source"]
    product["fetched_at"] = row["fetched_at"]
    return product


async def get_cached_product(barcode: str, cache_days: int) -> Optional[Dict[str, Any]]:
    """Return the cached product if it was fetched within cache_days, else None."""
    async with get_db() as db:
        async with db.execute("SELECT * FROM packaged_products WHERE barcode = ?", (barcode,)) as cursor:
            row = await cursor.fetchone()
    if row is None:
        return None
    fetched_at = datetime.fromisoformat(row["fetched_at"])
    if datetime.now(timezone.utc) - fetched_at > timedelta(days=cache_days):
        return None
    return _row_to_product(row)


async def save_product(product: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Insert or refresh a product; records where it came from and when."""
    fetched_at = datetime.now(timezone.utc).isoformat()
    values = [product.get(key) for key in _COLUMNS]
    placeholders = ", ".join("?" for _ in range(len(_COLUMNS) + 3))
    async with get_db() as db:
        await db.execute(
            f"INSERT OR REPLACE INTO packaged_products ({', '.join(_COLUMNS)}, allergens_json, source, fetched_at) "
            f"VALUES ({placeholders})",
            values + [json.dumps(product.get("allergens", [])), source, fetched_at],
        )
        await db.commit()
    return {**product, "source": source, "fetched_at": fetched_at}


async def load_products_by_ids(record_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Map record_id -> product for the given 'OFF-...' ids (unknown ids are skipped)."""
    if not record_ids:
        return {}
    placeholders = ",".join("?" for _ in record_ids)
    async with get_db() as db:
        async with db.execute(
            f"SELECT * FROM packaged_products WHERE record_id IN ({placeholders})", record_ids
        ) as cursor:
            rows = await cursor.fetchall()
    return {row["record_id"]: _row_to_product(row) for row in rows}
