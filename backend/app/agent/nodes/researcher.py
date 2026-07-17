"""RESEARCHER — a market research analyst who turns live news into usable, audience-relevant angles."""
import json

from app.agent.llm_call import TEMP_BALANCED, call_llm_for_json
from app.agent.state import WeekState
from app.research.tavily_research import ResearchError
from app.research.tavily_research import search as tavily_search

SYSTEM = (
    "You are the RESEARCHER — a market research analyst on an elite LinkedIn team. You are handed REAL, "
    "live search results and your job is to find the few that THIS specific audience would genuinely "
    "care about this week, and turn each into a usable content angle.\n\n"
    "Your craft:\n"
    "- Relevance to the ACTUAL audience beats general interest. A story only matters if this audience "
    "would stop scrolling for it. Rank by that.\n"
    "- Timeliness matters: a dated, current development is worth more than evergreen commentary.\n"
    "- For each pick, name the ANGLE — how a thoughtful practitioner could use it (a contrarian take, a "
    "'what this means for you' explainer, a prediction, a lesson). Research that can't become a post is "
    "noise.\n"
    "- ABSOLUTE RULE: you may only reference titles, URLs, dates, and facts literally present in the "
    "provided results. Invent nothing. If nothing provided is genuinely useful, say so plainly — a "
    "fabricated trend is worse than an honest 'nothing strong this week'.\n\n"
    "Return ONLY a single JSON object, no markdown fences, no commentary."
)

EXPECTED_SHAPE = """{
  "findings": [
    {"title": "string (verbatim)", "url": "string (verbatim)", "published_date": "string or null",
     "why_relevant": "why THIS audience cares", "content_angle": "how it could become a post"}
  ],
  "no_useful_trends": true|false,
  "note": "string or null"
}"""


async def researcher_node(state: WeekState) -> WeekState:
    project = state["project"]
    profile = state.get("audience_profile", {})
    audience_summary = profile.get("actual_audience_summary", "")
    niche = project.get("niche") or project.get("name") or "this account's niche"

    query = f"{niche} trends news this week"
    try:
        raw = await tavily_search(query, days=14, max_results=6)
    except ResearchError as e:
        return {
            "research_findings": {
                "findings": [], "no_useful_trends": True,
                "note": f"Research tool error: {e.message}",
            }
        }

    if not raw["results"]:
        return {
            "research_findings": {
                "findings": [], "no_useful_trends": True,
                "note": raw.get("warning", "No live results found for this niche this week."),
            }
        }

    prompt = f"""
Niche: {niche}
Actual audience: {audience_summary or "not yet profiled"}
What this audience cares about (implications): {json.dumps(profile.get("content_implications", []))}

Raw search results (the ONLY facts you may reference — quote titles/urls verbatim, invent nothing):
{json.dumps(raw["results"], indent=2, default=str)}

Select and frame only what this audience would genuinely care about. Return JSON matching:
{EXPECTED_SHAPE}
"""
    result = await call_llm_for_json(
        prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE, temperature=TEMP_BALANCED
    )
    return {"research_findings": result}
