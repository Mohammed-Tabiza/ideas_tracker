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
                domain TEXT NOT NULL DEFAULT 'OTHER'
                    CHECK(domain IN ('IA4IT','IA4ALL','STRATEGY','ARCHITECTURE','OTHER')),
                tags TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(tags)),
                source_type TEXT NOT NULL DEFAULT 'INTUITION'
                    CHECK(source_type IN ('CONVERSATION','MEETING','READING','EXPERIMENT','INTUITION','OTHER')),
                source_context TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                current_status TEXT NOT NULL DEFAULT 'GERME'
                    CHECK(current_status IN ('GERME','EXPLORATION','POC','TRANSMIS','EN_VEILLE','ABANDONNE','REALISE')),
                confidence_level INTEGER CHECK(confidence_level BETWEEN 1 AND 5 OR confidence_level IS NULL),
                estimated_value INTEGER CHECK(estimated_value BETWEEN 1 AND 5 OR estimated_value IS NULL),
                estimated_effort INTEGER CHECK(estimated_effort BETWEEN 1 AND 5 OR estimated_effort IS NULL),
                next_action TEXT,
                revisit_at TEXT,
                archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0,1))
            );

            CREATE TABLE IF NOT EXISTS idea_events (
                id TEXT PRIMARY KEY,
                idea_id TEXT NOT NULL,
                event_type TEXT NOT NULL
                    CHECK(event_type IN ('CREATION','TRANSITION','EDIT','NOTE')),
                from_status TEXT
                    CHECK(from_status IN ('GERME','EXPLORATION','POC','TRANSMIS','EN_VEILLE','ABANDONNE','REALISE')
                    OR from_status IS NULL),
                to_status TEXT
                    CHECK(to_status IN ('GERME','EXPLORATION','POC','TRANSMIS','EN_VEILLE','ABANDONNE','REALISE')
                    OR to_status IS NULL),
                comment TEXT NOT NULL DEFAULT '',
                reason_code TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(idea_id) REFERENCES ideas(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS idea_links (
                id TEXT PRIMARY KEY,
                source_idea_id TEXT NOT NULL,
                target_idea_id TEXT NOT NULL,
                link_type TEXT NOT NULL
                    CHECK(link_type IN ('parent','child','related','duplicate','derived_from')),
                FOREIGN KEY(source_idea_id) REFERENCES ideas(id) ON DELETE CASCADE,
                FOREIGN KEY(target_idea_id) REFERENCES ideas(id) ON DELETE CASCADE
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS ideas_fts USING fts5(
                idea_id UNINDEXED,
                title,
                description,
                aggregated_events_text
            );

            CREATE INDEX IF NOT EXISTS idx_ideas_status ON ideas(current_status);
            CREATE INDEX IF NOT EXISTS idx_ideas_domain ON ideas(domain);
            CREATE INDEX IF NOT EXISTS idx_ideas_updated ON ideas(updated_at);
            CREATE INDEX IF NOT EXISTS idx_ideas_archived ON ideas(archived);
            CREATE INDEX IF NOT EXISTS idx_events_idea_id ON idea_events(idea_id);
            CREATE INDEX IF NOT EXISTS idx_links_source ON idea_links(source_idea_id);
            CREATE INDEX IF NOT EXISTS idx_links_target ON idea_links(target_idea_id);
            """
        )
