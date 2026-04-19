from __future__ import annotations

from . import repository
from .schemas import (
    ABANDONNE_REASON_CODES,
    EN_VEILLE_REASON_CODES,
    IdeaCreate,
    IdeaLinkCreate,
    IdeaUpdate,
    TransitionRequest,
)

ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "GERME": ["EXPLORATION", "ABANDONNE"],
    "EXPLORATION": ["POC", "EN_VEILLE", "ABANDONNE"],
    "POC": ["TRANSMIS", "EN_VEILLE", "ABANDONNE"],
    "TRANSMIS": ["REALISE", "EN_VEILLE"],
    "EN_VEILLE": ["EXPLORATION", "ABANDONNE"],
    "ABANDONNE": ["EXPLORATION"],
    "REALISE": [],
}


class ServiceError(Exception):
    pass


class NotFoundError(ServiceError):
    pass


class ValidationError(ServiceError):
    pass


def create_idea(payload: IdeaCreate) -> dict:
    title = payload.title.strip()
    if not title:
        raise ValidationError("title must not be empty")

    timestamp = repository.now_iso()
    idea_id = repository.create_idea_record(
        {
            "title": title,
            "description": payload.description,
            "domain": payload.domain.value,
            "tags": payload.tags,
            "source_type": payload.source_type.value,
            "source_context": payload.source_context,
            "created_at": timestamp,
            "updated_at": timestamp,
            "current_status": "GERME",
            "archived": False,
            "confidence_level": payload.confidence_level,
            "estimated_value": payload.estimated_value,
            "estimated_effort": payload.estimated_effort,
            "next_action": payload.next_action,
            "revisit_at": payload.revisit_at.isoformat() if payload.revisit_at else None,
        }
    )
    idea = repository.get_idea_by_id(idea_id)
    if idea is None:
        raise NotFoundError("Idea not found")
    return idea


def get_idea(idea_id: str) -> dict:
    idea = repository.get_idea_by_id(idea_id)
    if idea is None:
        raise NotFoundError("Idea not found")
    return idea


def update_idea(idea_id: str, payload: IdeaUpdate) -> dict:
    current = repository.get_idea_by_id(idea_id)
    if current is None:
        raise NotFoundError("Idea not found")

    updates = _build_idea_updates(payload)
    if updates:
        updates["updated_at"] = repository.now_iso()
        updated = repository.update_idea_record(idea_id, updates)
        if not updated:
            raise NotFoundError("Idea not found")

    idea = repository.get_idea_by_id(idea_id)
    if idea is None:
        raise NotFoundError("Idea not found")
    return idea


def archive_idea(idea_id: str) -> None:
    archived = repository.archive_idea_record(idea_id, repository.now_iso())
    if not archived:
        raise NotFoundError("Idea not found")


def transition_idea(idea_id: str, payload: TransitionRequest) -> dict:
    current = repository.get_idea_by_id(idea_id)
    if current is None:
        raise NotFoundError("Idea not found")

    current_status = current["current_status"]
    to_status = payload.to_status.value
    _validate_transition(current_status, payload)

    updated = repository.transition_idea_record(
        idea_id,
        to_status=to_status,
        from_status=current_status,
        comment=payload.comment.strip(),
        reason_code=payload.reason_code.value if payload.reason_code else None,
        revisit_at=payload.revisit_at.isoformat() if payload.revisit_at and to_status == "EN_VEILLE" else None,
        updated_at=repository.now_iso(),
    )
    if not updated:
        raise NotFoundError("Idea not found")

    idea = repository.get_idea_by_id(idea_id)
    if idea is None:
        raise NotFoundError("Idea not found")
    return idea


def list_idea_events(idea_id: str) -> list[dict]:
    _ = get_idea(idea_id)
    return repository.list_idea_events(idea_id)


def get_idea_graph(idea_id: str) -> dict:
    graph = repository.get_idea_graph(idea_id)
    if graph is None:
        raise NotFoundError("Idea not found")
    return graph


