from abc import ABC, abstractmethod


class LLMError(Exception):
    """Carries the REAL, provider-specific error — never collapse this into a generic message."""

    def __init__(self, provider: str, message: str):
        self.provider = provider
        self.message = message
        super().__init__(f"[{provider}] {message}")


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, prompt: str, system: str | None = None) -> str:
        ...
