"""COPYWRITER — a world-class LinkedIn writer + behavioral psychologist. Regenerates only flagged posts on revision."""
import json

from app.agent.knowledge import LINKEDIN_MECHANICS
from app.agent.llm_call import TEMP_CREATIVE, call_llm_for_json
from app.agent.state import WeekState

SYSTEM = (
    "You are the COPYWRITER — a world-class LinkedIn writer with the instincts of a behavioral "
    "psychologist. You write posts people stop scrolling to read, finish, and act on. You know that on "
    "LinkedIn the writing IS the distribution.\n\n"
    f"{LINKEDIN_MECHANICS}\n\n"
    "HOOK PATTERNS (vary them; never reuse the same pattern twice in one week or repeat last week's): "
    "curiosity gap, contrarian-but-defensible truth, specific-number shock, in-media-res story open, "
    "direct question, pattern interrupt.\n"
    "STRUCTURES: PAS (problem-agitate-solve), before-after-bridge, listicle, mini-case-study, personal "
    "lesson, teardown. Match structure to the idea.\n"
    "PSYCHOLOGY (deploy deliberately and NAME which you used and why): specificity beats superlatives, "
    "open loops (Zeigarnik), social proof, loss aversion, identity resonance ('this is for people like "
    "me'), the Von Restorff isolation effect, earned authority over claimed.\n"
    "CRAFT: the first 2 lines must earn the 'see more' click — lead with the sharpest thing, no "
    "preamble. Short lines, generous white space, one idea per post. End with a soft CTA or a real "
    "question that invites comments (never 'agree?' bait). If a link is essential, tell the reader it's "
    "in the comments — never in the body. Conversational, confident, zero corporate jargon, no emoji "
    "spam.\n"
    "HARD RULES: never fabricate statistics, case studies, clients, or results. If an example is "
    "illustrative, keep it generic or write a fill-in-the-blank the owner can complete with a real "
    "detail — never invent their life. Tag suggestions describe TYPES of people/companies and why — "
    "never invent real handles or names. Adapt voice to account type (a company page is not a personal "
    "brand is not a consultant).\n\n"
    "Return ONLY a single JSON object, no markdown fences, no commentary."
)

POST_SHAPE = """{
  "post_code": "string",
  "format": "text|carousel|document|image+text|video-script",
  "funnel_job": "reach|trust|convert",
  "scheduled_day": "string",
  "best_time": "string",
  "best_time_reason": "grounded in the audience's timezone/behavior",
  "hook": "the first 1-2 lines, verbatim as they'll appear before 'see more'",
  "hook_pattern": "which hook pattern this is",
  "structure": "which structure this uses",
  "caption": "the full post, ready to paste, with line breaks",
  "hashtags": ["3-8, mix of broad + niche", ...],
  "tag_suggestions": "TYPES of people/companies to tag and why (no real handles)",
  "psychology_notes": "which principle(s) you used and why they fit this audience",
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
Revise ONLY these posts using the Critic's feedback. Keep each post_code. Make a real improvement —
do not just reword; fix the actual weakness the Critic named.

Critic's revision instructions:
{instructions}

The posts as originally written:
{json.dumps(posts_to_fix, indent=2, default=str)}

Account type: {project.get("account_type")}
Niche: {project.get("niche") or "not specified"}
Audience: {project.get("audience") or "not specified"}

Return JSON matching (only the revised posts, same count):
{EXPECTED_SHAPE}
"""
        result = await call_llm_for_json(
            prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE, temperature=TEMP_CREATIVE
        )
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
    winning_hooks = state.get("historical_memories", {}).get("winning_hook", [])

    prompt = f"""
Account type: {project.get("account_type")}
Niche: {project.get("niche") or "not specified"}
Audience: {project.get("audience") or "not specified"}
Week theme (keep all posts coherent to this): {strategy.get("week_theme")}
Funnel mix target this week: {json.dumps(strategy.get("funnel_mix", {}))}
Positioning shift (if any): {strategy.get("positioning_shift") or "none"}

Write exactly {cadence_count} posts, one per scheduled slot:
{json.dumps(schedule, indent=2, default=str)}

What has WON before for this audience (echo the underlying pattern, not the words):
{json.dumps(winning_hooks, indent=2, default=str) if winning_hooks else "No proven winners recorded yet."}

Last week's hooks (DO NOT repeat these patterns or anything close):
{json.dumps(last_week_hooks, indent=2, default=str) if last_week_hooks else "None — this is week 1."}

Live trends + angles to draw on (only if genuinely useful; never fabricate beyond these):
{json.dumps(state.get("research_findings", {}).get("findings", []), indent=2, default=str)}

Who you're really writing for (write at their altitude, in their vocabulary):
{json.dumps(state.get("audience_profile", {}), indent=2, default=str)}

Return JSON matching:
{EXPECTED_SHAPE}
"""
    result = await call_llm_for_json(
        prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE, temperature=TEMP_CREATIVE
    )
    posts = result.get("posts", [])
    # Enforce deterministic, unique post codes regardless of what the model returned.
    for i, post in enumerate(posts):
        post["post_code"] = _post_code(week_number, i + 1)
    return {"posts": posts, "revision_count": 0}
