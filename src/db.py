"""Shared database module — all tables in a single toolkit.db."""

import sqlite3
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (no-op if file doesn't exist)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

DB_PATH = os.environ.get("TOOLKIT_DB", "data/toolkit.db")


def get_conn() -> sqlite3.Connection:
    """Get a SQLite connection (context-manager friendly).

    Each call creates a fresh connection — SQLite connections are lightweight
    and WAL mode allows concurrent reads.  check_same_thread=False enables
    use from async code via asyncio.to_thread.

    Use as ``with get_conn() as conn: ...`` so the Connection context manager
    auto-commits on success and rolls back on exception.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with get_conn() as conn:
        # --- accounting ---
        conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- todo ---
        conn.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                priority INTEGER DEFAULT 1,
                due_date TEXT,
                done INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- calendar ---
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                event_time TIMESTAMP NOT NULL,
                remind_before INTEGER DEFAULT 10,
                repeat TEXT,
                reminded INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                user_id TEXT,
                title TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- notify ---
        conn.execute("""
            CREATE TABLE IF NOT EXISTS webhooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                method TEXT DEFAULT 'POST',
                headers TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notify_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                channel TEXT,
                target TEXT,
                title TEXT,
                body TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- indexes for common queries ---
        conn.execute("CREATE INDEX IF NOT EXISTS idx_records_user_id ON records(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_todos_user_id ON todos(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_user_id_time ON events(user_id, event_time)")
        conn.commit()
