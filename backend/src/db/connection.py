"""
Database connection for SQLite (local dev/tests) or Postgres (Supabase, production).

DATABASE_URL decides which one is used:
  - unset or sqlite:///path   -> SQLite file (default backend/data/app.db)
  - postgresql://...          -> Postgres via an asyncpg pool

Both expose the same small interface through get_db(): execute() (awaitable or
'async with' giving fetchone/fetchall), executemany(), commit(). SQL is written with
'?' placeholders and converted to $1, $2, ... for Postgres.

Migrations are numbered, forward-only SQL files (db/migrations for SQLite,
db/migrations_postgres for Postgres); each file runs once and is recorded in
schema_migrations.
"""
import os
import re
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

import aiosqlite

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).parent.parent.parent
raw_url = os.getenv("DATABASE_URL") or ""
IS_POSTGRES = raw_url.startswith(("postgres://", "postgresql://"))

if IS_POSTGRES:
    MIGRATIONS_DIR = BACKEND_DIR / "db" / "migrations_postgres"
    DB_FILE = None
else:
    MIGRATIONS_DIR = BACKEND_DIR / "db" / "migrations"
    if raw_url:
        # Strip URL schemes if passed like sqlite:/// or sqlite+aiosqlite:///
        db_path = Path(raw_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", ""))
    else:
        db_path = BACKEND_DIR / "data" / "app.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    DB_FILE = str(db_path)

_db_conn: Optional[aiosqlite.Connection] = None
_pg_pool = None

_PLACEHOLDER = re.compile(r"\?")


def _to_postgres_sql(sql: str) -> str:
    """Turn '?' placeholders into $1, $2, ... (our SQL never has '?' inside literals)."""
    counter = iter(range(1, 10_000))
    return _PLACEHOLDER.sub(lambda _: f"${next(counter)}", sql)


class _PgResult:
    """Mimics aiosqlite's execute() result: awaitable and usable with 'async with'."""

    def __init__(self, conn, sql: str, params: Sequence[Any]):
        self._conn = conn
        self._sql = _to_postgres_sql(sql)
        self._params = tuple(params)
        self._rows: list = []

    async def _run(self) -> "_PgResult":
        self._rows = await self._conn.fetch(self._sql, *self._params)
        return self

    def __await__(self):
        return self._run().__await__()

    async def __aenter__(self) -> "_PgResult":
        return await self._run()

    async def __aexit__(self, *exc) -> None:
        return None

    async def fetchone(self):
        return self._rows[0] if self._rows else None

    async def fetchall(self):
        return self._rows


class PgConnection:
    """The subset of the aiosqlite connection API the app uses, on top of asyncpg."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql: str, params: Sequence[Any] = ()) -> _PgResult:
        return _PgResult(self._conn, sql, params)

    async def executemany(self, sql: str, rows: Iterable[Sequence[Any]]) -> None:
        await self._conn.executemany(_to_postgres_sql(sql), list(rows))

    async def commit(self) -> None:
        # Each statement autocommits through the pooler; nothing to do
        return None


async def _applied_migrations(execute_fn) -> set:
    rows = await execute_fn("SELECT filename FROM schema_migrations")
    return {r["filename"] for r in rows}


async def _run_migrations_sqlite(conn: aiosqlite.Connection) -> None:
    await conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (filename TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    async with conn.execute("SELECT filename FROM schema_migrations") as cursor:
        applied = {r["filename"] for r in await cursor.fetchall()}
    for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if migration.name in applied:
            continue
        logger.info(f"Running migration {migration.name}")
        await conn.executescript(migration.read_text(encoding="utf-8"))
        await conn.execute("INSERT INTO schema_migrations (filename, applied_at) VALUES (?, datetime('now'))",
                           (migration.name,))
    await conn.commit()


async def _run_migrations_postgres(pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (filename TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
        applied = {r["filename"] for r in await conn.fetch("SELECT filename FROM schema_migrations")}
        for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if migration.name in applied:
                continue
            logger.info(f"Running migration {migration.name}")
            async with conn.transaction():
                await conn.execute(migration.read_text(encoding="utf-8"))
                await conn.execute("INSERT INTO schema_migrations (filename, applied_at) VALUES ($1, now()::text)",
                                   migration.name)


async def init_db():
    global _db_conn, _pg_pool
    if IS_POSTGRES:
        if _pg_pool is None:
            import asyncpg
            # statement_cache_size=0: required behind Supabase's transaction pooler (pgBouncer)
            _pg_pool = await asyncpg.create_pool(raw_url, min_size=1, max_size=5,
                                                 statement_cache_size=0, command_timeout=60)
            await _run_migrations_postgres(_pg_pool)
    elif _db_conn is None:
        _db_conn = await aiosqlite.connect(DB_FILE)
        _db_conn.row_factory = aiosqlite.Row
        if MIGRATIONS_DIR.exists():
            await _run_migrations_sqlite(_db_conn)


async def close_db():
    global _db_conn, _pg_pool
    if _db_conn:
        await _db_conn.close()
        _db_conn = None
    if _pg_pool is not None:
        await _pg_pool.close()
        _pg_pool = None


@asynccontextmanager
async def get_db():
    if IS_POSTGRES:
        if _pg_pool is None:
            await init_db()
        async with _pg_pool.acquire() as conn:
            yield PgConnection(conn)
    else:
        if not _db_conn:
            await init_db()
        yield _db_conn
