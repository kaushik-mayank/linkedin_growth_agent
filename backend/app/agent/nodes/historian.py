"""HISTORIAN — retrieves the most useful past learnings from memory. Pure retrieval, no LLM call.

Two upgrades over naive top-k similarity: (1) a richer query built from the current situation AND the
audience, so retrieval reflects what the team is actually about to reason about; (2) recency-aware
re-ranking — among semantically close memories, prefer the more recent (and thus more currently true)
ones, since an audience and what works for it drift over time.
"""
from typing import Any

from app.agent.state import WeekState
from app.memory_store import search_memory_multi

MEMORY_KINDS = ["winning_hook", "flop", "audience_insight", "strategy_shift"]
RECENCY_WEIGHT = 0.05  # gentle nudge toward recent learnings; never overrides a clearly better match


def _rerank(rows: list[dict[str, Any]], keep: int) -> list[dict[str, Any]]:
    if not rows:
        return []
    weeks = [
        (r.get("metadata") or {}).get("week_number", 0) or 0 for r in rows
    ]
    max_week = max(weeks) or 1
    scored = []
    for r in rows:
        similarity = r.get("similarity", 0) or 0
        week = (r.get("metadata") or {}).get("week_number", 0) or 0
        score = similarity + RECENCY_WEIGHT * (week / max_week)
        scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:keep]]


async def historian_node(state: WeekState) -> WeekState:
    project = state["project"]
    diagnosis = state.get("analyst_diagnosis", {})
    profile = state.get("audience_profile", {})

    # A richer query than the niche alone: what's happening + who's here + the read of the account.
    query = (
        f"LinkedIn growth for {project.get('niche') or project.get('name')}. "
        f"Account state: {diagnosis.get('account_state', 'unknown')}, "
        f"trajectory: {diagnosis.get('trajectory', '')}. "
        f"Audience: {profile.get('actual_audience_summary', '')}. "
        f"{diagnosis.get('narrative', '')}"
    )

    # Fetch more than we need, then recency-aware re-rank down to the best few per kind.
    raw = await search_memory_multi(project["id"], query, MEMORY_KINDS, match_count=6)
    memories = {kind: _rerank(rows, keep=3) for kind, rows in raw.items()}
    return {"historical_memories": memories}
