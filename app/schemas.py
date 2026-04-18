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
