from __future__ import annotations

import json
import sqlite3

DEMO_IDEAS = [
    {
        "id": "b8d9c64d-e7d8-4c63-85ee-b7127860b001",
        "title": "Radar de signaux faibles IA pour l'architecture",
        "description": "Construire un cockpit local pour capter les signaux faibles, les relier aux choix de plateforme et documenter les arbitrages.",
        "domain": "ARCHITECTURE",
        "tags": ["radar", "llm", "platform"],
        "source_type": "READING",
        "source_context": "Notes prises apres plusieurs lectures sur l'evolution des agents et de l'outillage infra.",
        "created_at": "2026-03-28T09:15:00+00:00",
        "updated_at": "2026-04-15T08:30:00+00:00",
        "current_status": "EXPLORATION",
        "confidence_level": 4,
        "estimated_value": 5,
        "estimated_effort": 3,
        "next_action": "Consolider une premiere grille de veille et la tester sur trois sujets IA4IT.",
        "revisit_at": None,
        "archived": 0,
    },
    {
        "id": "b8d9c64d-e7d8-4c63-85ee-b7127860b002",
        "title": "Notebook de transmission pour idees techniques",
        "description": "Formaliser une fiche de transmission courte entre intuition, exploration, preuve de concept et relais vers l'equipe.",
        "domain": "STRATEGY",
        "tags": ["knowledge", "process", "handoff"],
        "source_type": "CONVERSATION",
        "source_context": "Discussion sur les idees qui meurent entre le moment ou elles emergent et celui ou elles sont partagees.",
        "created_at": "2026-03-21T10:40:00+00:00",
        "updated_at": "2026-04-12T14:15:00+00:00",
        "current_status": "TRANSMIS",
        "confidence_level": 4,
        "estimated_value": 4,
        "estimated_effort": 2,
        "next_action": "Recueillir le retour de deux personnes ayant recu la fiche.",
        "revisit_at": None,
        "archived": 0,
    },
    {
        "id": "b8d9c64d-e7d8-4c63-85ee-b7127860b003",
        "title": "Atelier POC pour agents d'architecture locale",
        "description": "Verifier si un agent local peut rejouer une timeline d'idee et suggerer la prochaine action utile.",
        "domain": "IA4IT",
        "tags": ["agent", "poc", "timeline"],
        "source_type": "EXPERIMENT",
        "source_context": "Prototype artisanal realise pour verifier la valeur de la timeline comme memoire de decision.",
        "created_at": "2026-04-02T07:50:00+00:00",
        "updated_at": "2026-04-17T11:00:00+00:00",
        "current_status": "POC",
        "confidence_level": 3,
        "estimated_value": 5,
        "estimated_effort": 4,
        "next_action": "Comparer l'agent avec un flux manuel sur cinq idees recentes.",
        "revisit_at": None,
        "archived": 0,
    },
    {
        "id": "b8d9c64d-e7d8-4c63-85ee-b7127860b004",
        "title": "Cartographie des idees en veille pour la roadmap Q3",
        "description": "Mettre de cote les idees interessantes mais trop tot, avec une date claire de relecture.",
        "domain": "OTHER",
        "tags": ["roadmap", "revisit", "portfolio"],
        "source_type": "MEETING",
        "source_context": "Point d'arbitrage de portefeuille avec plusieurs pistes pertinentes mais hors timing.",
        "created_at": "2026-02-11T13:20:00+00:00",
        "updated_at": "2026-04-10T16:00:00+00:00",
        "current_status": "EN_VEILLE",
        "confidence_level": 3,
        "estimated_value": 4,
        "estimated_effort": 2,
        "next_action": "Revoir apres stabilisation de la roadmap produit.",
        "revisit_at": "2026-04-24T09:00:00+00:00",
        "archived": 0,
    },
    {
        "id": "b8d9c64d-e7d8-4c63-85ee-b7127860b005",
        "title": "Schema de score automatique pour prioriser les idees",
        "description": "Essai de score composite base sur confiance, valeur et effort pour trier les idees.",
        "domain": "IA4ALL",
        "tags": ["scoring", "prioritization"],
        "source_type": "INTUITION",
        "source_context": "Intuition rapide sur une maniere de sortir du flou quand trop d'idees competissent.",
        "created_at": "2026-01-18T08:10:00+00:00",
        "updated_at": "2026-02-02T09:00:00+00:00",
        "current_status": "ABANDONNE",
        "confidence_level": 2,
        "estimated_value": 2,
        "estimated_effort": 3,
        "next_action": None,
        "revisit_at": None,
        "archived": 0,
    },
    {
        "id": "b8d9c64d-e7d8-4c63-85ee-b7127860b006",
        "title": "Journal d'idees historiques archivees",
        "description": "Conserver un exemple archive pour montrer le comportement des listes et du graphe.",
        "domain": "OTHER",
        "tags": ["archive", "history"],
        "source_type": "OTHER",
        "source_context": "Ancienne piste gardee uniquement comme reference de travail.",
        "created_at": "2025-12-15T10:00:00+00:00",
        "updated_at": "2026-01-05T10:00:00+00:00",
        "current_status": "REALISE",
        "confidence_level": 5,
        "estimated_value": 3,
        "estimated_effort": 1,
        "next_action": None,
        "revisit_at": None,
        "archived": 1,
    },
]

