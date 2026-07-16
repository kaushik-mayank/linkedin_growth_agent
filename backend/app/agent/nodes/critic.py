"""CRITIC — ruthlessly scores each post 1-10 and decides what needs revision. Max 2 revision loops."""
import json

from app.agent.llm_call import call_llm_for_json
from app.agent.state import WeekState

MAX_REVISION_LOOPS = 2  # per spec: "Maximum 2 revision loops, then proceed with the best version"

SYSTEM = (
    "You are the CRITIC — a ruthless editor on a LinkedIn growth team. Score each post 1-10 "
    "against: hook strength, specificity, audience fit (using the REAL demographics given), "
    "similarity to past FLOPS in memory, originality vs. last week's posts, and whether it serves "
    "its assigned funnel job. Any score below 7 needs revision — give specific, actionable "
    "revision_instructions (not vague praise/criticism). Return ONLY a single JSON object, no "
    "markdown fences, no commentary."
)

EXPECTED_SHAPE = """{
  "reviews": [
    {"post_code": "string", "score": 0, "notes": "string", "needs_revision": true|false, "revision_instructions": "string or null"}
  ]
}"""


async def critic_node(state: WeekState) -> WeekState:
    posts = state.get("posts", [])
    if not posts:
        return {"critic_reviews": []}

    prompt = f"""
Audience profile (use this for the audience-fit score):
{json.dumps(state.get("audience_profile", {}), indent=2, default=str)}

Past flops recalled from memory (penalize similarity to these):
{json.dumps(state.get("historical_memories", {}).get("flop", []), indent=2, default=str)}

Last week's posts (penalize repeated hooks/structures vs. these):
{json.dumps([
    {"hook": p.get("hook"), "format": p.get("format")} for p in state.get("last_week_posts", [])
], indent=2, default=str)}

This week's posts to score:
{json.dumps(posts, indent=2, default=str)}

Return JSON matching:
{EXPECTED_SHAPE}
"""
    result = await call_llm_for_json(prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE)
    reviews = result.get("reviews", [])

    if state.get("revision_count", 0) >= MAX_REVISION_LOOPS:
        for r in reviews:
            r["needs_revision"] = False  # out of revision budget — proceed with the best version

    by_code = {r["post_code"]: r for r in reviews}
    updated_posts = []
    for post in posts:
        post = dict(post)
        review = by_code.get(post.get("post_code"), {})
        post["critic_score"] = review.get("score")
        post["critic_notes"] = review.get("notes")
        updated_posts.append(post)

    return {"critic_reviews": reviews, "posts": updated_posts}
