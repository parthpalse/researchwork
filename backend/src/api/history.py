from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from src.auth.users import CurrentUser, get_current_user, check_child_access
from src.db.connection import get_db

router = APIRouter(prefix="/api", tags=["history"])

@router.get("/child/{child_id}/history")
async def get_history(child_id: str, user: CurrentUser = Depends(get_current_user)):
    async with get_db() as db:
        await check_child_access(db, child_id, user)
        async with db.execute("""
            SELECT timestamp, final_risk_level, final_confidence, clinician_override
            FROM traces
            WHERE child_id = ?
            ORDER BY timestamp DESC
        """, (child_id,)) as cursor:
            rows = await cursor.fetchall()

    return [
        {
            "timestamp": r['timestamp'],
            "final_risk_level": r['final_risk_level'],
            "final_confidence": r['final_confidence'],
            "has_override": r['clinician_override'] is not None
        }
        for r in rows
    ]
