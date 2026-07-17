"""STRATEGIST — the senior decision-maker. Weighs options against evidence and commits to a cadence.

The cadence decision is the product's core output: it must be willing to say "post less" or
"post nothing this week" when the evidence supports it, and must justify the number by weighing
real alternatives — never default to a fixed count, never merely summarize the other specialists.
"""
import json

from app.agent.knowledge import GROWTH_STAGE_PLAYBOOKS, LINKEDIN_MECHANICS
from app.agent.llm_call import TEMP_RIGOROUS, call_llm_for_json
from app.agent.state import WeekState

SYSTEM = (
    "You are the STRATEGIST — the senior growth and brand strategist who runs this account, with the "
    "judgment of a CXO who has taken many accounts from zero to serious reach. The Analyst, Audience "
    "Profiler, Researcher, and Historian report to you. Your job is not to summarize them — it is to "
    "make a DECISION they could not, by weighing their evidence against each other and against how "
    "LinkedIn actually works.\n\n"
    f"{GROWTH_STAGE_PLAYBOOKS}\n\n"
    f"{LINKEDIN_MECHANICS}\n\n"
    "THE CADENCE DECISION IS YOUR MOST IMPORTANT OUTPUT. Before you pick a number, genuinely CONSIDER "
    "AT LEAST TWO options (e.g. 'post 3 aggressive' vs 'post 1 and protect the last winner' vs 'post 0 "
    "and reposition') and explain why you REJECTED the alternative. Ground the choice in specific "
    "evidence you were given: the engagement-rate and reach-per-post trend, fatigue signals, dormancy, "
    "whether a recent post is still compounding (don't bury a winner), the growth stage, and the goal. "
    "You MUST be willing to recommend fewer posts, or ZERO posts with a recovery/repositioning plan, "
    "when the evidence says so. A strategist who always lands on the same number regardless of the data "
    "has failed. More posts is NOT more growth if reach-per-post is falling.\n\n"
    "Also decide: the week's THEME (one coherent idea, not scattered topics — topical consistency "
    "compounds), the FUNNEL MIX (reach/trust/convert %) tied to the stage and goal, and any POSITIONING "
    "shift the evidence demands.\n\n"
    "Think in 'situation_assessment' and 'options_considered' FIRST, then commit. Return ONLY a single "
    "JSON object, no markdown fences, no commentary."
)

EXPECTED_SHAPE = """{
  "situation_assessment": "your synthesis of the evidence and the central tension to resolve this week",
  "options_considered": [
    {"option": "e.g. post 3 this week", "for": "why it could be right", "against": "why it might not be", "chosen": true|false}
  ],
  "growth_stage": "foundation|signal|reach|authority|scale",
  "week_theme": "one coherent theme for the week",
  "cadence_decision": {
    "posts_this_week": 0,
    "schedule": [{"day": "string", "reason": "string grounded in audience timing/evidence"}],
    "reasoning": "why THIS number, citing the specific evidence and the rejected alternative"
  },
  "funnel_mix": {"reach_pct": 0, "trust_pct": 0, "convert_pct": 0},
  "positioning_shift": "string or null",
  "reasoning_summary": "the one-line decision the dashboard shows as the hero",
  "is_recovery_week": true|false,
  "recovery_plan": "if 0 posts: the concrete repositioning/recovery work to do instead, else null"
}"""


async def strategist_node(state: WeekState) -> WeekState:
    project = state["project"]
    cold_start_note = (
        "\nCOLD START: this is week 1 — no history yet. Lean on demographics and niche research, keep "
        "confidence modest, and be explicit that this week is a baseline PROBE designed to generate "
        "signal (learn what resonates), not a fully optimized plan.\n"
        if state.get("is_cold_start") else ""
    )

    performance = state.get("post_performance", [])
    perf_note = (
        json.dumps(performance[:8], indent=2, default=str)
        if performance
        else "No real post-performance data yet."
    )

    prompt = f"""
Project: {project.get("name")} ({project.get("account_type")})
Niche: {project.get("niche") or "not specified"}
Stated audience: {project.get("audience") or "not specified"}
Goal: {project.get("goal") or "not specified"}
Owner notes: {project.get("notes") or "none"}
Growth stage on file (may be stale): {project.get("growth_stage") or "unknown"}
{cold_start_note}
ANALYST diagnosis:
{json.dumps(state.get("analyst_diagnosis", {}), indent=2, default=str)}

Computed deltas + full trend line:
{json.dumps({"deltas": state.get("deltas", {}), "trend": state.get("trend", {})}, indent=2, default=str)}

AUDIENCE PROFILER findings:
{json.dumps(state.get("audience_profile", {}), indent=2, default=str)}

RESEARCHER live trends + angles:
{json.dumps(state.get("research_findings", {}), indent=2, default=str)}

HISTORIAN recall (past learnings; empty if no history):
{json.dumps(state.get("historical_memories", {}), indent=2, default=str)}

REAL post performance (what actually worked):
{perf_note}

Weigh the options and decide this week's strategy. Return JSON matching:
{EXPECTED_SHAPE}
"""
    result = await call_llm_for_json(
        prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE, temperature=TEMP_RIGOROUS
    )
    # Routing depends only on the actual cadence number, never the model's own is_recovery_week flag —
    # the two can disagree (seen live), and the number is authoritative.
    posts_this_week = result.get("cadence_decision", {}).get("posts_this_week", 0)
    return {"strategy": result, "is_recovery_week": posts_this_week == 0}
