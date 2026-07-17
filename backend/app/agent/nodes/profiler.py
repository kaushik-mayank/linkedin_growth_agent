"""AUDIENCE PROFILER — an audience researcher who reads who is REALLY here and calls drift honestly."""
import json

from app.agent.llm_call import TEMP_BALANCED, call_llm_for_json
from app.agent.state import WeekState

SYSTEM = (
    "You are the AUDIENCE PROFILER — an audience researcher and segmentation strategist on an elite "
    "LinkedIn team. You read LinkedIn's real demographics (job titles, seniority, industries, "
    "locations, company sizes) and describe who is ACTUALLY following this account, in the language a "
    "brand strategist would use.\n\n"
    "Your craft:\n"
    "- Separate the audience the owner WANTS from the audience they are actually BUILDING. Quantify the "
    "gap with the real percentages ('you're targeting X, but 38% are Y').\n"
    "- Make the hard call: when there's drift, is the actual audience a BETTER commercial opportunity "
    "than the stated target (embrace and re-aim), or a distraction pulling them off-goal (correct "
    "course)? Take a position and justify it — do not just report the drift.\n"
    "- Read what the audience composition implies for CONTENT: seniority sets altitude (operators want "
    "tactics, executives want POV), industry sets vocabulary, location sets timezone and cultural "
    "reference points.\n"
    "- Never invent demographic data that isn't in the export. If a category is missing, say so.\n\n"
    "Think in the 'reasoning' field first, then commit. Return ONLY a single JSON object, no markdown "
    "fences, no commentary."
)

EXPECTED_SHAPE = """{
  "reasoning": "your read of who is actually here and what it implies, before you conclude",
  "top_job_titles": ["string", ...],
  "top_seniority": ["string", ...],
  "top_industries": ["string", ...],
  "top_locations": ["string", ...],
  "top_company_sizes": ["string", ...],
  "actual_audience_summary": "one vivid sentence describing who is really following",
  "drift_detected": true|false,
  "drift_explanation": "string with real percentages, or null",
  "drift_verdict": "embrace|correct_course|on_target",
  "content_implications": ["what this audience means for altitude, vocabulary, timing", ...],
  "recommendation": "the one clear move on positioning/audience this week"
}"""

_EMPTY_RESULT = {
    "reasoning": "No demographics were present in this export (common for very new or dormant accounts).",
    "top_job_titles": [], "top_seniority": [], "top_industries": [],
    "top_locations": [], "top_company_sizes": [],
    "actual_audience_summary": "No demographics data in this export.",
    "drift_detected": False, "drift_explanation": None, "drift_verdict": "on_target",
    "content_implications": [],
    "recommendation": "Not enough demographic data yet to compare against the stated target audience.",
}


async def profiler_node(state: WeekState) -> WeekState:
    project = state["project"]
    demographics = state["current_snapshot"].get("raw", {}).get("demographics", {})

    if not demographics:
        return {"audience_profile": dict(_EMPTY_RESULT)}

    prompt = f"""
Account type: {project.get("account_type")}
Niche: {project.get("niche") or "not specified"}
Stated target audience: {project.get("audience") or "not specified"}
Goal: {project.get("goal") or "not specified"}

Real demographics from this week's export (category -> list of {{value, percentage}}):
{json.dumps(demographics, indent=2, default=str)}

Analyze who is ACTUALLY following, judge the drift, and give the implications. Return JSON matching:
{EXPECTED_SHAPE}
"""
    result = await call_llm_for_json(
        prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE, temperature=TEMP_BALANCED
    )
    return {"audience_profile": result}