def create_idea_link(idea_id: str, payload: IdeaLinkCreate) -> dict:
    source = repository.get_idea_by_id(idea_id)
    if source is None:
        raise NotFoundError("Idea not found")

    target_id = str(payload.target_idea_id)
    target = repository.get_idea_by_id(target_id)
    if target is None:
        raise NotFoundError("Target idea not found")

    if idea_id == target_id:
        raise ValidationError("An idea cannot link to itself")

    if repository.idea_link_exists(idea_id, target_id, payload.link_type.value):
        raise ValidationError("This link already exists")

    return repository.create_idea_link_record(
        source_idea_id=idea_id,
        target_idea_id=target_id,
        link_type=payload.link_type.value,
        updated_at=repository.now_iso(),
    )


def delete_idea_link(idea_id: str, link_id: str) -> None:
    _ = get_idea(idea_id)

    link = repository.get_idea_link_by_id(link_id)
    if link is None or link["source_idea_id"] != idea_id:
        raise NotFoundError("IdeaLink not found")

    deleted = repository.delete_idea_link_record(link_id, idea_id, repository.now_iso())
    if not deleted:
        raise NotFoundError("IdeaLink not found")


def search_ideas(query_text: str, include_archived: bool) -> list[dict]:
    query = query_text.strip()
    if not query:
        raise ValidationError("q must not be empty")
    return repository.search_ideas(query, include_archived=include_archived)


def _build_idea_updates(payload: IdeaUpdate) -> dict:
    updates: dict = {}

    if "title" in payload.model_fields_set:
        if payload.title is None:
            raise ValidationError("title cannot be null")
        title = payload.title.strip()
        if not title:
            raise ValidationError("title must not be empty")
        updates["title"] = title

    if "description" in payload.model_fields_set:
        updates["description"] = payload.description
    if "domain" in payload.model_fields_set:
        updates["domain"] = payload.domain.value if payload.domain else None
    if "tags" in payload.model_fields_set:
        updates["tags"] = payload.tags or []
    if "source_type" in payload.model_fields_set:
        updates["source_type"] = payload.source_type.value if payload.source_type else None
    if "source_context" in payload.model_fields_set:
        updates["source_context"] = payload.source_context
    if "confidence_level" in payload.model_fields_set:
        updates["confidence_level"] = payload.confidence_level
    if "estimated_value" in payload.model_fields_set:
        updates["estimated_value"] = payload.estimated_value
    if "estimated_effort" in payload.model_fields_set:
        updates["estimated_effort"] = payload.estimated_effort
    if "next_action" in payload.model_fields_set:
        updates["next_action"] = payload.next_action
    if "revisit_at" in payload.model_fields_set:
        updates["revisit_at"] = payload.revisit_at.isoformat() if payload.revisit_at else None

    return updates


def _validate_transition(current_status: str, payload: TransitionRequest) -> None:
    to_status = payload.to_status.value

    if to_status == current_status:
        raise ValidationError("Transition to the same status is not allowed")

    allowed = ALLOWED_TRANSITIONS[current_status]
    if to_status not in allowed:
        raise ValidationError(f"Transition from {current_status} to {to_status} is not allowed")

    comment = payload.comment.strip()
    reason_code = payload.reason_code.value if payload.reason_code else None

    if to_status in {"TRANSMIS", "EN_VEILLE", "ABANDONNE", "REALISE"} and not comment:
        raise ValidationError(f"comment is required when transitioning to {to_status}")

    if to_status == "EN_VEILLE":
        if reason_code not in EN_VEILLE_REASON_CODES:
            raise ValidationError("reason_code is required and must be valid for EN_VEILLE")
        if payload.revisit_at is None:
            raise ValidationError("revisit_at is required when transitioning to EN_VEILLE")
    elif to_status == "ABANDONNE":
        if reason_code not in ABANDONNE_REASON_CODES:
            raise ValidationError("reason_code is required and must be valid for ABANDONNE")
        if payload.revisit_at is not None:
            raise ValidationError("revisit_at is only allowed for EN_VEILLE")
    else:
        if reason_code is not None:
            raise ValidationError(f"reason_code is not allowed when transitioning to {to_status}")
        if payload.revisit_at is not None:
            raise ValidationError("revisit_at is only allowed for EN_VEILLE")
