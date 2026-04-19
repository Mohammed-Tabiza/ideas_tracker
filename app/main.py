from __future__ import annotations

from datetime import date

from fastapi import FastAPI, HTTPException, Query

from .db import init_db
from .repository import archive_idea, create_idea, get_idea_by_id, list_ideas, update_idea
from .schemas import Domain, IdeaCreate, IdeaResponse, IdeaUpdate, SortField, SortOrder, Status

app = FastAPI(title="Idea Lifecycle Tracker API", version="0.2.0")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.post("/ideas", response_model=IdeaResponse, status_code=201)
def create_idea_endpoint(payload: IdeaCreate) -> IdeaResponse:
    try:
        created = create_idea(payload)
        return IdeaResponse.model_validate(created)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/ideas", response_model=list[IdeaResponse])
def list_ideas_endpoint(
    include_archived: bool = Query(default=False),
    status: Status | None = Query(default=None),
    domain: Domain | None = Query(default=None),
    tags: str | None = Query(default=None, description="Comma separated tags"),
    stale: bool | None = Query(default=None),
    revisit_before: date | None = Query(default=None),
    sort: SortField = Query(default=SortField.created_at),
    order: SortOrder = Query(default=SortOrder.desc),
) -> list[IdeaResponse]:
    tag_values = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else None

    rows = list_ideas(
        include_archived=include_archived,
        status=status.value if status else None,
        domain=domain.value if domain else None,
        tags=tag_values,
        stale=stale,
        revisit_before=revisit_before.isoformat() if revisit_before else None,
        sort=sort.value,
        order=order.value,
    )
    return [IdeaResponse.model_validate(row) for row in rows]


@app.get("/ideas/{idea_id}", response_model=IdeaResponse)
def get_idea_endpoint(idea_id: str) -> IdeaResponse:
    try:
        return IdeaResponse.model_validate(get_idea_by_id(idea_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/ideas/{idea_id}", response_model=IdeaResponse)
def update_idea_endpoint(idea_id: str, payload: IdeaUpdate) -> IdeaResponse:
    try:
        updated = update_idea(idea_id, payload)
        return IdeaResponse.model_validate(updated)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@app.delete("/ideas/{idea_id}", response_model=IdeaResponse)
def archive_idea_endpoint(idea_id: str) -> IdeaResponse:
    try:
        archived = archive_idea(idea_id)
        return IdeaResponse.model_validate(archived)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
