from fastapi import APIRouter, HTTPException

from app.db.supabase_client import get_supabase
from app.embeddings.gemini_embeddings import EmbeddingError, embed_text
from app.models.memory import MemoryCreate, MemoryMatch, MemoryOut, MemorySearchRequest

router = APIRouter(prefix="/projects/{project_id}/memory", tags=["memory"])


@router.post("", response_model=MemoryOut)
async def create_memory(project_id: str, body: MemoryCreate):
    try:
        vector = await embed_text(body.content)
    except EmbeddingError as e:
        raise HTTPException(status_code=502, detail=f"Embedding error: {e.message}") from e

    row = {
        "project_id": project_id,
        "kind": body.kind,
        "content": body.content,
        "metadata": body.metadata,
        "embedding": vector,
    }
    try:
        supabase = get_supabase()
        resp = supabase.table("memory").insert(row).execute()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase error saving memory: {e}") from e

    if not resp.data:
        raise HTTPException(status_code=502, detail="Supabase returned no data after insert")
    return resp.data[0]


@router.post("/search", response_model=list[MemoryMatch])
async def search_memory(project_id: str, body: MemorySearchRequest):
    try:
        vector = await embed_text(body.query)
    except EmbeddingError as e:
        raise HTTPException(status_code=502, detail=f"Embedding error: {e.message}") from e

    try:
        supabase = get_supabase()
        resp = supabase.rpc(
            "match_memory",
            {
                "query_embedding": vector,
                "match_project_id": project_id,
                "match_count": body.match_count,
                "filter_kind": body.kind,
            },
        ).execute()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase error searching memory: {e}") from e

    return resp.data
