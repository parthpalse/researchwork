import os
import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

raw_url = os.getenv("DATABASE_URL")
if not raw_url:
    backend_dir = Path(__file__).parent.parent.parent
    db_path = backend_dir / "data" / "app.db"
else:
    # Strip URL schemes if passed like sqlite:/// or sqlite+aiosqlite:///
    clean = raw_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
    db_path = Path(clean)

db_path.parent.mkdir(parents=True, exist_ok=True)
DB_FILE = str(db_path)
MIGRATIONS_DIR = Path(__file__).parent.parent.parent / "db" / "migrations"

_db_conn = None

async def init_db():
    global _db_conn
    if _db_conn is None:
        _db_conn = await aiosqlite.connect(DB_FILE)
        _db_conn.row_factory = aiosqlite.Row

        # Run numbered migrations in order
        if MIGRATIONS_DIR.exists():
            migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
            for migration in migrations:
                logger.info(f"Running migration {migration.name}")
                with open(migration, "r", encoding="utf-8") as f:
                    script = f.read()
                    await _db_conn.executescript(script)
            await _db_conn.commit()

async def close_db():
    global _db_conn
    if _db_conn:
        await _db_conn.close()
        _db_conn = None

@asynccontextmanager
async def get_db():
    global _db_conn
    if not _db_conn:
        await init_db()
    yield _db_conn
