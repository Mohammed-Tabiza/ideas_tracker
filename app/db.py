from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "ideas.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS ideas (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                domain TEXT NOT NULL DEFAULT 'OTHER',
                tags TEXT NOT NULL DEFAULT '[]',
                source_type TEXT NOT NULL DEFAULT 'INTUITION',
                source_context TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                current_status TEXT NOT NULL DEFAULT 'GERME',
                confidence_level INTEGER,
                estimated_value INTEGER,
                estimated_effort INTEGER,
                next_action TEXT,
                revisit_at TEXT,
                archived INTEGER NOT NULL DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_ideas_status ON ideas(current_status);
            CREATE INDEX IF NOT EXISTS idx_ideas_domain ON ideas(domain);
            CREATE INDEX IF NOT EXISTS idx_ideas_updated ON ideas(updated_at);
            CREATE INDEX IF NOT EXISTS idx_ideas_archived ON ideas(archived);
            """
        )
