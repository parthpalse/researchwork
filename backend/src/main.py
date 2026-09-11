from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import csv
import logging
from src.db.connection import init_db, close_db, get_db
from src.api import assess, history, clinician, meals, trace

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    await init_db()
    logger.info("Loading dish dataset if needed...")
    await load_dishes_csv()
    yield
    # Shutdown
    await close_db()

app = FastAPI(
    title="Trust-First AI Nutrition Risk System API",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assess.router)
app.include_router(history.router)
app.include_router(clinician.router)
app.include_router(meals.router)
app.include_router(trace.router)

@app.get("/api/health")
async def health():
    return {"status": "ok", "system": "Trust-First AI Nutrition Risk Engine"}

async def load_dishes_csv():
    """Load Indian dishes dataset (20,000 records) into SQLite table in batches."""
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    default_csv = os.path.join(backend_dir, "data", "indian_dishes.csv")
    csv_path = os.getenv("DISHES_CSV_PATH", default_csv)

    if not os.path.exists(csv_path):
        logger.warning(f"Dishes CSV not found at {csv_path}. Skipping initial load.")
        return

    async with get_db() as db:
        async with db.execute("SELECT COUNT(*) as count FROM dishes") as cursor:
            row = await cursor.fetchone()
            if row and row['count'] > 0:
                logger.info(f"Dishes table already populated with {row['count']} records.")
                return

        logger.info(f"Populating dishes table from {csv_path}...")
        batch = []
        batch_size = 2000

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                batch.append((
                    r.get('Record_ID', ''),
                    r.get('Base_Ingredient_Name', ''),
                    r.get('Dish_Variant_Name', ''),
                    r.get('Category', ''),
                    r.get('Cooking_Method', ''),
                    r.get('Fat_Medium_Used', ''),
                    float(r.get('Moisture_g') or 0.0),
                    float(r.get('Energy_kcal') or 0.0),
                    float(r.get('Protein_g') or 0.0),
                    float(r.get('Total_Fat_g') or 0.0),
                    float(r.get('Carbohydrate_g') or 0.0),
                    float(r.get('Dietary_Fiber_g') or 0.0),
                    float(r.get('Sugars_g') or 0.0),
                    float(r.get('Calcium_mg') or 0.0),
                    float(r.get('Iron_mg') or 0.0),
                    float(r.get('Zinc_mg') or 0.0),
                    float(r.get('Potassium_mg') or 0.0),
                    float(r.get('Sodium_mg') or 0.0),
                    float(r.get('Vitamin_C_mg') or 0.0),
                    float(r.get('Thiamin_B1_mg') or 0.0),
                    float(r.get('Folate_mcg') or 0.0),
                    float(r.get('Glycemic_Index_Est') or 0.0),
                    int(r.get('NOVA_Group') or 1)
                ))

                if len(batch) >= batch_size:
                    await db.executemany("""
                        INSERT INTO dishes (
                            record_id, base_ingredient, dish_name, category, cooking_method, fat_medium,
                            moisture_g, energy_kcal, protein_g, total_fat_g, carbohydrate_g, dietary_fiber_g,
                            sugars_g, calcium_mg, iron_mg, zinc_mg, potassium_mg, sodium_mg, vitamin_c_mg,
                            thiamin_mg, folate_mcg, glycemic_index, nova_group
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, batch)
                    batch = []

            if batch:
                await db.executemany("""
                    INSERT INTO dishes (
                        record_id, base_ingredient, dish_name, category, cooking_method, fat_medium,
                        moisture_g, energy_kcal, protein_g, total_fat_g, carbohydrate_g, dietary_fiber_g,
                        sugars_g, calcium_mg, iron_mg, zinc_mg, potassium_mg, sodium_mg, vitamin_c_mg,
                        thiamin_mg, folate_mcg, glycemic_index, nova_group
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)

        await db.commit()
        logger.info("Dishes table successfully populated.")
