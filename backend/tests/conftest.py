import asyncio
from src.db.connection import close_db


def pytest_sessionfinish(session, exitstatus):
    # API tests open the shared SQLite connection; its worker thread keeps the
    # process alive after the run unless the connection is closed.
    asyncio.run(close_db())
