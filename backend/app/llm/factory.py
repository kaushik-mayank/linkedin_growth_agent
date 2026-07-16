from app import config
from app.llm.base import LLMProvider
from app.llm.gemini_provider import GeminiProvider
from app.llm.groq_provider import GroqProvider

_PROVIDERS = {
    "groq": GroqProvider,
    "gemini": GeminiProvider,
}


def get_provider(name: str) -> LLMProvider:
    provider_cls = _PROVIDERS.get(name.lower())
    if provider_cls is None:
        raise ValueError(f"Unknown LLM provider '{name}'. Valid options: {list(_PROVIDERS)}")
    return provider_cls()


def get_default_provider() -> LLMProvider:
    return get_provider(config.LLM_PROVIDER)


def get_other_provider_name(name: str) -> str:
    """The one remaining provider, used as a fallback when the default fails."""
    others = [n for n in _PROVIDERS if n != name.lower()]
    return others[0]
