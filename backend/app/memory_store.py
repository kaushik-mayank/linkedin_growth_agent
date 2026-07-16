"""Shared read/write helpers for the `memory` table — used by the API router and the Librarian agent node."""
from typing import Any

from app.db.supabase_client import get_supabase
from app.embeddings.gemini_embeddings import embed_text


async def store_memory(
    project_id: str, kind: str, content: str, metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    vector = await embed_text(content)
    row = {"project_id": project_id, "kind": kind, "content": content, "metadata": metadata, "embedding": vector}
    resp = get_supabase().table("memory").insert(row).execute()
    if not resp.data:
        raise RuntimeError("Supabase returned no data after memory insert")
    return resp.data[0]


async def search_memory(project_id: str, query: str, kind: str, match_count: int = 5) -> list[dict[str, Any]]:
    vector = await embed_text(query)
    resp = get_supabase().rpc(
        "match_memory",
        {
            "query_embedding": vector,
            "match_project_id": project_id,
            "match_count": match_count,
            "filter_kind": kind,
        },
    ).execute()
    return resp.data


async def search_memory_multi(
    project_id: str, query: str, kinds: list[str], match_count: int = 3
) -> dict[str, list[dict[str, Any]]]:
    """One embedding call, one match_memory RPC call per kind (filter_kind is required, not optional)."""
    vector = await embed_text(query)
    supabase = get_supabase()
    out: dict[str, list[dict[str, Any]]] = {}
    for kind in kinds:
        resp = supabase.rpc(
            "match_memory",
            {
                "query_embedding": vector,
                "match_project_id": project_id,
                "match_count": match_count,
                "filter_kind": kind,
            },
        ).execute()
        out[kind] = resp.data
    return out
