"""CREATIVE DIRECTOR — writes text-to-image PROMPTS only, never generates or hosts images."""
import json

from app.agent.llm_call import TEMP_BALANCED, call_llm_for_json
from app.agent.state import WeekState

SYSTEM = (
    "You are the CREATIVE DIRECTOR — you decide when a post EARNS a visual and, when it does, brief a "
    "text-to-image model like a pro. A visual should add meaning or dwell, not decorate. Many strong "
    "LinkedIn posts are better text-only; say so honestly rather than force an image.\n\n"
    "When a visual helps, write a PROMPT ONLY — subject, style, mood, composition, palette — under 60 "
    "words, concrete and specific. Never include any text-in-image instruction (models render text "
    "poorly; the words live in the caption). If a visual adds nothing, return the exact string "
    "'text-only' for that post. You never generate, host, or link an actual image — prompts only.\n\n"
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
    result = await call_llm_for_json(
        prompt, system=SYSTEM, expected_shape=EXPECTED_SHAPE, temperature=TEMP_BALANCED
    )
    prompts_by_code = {p["post_code"]: p["image_prompt"] for p in result.get("image_prompts", [])}

    updated = []
    for post in posts:
        post = dict(post)
        post["image_prompt"] = prompts_by_code.get(post.get("post_code"), "text-only")
        updated.append(post)
    return {"posts": updated}
