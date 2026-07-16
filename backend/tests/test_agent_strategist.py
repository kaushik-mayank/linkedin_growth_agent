from unittest.mock import AsyncMock

import pytest

from app.agent.nodes import strategist as strategist_module


@pytest.mark.asyncio
async def test_is_recovery_week_derived_from_cadence_not_the_models_own_flag(monkeypatch):
    """Regression test: live run showed the model can set is_recovery_week=true while
    cadence_decision.posts_this_week=2 in the same reply. Routing must trust the number."""
    fake_llm_result = {
        "growth_stage": "signal",
        "week_theme": "Reduce and refocus",
        "cadence_decision": {"posts_this_week": 2, "schedule": [], "reasoning": "Cut volume."},
        "funnel_mix": {"reach_pct": 50, "trust_pct": 30, "convert_pct": 20},
        "positioning_shift": None,
        "reasoning_summary": "Reduce volume due to fatigue.",
        "is_recovery_week": True,  # inconsistent on purpose, mirroring the real observed bug
        "recovery_plan": None,
    }
    monkeypatch.setattr(strategist_module, "call_llm_for_json", AsyncMock(return_value=fake_llm_result))

    state = {
        "project": {"name": "Test", "account_type": "creator"},
        "analyst_diagnosis": {}, "deltas": {}, "audience_profile": {},
        "research_findings": {}, "historical_memories": {},
    }
    result = await strategist_module.strategist_node(state)

    assert result["is_recovery_week"] is False
    assert result["strategy"]["cadence_decision"]["posts_this_week"] == 2


@pytest.mark.asyncio
async def test_zero_posts_is_correctly_flagged_as_recovery_week(monkeypatch):
    fake_llm_result = {
        "growth_stage": "foundation",
        "cadence_decision": {"posts_this_week": 0, "schedule": [], "reasoning": "Fix positioning first."},
        "is_recovery_week": True,
        "recovery_plan": "Rewrite your headline before posting again.",
    }
    monkeypatch.setattr(strategist_module, "call_llm_for_json", AsyncMock(return_value=fake_llm_result))

    state = {
        "project": {"name": "Test", "account_type": "creator"},
        "analyst_diagnosis": {}, "deltas": {}, "audience_profile": {},
        "research_findings": {}, "historical_memories": {},
    }
    result = await strategist_module.strategist_node(state)

    assert result["is_recovery_week"] is True
