"""Shared helper: call the LLM with a system+user prompt, fall back across providers, parse JSON robustly.

Weekly runs make many LLM calls, and the free Groq tier has a per-minute token cap. If the
default provider fails on a call (rate limit, transient error), we fall back to the other
configured provider so a single hiccup doesn't collapse the whole 9-node run. If BOTH fail we
raise a combined error that shows each provider's REAL message — never a generic "all failed".

Temperature is per-call: rigorous specialists (Analyst, Critic, Strategist) run cold for
consistency; the Copywriter runs warm for genuine variety. Defaults live in this module so a
node only overrides when it wants to.
"""
from typing import Any

from app.agent.json_utils import parse_json_with_repair
from app.llm.base import LLMError
from app.llm.factory import get_default_provider, get_other_provider_name, get_provider

# Sensible default temperatures per reasoning style. Nodes pass one of these explicitly.
TEMP_RIGOROUS = 0.2   # analysis, scoring, strategy — we want consistency, not surprises
TEMP_BALANCED = 0.5   # profiling, research selection, synthesis prose
TEMP_CREATIVE = 0.8   # copywriting — real variety in hooks and structure


async def generate_with_fallback(
    prompt: str, system: str | None = None, temperature: float | None = None
) -> str:
    primary = get_default_provider()
    errors: dict[str, str] = {}
    try:
        return await primary.generate(prompt, system=system, temperature=temperature)
    except LLMError as e:
        errors[e.provider] = e.message

    fallback = get_provider(get_other_provider_name(primary.name))
    try:
        return await fallback.generate(prompt, system=system, temperature=temperature)
    except LLMError as e:
        errors[e.provider] = e.message

    detail = "; ".join(f"[{prov}] {msg}" for prov, msg in errors.items())
    raise LLMError("all", f"every provider failed — {detail}")


async def call_llm_for_json(
    prompt: str, *, system: str, expected_shape: str, temperature: float = TEMP_RIGOROUS
) -> dict[str, Any]:
    async def _gen(p: str, system: str | None = None) -> str:
        return await generate_with_fallback(p, system=system, temperature=temperature)

    raw = await _gen(prompt, system=system)
    return await parse_json_with_repair(raw, _gen, expected_shape=expected_shape, system=system)
