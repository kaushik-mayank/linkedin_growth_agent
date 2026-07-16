"""Robust JSON extraction from LLM replies.

LLMs wrap JSON in markdown fences, add commentary, or occasionally emit a
stray trailing token. Strip fences, grab the outermost {...}, and if that
still doesn't parse, ask the model to repair it once. Never crash on a
malformed reply — raise a clear JSONParseError instead.
"""
import json
import re
from typing import Any, Awaitable, Callable

GenerateFn = Callable[..., Awaitable[str]]


class JSONParseError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_outer_json(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def try_parse(raw_text: str) -> dict[str, Any] | None:
    candidate = _extract_outer_json(_strip_fences(raw_text))
    if not candidate:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


async def parse_json_with_repair(
    raw_text: str,
    generate: GenerateFn,
    *,
    expected_shape: str,
    system: str | None = None,
) -> dict[str, Any]:
    """Parse JSON from raw_text; on failure, ask the model to repair it once."""
    parsed = try_parse(raw_text)
    if parsed is not None:
        return parsed

    repair_prompt = (
        "The text below was supposed to be a single valid JSON object matching this shape:\n"
        f"{expected_shape}\n\n"
        "It failed to parse. Return ONLY the corrected, valid JSON object — no markdown "
        "fences, no commentary, no explanation.\n\nTEXT TO FIX:\n" + raw_text
    )
    repaired = await generate(repair_prompt, system=system)
    parsed = try_parse(repaired)
    if parsed is not None:
        return parsed

    raise JSONParseError(
        f"Could not parse JSON even after one repair attempt. Raw reply: {raw_text[:800]}"
    )