DEMO_EVENTS = [
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000001",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b001",
        "event_type": "CREATION",
        "from_status": None,
        "to_status": "GERME",
        "comment": "Notes initiales issues d'une veille ciblee.",
        "reason_code": None,
        "created_at": "2026-03-28T09:15:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000002",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b001",
        "event_type": "TRANSITION",
        "from_status": "GERME",
        "to_status": "EXPLORATION",
        "comment": "Validee comme piste de travail recurrente pour les arbitrages d'architecture.",
        "reason_code": None,
        "created_at": "2026-04-01T08:00:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000003",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b001",
        "event_type": "NOTE",
        "from_status": None,
        "to_status": None,
        "comment": "La valeur vient surtout de la trace des arbitrages, pas du score lui-meme.",
        "reason_code": None,
        "created_at": "2026-04-15T08:30:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000004",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b002",
        "event_type": "CREATION",
        "from_status": None,
        "to_status": "GERME",
        "comment": "Capture apres discussion sur la perte de contexte des idees.",
        "reason_code": None,
        "created_at": "2026-03-21T10:40:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000005",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b002",
        "event_type": "TRANSITION",
        "from_status": "GERME",
        "to_status": "EXPLORATION",
        "comment": "Premier canevas de fiche etabli.",
        "reason_code": None,
        "created_at": "2026-03-24T11:00:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000006",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b002",
        "event_type": "TRANSITION",
        "from_status": "EXPLORATION",
        "to_status": "POC",
        "comment": "Prototype de fiche partagee sur trois idees concretes.",
        "reason_code": None,
        "created_at": "2026-04-03T09:20:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000007",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b002",
        "event_type": "TRANSITION",
        "from_status": "POC",
        "to_status": "TRANSMIS",
        "comment": "Envoyee a deux relais internes pour retour usage.",
        "reason_code": None,
        "created_at": "2026-04-12T14:15:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000008",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b003",
        "event_type": "CREATION",
        "from_status": None,
        "to_status": "GERME",
        "comment": "Capture apres un premier essai local.",
        "reason_code": None,
        "created_at": "2026-04-02T07:50:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000009",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b003",
        "event_type": "TRANSITION",
        "from_status": "GERME",
        "to_status": "EXPLORATION",
        "comment": "La piste merite une validation plus structuree.",
        "reason_code": None,
        "created_at": "2026-04-04T08:05:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000010",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b003",
        "event_type": "TRANSITION",
        "from_status": "EXPLORATION",
        "to_status": "POC",
        "comment": "POC lance sur un petit corpus de timelines.",
        "reason_code": None,
        "created_at": "2026-04-17T11:00:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000011",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b004",
        "event_type": "CREATION",
        "from_status": None,
        "to_status": "GERME",
        "comment": "Plusieurs idees prometteuses, mais pas actionnables tout de suite.",
        "reason_code": None,
        "created_at": "2026-02-11T13:20:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000012",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b004",
        "event_type": "TRANSITION",
        "from_status": "GERME",
        "to_status": "ABANDONNE",
        "comment": "Trop floue initialement, a retravailler.",
        "reason_code": "CONTEXT_CHANGED",
        "created_at": "2026-02-20T10:15:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000013",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b004",
        "event_type": "TRANSITION",
        "from_status": "ABANDONNE",
        "to_status": "EXPLORATION",
        "comment": "Relancee pendant l'arbitrage de portefeuille.",
        "reason_code": None,
        "created_at": "2026-04-02T09:45:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000014",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b004",
        "event_type": "TRANSITION",
        "from_status": "EXPLORATION",
        "to_status": "EN_VEILLE",
        "comment": "A reevaluer apres la sequence roadmap Q3.",
        "reason_code": "NO_PRIORITY",
        "created_at": "2026-04-10T16:00:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000015",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b005",
        "event_type": "CREATION",
        "from_status": None,
        "to_status": "GERME",
        "comment": "Piste de scoring capturee a chaud.",
        "reason_code": None,
        "created_at": "2026-01-18T08:10:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000016",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b005",
        "event_type": "TRANSITION",
        "from_status": "GERME",
        "to_status": "ABANDONNE",
        "comment": "Le score masque le vrai enjeu qui est la qualite du contexte.",
        "reason_code": "NO_VALUE",
        "created_at": "2026-02-02T09:00:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000017",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b006",
        "event_type": "CREATION",
        "from_status": None,
        "to_status": "GERME",
        "comment": "Reference historique pour les demonstrations.",
        "reason_code": None,
        "created_at": "2025-12-15T10:00:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000018",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b006",
        "event_type": "TRANSITION",
        "from_status": "GERME",
        "to_status": "EXPLORATION",
        "comment": "Prototype rapide utilise comme support.",
        "reason_code": None,
        "created_at": "2025-12-20T09:00:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000019",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b006",
        "event_type": "TRANSITION",
        "from_status": "EXPLORATION",
        "to_status": "POC",
        "comment": "Testee dans un atelier interne.",
        "reason_code": None,
        "created_at": "2025-12-26T11:00:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000020",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b006",
        "event_type": "TRANSITION",
        "from_status": "POC",
        "to_status": "TRANSMIS",
        "comment": "Reprise par un collegue pour adaptation locale.",
        "reason_code": None,
        "created_at": "2026-01-02T09:15:00+00:00",
    },
    {
        "id": "d3bf17bc-8780-4b7b-95db-8d07f9000021",
        "idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b006",
        "event_type": "TRANSITION",
        "from_status": "TRANSMIS",
        "to_status": "REALISE",
        "comment": "Utilise comme base d'une documentation de reference.",
        "reason_code": None,
        "created_at": "2026-01-05T10:00:00+00:00",
    },
]

