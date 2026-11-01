from fastapi import APIRouter, Body, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime, timezone
from src.auth.users import require_clinician
from src.db.connection import get_db

# Overrides change a child's risk level: clinicians only
router = APIRouter(prefix="/api/clinician", tags=["clinician"], dependencies=[Depends(require_clinician)])

@router.post("/override")
async def override_trace(payload: Dict[str, Any] = Body(...)):
    trace_id = payload.get("trace_id")
    new_risk = payload.get("new_risk_level")
    reason = payload.get("reason")

    if not all([trace_id, new_risk, reason]):
        raise HTTPException(status_code=400, detail="Missing fields")
    try:
        trace_id = int(trace_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="trace_id must be a number")

    async with get_db() as db:
        await db.execute("""
            UPDATE traces
            SET clinician_override = ?, override_reason = ?, override_at = ?
            WHERE id = ?
        """, (new_risk, reason, datetime.now(timezone.utc).isoformat(), trace_id))
        await db.commit()
        
        async with db.execute("SELECT * FROM traces WHERE id = ?", (trace_id,)) as cursor:
            row = await cursor.fetchone()
            
    if not row:
        raise HTTPException(status_code=404, detail="Trace not found")
        
    return dict(row)
