import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from src.auth.users import CurrentUser, get_current_user, check_child_access
from src.db.connection import get_db
from src.models.child import ChildInput

router = APIRouter(prefix="/api", tags=["child"])

RECENT_MEAL_LOGS = 10


@router.get("/children")
async def list_children(user: CurrentUser = Depends(get_current_user)):
    """Parents: their own children. Clinicians: every child. Newest first, with latest risk."""
    query = """
        SELECT c.child_id, c.age_months, c.sex, c.updated_at,
               (SELECT t.final_risk_level FROM traces t WHERE t.child_id = c.child_id ORDER BY t.id DESC LIMIT 1) AS risk,
               (SELECT t.clinician_override FROM traces t WHERE t.child_id = c.child_id ORDER BY t.id DESC LIMIT 1) AS override
        FROM children c
    """
    params: tuple = ()
    if not user.is_clinician:
        query += " WHERE c.owner_id = ?"
        params = (user.user_id,)
    query += " ORDER BY c.updated_at DESC LIMIT 200"

    async with get_db() as db:
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
    return [
        {"child_id": r["child_id"], "age_months": r["age_months"], "sex": r["sex"],
         "updated_at": r["updated_at"], "latest_risk": r["override"] or r["risk"]}
        for r in rows
    ]


@router.post("/child")
async def save_child(child: ChildInput, user: CurrentUser = Depends(get_current_user)):
    """Create or update a child's details (step 1), before meals are logged.
    Calculated fields (z-score, MUAC band) are filled in by /api/assess."""
    now = datetime.now(timezone.utc).isoformat()
    async with get_db() as db:
        await check_child_access(db, child.child_id, user, allow_new=True)
        # owner_id is set only when the child is created; updates never change the owner
        await db.execute("""
            INSERT INTO children (child_id, age_months, sex, weight_kg, height_cm, muac_cm, growth_trend, updated_at, owner_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(child_id) DO UPDATE SET
                age_months = excluded.age_months, sex = excluded.sex, weight_kg = excluded.weight_kg,
                height_cm = excluded.height_cm, muac_cm = excluded.muac_cm,
                growth_trend = excluded.growth_trend, updated_at = excluded.updated_at
        """, (child.child_id, child.age_months, child.sex, child.weight_kg, child.height_cm,
              child.muac_cm, child.growth_trend.value, now, user.user_id))
        await db.commit()
    return {"child_id": child.child_id, "saved_at": now}


@router.get("/child/{child_id}")
async def get_child_overview(child_id: str, user: CurrentUser = Depends(get_current_user)):
    """Everything the parent and clinician views need: details, latest assessment, recent meals."""
    async with get_db() as db:
        await check_child_access(db, child_id, user)
        async with db.execute("SELECT * FROM children WHERE child_id = ?", (child_id,)) as cursor:
            child = await cursor.fetchone()

        async with db.execute("""
            SELECT id, trace_json, explanation_json, clinician_override, override_reason
            FROM traces WHERE child_id = ? ORDER BY id DESC LIMIT 1
        """, (child_id,)) as cursor:
            trace_row = await cursor.fetchone()

        async with db.execute("""
            SELECT id, log_date, meals_json, nutrient_summary_json, created_at
            FROM meal_logs WHERE child_id = ? ORDER BY id DESC LIMIT ?
        """, (child_id, RECENT_MEAL_LOGS)) as cursor:
            log_rows = await cursor.fetchall()

    latest = None
    if trace_row is not None:
        trace = json.loads(trace_row["trace_json"])
        if trace_row["clinician_override"]:
            trace["final_risk_level"] = trace_row["clinician_override"]
        latest = {
            "trace_id": trace_row["id"],
            "trace": trace,
            "explanation": json.loads(trace_row["explanation_json"] or "{}"),
            "clinician_override": trace_row["clinician_override"],
            "override_reason": trace_row["override_reason"],
        }

    return {
        "child": {
            "child_id": child["child_id"],
            "age_months": child["age_months"],
            "sex": child["sex"],
            "weight_kg": child["weight_kg"],
            "height_cm": child["height_cm"],
            "muac_cm": child["muac_cm"],
            "growth_trend": child["growth_trend"],
        },
        "latest_assessment": latest,
        "meal_logs": [
            {
                "id": r["id"],
                "log_date": r["log_date"],
                "meals": json.loads(r["meals_json"]),
                "nutrient_summary": json.loads(r["nutrient_summary_json"] or "null"),
                "created_at": r["created_at"],
            }
            for r in log_rows
        ],
    }
