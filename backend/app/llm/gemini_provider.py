import httpx

from app import config
from app.llm.base import LLMError, LLMProvider


class GeminiProvider(LLMProvider):
    name = "gemini"

    async def generate(self, prompt: str) -> str:
        if not config.GEMINI_API_KEY:
            raise LLMError(self.name, "GEMINI_API_KEY is empty — add it to backend/.env")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}"
        )
        headers = {
            "Content-Type": "application/json",
            "User-Agent": config.HTTP_USER_AGENT,
        }
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
        except httpx.RequestError as e:
            raise LLMError(self.name, f"network error reaching Gemini: {e}") from e

        if resp.status_code != 200:
            raise LLMError(self.name, f"HTTP {resp.status_code} from Gemini: {resp.text[:500]}")

        try:
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, ValueError) as e:
            raise LLMError(
                self.name, f"unexpected response shape from Gemini: {e} — raw: {resp.text[:500]}"
            ) from e
