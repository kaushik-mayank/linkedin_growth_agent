import httpx

from app import config
from app.llm.base import LLMError, LLMProvider

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqProvider(LLMProvider):
    name = "groq"

    async def generate(self, prompt: str) -> str:
        if not config.GROQ_API_KEY:
            raise LLMError(self.name, "GROQ_API_KEY is empty — add it to backend/.env")

        headers = {
            "Authorization": f"Bearer {config.GROQ_API_KEY}",
            "Content-Type": "application/json",
            # Required: Groq's Cloudflare front door 403s default Python user-agents.
            "User-Agent": config.HTTP_USER_AGENT,
        }
        payload = {
            "model": config.GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(GROQ_CHAT_URL, headers=headers, json=payload)
        except httpx.RequestError as e:
            raise LLMError(self.name, f"network error reaching Groq: {e}") from e

        if resp.status_code != 200:
            raise LLMError(self.name, f"HTTP {resp.status_code} from Groq: {resp.text[:500]}")

        try:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as e:
            raise LLMError(
                self.name, f"unexpected response shape from Groq: {e} — raw: {resp.text[:500]}"
            ) from e
