from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class MemoryCreate(BaseModel):
    kind: str  # e.g. "winning_hook", "flop", "audience_insight", "strategy_shift"
    content: str
    metadata: Optional[dict[str, Any]] = None


class MemoryOut(BaseModel):
    id: UUID
    project_id: Optional[UUID] = None
    kind: Optional[str] = None
    content: str
    metadata: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None


class MemorySearchRequest(BaseModel):
    query: str
    kind: str
    match_count: int = 5


class MemoryMatch(BaseModel):
    id: UUID
    kind: Optional[str] = None
    content: str
    metadata: Optional[dict[str, Any]] = None
    similarity: float
