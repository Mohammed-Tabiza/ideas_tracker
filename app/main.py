from __future__ import annotations

from fastapi import FastAPI, Query

from .db import init_db
from .repository import create_idea, list_ideas
from .schemas import IdeaCreate, IdeaResponse

app = FastAPI(title="Idea Lifecycle Tracker API", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.post("/ideas", response_model=IdeaResponse, status_code=201)
def create_idea_endpoint(payload: IdeaCreate) -> IdeaResponse:
    created = create_idea(payload)
    return IdeaResponse.model_validate(created)


@app.get("/ideas", response_model=list[IdeaResponse])
def list_ideas_endpoint(
    include_archived: bool = Query(default=False),
) -> list[IdeaResponse]:
    rows = list_ideas(include_archived=include_archived)
    return [IdeaResponse.model_validate(row) for row in rows]
