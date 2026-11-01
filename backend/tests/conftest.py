import asyncio
import os
import tempfile
from pathlib import Path

# Tests always use a throwaway SQLite file — never the real database in backend/.env.
# Must be set before src.db.connection is imported (load_dotenv won't override it).
_TEST_DB = Path(tempfile.gettempdir()) / f"nutriscan_test_{os.getpid()}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"

from src.db.connection import close_db  # noqa: E402


def pytest_sessionfinish(session, exitstatus):
    # API tests open the shared SQLite connection; its worker thread keeps the
    # process alive after the run unless the connection is closed.
    asyncio.run(close_db())
    _TEST_DB.unlink(missing_ok=True)