DEMO_LINKS = [
    {
        "id": "af20b13f-75d0-4a2e-9e16-2d87e5000001",
        "source_idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b003",
        "target_idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b001",
        "link_type": "derived_from",
    },
    {
        "id": "af20b13f-75d0-4a2e-9e16-2d87e5000002",
        "source_idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b002",
        "target_idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b001",
        "link_type": "related",
    },
    {
        "id": "af20b13f-75d0-4a2e-9e16-2d87e5000003",
        "source_idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b004",
        "target_idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b002",
        "link_type": "related",
    },
    {
        "id": "af20b13f-75d0-4a2e-9e16-2d87e5000004",
        "source_idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b005",
        "target_idea_id": "b8d9c64d-e7d8-4c63-85ee-b7127860b001",
        "link_type": "duplicate",
    },
]

DEMO_IDEA_IDS = tuple(idea["id"] for idea in DEMO_IDEAS)


def seed_demo_data(conn: sqlite3.Connection) -> None:
    existing = conn.execute("SELECT COUNT(*) AS count FROM ideas").fetchone()
    if existing is not None and existing["count"] > 0:
        return

    conn.executemany(
        """
        INSERT INTO ideas (
            id, title, description, domain, tags, source_type, source_context,
            created_at, updated_at, current_status, archived,
            confidence_level, estimated_value, estimated_effort,
            next_action, revisit_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                idea["id"],
                idea["title"],
                idea["description"],
                idea["domain"],
                json.dumps(idea["tags"]),
                idea["source_type"],
                idea["source_context"],
                idea["created_at"],
                idea["updated_at"],
                idea["current_status"],
                idea["archived"],
                idea["confidence_level"],
                idea["estimated_value"],
                idea["estimated_effort"],
                idea["next_action"],
                idea["revisit_at"],
            )
            for idea in DEMO_IDEAS
        ],
    )

    conn.executemany(
        """
        INSERT INTO idea_events (
            id, idea_id, event_type, from_status, to_status, comment, reason_code, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                event["id"],
                event["idea_id"],
                event["event_type"],
                event["from_status"],
                event["to_status"],
                event["comment"],
                event["reason_code"],
                event["created_at"],
            )
            for event in DEMO_EVENTS
        ],
    )

    conn.executemany(
        """
        INSERT INTO idea_links (id, source_idea_id, target_idea_id, link_type)
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                link["id"],
                link["source_idea_id"],
                link["target_idea_id"],
                link["link_type"],
            )
            for link in DEMO_LINKS
        ],
    )


def remove_demo_data(conn: sqlite3.Connection) -> int:
    if not DEMO_IDEA_IDS:
        return 0

    placeholders = ", ".join("?" for _ in DEMO_IDEA_IDS)
    result = conn.execute(
        f"DELETE FROM ideas WHERE id IN ({placeholders})",
        DEMO_IDEA_IDS,
    )
    return result.rowcount
