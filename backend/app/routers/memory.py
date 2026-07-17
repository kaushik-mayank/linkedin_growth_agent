from fastapi import APIRouter, HTTPException

from app.db.supabase_client import get_supabase
from app.embeddings.gemini_embeddings import EmbeddingError
from app.memory_store import search_memory as search_memory_rows
from app.memory_store import store_memory
from app.models.memory import MemoryCreate, MemoryMatch, MemoryOut, MemorySearchRequest

router = APIRouter(prefix="/projects/{project_id}/memory", tags=["memory"])


@router.get("", response_model=list[MemoryOut])
async def list_memory(project_id: str):
    """All learnings for a project, newest first — powers the 'what the agent has learned' view."""
    try:
        resp = (
            get_supabase()
            .table("memory")
            .select("id, project_id, kind, content, metadata, created_at")
            .eq("project_id", project_id)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase error listing memory: {e}") from e
    return resp.data


@router.post("", response_model=MemoryOut)
async def create_memory(project_id: str, body: MemoryCreate):
    try:
        return await store_memory(project_id, body.kind, body.content, body.metadata)
    except EmbeddingError as e:
        raise HTTPException(status_code=502, detail=f"Embedding error: {e.message}") from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase error saving memory: {e}") from e


@router.post("/search", response_model=list[MemoryMatch])
async def search_memory(project_id: str, body: MemorySearchRequest):
    try:
        return await search_memory_rows(project_id, body.query, body.kind, body.match_count)
    except EmbeddingError as e:
        raise HTTPException(status_code=502, detail=f"Embedding error: {e.message}") from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase error searching memory: {e}") from e
