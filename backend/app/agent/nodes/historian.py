"""HISTORIAN — pulls the most relevant past learnings from memory via pgvector. Pure retrieval, no LLM call."""
from app.agent.state import WeekState
from app.memory_store import search_memory_multi

MEMORY_KINDS = ["winning_hook", "flop", "audience_insight", "strategy_shift"]


async def historian_node(state: WeekState) -> WeekState:
    project = state["project"]
    diagnosis = state.get("analyst_diagnosis", {})
    query = (
        f"LinkedIn growth for {project.get('niche') or project.get('name')}: "
        f"account state {diagnosis.get('account_state', 'unknown')}. {diagnosis.get('narrative', '')}"
    )

    memories = await search_memory_multi(project["id"], query, MEMORY_KINDS, match_count=3)
    return {"historical_memories": memories}
