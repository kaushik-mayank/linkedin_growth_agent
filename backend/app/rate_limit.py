"""Tiny in-memory rate limiter for the expensive agent endpoints.

Keeps the free LLM/search quotas safe from accidental rapid re-runs (e.g. a double
click, or a stuck retry loop). In-memory is fine for a single-process free-tier
deploy; if you ever scale to multiple workers, swap this for a shared store.
"""
import time
from collections import defaultdict

from fastapi import HTTPException

_calls: dict[str, list[float]] = defaultdict(list)


def enforce_rate_limit(key: str, *, max_calls: int, per_seconds: int) -> None:
    now = time.time()
    window_start = now - per_seconds
    recent = [t for t in _calls[key] if t >= window_start]
    if len(recent) >= max_calls:
        retry_in = int(per_seconds - (now - recent[0])) + 1
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit reached: max {max_calls} runs per {per_seconds}s. Try again in ~{retry_in}s.",
        )
    recent.append(now)
    _calls[key] = recent
