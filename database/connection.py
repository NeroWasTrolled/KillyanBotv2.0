import sqlite3
from typing import Optional

DB_PATH = "characters.db"


def create_connection(db_path: Optional[str] = None, *, timeout: float = 5.0) -> sqlite3.Connection:
    """Create a SQLite connection with the project's standard PRAGMA setup."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path, check_same_thread=False, timeout=timeout)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn
