from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from .db import get_connection

SORT_COLUMNS: dict[str, str] = {
    "created_at": "created_at",
    "last_activity": "last_activity",
    "estimated_value": "estimated_value",
}

Order = Literal["asc", "desc"]


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def create_idea_record(data: dict[str, Any]) -> str:
    idea_id = str(uuid4())

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO ideas (
                id, title, description, domain, tags, source_type, source_context,
                created_at, updated_at, current_status, archived,
                confidence_level, estimated_value, estimated_effort,
                next_action, revisit_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                idea_id,
                data["title"],
                data["description"],
                data["domain"],
                json.dumps(data["tags"]),
                data["source_type"],
                data["source_context"],
                data["created_at"],
                data["updated_at"],
                data["current_status"],
                int(data["archived"]),
                data["confidence_level"],
                data["estimated_value"],
                data["estimated_effort"],
                data["next_action"],
                data["revisit_at"],
            ),
        )
        create_event_record(
            conn,
            {
                "idea_id": idea_id,
                "event_type": "CREATION",
                "from_status": None,
                "to_status": data["current_status"],
                "comment": data["source_context"] or "",
                "reason_code": None,
                "created_at": data["created_at"],
            },
        )
        rebuild_fts_for_idea(conn, idea_id)

    return idea_id


def get_idea_by_id(idea_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            {_ideas_with_activity_cte()}
            SELECT * FROM ideas_with_activity WHERE id = ?
            """,
            (idea_id,),
        ).fetchone()

    if row is None:
        return None

    return _idea_row_to_dict(row)


def list_ideas(
    include_archived: bool = False,
    status: str | None = None,
    domain: str | None = None,
    tags: list[str] | None = None,
    stale: bool | None = None,
    revisit_before: str | None = None,
    sort: str = "created_at",
    order: Order = "desc",
) -> list[dict[str, Any]]:
    where: list[str] = []
    params: list[str] = []

    if not include_archived:
        where.append("archived = 0")
    if status:
        where.append("current_status = ?")
        params.append(status)
    if domain:
        where.append("domain = ?")
        params.append(domain)
    if revisit_before:
        where.append("revisit_at IS NOT NULL AND date(revisit_at) <= date(?)")
        params.append(revisit_before)
    if stale is True:
        where.append("datetime(last_activity) <= datetime('now', '-30 day')")
    if tags:
        for tag in tags:
            where.append("EXISTS (SELECT 1 FROM json_each(ideas_with_activity.tags) WHERE value = ?)")
            params.append(tag)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    sort_column = SORT_COLUMNS.get(sort, "created_at")
    sort_order = "ASC" if order == "asc" else "DESC"

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            {_ideas_with_activity_cte()}
            SELECT * FROM ideas_with_activity
            {where_sql}
            ORDER BY {sort_column} {sort_order}
            """,
            params,
        ).fetchall()

    return [_idea_row_to_dict(row) for row in rows]


def update_idea_record(idea_id: str, updates: dict[str, Any]) -> bool:
    if not updates:
        return False

    set_clauses = ", ".join(f"{column} = ?" for column in updates)
    params = list(_serialize_idea_update_values(updates)) + [idea_id]

    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE ideas SET {set_clauses} WHERE id = ?",
            params,
        )
        if cursor.rowcount == 0:
            return False

        create_event_record(
            conn,
            {
                "idea_id": idea_id,
                "event_type": "EDIT",
                "from_status": None,
                "to_status": None,
                "comment": "",
                "reason_code": None,
                "created_at": updates["updated_at"],
            },
        )
        rebuild_fts_for_idea(conn, idea_id)

    return True


def archive_idea_record(idea_id: str, updated_at: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE ideas SET archived = 1, updated_at = ? WHERE id = ?",
            (updated_at, idea_id),
        )
        if cursor.rowcount == 0:
            return False

        rebuild_fts_for_idea(conn, idea_id)

    return True


