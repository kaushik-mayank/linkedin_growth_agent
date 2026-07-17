"""CRITIC — a ruthless editor who scores drafts against an explicit rubric. Max 2 revision loops."""
import json

from app.agent.knowledge import LINKEDIN_MECHANICS
from app.agent.llm_call import TEMP_RIGOROUS, call_llm_for_json
from app.agent.state import WeekState

MAX_REVISION_LOOPS = 2  # per spec: "Maximum 2 revision loops, then proceed with the best version"

SYSTEM = (
    "You are the CRITIC — a ruthless senior editor on an elite LinkedIn team. You have killed more "
    "mediocre posts than most people have written. You score against an explicit rubric and you do not "
    "grade on a curve: a 7 means genuinely good, a 9+ is rare. Vague praise is useless; every score "
    "comes with a specific reason and, when it's short of 7, an ACTIONABLE fix.\n\n"
    f"{LINKEDIN_MECHANICS}\n\n"
    "Score each post 1-10 on each dimension:\n"
    "- hook_strength: do the first 2 lines force the 'see more' click? Preamble = low.\n"
    "- specificity: concrete, specific, and true — not superlatives or generic advice.\n"
    "- audience_fit: written at the real audience's altitude and vocabulary (use the demographics).\n"
    "- originality: fresh vs. last week's posts and vs. past FLOPS in memory (penalize similarity).\n"
    "- funnel_fit: does it actually do its assigned reach/trust/convert job?\n"
    "- algorithm_fit: dwell-worthy, comment-inviting, no in-body links, no engagement bait.\n"
    "The OVERALL score is your holistic judgment (not a blind average). Any overall below 7 needs "
    "revision with a precise instruction naming the weakest dimension and how to fix it. Also fail any "
    "post that fabricates statistics, clients, or results.\n\n"
    "Think per post in 'reasoning' first, then score. Return ONLY a single JSON object, no markdown "
    "fences, no commentary."
)

EXPECTED_SHAPE = """{
  "reviews": [
    {
      "post_code": "string",
      "reasoning": "what's strong and what's weak, specifically",
      "scores": {"hook_strength": 0, "specificity": 0, "audience_fit": 0, "originality": 0, "funnel_fit": 0, "algorithm_fit": 0},
      "score": 0,
      "notes": "one-line verdict",
      "needs_revision": true|false,
      "revision_instructions": "the specific fix if below 7, else null"
    }
  ]
}"""


async def critic_node(state: WeekState) -> WeekState:
    posts = state.get("posts", [])
    if not posts:
        return {"critic_reviews": []}

    prompt = f"""
Who this must land with (score audience_fit against this):
{json.dumps(state.get("audience_profile", {}), indent=2, default=str)}

Past FLOPS from memory (penalize any resemblance):
{json.dumps(state.get("historical_memories", {}).get("flop", []), indent=2, default=str)}

Last week's posts (penalize repeated hooks/structures):
{json.dumps([
    {"hook": p.get("hook"), "format": p.get("format")} for p in state.get("last_week_posts", [])
], indent=2, default=str)}

This week's drafts to score:
{json.dumps(posts, indent=2, default=str)}

Score every post against the rubric. Return JSON matching:
{EXPECTED_SHAPE}
"""
    result = await call_llm_for_json(
        prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE, temperature=TEMP_RIGOROUS
    )
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
