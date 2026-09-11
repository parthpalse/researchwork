CREATE TABLE IF NOT EXISTS dishes (
    record_id TEXT PRIMARY KEY,
    base_ingredient TEXT NOT NULL,
    dish_name TEXT NOT NULL,
    category TEXT NOT NULL,
    cooking_method TEXT NOT NULL,
    fat_medium TEXT,
    moisture_g REAL,
    energy_kcal REAL NOT NULL,
    protein_g REAL NOT NULL,
    total_fat_g REAL NOT NULL,
    carbohydrate_g REAL NOT NULL,
    dietary_fiber_g REAL,
    sugars_g REAL,
    calcium_mg REAL,
    iron_mg REAL,
    zinc_mg REAL,
    potassium_mg REAL,
    sodium_mg REAL,
    vitamin_c_mg REAL,
    thiamin_mg REAL,
    folate_mcg REAL,
    glycemic_index REAL,
    nova_group INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_dishes_name ON dishes(dish_name);
CREATE INDEX IF NOT EXISTS idx_dishes_category ON dishes(category);
