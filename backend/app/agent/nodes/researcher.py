"""RESEARCHER — live news/trends via Tavily, filtered for what this specific audience cares about."""
import json

from app.agent.llm_call import call_llm_for_json
from app.agent.state import WeekState
from app.research.tavily_research import ResearchError
from app.research.tavily_research import search as tavily_search

SYSTEM = (
    "You are the RESEARCHER on a senior LinkedIn growth team. You are given raw, real search "
    "results (titles, urls, dates, snippets) and must select only the ones this SPECIFIC audience "
    "would actually care about, explaining why. You NEVER invent a trend, title, url, or date that "
    "is not literally present in the provided search results. If nothing provided is useful, say so "
    "plainly rather than fabricate. Return ONLY a single JSON object."
)

EXPECTED_SHAPE = """{
  "findings": [{"title": "string", "url": "string", "published_date": "string or null", "why_relevant": "string"}, ...],
  "no_useful_trends": true|false,
  "note": "string or null"
}"""


async def researcher_node(state: WeekState) -> WeekState:
    project = state["project"]
    audience_summary = state.get("audience_profile", {}).get("actual_audience_summary", "")
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
Actual audience (from this week's demographics): {audience_summary or "not yet profiled"}

Raw search results (these are the ONLY facts you may reference — do not add anything not here):
{json.dumps(raw["results"], indent=2, default=str)}

Select and explain only the results this specific audience would care about. Return JSON matching:
{EXPECTED_SHAPE}
"""
    result = await call_llm_for_json(prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE)
    return {"research_findings": result}
