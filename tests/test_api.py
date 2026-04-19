from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import app.db as db_module
from app.main import app


class IdeaApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        db_module.DB_PATH = Path(self.temp_dir.name) / "ideas.db"
        db_module.init_db(seed_demo=False)
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.temp_dir.cleanup()

    def test_create_get_and_search_idea(self) -> None:
        create_response = self.client.post(
            "/ideas",
            json={
                "title": "Agent memory notebook",
                "description": "Capture context and revive ideas",
                "tags": ["llm", "notes"],
            },
        )

        self.assertEqual(create_response.status_code, 201)
        idea = create_response.json()
        self.assertEqual(idea["current_status"], "GERME")

        get_response = self.client.get(f"/ideas/{idea['id']}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json()["title"], "Agent memory notebook")

        search_response = self.client.get("/search", params={"q": "context"})
        self.assertEqual(search_response.status_code, 200)
        self.assertEqual(len(search_response.json()), 1)

    def test_transition_rules_and_events_timeline(self) -> None:
        create_response = self.client.post("/ideas", json={"title": "Idea sleeping"})
        idea_id = create_response.json()["id"]

        invalid_transition = self.client.post(
            f"/ideas/{idea_id}/transition",
            json={"to_status": "EN_VEILLE"},
        )
        self.assertEqual(invalid_transition.status_code, 400)

        transition_response = self.client.post(
            f"/ideas/{idea_id}/transition",
            json={
                "to_status": "EXPLORATION",
                "comment": "",
            },
        )
        self.assertEqual(transition_response.status_code, 200)
        self.assertEqual(transition_response.json()["current_status"], "EXPLORATION")

        events_response = self.client.get(f"/ideas/{idea_id}/events")
        self.assertEqual(events_response.status_code, 200)
        self.assertEqual([event["event_type"] for event in events_response.json()], ["CREATION", "TRANSITION"])

    def test_archive_hides_from_list_but_not_detail(self) -> None:
        create_response = self.client.post("/ideas", json={"title": "Archive me"})
        idea_id = create_response.json()["id"]

        delete_response = self.client.delete(f"/ideas/{idea_id}")
        self.assertEqual(delete_response.status_code, 204)

        list_response = self.client.get("/ideas")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json(), [])

        detail_response = self.client.get(f"/ideas/{idea_id}")
        self.assertEqual(detail_response.status_code, 200)
        self.assertTrue(detail_response.json()["archived"])

        search_response = self.client.get("/search", params={"q": "Archive"})
        self.assertEqual(search_response.status_code, 200)
        self.assertEqual(search_response.json(), [])

    def test_create_and_delete_idea_link(self) -> None:
        source_response = self.client.post("/ideas", json={"title": "Source idea"})
        target_response = self.client.post("/ideas", json={"title": "Target idea"})
        source_id = source_response.json()["id"]
        target_id = target_response.json()["id"]

        create_link_response = self.client.post(
            f"/ideas/{source_id}/links",
            json={
                "target_idea_id": target_id,
                "link_type": "related",
            },
        )
        self.assertEqual(create_link_response.status_code, 201)
        link = create_link_response.json()
        self.assertEqual(link["source_idea_id"], source_id)
        self.assertEqual(link["target_idea_id"], target_id)
        self.assertEqual(link["link_type"], "related")

        graph_response = self.client.get(f"/ideas/{source_id}/graph")
        self.assertEqual(graph_response.status_code, 200)
        self.assertEqual(len(graph_response.json()["links"]), 1)
        self.assertEqual(graph_response.json()["links"][0]["id"], link["id"])

        duplicate_link_response = self.client.post(
            f"/ideas/{source_id}/links",
            json={
                "target_idea_id": target_id,
                "link_type": "related",
            },
        )
        self.assertEqual(duplicate_link_response.status_code, 400)

        delete_link_response = self.client.delete(f"/ideas/{source_id}/links/{link['id']}")
        self.assertEqual(delete_link_response.status_code, 204)

        graph_after_delete = self.client.get(f"/ideas/{source_id}/graph")
        self.assertEqual(graph_after_delete.status_code, 200)
        self.assertEqual(graph_after_delete.json()["links"], [])

    def test_init_db_removes_demo_seed_but_preserves_user_ideas(self) -> None:
        seeded_dir = tempfile.TemporaryDirectory()
        original_db_path = db_module.DB_PATH

        try:
            db_module.DB_PATH = Path(seeded_dir.name) / "seeded.db"
            db_module.init_db(seed_demo=True, cleanup_demo=False)
            with db_module.get_connection() as conn:
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
                        "user-idea-1",
                        "User idea",
                        "Keep this row",
                        "OTHER",
                        json.dumps(["keep"]),
                        "INTUITION",
                        None,
                        "2026-04-19T09:00:00+00:00",
                        "2026-04-19T09:00:00+00:00",
                        "GERME",
                        0,
                        None,
                        None,
                        None,
                        None,
                        None,
                    ),
                )

            db_module.init_db()

            with db_module.get_connection() as conn:
                remaining_titles = [
                    row["title"]
                    for row in conn.execute("SELECT title FROM ideas ORDER BY title").fetchall()
                ]
                event_count = conn.execute("SELECT COUNT(*) AS count FROM idea_events").fetchone()["count"]
                link_count = conn.execute("SELECT COUNT(*) AS count FROM idea_links").fetchone()["count"]

            self.assertEqual(remaining_titles, ["User idea"])
            self.assertEqual(event_count, 0)
            self.assertEqual(link_count, 0)
        finally:
            db_module.DB_PATH = original_db_path
            seeded_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
