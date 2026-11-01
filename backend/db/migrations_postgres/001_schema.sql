-- Postgres (Supabase) schema: same tables and columns as db/migrations 001-005 (SQLite).
-- Timestamps stay ISO-8601 TEXT so both databases behave the same in the app.

CREATE TABLE IF NOT EXISTS children (
    child_id TEXT PRIMARY KEY,
    age_months INTEGER NOT NULL,
    sex TEXT NOT NULL CHECK (sex IN ('M', 'F')),
    weight_kg DOUBLE PRECISION NOT NULL,
    height_cm DOUBLE PRECISION NOT NULL,
    muac_cm DOUBLE PRECISION NOT NULL,
    growth_trend TEXT NOT NULL,
    weight_for_height_z DOUBLE PRECISION,
    muac_risk_band TEXT,
    created_at TEXT NOT NULL DEFAULT (now()::text),
    updated_at TEXT NOT NULL DEFAULT (now()::text)
);

CREATE TABLE IF NOT EXISTS traces (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    child_id TEXT NOT NULL REFERENCES children(child_id),
    timestamp TEXT NOT NULL,
    trace_json TEXT NOT NULL,
    explanation_json TEXT,
    final_risk_level TEXT NOT NULL,
    final_confidence DOUBLE PRECISION NOT NULL,
    clinician_override TEXT,
    override_reason TEXT,
    override_at TEXT,
    created_at TEXT NOT NULL DEFAULT (now()::text)
);
CREATE INDEX IF NOT EXISTS idx_traces_child_id ON traces(child_id);
CREATE INDEX IF NOT EXISTS idx_traces_timestamp ON traces(timestamp);

CREATE TABLE IF NOT EXISTS meal_logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    child_id TEXT NOT NULL REFERENCES children(child_id),
    log_date TEXT NOT NULL,
    meals_json TEXT NOT NULL,
    nutrient_summary_json TEXT,
    created_at TEXT NOT NULL DEFAULT (now()::text)
);
CREATE INDEX IF NOT EXISTS idx_meal_logs_child ON meal_logs(child_id);

CREATE TABLE IF NOT EXISTS dishes (
    record_id TEXT PRIMARY KEY,
    base_ingredient TEXT NOT NULL,
    dish_name TEXT NOT NULL,
    category TEXT NOT NULL,
    cooking_method TEXT NOT NULL,
    fat_medium TEXT,
    moisture_g DOUBLE PRECISION,
    energy_kcal DOUBLE PRECISION NOT NULL,
    protein_g DOUBLE PRECISION NOT NULL,
    total_fat_g DOUBLE PRECISION NOT NULL,
    carbohydrate_g DOUBLE PRECISION NOT NULL,
    dietary_fiber_g DOUBLE PRECISION,
    sugars_g DOUBLE PRECISION,
    calcium_mg DOUBLE PRECISION,
    iron_mg DOUBLE PRECISION,
    zinc_mg DOUBLE PRECISION,
    potassium_mg DOUBLE PRECISION,
    sodium_mg DOUBLE PRECISION,
    vitamin_c_mg DOUBLE PRECISION,
    thiamin_mg DOUBLE PRECISION,
    folate_mcg DOUBLE PRECISION,
    glycemic_index DOUBLE PRECISION,
    nova_group INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_dishes_name ON dishes(dish_name);
CREATE INDEX IF NOT EXISTS idx_dishes_category ON dishes(category);

CREATE TABLE IF NOT EXISTS packaged_products (
    record_id TEXT PRIMARY KEY,
    barcode TEXT NOT NULL UNIQUE,
    dish_name TEXT NOT NULL,
    category TEXT NOT NULL,
    energy_kcal DOUBLE PRECISION NOT NULL,
    protein_g DOUBLE PRECISION NOT NULL,
    total_fat_g DOUBLE PRECISION NOT NULL,
    carbohydrate_g DOUBLE PRECISION NOT NULL,
    dietary_fiber_g DOUBLE PRECISION,
    sugars_g DOUBLE PRECISION,
    added_sugars_g DOUBLE PRECISION,
    calcium_mg DOUBLE PRECISION,
    iron_mg DOUBLE PRECISION,
    zinc_mg DOUBLE PRECISION,
    sodium_mg DOUBLE PRECISION,
    vitamin_c_mg DOUBLE PRECISION,
    thiamin_mg DOUBLE PRECISION,
    folate_mcg DOUBLE PRECISION,
    glycemic_index DOUBLE PRECISION,
    nova_group INTEGER NOT NULL,
    serving_g DOUBLE PRECISION,
    allergens_json TEXT NOT NULL,
    source TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);

-- The API reaches these tables with its own database login; block Supabase's public
-- REST API (anon key) from reading or writing them directly.
ALTER TABLE children ENABLE ROW LEVEL SECURITY;
ALTER TABLE traces ENABLE ROW LEVEL SECURITY;
ALTER TABLE meal_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE dishes ENABLE ROW LEVEL SECURITY;
ALTER TABLE packaged_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE schema_migrations ENABLE ROW LEVEL SECURITY;
