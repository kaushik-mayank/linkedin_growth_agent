"""Gemini embeddings, truncated to EMBEDDING_DIMENSIONS and manually L2-normalized.

gemini-embedding-001 defaults to 3072 dimensions, which pgvector's index types
cannot index (they cap at 2000). Requesting a smaller outputDimensionality gives
a valid but NOT unit-length vector — cosine/similarity search degrades silently
unless we renormalize by hand. See tests/test_gemini_embeddings.py.
"""
import math

import httpx

from app import config

EMBED_URL_TMPL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={key}"

TASK_DOCUMENT = "RETRIEVAL_DOCUMENT"  # use when storing
TASK_QUERY = "RETRIEVAL_QUERY"        # use when searching


class EmbeddingError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0:
        return vector
    return [x / norm for x in vector]


async def embed_text(text: str, task_type: str | None = None) -> list[float]:
    """Embed one string.

    task_type asymmetry matters for retrieval quality with gemini-embedding-001:
    pass "RETRIEVAL_DOCUMENT" when STORING a memory and "RETRIEVAL_QUERY" when
    SEARCHING. The model places queries and documents in complementary regions of
    the space, so matching the task type on each side sharpens similarity.
    """
    if not config.GEMINI_API_KEY:
        raise EmbeddingError("GEMINI_API_KEY is empty — add it to backend/.env")

    url = EMBED_URL_TMPL.format(model=config.EMBEDDING_MODEL, key=config.GEMINI_API_KEY)
    headers = {"Content-Type": "application/json", "User-Agent": config.HTTP_USER_AGENT}
    payload = {
        "model": f"models/{config.EMBEDDING_MODEL}",
        "content": {"parts": [{"text": text}]},
        "outputDimensionality": config.EMBEDDING_DIMENSIONS,
    }
    if task_type:
        payload["taskType"] = task_type

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
    except httpx.RequestError as e:
        raise EmbeddingError(f"network error reaching Gemini embeddings: {e}") from e

    if resp.status_code != 200:
        raise EmbeddingError(f"HTTP {resp.status_code} from Gemini embeddings: {resp.text[:500]}")

    try:
        values = resp.json()["embedding"]["values"]
    except (KeyError, ValueError) as e:
        raise EmbeddingError(f"unexpected response shape: {e} — raw: {resp.text[:500]}") from e

    if len(values) != config.EMBEDDING_DIMENSIONS:
        raise EmbeddingError(
            f"Gemini returned {len(values)} dimensions, expected {config.EMBEDDING_DIMENSIONS}"
        )

    return normalize(values)
