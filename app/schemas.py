from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Domain(str, Enum):
    IA4IT = "IA4IT"
    IA4ALL = "IA4ALL"
    STRATEGY = "STRATEGY"
    ARCHITECTURE = "ARCHITECTURE"
    OTHER = "OTHER"


class SourceType(str, Enum):
    CONVERSATION = "CONVERSATION"
    MEETING = "MEETING"
    READING = "READING"
    EXPERIMENT = "EXPERIMENT"
    INTUITION = "INTUITION"
    OTHER = "OTHER"


class Status(str, Enum):
    GERME = "GERME"
    EXPLORATION = "EXPLORATION"
    POC = "POC"
    TRANSMIS = "TRANSMIS"
    EN_VEILLE = "EN_VEILLE"
    ABANDONNE = "ABANDONNE"
    REALISE = "REALISE"


class ReasonCode(str, Enum):
    TOO_EARLY = "TOO_EARLY"
    NO_PRIORITY = "NO_PRIORITY"
    WAITING_DEPENDENCY = "WAITING_DEPENDENCY"
    NO_VALUE = "NO_VALUE"
    TOO_COMPLEX = "TOO_COMPLEX"
    DUPLICATE = "DUPLICATE"
    CONTEXT_CHANGED = "CONTEXT_CHANGED"


EN_VEILLE_REASON_CODES = {
    ReasonCode.TOO_EARLY.value,
    ReasonCode.NO_PRIORITY.value,
    ReasonCode.WAITING_DEPENDENCY.value,
}

ABANDONNE_REASON_CODES = {
    ReasonCode.NO_VALUE.value,
    ReasonCode.TOO_COMPLEX.value,
    ReasonCode.DUPLICATE.value,
    ReasonCode.CONTEXT_CHANGED.value,
}


class IdeaCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    domain: Domain = Domain.OTHER
    tags: list[str] = Field(default_factory=list)
    source_type: SourceType = SourceType.INTUITION
    source_context: Optional[str] = None
    confidence_level: Optional[int] = Field(default=None, ge=1, le=5)
    estimated_value: Optional[int] = Field(default=None, ge=1, le=5)
    estimated_effort: Optional[int] = Field(default=None, ge=1, le=5)
    next_action: Optional[str] = None
    revisit_at: Optional[datetime] = None


class IdeaUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    domain: Domain | None = None
    tags: list[str] | None = None
    source_type: SourceType | None = None
    source_context: Optional[str] = None
    confidence_level: Optional[int] = Field(default=None, ge=1, le=5)
    estimated_value: Optional[int] = Field(default=None, ge=1, le=5)
    estimated_effort: Optional[int] = Field(default=None, ge=1, le=5)
    next_action: Optional[str] = None
    revisit_at: Optional[datetime] = None


class IdeaResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    domain: Domain
    tags: list[str]
    source_type: SourceType
    source_context: Optional[str]
    created_at: datetime
    updated_at: datetime
    current_status: Status
    confidence_level: Optional[int]
    estimated_value: Optional[int]
    estimated_effort: Optional[int]
    next_action: Optional[str]
    revisit_at: Optional[datetime]
    archived: bool


class SortField(str, Enum):
    created_at = "created_at"
    last_activity = "last_activity"
    estimated_value = "estimated_value"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class TransitionRequest(BaseModel):
    to_status: Status
    comment: str = ""
    reason_code: ReasonCode | None = None
    revisit_at: Optional[datetime] = None


class EventType(str, Enum):
    CREATION = "CREATION"
    TRANSITION = "TRANSITION"
    EDIT = "EDIT"
    NOTE = "NOTE"


class IdeaEventResponse(BaseModel):
    id: UUID
    idea_id: UUID
    event_type: EventType
    from_status: Status | None
    to_status: Status | None
    comment: str
    reason_code: ReasonCode | None
    created_at: datetime


class LinkType(str, Enum):
    parent = "parent"
    child = "child"
    related = "related"
    duplicate = "duplicate"
    derived_from = "derived_from"


class LinkDirection(str, Enum):
    outgoing = "outgoing"
    incoming = "incoming"


class IdeaLinkCreate(BaseModel):
    target_idea_id: UUID
    link_type: LinkType


class IdeaLinkResponse(BaseModel):
    id: UUID
    source_idea_id: UUID
    target_idea_id: UUID
    link_type: LinkType


class LinkedIdeaSummary(BaseModel):
    id: UUID
    title: str
    current_status: Status
    archived: bool


class IdeaGraphLinkResponse(BaseModel):
    id: UUID
    link_type: LinkType
    direction: LinkDirection
    target: LinkedIdeaSummary


class IdeaGraphResponse(BaseModel):
    idea: IdeaResponse
    links: list[IdeaGraphLinkResponse]


class IdeaSearchResponse(IdeaResponse):
    rank: float
