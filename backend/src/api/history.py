from fastapi import APIRouter
from typing import List, Dict, Any
from src.db.connection import get_db

router = APIRouter(prefix="/api", tags=["history"])

@router.get("/child/{child_id}/history")
async def get_history(child_id: str):
    async with get_db() as db:
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
