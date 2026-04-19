from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from .db import get_connection
from .schemas import IdeaCreate, IdeaUpdate

SORT_COLUMNS: dict[str, str] = {
    "created_at": "created_at",
    "last_activity": "last_activity",
    "estimated_value": "estimated_value",
}

Order = Literal["asc", "desc"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
        conn.execute(
            """
            INSERT INTO idea_events (
                id, idea_id, event_type, from_status, to_status, comment, reason_code, created_at
            ) VALUES (?, ?, 'CREATION', NULL, 'GERME', '', NULL, ?)
            """,
            (str(uuid4()), idea_id, timestamp),
        )
        conn.execute(
            """
            INSERT INTO ideas_fts (idea_id, title, description, aggregated_events_text)
            VALUES (?, ?, ?, '')
            """,
            (idea_id, title, payload.description),
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
        where.append("datetime(last_activity) <= datetime('now', '-30 day')")

    if tags:
        for tag in tags:
            where.append("EXISTS (SELECT 1 FROM json_each(ideas.tags) WHERE value = ?)")
            params.append(tag)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    sort_column = SORT_COLUMNS.get(sort, "created_at")
    sort_order = "ASC" if order == "asc" else "DESC"

    query = f"""
    WITH latest_events AS (
        SELECT idea_id, MAX(created_at) AS last_event_at
        FROM idea_events
        GROUP BY idea_id
    )
    SELECT
        ideas.*,
        CASE
            WHEN latest_events.last_event_at IS NULL THEN ideas.updated_at
            WHEN datetime(latest_events.last_event_at) > datetime(ideas.updated_at) THEN latest_events.last_event_at
            ELSE ideas.updated_at
        END AS last_activity
    FROM ideas
    LEFT JOIN latest_events ON latest_events.idea_id = ideas.id
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


def update_idea(idea_id: str, payload: IdeaUpdate) -> dict:
    existing = get_idea_by_id(idea_id)
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return existing

    now = now_iso()
    fields: list[str] = []
    values: list[str | int | None] = []

    for field, value in update_data.items():
        if field == "title" and value is not None:
            value = value.strip()
            if not value:
                raise ValueError("title must not be empty")
        if field == "tags" and value is not None:
            value = json.dumps(value)
        if field == "domain" and value is not None:
            value = value.value
        if field == "source_type" and value is not None:
            value = value.value
        if field == "archived" and value is not None:
            value = int(value)
        fields.append(f"{field} = ?")
        values.append(value)

    fields.append("updated_at = ?")
    values.append(now)
    values.append(idea_id)

    with get_connection() as conn:
        conn.execute(f"UPDATE ideas SET {', '.join(fields)} WHERE id = ?", values)
        conn.execute(
            """
            INSERT INTO idea_events (
                id, idea_id, event_type, from_status, to_status, comment, reason_code, created_at
            ) VALUES (?, ?, 'EDIT', NULL, NULL, ?, NULL, ?)
            """,
            (str(uuid4()), idea_id, "Idea updated", now),
        )
        _rebuild_fts(conn, idea_id)

    return get_idea_by_id(idea_id)


def archive_idea(idea_id: str) -> dict:
    now = now_iso()
    with get_connection() as conn:
        found = conn.execute("SELECT id FROM ideas WHERE id = ?", (idea_id,)).fetchone()
        if found is None:
            raise ValueError("Idea not found")
        conn.execute(
            "UPDATE ideas SET archived = 1, updated_at = ? WHERE id = ?",
            (now, idea_id),
        )
        conn.execute(
            """
            INSERT INTO idea_events (
                id, idea_id, event_type, from_status, to_status, comment, reason_code, created_at
            ) VALUES (?, ?, 'EDIT', NULL, NULL, ?, NULL, ?)
            """,
            (str(uuid4()), idea_id, "Idea archived", now),
        )
        _rebuild_fts(conn, idea_id)

    return get_idea_by_id(idea_id)


def _rebuild_fts(conn, idea_id: str) -> None:
    base = conn.execute(
        "SELECT title, description FROM ideas WHERE id = ?",
        (idea_id,),
    ).fetchone()
    if base is None:
        return
    events = conn.execute(
        "SELECT comment FROM idea_events WHERE idea_id = ? ORDER BY created_at ASC",
        (idea_id,),
    ).fetchall()
    events_text = " ".join((row["comment"] or "").strip() for row in events if row["comment"])
    updated = conn.execute(
        """
        UPDATE ideas_fts
        SET title = ?, description = ?, aggregated_events_text = ?
        WHERE idea_id = ?
        """,
        (base["title"], base["description"], events_text, idea_id),
    )
    if updated.rowcount == 0:
        conn.execute(
            """
            INSERT INTO ideas_fts (idea_id, title, description, aggregated_events_text)
            VALUES (?, ?, ?, ?)
            """,
            (idea_id, base["title"], base["description"], events_text),
        )
