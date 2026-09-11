CREATE TABLE IF NOT EXISTS meal_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id TEXT NOT NULL REFERENCES children(child_id),
    log_date TEXT NOT NULL,
    meals_json TEXT NOT NULL,  -- list of MealEntry as JSON
    nutrient_summary_json TEXT,  -- NutrientSummary as JSON
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_meal_logs_child ON meal_logs(child_id);
