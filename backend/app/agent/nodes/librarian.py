"""LIBRARIAN — writes new learnings to memory. Selective: insights, not noise."""
import json

from app.agent.llm_call import call_llm_for_json
from app.agent.state import WeekState
from app.memory_store import store_memory

SYSTEM = (
    "You are the LIBRARIAN. You decide what from this week is worth remembering for future weeks: "
    "winning hook patterns, formats that flopped and why, audience insights, strategy shifts and "
    "their rationale. Be SELECTIVE — store insights, not noise. A week with nothing genuinely new "
    "to learn should produce zero or one entry, not a padded list. Each entry's kind must be exactly "
    "one of: winning_hook, flop, audience_insight, strategy_shift. Return ONLY a single JSON object, "
    "no markdown fences, no commentary."
)

EXPECTED_SHAPE = """{"memories": [{"kind": "winning_hook|flop|audience_insight|strategy_shift", "content": "string"}, ...]}"""


async def librarian_node(state: WeekState) -> WeekState:
    prompt = f"""
This week's diagnosis:
{json.dumps(state.get("analyst_diagnosis", {}), indent=2, default=str)}

Audience profile:
{json.dumps(state.get("audience_profile", {}), indent=2, default=str)}

Strategy decided:
{json.dumps(state.get("strategy", {}), indent=2, default=str)}

Posts written and their critic scores (empty if this was a recovery week with no posts):
{json.dumps([
    {
        "hook": p.get("hook"),
        "format": p.get("format"),
        "critic_score": p.get("critic_score"),
        "critic_notes": p.get("critic_notes"),
    }
    for p in state.get("posts", [])
], indent=2, default=str)}

What is genuinely worth remembering for future weeks? Return JSON matching:
{EXPECTED_SHAPE}
"""
    result = await call_llm_for_json(prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE)
    memories = result.get("memories", [])

    stored = []
    warnings = list(state.get("warnings", []))
    for m in memories:
        try:
            row = await store_memory(state["project"]["id"], m["kind"], m["content"])
            stored.append(row)
        except Exception as e:
            warnings.append(f"Librarian: failed to store a memory ({m.get('kind')}): {e}")

    return {"memories_to_store": stored, "warnings": warnings}
