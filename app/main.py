from __future__ import annotations

from datetime import date

from fastapi import FastAPI, HTTPException, Query, Response

from .db import init_db
from .repository import list_ideas
from .schemas import (
    Domain,
    IdeaCreate,
    IdeaEventResponse,
    IdeaGraphResponse,
    IdeaLinkCreate,
    IdeaLinkResponse,
    IdeaResponse,
    IdeaSearchResponse,
    IdeaUpdate,
    SortField,
    SortOrder,
    Status,
    TransitionRequest,
)
from .services import (
    NotFoundError,
    ValidationError,
    archive_idea,
    create_idea,
    create_idea_link,
    delete_idea_link,
    get_idea,
    get_idea_graph,
    list_idea_events,
    search_ideas,
    transition_idea,
    update_idea,
)

app = FastAPI(title="Idea Lifecycle Tracker API", version="0.2.0")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.post("/ideas", response_model=IdeaResponse, status_code=201)
def create_idea_endpoint(payload: IdeaCreate) -> IdeaResponse:
    try:
        created = create_idea(payload)
        return IdeaResponse.model_validate(created)
    except ValidationError as exc:
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
        return IdeaResponse.model_validate(get_idea(idea_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/ideas/{idea_id}", response_model=IdeaResponse)
def update_idea_endpoint(idea_id: str, payload: IdeaUpdate) -> IdeaResponse:
    try:
        return IdeaResponse.model_validate(update_idea(idea_id, payload))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/ideas/{idea_id}", status_code=204)
def delete_idea_endpoint(idea_id: str) -> Response:
    try:
        archive_idea(idea_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=204)


@app.post("/ideas/{idea_id}/transition", response_model=IdeaResponse)
def transition_idea_endpoint(idea_id: str, payload: TransitionRequest) -> IdeaResponse:
    try:
        return IdeaResponse.model_validate(transition_idea(idea_id, payload))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/ideas/{idea_id}/events", response_model=list[IdeaEventResponse])
def get_idea_events_endpoint(idea_id: str) -> list[IdeaEventResponse]:
    try:
        return [IdeaEventResponse.model_validate(row) for row in list_idea_events(idea_id)]
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/ideas/{idea_id}/graph", response_model=IdeaGraphResponse)
def get_idea_graph_endpoint(idea_id: str) -> IdeaGraphResponse:
    try:
        return IdeaGraphResponse.model_validate(get_idea_graph(idea_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/ideas/{idea_id}/links", response_model=IdeaLinkResponse, status_code=201)
def create_idea_link_endpoint(idea_id: str, payload: IdeaLinkCreate) -> IdeaLinkResponse:
    try:
        return IdeaLinkResponse.model_validate(create_idea_link(idea_id, payload))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/ideas/{idea_id}/links/{link_id}", status_code=204)
def delete_idea_link_endpoint(idea_id: str, link_id: str) -> Response:
    try:
        delete_idea_link(idea_id, link_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=204)


@app.get("/search", response_model=list[IdeaSearchResponse])
def search_ideas_endpoint(
    q: str = Query(..., min_length=1),
    include_archived: bool = Query(default=False),
) -> list[IdeaSearchResponse]:
    try:
        rows = search_ideas(q, include_archived=include_archived)
        return [IdeaSearchResponse.model_validate(row) for row in rows]
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
