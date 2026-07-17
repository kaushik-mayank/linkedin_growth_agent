import pytest

from app.agent import llm_call
from app.llm.base import LLMError


class _FakeProvider:
    def __init__(self, name, reply=None, error=None):
        self.name = name
        self._reply = reply
        self._error = error

    async def generate(self, prompt, system=None):
        if self._error:
            raise LLMError(self.name, self._error)
        return self._reply


@pytest.mark.asyncio
async def test_uses_primary_when_it_succeeds(monkeypatch):
    monkeypatch.setattr(llm_call, "get_default_provider", lambda: _FakeProvider("groq", reply="ok"))
    result = await llm_call.generate_with_fallback("hi")
    assert result == "ok"


@pytest.mark.asyncio
async def test_falls_back_to_second_provider_when_primary_fails(monkeypatch):
    monkeypatch.setattr(
        llm_call, "get_default_provider", lambda: _FakeProvider("groq", error="HTTP 429 rate limit")
    )
    monkeypatch.setattr(llm_call, "get_other_provider_name", lambda name: "gemini")
    monkeypatch.setattr(llm_call, "get_provider", lambda name: _FakeProvider("gemini", reply="fallback ok"))
    result = await llm_call.generate_with_fallback("hi")
    assert result == "fallback ok"


@pytest.mark.asyncio
async def test_raises_combined_error_showing_both_real_messages(monkeypatch):
    monkeypatch.setattr(
        llm_call, "get_default_provider", lambda: _FakeProvider("groq", error="HTTP 429 groq limit")
    )
    monkeypatch.setattr(llm_call, "get_other_provider_name", lambda name: "gemini")
    monkeypatch.setattr(
        llm_call, "get_provider", lambda name: _FakeProvider("gemini", error="HTTP 403 gemini key bad")
    )
    with pytest.raises(LLMError) as exc:
        await llm_call.generate_with_fallback("hi")
    msg = exc.value.message
    assert "groq limit" in msg
    assert "gemini key bad" in msg
