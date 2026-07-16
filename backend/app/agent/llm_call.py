"""Shared helper: call the default LLM provider with a system+user prompt, parse JSON robustly."""
from typing import Any

from app.agent.json_utils import parse_json_with_repair
from app.llm.factory import get_default_provider


async def call_llm_for_json(prompt: str, *, system: str, expected_shape: str) -> dict[str, Any]:
    provider = get_default_provider()
    raw = await provider.generate(prompt, system=system)
    return await parse_json_with_repair(raw, provider.generate, expected_shape=expected_shape, system=system)
