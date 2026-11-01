from fastapi import APIRouter, Depends, HTTPException
from src.auth.users import CurrentUser, get_current_user, check_child_access
from src.db.connection import get_db
import json

router = APIRouter(prefix="/api", tags=["trace"])

@router.get("/child/{child_id}/trace/{trace_id}")
async def get_trace(child_id: str, trace_id: int, user: CurrentUser = Depends(get_current_user)):
    async with get_db() as db:
        await check_child_access(db, child_id, user)
        async with db.execute("""
            SELECT trace_json, explanation_json
            FROM traces
            WHERE child_id = ? AND id = ?
        """, (child_id, trace_id)) as cursor:
            row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Trace not found")

    return {
        "trace": json.loads(row['trace_json']),
        "explanation": json.loads(row['explanation_json'] or '{}')
    }
