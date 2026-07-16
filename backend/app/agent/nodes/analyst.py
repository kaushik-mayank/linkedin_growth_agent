"""ANALYST — reads the parsed export + deltas, diagnoses account health honestly."""
import json

from app.agent.deltas import compute_deltas
from app.agent.llm_call import call_llm_for_json
from app.agent.state import WeekState

SYSTEM = (
    "You are the ANALYST on a senior LinkedIn growth team. You read raw analytics data and "
    "diagnose what actually happened — honestly, without spin. You classify account state as "
    "exactly one of: dormant, declining, flat, growing, breakout. You detect AUDIENCE FATIGUE "
    "(reach per post falling while post volume rises). You always state what you do NOT know "
    "given small sample sizes — never overclaim confidence from a handful of data points. "
    "Return ONLY a single JSON object, no markdown fences, no commentary."
)

EXPECTED_SHAPE = """{
  "account_state": "dormant|declining|flat|growing|breakout",
  "fatigue_detected": true|false,
  "fatigue_evidence": "string or null",
  "key_observations": ["string", ...],
  "unknowns": ["string", ...],
  "narrative": "string"
}"""


async def analyst_node(state: WeekState) -> WeekState:
    current = state["current_snapshot"]
    prior = state.get("prior_snapshot")
    deltas = compute_deltas(current, prior)
    project = state["project"]

    cold_start_note = (
        "\nThis is the FIRST upload ever for this project — there is no prior period to compare "
        "against. Treat this as a baseline probe, not a trend.\n"
        if not deltas["has_prior_period"] else ""
    )

    prompt = f"""
Project: {project.get("name")} ({project.get("account_type")})
Niche: {project.get("niche") or "not specified"}
Stated goal: {project.get("goal") or "not specified"}
{cold_start_note}
This period's raw numbers:
{json.dumps(current, indent=2, default=str)}

Computed deltas vs. the prior period (math already done for you, do not recompute):
{json.dumps(deltas, indent=2, default=str)}

Diagnose this account's current state. Return JSON matching:
{EXPECTED_SHAPE}
"""
    result = await call_llm_for_json(prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE)
    return {"analyst_diagnosis": result, "deltas": deltas, "is_cold_start": not deltas["has_prior_period"]}
