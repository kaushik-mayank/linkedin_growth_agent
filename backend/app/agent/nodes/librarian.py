"""LIBRARIAN — the knowledge manager. Learns from REAL outcomes, not the team's own opinion of itself."""
import json

from app.agent.llm_call import TEMP_RIGOROUS, call_llm_for_json
from app.agent.state import WeekState
from app.memory_store import store_memory

VALID_KINDS = {"winning_hook", "flop", "audience_insight", "strategy_shift"}

SYSTEM = (
    "You are the LIBRARIAN — the knowledge manager for this account's long-term memory. Next week's "
    "team will only be as smart as what you choose to record now. You are SELECTIVE: store durable "
    "insights, never noise. A week with nothing genuinely new should produce zero or one entry.\n\n"
    "The single most important discipline: distinguish EVIDENCE from OPINION.\n"
    "- Label something a 'winning_hook' or a 'flop' ONLY when REAL post-performance data supports it "
    "(actual impressions/engagements from an export). A high internal draft score is NOT evidence a "
    "post worked in the real world — never record a winner or flop from a critic score alone.\n"
    "- 'audience_insight' and 'strategy_shift' can be recorded from this week's reasoning (demographics, "
    "the drift verdict, the strategic decision and why), because those are conclusions, not unproven "
    "performance claims.\n"
    "- Write each memory as a crisp, self-contained lesson a future strategist can act on out of "
    "context ('For this audience, X because Y'), not a vague note.\n\n"
    "Each entry's kind must be exactly one of: winning_hook, flop, audience_insight, strategy_shift. "
    "Return ONLY a single JSON object, no markdown fences, no commentary."
)

EXPECTED_SHAPE = """{
  "memories": [
    {"kind": "winning_hook|flop|audience_insight|strategy_shift",
     "content": "the self-contained lesson",
     "evidence": "real_performance|reasoning",
     "confidence": "low|medium|high"}
  ]
}"""


async def librarian_node(state: WeekState) -> WeekState:
    week_number = state.get("week_number", 1)
    performance = state.get("post_performance", [])
    perf_note = (
        json.dumps(performance[:10], indent=2, default=str)
        if performance
        else "No real post-performance data yet — do NOT record any winning_hook or flop this week."
    )

    prompt = f"""
This week's diagnosis:
{json.dumps(state.get("analyst_diagnosis", {}), indent=2, default=str)}

Audience profile + drift verdict:
{json.dumps(state.get("audience_profile", {}), indent=2, default=str)}

Strategy decided (and why):
{json.dumps(state.get("strategy", {}), indent=2, default=str)}

REAL post performance (the ONLY valid basis for a winning_hook/flop):
{perf_note}

Drafts written this week and their internal critic scores (these are OPINION, not real outcomes —
do not treat a high score as proof anything worked):
{json.dumps([
    {"hook": p.get("hook"), "format": p.get("format"), "critic_score": p.get("critic_score")}
    for p in state.get("posts", [])
], indent=2, default=str)}

What is genuinely worth remembering for future weeks? Return JSON matching:
{EXPECTED_SHAPE}
"""
    result = await call_llm_for_json(
        prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE, temperature=TEMP_RIGOROUS
    )
    memories = result.get("memories", [])

    stored = []
    warnings = list(state.get("warnings", []))
    for m in memories:
        kind = m.get("kind")
        if kind not in VALID_KINDS:
            continue
        metadata = {
            "week_number": week_number,
            "evidence": m.get("evidence", "reasoning"),
            "confidence": m.get("confidence", "medium"),
        }
        try:
            row = await store_memory(state["project"]["id"], kind, m["content"], metadata)
            stored.append(row)
        except Exception as e:
            warnings.append(f"Librarian: failed to store a memory ({kind}): {e}")

    return {"memories_to_store": stored, "warnings": warnings}