def transition_idea_record(
    idea_id: str,
    *,
    to_status: str,
    from_status: str,
    comment: str,
    reason_code: str | None,
    revisit_at: str | None,
    updated_at: str,
) -> bool:
    with get_connection() as conn:
        create_event_record(
            conn,
            {
                "idea_id": idea_id,
                "event_type": "TRANSITION",
                "from_status": from_status,
                "to_status": to_status,
                "comment": comment,
                "reason_code": reason_code,
                "created_at": updated_at,
            },
        )
        cursor = conn.execute(
            """
            UPDATE ideas
            SET current_status = ?, revisit_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (to_status, revisit_at, updated_at, idea_id),
        )
        if cursor.rowcount == 0:
            conn.execute("DELETE FROM idea_events WHERE idea_id = ? AND created_at = ? AND event_type = 'TRANSITION'", (idea_id, updated_at))
            return False
        rebuild_fts_for_idea(conn, idea_id)

    return True


def list_idea_events(idea_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, idea_id, event_type, from_status, to_status, comment, reason_code, created_at
            FROM idea_events
            WHERE idea_id = ?
            ORDER BY created_at ASC
            """,
            (idea_id,),
        ).fetchall()

    return [_event_row_to_dict(row) for row in rows]


def get_idea_graph(idea_id: str) -> dict[str, Any] | None:
    idea = get_idea_by_id(idea_id)
    if idea is None:
        return None

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                links.id AS link_id,
                links.link_type AS link_type,
                'outgoing' AS direction,
                target.id AS target_id,
                target.title AS target_title,
                target.current_status AS target_current_status,
                target.archived AS target_archived
            FROM idea_links AS links
            JOIN ideas AS target ON target.id = links.target_idea_id
            WHERE links.source_idea_id = ?

            UNION ALL

            SELECT
                links.id AS link_id,
                links.link_type AS link_type,
                'incoming' AS direction,
                source.id AS target_id,
                source.title AS target_title,
                source.current_status AS target_current_status,
                source.archived AS target_archived
            FROM idea_links AS links
            JOIN ideas AS source ON source.id = links.source_idea_id
            WHERE links.target_idea_id = ?

            ORDER BY target_title ASC, link_type ASC
            """,
            (idea_id, idea_id),
        ).fetchall()

    return {
        "idea": idea,
        "links": [
            {
                "id": row["link_id"],
                "link_type": row["link_type"],
                "direction": row["direction"],
                "target": {
                    "id": row["target_id"],
                    "title": row["target_title"],
                    "current_status": row["target_current_status"],
                    "archived": bool(row["target_archived"]),
                },
            }
            for row in rows
        ],
    }


def create_idea_link_record(
    source_idea_id: str,
    target_idea_id: str,
    link_type: str,
    updated_at: str,
) -> dict[str, Any]:
    link_id = str(uuid4())

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO idea_links (id, source_idea_id, target_idea_id, link_type)
            VALUES (?, ?, ?, ?)
            """,
            (link_id, source_idea_id, target_idea_id, link_type),
        )
        conn.execute(
            "UPDATE ideas SET updated_at = ? WHERE id = ?",
            (updated_at, source_idea_id),
        )

    return {
        "id": link_id,
        "source_idea_id": source_idea_id,
        "target_idea_id": target_idea_id,
        "link_type": link_type,
    }


def get_idea_link_by_id(link_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, source_idea_id, target_idea_id, link_type
            FROM idea_links
            WHERE id = ?
            """,
            (link_id,),
        ).fetchone()

    return dict(row) if row is not None else None


def idea_link_exists(source_idea_id: str, target_idea_id: str, link_type: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM idea_links
            WHERE source_idea_id = ? AND target_idea_id = ? AND link_type = ?
            LIMIT 1
            """,
            (source_idea_id, target_idea_id, link_type),
        ).fetchone()

    return row is not None


