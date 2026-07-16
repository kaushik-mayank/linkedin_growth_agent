from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app import config
from app.research import tavily_research as tr


def _fake_response(payload: dict) -> SimpleNamespace:
    return SimpleNamespace(status_code=200, text=str(payload), json=lambda: payload)


def test_cache_key_is_deterministic_and_query_specific():
    k1 = tr._cache_key("ai trends", 7, 5)
    k2 = tr._cache_key("ai trends", 7, 5)
    k3 = tr._cache_key("a different query", 7, 5)
    assert k1 == k2
    assert k1 != k3


@pytest.mark.asyncio
async def test_second_call_uses_cache_and_never_hits_network_again(tmp_path, monkeypatch):
    monkeypatch.setattr(tr, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "TAVILY_API_KEY", "fake-key-for-test")

    fake_payload = {
        "results": [
            {
                "title": "Test headline",
                "url": "https://example.com/article",
                "content": "some content",
                "published_date": "2026-07-10",
                "score": 0.9,
            }
        ]
    }

    with patch.object(
        tr.httpx.AsyncClient, "post", new=AsyncMock(return_value=_fake_response(fake_payload))
    ) as mock_post:
        first = await tr.search("unique test query", days=7, max_results=5)
        second = await tr.search("unique test query", days=7, max_results=5)

    assert first["from_cache"] is False
    assert second["from_cache"] is True
    assert second["results"] == first["results"]
    assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_empty_results_produce_a_warning_instead_of_fabricating(tmp_path, monkeypatch):
    monkeypatch.setattr(tr, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "TAVILY_API_KEY", "fake-key-for-test")

    with patch.object(
        tr.httpx.AsyncClient, "post", new=AsyncMock(return_value=_fake_response({"results": []}))
    ):
        result = await tr.search("a query with no hits", days=7, max_results=5)

    assert result["results"] == []
    assert "warning" in result


@pytest.mark.skipif(not config.TAVILY_API_KEY, reason="TAVILY_API_KEY not set — skipping live Tavily call")
@pytest.mark.asyncio
async def test_live_search_returns_real_dated_sourced_results():
    result = await tr.search("LinkedIn creator growth strategy 2026", days=30, max_results=3)
    assert result["results"], "expected at least one live result from Tavily"
    for r in result["results"]:
        assert r["url"]
