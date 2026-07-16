"""COPYWRITER — writes the week's posts. On a revision pass, only regenerates flagged posts."""
import json

from app.agent.llm_call import call_llm_for_json
from app.agent.state import WeekState

SYSTEM = (
    "You are the COPYWRITER — a world-class LinkedIn writer with a real psychological toolkit. "
    "Hook patterns to vary across posts (never repeat the same one twice in a week, never repeat "
    "last week's): curiosity gap, contrarian truth, specific-number shock, in-media-res story open, "
    "direct question, pattern interrupt. Structures: PAS (problem-agitate-solve), before-after-"
    "bridge, listicle, mini-case-study, personal lesson, teardown. Psychology to use deliberately "
    "and name explicitly: specificity beats superlatives, open loops (Zeigarnik effect), social "
    "proof, loss aversion, identity resonance, the Von Restorff isolation effect, earned authority "
    "over claimed. LinkedIn craft: first 2 lines must earn the 'see more' click, short lines, white "
    "space, one idea per post, a soft CTA or a real question that invites comments, conversational, "
    "confident, zero corporate jargon, no emoji spam, no engagement bait. HARD RULE: never fabricate "
    "statistics, case studies, clients, or results — if an example is illustrative keep it generic, "
    "or write a fill-in-the-blank prompt instead of inventing the user's life. Adapt voice to the "
    "account type (a company page is not a personal brand is not a consultant). Tag suggestions must "
    "describe TYPES of people/companies and why — never invent real handles or fake names. "
    "Return ONLY a single JSON object, no markdown fences, no commentary."
)

POST_SHAPE = """{
  "post_code": "string",
  "format": "string",
  "funnel_job": "reach|trust|convert",
  "scheduled_day": "string",
  "best_time": "string",
  "best_time_reason": "string",
  "hook": "string",
  "hook_pattern": "string",
  "structure": "string",
  "caption": "string",
  "hashtags": ["string", ...],
  "tag_suggestions": "string",
  "psychology_notes": "string",
  "needs_visual": true|false
}"""

EXPECTED_SHAPE = "{\"posts\": [" + POST_SHAPE + ", ...]}"


def _post_code(week_number: int, index: int) -> str:
    return f"W{week_number:02d}-{index:02d}"


async def copywriter_node(state: WeekState) -> WeekState:
    project = state["project"]
    strategy = state["strategy"]
    cadence = strategy["cadence_decision"]
    week_number = state.get("week_number", 1)

    reviews = state.get("critic_reviews")
    existing_posts = state.get("posts", [])

    if reviews:
        to_revise = [r for r in reviews if r.get("needs_revision")]
        if not to_revise:
            return {}

        by_code = {p["post_code"]: p for p in existing_posts}
        instructions = "\n".join(f"- {r['post_code']}: {r['revision_instructions']}" for r in to_revise)
        posts_to_fix = [by_code[r["post_code"]] for r in to_revise if r["post_code"] in by_code]

        prompt = f"""
Revise ONLY these specific posts based on the Critic's feedback. Keep the same post_code for each.

Critic's revision instructions:
{instructions}

The posts needing revision, as originally written:
{json.dumps(posts_to_fix, indent=2, default=str)}

Account type: {project.get("account_type")}
Niche: {project.get("niche") or "not specified"}
Audience: {project.get("audience") or "not specified"}

Return JSON matching (only the revised posts, same count as listed above):
{EXPECTED_SHAPE}
"""
        result = await call_llm_for_json(prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE)
        revised_by_code = {p["post_code"]: p for p in result.get("posts", [])}
        merged = [revised_by_code.get(p["post_code"], p) for p in existing_posts]
        return {"posts": merged, "revision_count": state.get("revision_count", 0) + 1}

    # First pass: generate all posts fresh.
    cadence_count = cadence.get("posts_this_week", 0)
    schedule = cadence.get("schedule", [])
    last_week_hooks = [
        {"hook": p.get("hook"), "psychology_notes": p.get("psychology_notes")}
        for p in state.get("last_week_posts", [])
    ]

    prompt = f"""
Account type: {project.get("account_type")}
Niche: {project.get("niche") or "not specified"}
Audience: {project.get("audience") or "not specified"}
Week theme: {strategy.get("week_theme")}
Funnel mix target this week: {json.dumps(strategy.get("funnel_mix", {}))}
Positioning shift (if any): {strategy.get("positioning_shift") or "none"}

Write exactly {cadence_count} posts for this schedule (one post per entry):
{json.dumps(schedule, indent=2, default=str)}

Last week's hooks and psychology notes (DO NOT repeat these hook patterns or very similar hooks):
{json.dumps(last_week_hooks, indent=2, default=str) if last_week_hooks else "None — this is week 1."}

Relevant live trends this week (reference only if genuinely useful, never fabricate beyond this):
{json.dumps(state.get("research_findings", {}).get("findings", []), indent=2, default=str)}

Audience insights to write for the REAL audience:
{json.dumps(state.get("audience_profile", {}), indent=2, default=str)}

Return JSON matching:
{EXPECTED_SHAPE}
"""
    result = await call_llm_for_json(prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE)
    posts = result.get("posts", [])
    # Enforce deterministic, unique post codes regardless of what the model returned.
    for i, post in enumerate(posts):
        post["post_code"] = _post_code(week_number, i + 1)
    return {"posts": posts, "revision_count": 0}
