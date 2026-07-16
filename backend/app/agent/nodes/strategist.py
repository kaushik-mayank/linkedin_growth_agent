"""STRATEGIST — synthesizes everything, decides growth stage, cadence, funnel mix, positioning.

The cadence decision is the product's core output: it must be willing to say "post less"
or "post nothing this week" when the evidence supports it, never default to a fixed number.
"""
import json

from app.agent.llm_call import call_llm_for_json
from app.agent.state import WeekState

SYSTEM = (
    "You are the STRATEGIST — the senior decision-maker on a LinkedIn growth team, equivalent to "
    "a top branding agency's strategy lead. You synthesize the Analyst's diagnosis, the Audience "
    "Profiler's findings, the Researcher's live trends, and the Historian's recalled memories into "
    "one coherent weekly strategy.\n\n"
    "GROWTH STAGES: foundation (0-500 followers: positioning + proof of life), signal (500-2k: "
    "find what resonates, test formats), reach (2k-10k: scale winners, ride trends), authority "
    "(10k-100k: depth, series, POV), scale (100k+: multi-format, community, repurposing).\n\n"
    "THE CADENCE DECISION IS YOUR MOST IMPORTANT OUTPUT. Decide how many posts this week (0 to "
    "7+), on which days, and WHY — grounded in the evidence you were given: engagement-rate trend, "
    "reach per post, fatigue signals, dormancy, whether a recent post is still compounding, and the "
    "growth stage. You MUST be willing to recommend fewer posts, or ZERO posts this week with a "
    "recovery/repositioning plan instead, if the evidence supports it. A strategist who always "
    "recommends a fixed number regardless of the data has failed at their job. Justify the number "
    "with the specific evidence — never a default.\n\n"
    "Return ONLY a single JSON object, no markdown fences, no commentary."
)

EXPECTED_SHAPE = """{
  "growth_stage": "foundation|signal|reach|authority|scale",
  "week_theme": "string",
  "cadence_decision": {
    "posts_this_week": 0,
    "schedule": [{"day": "string", "reason": "string"}, ...],
    "reasoning": "string"
  },
  "funnel_mix": {"reach_pct": 0, "trust_pct": 0, "convert_pct": 0},
  "positioning_shift": "string or null",
  "reasoning_summary": "string",
  "is_recovery_week": true|false,
  "recovery_plan": "string or null"
}"""


async def strategist_node(state: WeekState) -> WeekState:
    project = state["project"]
    cold_start_note = (
        "\nCOLD START: this is week 1 — there is no history yet. Lean on demographics and niche "
        "research instead of trend-vs-history deltas. Be explicit that this week is a baseline "
        "probe designed to generate signal, not a fully optimized plan.\n"
        if state.get("is_cold_start") else ""
    )

    prompt = f"""
Project: {project.get("name")} ({project.get("account_type")})
Niche: {project.get("niche") or "not specified"}
Stated audience: {project.get("audience") or "not specified"}
Goal: {project.get("goal") or "not specified"}
Extra notes from the account owner: {project.get("notes") or "none"}
Current growth stage on file (may be stale): {project.get("growth_stage") or "unknown"}
{cold_start_note}
ANALYST diagnosis:
{json.dumps(state.get("analyst_diagnosis", {}), indent=2, default=str)}

Computed deltas:
{json.dumps(state.get("deltas", {}), indent=2, default=str)}

AUDIENCE PROFILER findings:
{json.dumps(state.get("audience_profile", {}), indent=2, default=str)}

RESEARCHER findings (live trends):
{json.dumps(state.get("research_findings", {}), indent=2, default=str)}

HISTORIAN recall (past learnings, empty lists if no history yet):
{json.dumps(state.get("historical_memories", {}), indent=2, default=str)}

Decide this week's strategy. Return JSON matching:
{EXPECTED_SHAPE}
"""
    result = await call_llm_for_json(prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE)
    # Routing must depend only on the actual cadence number, never the model's own
    # self-reported is_recovery_week flag — the two can disagree (seen live: the model
    # said is_recovery_week=true while posts_this_week=2), and the number is authoritative.
    posts_this_week = result.get("cadence_decision", {}).get("posts_this_week", 0)
    return {"strategy": result, "is_recovery_week": posts_this_week == 0}
