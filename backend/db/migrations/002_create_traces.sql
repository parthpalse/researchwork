CREATE TABLE IF NOT EXISTS traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id TEXT NOT NULL REFERENCES children(child_id),
    timestamp TEXT NOT NULL,
    trace_json TEXT NOT NULL,  -- full TraceObject as JSON
    explanation_json TEXT,     -- LLMExplanation as JSON
    final_risk_level TEXT NOT NULL,
    final_confidence REAL NOT NULL,
    clinician_override TEXT,   -- overridden risk level, if any
    override_reason TEXT,
    override_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_traces_child_id ON traces(child_id);
CREATE INDEX IF NOT EXISTS idx_traces_timestamp ON traces(timestamp);
