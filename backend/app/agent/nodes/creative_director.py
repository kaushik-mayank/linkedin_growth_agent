"""CREATIVE DIRECTOR — writes text-to-image PROMPTS only, never generates or hosts images."""
import json

from app.agent.llm_call import call_llm_for_json
from app.agent.state import WeekState

SYSTEM = (
    "You are the CREATIVE DIRECTOR. For posts that would benefit from a visual, write a polished "
    "text-to-image PROMPT ONLY — subject, style, mood, composition, palette — under 60 words. "
    "Never include text-in-image instructions (image models render text poorly). If a visual would "
    "add nothing to a post, return the literal string 'text-only' for that post instead of a prompt. "
    "You never generate, host, or link to an actual image — prompts only. "
    "Return ONLY a single JSON object, no markdown fences, no commentary."
)

EXPECTED_SHAPE = """{"image_prompts": [{"post_code": "string", "image_prompt": "string"}, ...]}"""


async def creative_director_node(state: WeekState) -> WeekState:
    posts = state.get("posts", [])
    if not posts:
        return {}

    prompt = f"""
For each post below, either write an image prompt (if needs_visual is true) or return the exact
string "text-only" (if needs_visual is false or a visual adds nothing).

Posts:
{json.dumps([
    {
        "post_code": p.get("post_code"),
        "format": p.get("format"),
        "hook": p.get("hook"),
        "caption": p.get("caption"),
        "needs_visual": p.get("needs_visual"),
    }
    for p in posts
], indent=2, default=str)}

Return JSON matching:
{EXPECTED_SHAPE}
"""
    result = await call_llm_for_json(prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE)
    prompts_by_code = {p["post_code"]: p["image_prompt"] for p in result.get("image_prompts", [])}

    updated = []
    for post in posts:
        post = dict(post)
        post["image_prompt"] = prompts_by_code.get(post.get("post_code"), "text-only")
        updated.append(post)
    return {"posts": updated}
