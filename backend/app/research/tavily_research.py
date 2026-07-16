"""Tavily live search with a local file cache.

Caches by (query, days, max_results) for TAVILY_CACHE_TTL_HOURS (default 7 days,
matching the weekly upload cadence) so repeat questions — during development, or
shared across projects in the same niche — don't burn the free quota.
"""
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import httpx

from app import config

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / ".cache" / "tavily"

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


class ResearchError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def _cache_key(query: str, days: int, max_results: int) -> str:
    raw = f"{query.strip().lower()}|{days}|{max_results}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def _read_cache(key: str) -> dict[str, Any] | None:
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    age_seconds = time.time() - cached.get("cached_at_epoch", 0)
    if age_seconds > config.TAVILY_CACHE_TTL_HOURS * 3600:
        return None
    return cached


def _write_cache(key: str, query: str, results: list[dict[str, Any]]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = {"query": query, "cached_at_epoch": time.time(), "results": results}
    _cache_path(key).write_text(json.dumps(cached), encoding="utf-8")


async def search(query: str, days: int = 7, max_results: int = 5) -> dict[str, Any]:
    if not query.strip():
        raise ResearchError("query is empty")

    key = _cache_key(query, days, max_results)
    cached = _read_cache(key)
    if cached is not None:
        return {"from_cache": True, "query": query, "results": cached["results"]}

    if not config.TAVILY_API_KEY:
        raise ResearchError("TAVILY_API_KEY is empty — add it to backend/.env")

    headers = {"Content-Type": "application/json", "User-Agent": config.HTTP_USER_AGENT}
    payload = {
        "api_key": config.TAVILY_API_KEY,
        "query": query,
        "topic": "news",
        "search_depth": "basic",
        "days": days,
        "max_results": max_results,
        "include_answer": False,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(TAVILY_SEARCH_URL, headers=headers, json=payload)
    except httpx.RequestError as e:
        raise ResearchError(f"network error reaching Tavily: {e}") from e

    if resp.status_code != 200:
        raise ResearchError(f"HTTP {resp.status_code} from Tavily: {resp.text[:500]}")

    try:
        raw_results = resp.json().get("results", [])
    except ValueError as e:
        raise ResearchError(f"unexpected response shape from Tavily: {e} — raw: {resp.text[:500]}") from e

    results = [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "content": r.get("content"),
            "published_date": r.get("published_date"),
            "score": r.get("score"),
        }
        for r in raw_results
    ]

    _write_cache(key, query, results)

    out: dict[str, Any] = {"from_cache": False, "query": query, "results": results}
    if not results:
        out["warning"] = "Tavily returned no results for this query — do not fabricate trends."
    return out
