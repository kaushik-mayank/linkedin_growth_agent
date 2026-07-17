"""Typed state that flows through every node of the weekly LangGraph agent."""
from typing import Any, Optional, TypedDict


class WeekState(TypedDict, total=False):
    project: dict[str, Any]
    week_number: int
    current_snapshot: dict[str, Any]
    prior_snapshot: Optional[dict[str, Any]]
    snapshot_history: list[dict[str, Any]]
    trend: dict[str, Any]
    post_performance: list[dict[str, Any]]
    is_cold_start: bool
    deltas: dict[str, Any]

    analyst_diagnosis: dict[str, Any]
    audience_profile: dict[str, Any]
    research_findings: dict[str, Any]
    historical_memories: dict[str, list[dict[str, Any]]]

    strategy: dict[str, Any]
    is_recovery_week: bool

    last_week_posts: list[dict[str, Any]]
    posts: list[dict[str, Any]]
    critic_reviews: list[dict[str, Any]]
    revision_count: int

    memories_to_store: list[dict[str, Any]]

    warnings: list[str]
