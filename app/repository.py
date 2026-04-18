from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from .db import get_connection
from .schemas import IdeaCreate


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def create_idea(payload: IdeaCreate) -> dict:
    idea_id = str(uuid4())
    timestamp = now_iso()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO ideas (
                id, title, description, domain, tags, source_type, source_context,
                created_at, updated_at, current_status, archived
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'GERME', 0)
            """,
            (
                idea_id,
                payload.title.strip(),
                payload.description,
                payload.domain.value,
                json.dumps(payload.tags),
                payload.source_type.value,
                payload.source_context,
                timestamp,
                timestamp,
            ),
        )

    return get_idea_by_id(idea_id)


def get_idea_by_id(idea_id: str) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,)).fetchone()

    if row is None:
        raise ValueError("Idea not found")

    return _row_to_dict(row)


def list_ideas(include_archived: bool = False) -> list[dict]:
    query = "SELECT * FROM ideas"
    params: tuple = ()
    if not include_archived:
        query += " WHERE archived = 0"
    query += " ORDER BY created_at DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [_row_to_dict(row) for row in rows]


def _row_to_dict(row) -> dict:
    data = dict(row)
    data["tags"] = json.loads(data.get("tags") or "[]")
    data["archived"] = bool(data.get("archived"))
    return data
