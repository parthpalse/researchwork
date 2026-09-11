import os
import yaml
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, Body, HTTPException
from src.db.connection import get_db
from src.engine.trace_builder import build_trace
from src.engine.zscore import compute_weight_for_height_z, classify_muac
from src.llm.explainer import explain_trace
from src.models.child import ChildInput

router = APIRouter(prefix="/api", tags=["assess"])

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
THRESHOLDS_PATH = CONFIG_DIR / "thresholds.yaml"
RDA_PATH = CONFIG_DIR / "rda_children.yaml"

def _load_configs():
    with open(THRESHOLDS_PATH, "r", encoding="utf-8") as f:
        thresholds_cfg = yaml.safe_load(f)
    with open(RDA_PATH, "r", encoding="utf-8") as f:
        rda_cfg = yaml.safe_load(f)
    return thresholds_cfg, rda_cfg

@router.post("/assess")
async def assess(payload: Dict[str, Any] = Body(...)):
    """Assess child nutritional risk from anthropometrics and optional meal summary.

    Expects payload with:
      - child: dict matching ChildInput schema (or top-level fields)
      - meal_summary / nutrient_summary: optional aggregated nutrients
    """
    # Extract child input data
    child_data = payload.get("child", payload)
    nutrient_summary = payload.get("nutrient_summary") or payload.get("meal_summary")

    # Validate minimal fields
    required_fields = ["child_id", "age_months", "sex", "weight_kg", "height_cm", "muac_cm", "growth_trend"]
    for field in required_fields:
        if field not in child_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")

    # Load configuration
    try:
        thresholds_cfg, rda_cfg = _load_configs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load engine configuration: {str(e)}")

    # 1. Execute reasoning engine pipeline -> TraceObject
    trace_obj = build_trace(
        child_input=child_data,
        nutrient_summary=nutrient_summary,
        config=thresholds_cfg,
        rda_config=rda_cfg
    )

    # 2. Generate LLM explanation strictly from trace object
    explanation = await explain_trace(trace_obj)

    # 3. Store child and trace in DB
    async with get_db() as db:
        wfh_z = trace_obj.get("_metadata", {}).get("weight_for_height_z", 0.0)
        muac_band = trace_obj.get("_metadata", {}).get("muac_risk_band", "normal")

        await db.execute("""
            INSERT OR REPLACE INTO children 
            (child_id, age_months, sex, weight_kg, height_cm, muac_cm, growth_trend, weight_for_height_z, muac_risk_band, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            child_data['child_id'],
            child_data['age_months'],
            child_data['sex'],
            child_data['weight_kg'],
            child_data['height_cm'],
            child_data['muac_cm'],
            child_data['growth_trend'],
            wfh_z,
            muac_band,
            datetime.now(timezone.utc).isoformat()
        ))

        cursor = await db.execute("""
            INSERT INTO traces
            (child_id, timestamp, trace_json, explanation_json, final_risk_level, final_confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            child_data['child_id'],
            trace_obj.get('timestamp', datetime.now(timezone.utc).isoformat()),
            json.dumps(trace_obj),
            json.dumps(explanation),
            trace_obj.get('final_risk_level', 'normal'),
            trace_obj.get('final_confidence', 0.0)
        ))
        trace_id = cursor.lastrowid
        await db.commit()

    return {
        "trace_id": trace_id,
        "trace": trace_obj,
        "explanation": explanation
    }
