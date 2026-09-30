"""
DocMindX AI — Dedicated Supabase PostgreSQL Database Architecture Layer
Production Database Engine: Supabase PostgreSQL Only.
Zero SQLite fallback. Provides thread-safe connection pooling, transaction safety,
and zero credential exposure health checks.
"""
import os
import re
import time
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, Tuple, Union
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("DocMindX.Database")

def _get_env_or_secret(key: str, default: str = "") -> str:
    """Reads environment variable or Streamlit secrets."""
    val = os.getenv(key, "")
    if not val:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and key in st.secrets:
                val = str(st.secrets[key])
        except Exception:
            pass
    return (val or default).strip()

def get_database_url() -> str:
    """Retrieves and validates PostgreSQL connection URL."""
    url = _get_env_or_secret("DATABASE_URL", "")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not configured. DocMindX AI requires a valid "
            "Supabase PostgreSQL connection URI. SQLite is permanently disabled."
        )
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url

def get_database_engine_name() -> str:
    """Returns the production database engine display name."""
    return "PostgreSQL (Supabase)"

# Thread-safe connection pool singleton
_pg_pool = None

def _init_pg_pool():
    """Initializes the PostgreSQL connection pool."""
    global _pg_pool
    if _pg_pool is not None:
        return _pg_pool

    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import DictCursor

    url = get_database_url()
    try:
        _pg_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=url,
            cursor_factory=DictCursor
        )
        logger.info("[DB] Supabase PostgreSQL connection pool initialized.")
        return _pg_pool
    except Exception as e:
        logger.error(f"[DB] Failed to connect to Supabase PostgreSQL: {e}")
        _pg_pool = None
        raise RuntimeError(f"Database connection failed: {e}")


class PostgresCursorWrapper:
    """
    Standard DB-API compatible cursor wrapper for Supabase PostgreSQL:
    - Auto-translates ? placeholders to %s
    - Auto-handles lastrowid for INSERT statements via RETURNING id
    - Multi-statement executescript() support
    - Dict-like row access (psycopg2 DictRow)
    """
    def __init__(self, raw_cursor, conn_wrapper=None):
        self._cursor = raw_cursor
        self._conn_wrapper = conn_wrapper
        self.lastrowid = None

    def _prepare_sql(self, sql: str) -> Tuple[str, bool]:
        is_insert = bool(re.match(r"^\s*INSERT\s+INTO", sql, re.IGNORECASE))
        translated = re.sub(r"\?", "%s", sql.strip())
        translated = re.sub(r"\s+COLLATE\s+NOCASE", "", translated, flags=re.IGNORECASE)
        
        # Add RETURNING id on INSERT if not present
        if is_insert and "RETURNING" not in translated.upper():
            translated = translated.rstrip(";") + " RETURNING id;"
            
        return translated, is_insert

    def execute(self, sql: str, params: Union[tuple, list, dict] = None):
        translated_sql, is_insert = self._prepare_sql(sql)
        try:
            if params is not None:
                if isinstance(params, list):
                    params = tuple(params)
                self._cursor.execute(translated_sql, params)
            else:
                self._cursor.execute(translated_sql)

            if is_insert and "RETURNING" in translated_sql.upper():
                try:
                    row = self._cursor.fetchone()
                    if row is not None:
                        if isinstance(row, dict) and "id" in row:
                            self.lastrowid = row["id"]
                        elif hasattr(row, "__getitem__"):
                            self.lastrowid = row[0]
                except Exception:
                    self.lastrowid = None
            return self
        except Exception as e:
            if is_insert and 'column "id" does not exist' in str(e).lower():
                raw_sql = re.sub(r"\s+RETURNING\s+id;?$", ";", translated_sql, flags=re.IGNORECASE)
                if params is not None:
                    self._cursor.execute(raw_sql, params)
                else:
                    self._cursor.execute(raw_sql)
                return self
            raise e

    def executemany(self, sql: str, seq_of_parameters):
        translated_sql, _ = self._prepare_sql(sql)
        return self._cursor.executemany(translated_sql, seq_of_parameters)

    def executescript(self, script_sql: str):
        cleaned = re.sub(r"--.*$", "", script_sql, flags=re.MULTILINE)
        statements = [s.strip() for s in cleaned.split(";") if s.strip()]
        for stmt in statements:
            self.execute(stmt)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchmany(self, size=None):
        return self._cursor.fetchmany(size) if size else self._cursor.fetchmany()

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def description(self):
        return self._cursor.description

    def close(self):
        return self._cursor.close()

    def __iter__(self):
        return iter(self._cursor)


class PostgresConnectionWrapper:
    """Pooled connection wrapper with commit, rollback, and cleanup."""
    def __init__(self, raw_conn, pool_ref):
        self._conn = raw_conn
        self._pool = pool_ref
        self._is_closed = False

    def cursor(self):
        import psycopg2.extras
        raw_cur = self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        return PostgresCursorWrapper(raw_cur, self)

    def execute(self, sql: str, params=None):
        cur = self.cursor()
        return cur.execute(sql, params)

    def commit(self):
        if not self._is_closed and self._conn:
            self._conn.commit()

    def rollback(self):
        if not self._is_closed and self._conn:
            self._conn.rollback()

    def close(self):
        if not self._is_closed:
            self._is_closed = True
            if self._pool and self._conn:
                try:
                    self._pool.putconn(self._conn)
                except Exception:
                    pass
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


def get_db_connection():
    """
    Acquires a pooled connection to Supabase PostgreSQL.
    Raises RuntimeError if DATABASE_URL is missing or unavailable.
    """
    pool_ref = _init_pg_pool()
    raw_conn = pool_ref.getconn()
    return PostgresConnectionWrapper(raw_conn, pool_ref)


@contextmanager
def get_db_cursor():
    """Context manager for acquiring a cursor with auto-commit and cleanup."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def check_database_health() -> Dict[str, Any]:
    """
    Probes Supabase PostgreSQL health.
    Never exposes passwords or secret credentials.
    """
    start_time = time.time()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        res = cursor.fetchone()
        conn.close()

        latency_ms = round((time.time() - start_time) * 1000, 2)
        if res and (res[0] == 1 or (isinstance(res, dict) and list(res.values())[0] == 1)):
            return {
                "status": "CONNECTED",
                "engine": "PostgreSQL (Supabase)",
                "mode": "PostgreSQL (Production / Supabase)",
                "latency_ms": latency_ms,
                "healthy": True
            }
        else:
            return {
                "status": "UNAVAILABLE",
                "engine": "PostgreSQL (Supabase)",
                "mode": "PostgreSQL",
                "latency_ms": latency_ms,
                "healthy": False,
                "error": "Unexpected probe response"
            }
    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        err_msg = str(e).split("@")[-1] if "@" in str(e) else str(e)
        return {
            "status": "UNAVAILABLE",
            "engine": "PostgreSQL (Supabase)",
            "mode": "PostgreSQL",
            "latency_ms": latency_ms,
            "healthy": False,
            "error": err_msg
        }
