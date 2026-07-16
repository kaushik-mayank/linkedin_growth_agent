import math

import pytest

from app import config
from app.embeddings.gemini_embeddings import embed_text, normalize


def test_normalize_produces_unit_norm_vector():
    vector = [3.0, 4.0] + [0.0] * 766  # 768-dim, norm=5 before normalizing
    result = normalize(vector)
    norm = math.sqrt(sum(x * x for x in result))
    assert len(result) == 768
    assert norm == pytest.approx(1.0, abs=1e-9)


def test_normalize_handles_zero_vector_without_dividing_by_zero():
    assert normalize([0.0, 0.0, 0.0]) == [0.0, 0.0, 0.0]


@pytest.mark.skipif(not config.GEMINI_API_KEY, reason="GEMINI_API_KEY not set — skipping live Gemini call")
@pytest.mark.asyncio
async def test_embed_text_returns_768_dim_normalized_vector():
    vector = await embed_text("This is a test sentence about LinkedIn growth strategy.")
    norm = math.sqrt(sum(x * x for x in vector))
    assert len(vector) == 768
    assert norm == pytest.approx(1.0, abs=1e-6)
