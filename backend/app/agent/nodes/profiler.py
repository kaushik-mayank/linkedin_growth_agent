"""AUDIENCE PROFILER — mines demographics, flags drift vs. the stated target audience."""
import json

from app.agent.llm_call import call_llm_for_json
from app.agent.state import WeekState

SYSTEM = (
    "You are the AUDIENCE PROFILER on a senior LinkedIn growth team. You read LinkedIn's "
    "demographics export (job titles, seniority, industries, locations, company sizes) and "
    "describe who is ACTUALLY following this account. You compare that to the account owner's "
    "STATED target audience and flag drift plainly and specifically — with real numbers — when "
    "they diverge, e.g. 'you're targeting X but 38% of your audience is Y'. You never invent "
    "demographic data that isn't in the export. Return ONLY a single JSON object."
)

EXPECTED_SHAPE = """{
  "top_job_titles": ["string", ...],
  "top_seniority": ["string", ...],
  "top_industries": ["string", ...],
  "top_locations": ["string", ...],
  "top_company_sizes": ["string", ...],
  "actual_audience_summary": "string",
  "drift_detected": true|false,
  "drift_explanation": "string or null",
  "recommendation": "string"
}"""

_EMPTY_RESULT = {
    "top_job_titles": [], "top_seniority": [], "top_industries": [],
    "top_locations": [], "top_company_sizes": [],
    "actual_audience_summary": "No demographics data in this export.",
    "drift_detected": False, "drift_explanation": None,
    "recommendation": "Not enough demographic data yet to compare against the stated target audience.",
}


async def profiler_node(state: WeekState) -> WeekState:
    project = state["project"]
    demographics = state["current_snapshot"].get("raw", {}).get("demographics", {})

    if not demographics:
        return {"audience_profile": dict(_EMPTY_RESULT)}

    prompt = f"""
Stated target audience: {project.get("audience") or "not specified"}

Demographics from this week's export (category -> list of {{value, percentage}}):
{json.dumps(demographics, indent=2, default=str)}

Analyze who is ACTUALLY following this account and compare to the stated target audience.
Return JSON matching:
{EXPECTED_SHAPE}
"""
    result = await call_llm_for_json(prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE)
    return {"audience_profile": result}
