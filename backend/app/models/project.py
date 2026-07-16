"""Mirrors the real `projects` table in Supabase — do not add fields that aren't columns there."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    # Suggested values: individual, creator, consultant, company_page, community
    account_type: str
    niche: Optional[str] = None
    audience: Optional[str] = None
    goal: Optional[str] = None
    notes: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    account_type: Optional[str] = None
    niche: Optional[str] = None
    audience: Optional[str] = None
    goal: Optional[str] = None
    notes: Optional[str] = None
    strategy: Optional[dict[str, Any]] = None
    growth_stage: Optional[str] = None
    current_cadence: Optional[dict[str, Any]] = None


class ProjectOut(BaseModel):
    id: UUID
    name: str
    account_type: str
    niche: Optional[str] = None
    audience: Optional[str] = None
    goal: Optional[str] = None
    notes: Optional[str] = None
    strategy: Optional[dict[str, Any]] = None
    growth_stage: Optional[str] = None
    current_cadence: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