def delete_idea_link_record(link_id: str, source_idea_id: str, updated_at: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            DELETE FROM idea_links
            WHERE id = ? AND source_idea_id = ?
            """,
            (link_id, source_idea_id),
        )
        if cursor.rowcount == 0:
            return False

        conn.execute(
            "UPDATE ideas SET updated_at = ? WHERE id = ?",
            (updated_at, source_idea_id),
        )

    return True


def search_ideas(query_text: str, include_archived: bool = False) -> list[dict[str, Any]]:
    where_clauses = ["ideas_fts MATCH ?"]
    if not include_archived:
        where_clauses.append("ideas_with_activity.archived = 0")
    where_sql = "WHERE " + " AND ".join(where_clauses)

    try:
        with get_connection() as conn:
            rows = conn.execute(
                f"""
                {_ideas_with_activity_cte()}
                SELECT
                    ideas_with_activity.*,
                    bm25(ideas_fts) AS rank
                FROM ideas_fts
                JOIN ideas_with_activity ON ideas_with_activity.id = ideas_fts.idea_id
                {where_sql}
                ORDER BY rank
                """,
                (query_text,),
            ).fetchall()
    except sqlite3.OperationalError as exc:
        raise ValueError(f"Invalid search query: {query_text}") from exc

    return [_search_row_to_dict(row) for row in rows]


def create_event_record(conn: sqlite3.Connection, event: dict[str, Any]) -> str:
    event_id = str(uuid4())
    conn.execute(
        """
        INSERT INTO idea_events (
            id, idea_id, event_type, from_status, to_status, comment, reason_code, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            event["idea_id"],
            event["event_type"],
            event["from_status"],
            event["to_status"],
            event["comment"],
            event["reason_code"],
            event["created_at"],
        ),
    )
    return event_id


def rebuild_fts_for_idea(conn: sqlite3.Connection, idea_id: str) -> None:
    row = conn.execute(
        """
        SELECT id, title, description
        FROM ideas
        WHERE id = ?
        """,
        (idea_id,),
    ).fetchone()
    if row is None:
        return

    aggregated_events_text = build_events_text(conn, idea_id)
    conn.execute("DELETE FROM ideas_fts WHERE idea_id = ?", (idea_id,))
    conn.execute(
        """
        INSERT INTO ideas_fts (idea_id, title, description, aggregated_events_text)
        VALUES (?, ?, ?, ?)
        """,
        (
            row["id"],
            row["title"],
            row["description"] or "",
            aggregated_events_text,
        ),
    )


def rebuild_all_fts() -> None:
    with get_connection() as conn:
        idea_ids = [row["id"] for row in conn.execute("SELECT id FROM ideas").fetchall()]
        conn.execute("DELETE FROM ideas_fts")
        for idea_id in idea_ids:
            rebuild_fts_for_idea(conn, idea_id)


def build_events_text(conn: sqlite3.Connection, idea_id: str) -> str:
    rows = conn.execute(
        """
        SELECT comment
        FROM idea_events
        WHERE idea_id = ?
        ORDER BY created_at ASC
        """,
        (idea_id,),
    ).fetchall()
    return " ".join(row["comment"] for row in rows if row["comment"])


def _ideas_with_activity_cte() -> str:
    return """
    WITH latest_events AS (
        SELECT idea_id, MAX(created_at) AS latest_event_at
        FROM idea_events
        GROUP BY idea_id
    ),
    ideas_with_activity AS (
        SELECT
            ideas.*,
            MAX(ideas.updated_at, COALESCE(latest_events.latest_event_at, ideas.updated_at)) AS last_activity
        FROM ideas
        LEFT JOIN latest_events ON latest_events.idea_id = ideas.id
    )
    """


def _serialize_idea_update_values(updates: dict[str, Any]) -> list[Any]:
    values: list[Any] = []
    for column, value in updates.items():
        if column == "tags":
            values.append(json.dumps(value))
        else:
            values.append(value)
    return values


def _idea_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["tags"] = json.loads(data.get("tags") or "[]")
    data["archived"] = bool(data.get("archived"))
    data.pop("last_activity", None)
    return data


def _event_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def _search_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = _idea_row_to_dict(row)
    data["rank"] = row["rank"]
    return data
