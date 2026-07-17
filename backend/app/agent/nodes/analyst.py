"""ANALYST — a senior growth analyst who reads the whole trend line and diagnoses honestly."""
import json

from app.agent.deltas import compute_deltas
from app.agent.llm_call import TEMP_RIGOROUS, call_llm_for_json
from app.agent.state import WeekState

SYSTEM = (
    "You are the ANALYST — a senior growth data analyst on an elite LinkedIn strategy team, the kind "
    "a brand would pay a fortune for. You turn raw analytics into an honest, precise diagnosis. You "
    "are rigorous about the difference between SIGNAL and NOISE: with only a few data points or tiny "
    "numbers, you say so and lower your confidence rather than inventing a story.\n\n"
    "Your craft:\n"
    "- Read the whole TREND LINE, not just this week vs. last. One down week is noise; three down "
    "weeks in a row is a pattern. Distinguish a blip from a slide.\n"
    "- Classify the account state as exactly one of: dormant (no meaningful activity/reach), declining "
    "(sustained fall), flat (stable, not growing), growing (steady up-and-to-the-right), breakout "
    "(a sharp, unusual spike).\n"
    "- Detect AUDIENCE FATIGUE precisely: reach-per-post falling while post volume rises means you are "
    "spending audience attention faster than you're earning it. Name the evidence.\n"
    "- Interpret reach through platform reality: impressions without engagement means the hook or "
    "relevance is weak; engagement without follower growth means posts are like-worthy but not "
    "follow-worthy.\n"
    "- Use REAL post performance when present: which specific posts actually earned reach/engagement, "
    "and what that implies. Do not confuse a high internal draft score with real-world success.\n"
    "- State plainly what you do NOT know and why (sample size, missing data, first week).\n\n"
    "Think step by step in the 'reasoning' field FIRST, then commit to the structured verdict. "
    "Return ONLY a single JSON object, no markdown fences, no commentary."
)

EXPECTED_SHAPE = """{
  "reasoning": "your step-by-step read of the trend line and evidence, written before you conclude",
  "account_state": "dormant|declining|flat|growing|breakout",
  "trajectory": "one line on the direction of travel across the whole history",
  "confidence": "low|medium|high",
  "fatigue_detected": true|false,
  "fatigue_evidence": "string or null",
  "best_performing_observations": ["what the real post-performance data shows, or 'no post data yet'"],
  "key_observations": ["string", ...],
  "unknowns": ["what you cannot conclude yet and why", ...],
  "narrative": "2-4 sentence plain-English diagnosis the rest of the team will rely on"
}"""


async def analyst_node(state: WeekState) -> WeekState:
    current = state["current_snapshot"]
    prior = state.get("prior_snapshot")
    deltas = compute_deltas(current, prior)
    project = state["project"]
    trend = state.get("trend", {})
    performance = state.get("post_performance", [])

    cold_start_note = (
        "\nThis is the FIRST upload ever for this project — there is no prior period to compare "
        "against. Treat every number as a baseline probe, not a trend. Keep confidence low.\n"
        if not deltas["has_prior_period"] else ""
    )

    perf_note = (
        json.dumps(performance[:10], indent=2, default=str)
        if performance
        else "No real post-performance data captured yet (no posts have appeared in an export)."
    )

    prompt = f"""
Project: {project.get("name")} ({project.get("account_type")})
Niche: {project.get("niche") or "not specified"}
Stated goal: {project.get("goal") or "not specified"}
{cold_start_note}
This period's raw numbers:
{json.dumps(current.get("raw", current), indent=2, default=str)[:2500]}

Computed deltas vs. the immediately prior period (math already done — do NOT recompute):
{json.dumps(deltas, indent=2, default=str)}

Full trend line across all uploads (oldest -> newest, with decline streaks already computed):
{json.dumps(trend, indent=2, default=str)}

REAL post performance captured from exports (actual impressions/engagements, best first):
{perf_note}

Diagnose this account. Return JSON matching:
{EXPECTED_SHAPE}
"""
    result = await call_llm_for_json(
        prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE, temperature=TEMP_RIGOROUS
    )
    return {"analyst_diagnosis": result, "deltas": deltas, "is_cold_start": not deltas["has_prior_period"]}
