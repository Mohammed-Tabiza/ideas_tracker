from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from .db import get_connection
from .schemas import IdeaCreate

SORT_COLUMNS: dict[str, str] = {
    "created_at": "created_at",
    "last_activity": "last_activity",
    "estimated_value": "estimated_value",
}

Order = Literal["asc", "desc"]


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def create_idea(payload: IdeaCreate) -> dict:
    idea_id = str(uuid4())
    title = payload.title.strip()
    if not title:
        raise ValueError("title must not be empty")

    timestamp = now_iso()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO ideas (
                id, title, description, domain, tags, source_type, source_context,
                created_at, updated_at, current_status, archived,
                confidence_level, estimated_value, estimated_effort,
                next_action, revisit_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'GERME', 0, ?, ?, ?, ?, ?)
            """,
            (
                idea_id,
                title,
                payload.description,
                payload.domain.value,
                json.dumps(payload.tags),
                payload.source_type.value,
                payload.source_context,
                timestamp,
                timestamp,
                payload.confidence_level,
                payload.estimated_value,
                payload.estimated_effort,
                payload.next_action,
                payload.revisit_at,
            ),
        )

    return get_idea_by_id(idea_id)


def get_idea_by_id(idea_id: str) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,)).fetchone()

    if row is None:
        raise ValueError("Idea not found")

    return _row_to_dict(row)


def list_ideas(
    include_archived: bool = False,
    status: str | None = None,
    domain: str | None = None,
    tags: list[str] | None = None,
    stale: bool | None = None,
    revisit_before: str | None = None,
    sort: str = "created_at",
    order: Order = "desc",
) -> list[dict]:
    where: list[str] = []
    params: list[str | int] = []

    if not include_archived:
        where.append("archived = 0")
    if status:
        where.append("current_status = ?")
        params.append(status)
    if domain:
        where.append("domain = ?")
        params.append(domain)
    if revisit_before:
        where.append("revisit_at IS NOT NULL AND revisit_at <= ?")
        params.append(revisit_before)

    if stale is True:
        where.append("datetime(updated_at) <= datetime('now', '-30 day')")

    if tags:
        for tag in tags:
            where.append("EXISTS (SELECT 1 FROM json_each(ideas.tags) WHERE value = ?)")
            params.append(tag)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    sort_column = SORT_COLUMNS.get(sort, "created_at")
    sort_order = "ASC" if order == "asc" else "DESC"

    query = f"""
    SELECT
        ideas.*, 
        ideas.updated_at AS last_activity
    FROM ideas
    {where_sql}
    ORDER BY {sort_column} {sort_order}
    """

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [_row_to_dict(row) for row in rows]


def _row_to_dict(row) -> dict:
    data = dict(row)
    data["tags"] = json.loads(data.get("tags") or "[]")
    data["archived"] = bool(data.get("archived"))
    data.pop("last_activity", None)
    return data
