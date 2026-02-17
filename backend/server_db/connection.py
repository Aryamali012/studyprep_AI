"""
server_db/connection.py
SQLite database connection and schema setup using built-in sqlite3.

Tables
──────
users          – user_id (UUID), full_name, email, password_hash
refresh_tokens – token_id, user_id (FK), token_hash, expires_at, revoked, created_at
                 (one row per issued refresh token; rotated on every /refresh call)
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, os.getenv("DB_PATH", "studyprep.db"))


def get_connection():
    """Return a new SQLite connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist yet."""
    conn = get_connection()
    with conn:
        # ── Users ──────────────────────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id       TEXT PRIMARY KEY,
                full_name     TEXT NOT NULL,
                email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at    TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # ── Refresh tokens ─────────────────────────────────────────────────────
        # We store a SHA-256 *hash* of the token, never the raw token itself.
        # On rotation the old row is revoked and a new row is inserted.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                token_id    TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                token_hash  TEXT NOT NULL UNIQUE,
                expires_at  TEXT NOT NULL,
                revoked     INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_rt_user ON refresh_tokens(user_id)"
        )

    conn.close()
    print(f"[DB] Database ready at: {DB_PATH}")
