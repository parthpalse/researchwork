CREATE TABLE IF NOT EXISTS children (
    child_id TEXT PRIMARY KEY,
    age_months INTEGER NOT NULL,
    sex TEXT NOT NULL CHECK(sex IN ('M', 'F')),
    weight_kg REAL NOT NULL,
    height_cm REAL NOT NULL,
    muac_cm REAL NOT NULL,
    growth_trend TEXT NOT NULL,
    weight_for_height_z REAL,
    muac_risk_band TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
