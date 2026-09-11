from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any, List, Optional
import json
from src.db.connection import get_db
from src.engine.dietary import calculate_nutrient_summary
from datetime import datetime, timezone

router = APIRouter(prefix="/api", tags=["meals"])

@router.post("/meal-log")
async def add_meal_log(payload: Dict[str, Any] = Body(...)):
    """Log meals for a child, calculate full nutritional breakdown from 20k dishes database,
    and persist log to database."""
    child_id = payload.get("child_id", "unknown")
    meals = payload.get("meals", [])
    log_date = payload.get("date", datetime.now(timezone.utc).date().isoformat())

    if not meals:
        raise HTTPException(status_code=422, detail="Meals list cannot be empty")

    dish_ids = [m.get("dish_id") for m in meals if m.get("dish_id")]

    async with get_db() as db:
        # Fetch matching dishes in one query
        placeholders = ",".join("?" for _ in dish_ids)
        query = f"SELECT * FROM dishes WHERE record_id IN ({placeholders})"
        async with db.execute(query, dish_ids) as cursor:
            rows = await cursor.fetchall()

        dish_lookup = {r["record_id"]: dict(r) for r in rows}

        # Calculate comprehensive nutrient summary
        nutrients = calculate_nutrient_summary(meals, dish_lookup)

        # Store in database
        await db.execute("""
            INSERT INTO meal_logs (child_id, log_date, meals_json, nutrient_summary_json, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            child_id,
            log_date,
            json.dumps(meals),
            json.dumps(nutrients),
            datetime.now(timezone.utc).isoformat()
        ))
        await db.commit()

    return {
        "child_id": child_id,
        "date": log_date,
        "meals_count": len(meals),
        "nutrient_summary": nutrients
    }

@router.get("/dishes/search")
async def search_dishes(q: str = "", category: Optional[str] = None, limit: int = 25):
    """Search dishes by name or ingredient with optional category filter."""
    async with get_db() as db:
        clauses = []
        params: List[Any] = []

        if q:
            clauses.append("(dish_name LIKE ? OR base_ingredient LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%"])

        if category:
            clauses.append("category = ?")
            params.append(category)

        where_stmt = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        query = f"""
            SELECT record_id, base_ingredient, dish_name, category, cooking_method,
                   energy_kcal, protein_g, total_fat_g, carbohydrate_g, sugars_g,
                   iron_mg, glycemic_index, nova_group
            FROM dishes
            {where_stmt}
            LIMIT ?
        """
        params.append(limit)

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()

    return [dict(r) for r in rows]

@router.get("/dishes/categories")
async def list_categories():
    """List distinct dish categories available in the database."""
    async with get_db() as db:
        async with db.execute("SELECT DISTINCT category FROM dishes ORDER BY category") as cursor:
            rows = await cursor.fetchall()
    return [r["category"] for r in rows if r["category"]]
