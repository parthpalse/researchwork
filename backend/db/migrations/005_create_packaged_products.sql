-- Packaged foods looked up by barcode (Open Food Facts), cached locally.
-- Nutrient columns use the same names and per-100 g units as the dishes table so
-- meal logging and nutrient summaries treat both the same way.
CREATE TABLE IF NOT EXISTS packaged_products (
    record_id TEXT PRIMARY KEY,          -- 'OFF-<barcode>'
    barcode TEXT NOT NULL UNIQUE,
    dish_name TEXT NOT NULL,             -- product name (+ brand)
    category TEXT NOT NULL,
    energy_kcal REAL NOT NULL,
    protein_g REAL NOT NULL,
    total_fat_g REAL NOT NULL,
    carbohydrate_g REAL NOT NULL,
    dietary_fiber_g REAL,
    sugars_g REAL,
    added_sugars_g REAL,                 -- NULL when the label does not say
    calcium_mg REAL,
    iron_mg REAL,
    zinc_mg REAL,
    sodium_mg REAL,
    vitamin_c_mg REAL,
    thiamin_mg REAL,
    folate_mcg REAL,
    glycemic_index REAL,
    nova_group INTEGER NOT NULL,
    serving_g REAL,
    allergens_json TEXT NOT NULL,        -- JSON list of allergen group names
    source TEXT NOT NULL,                -- e.g. 'openfoodfacts'
    fetched_at TEXT NOT NULL             -- ISO-8601 UTC
);
CREATE INDEX IF NOT EXISTS idx_packaged_barcode ON packaged_products(barcode);
