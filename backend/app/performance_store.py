"""Real-world post performance — the feedback loop that lets the agent learn what ACTUALLY worked.

Each weekly export's TOP POSTS sheet lists real posts with real impressions/engagements. We store
those in `post_performance` keyed by URL. Because the user posts by hand, we don't automatically
know which of our drafts a URL corresponds to — so `post_code` starts null and can be mapped later
(the user pastes/links a URL to a draft in the UI). Either way, the raw outcome is captured, so the
Analyst and Librarian can reason about what genuinely performed instead of trusting the Critic's
self-assessment.
"""
from typing import Any, Optional

from app.db.supabase_client import get_supabase


def sync_post_performance(project_id: str, top_posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Upsert parsed TOP POSTS rows into post_performance, de-duped by (project_id, post_url).

    Done with select-then-insert/update rather than a DB upsert so we don't depend on a unique
    constraint that may not exist on the table. Re-uploading a period refreshes the numbers.
    """
    supabase = get_supabase()
    rows_with_url = [p for p in top_posts if p.get("url")]
    if not rows_with_url:
        return []

    existing = (
        supabase.table("post_performance")
        .select("id, post_url")
        .eq("project_id", project_id)
        .execute()
        .data
        or []
    )
    id_by_url = {r["post_url"]: r["id"] for r in existing}

    saved: list[dict[str, Any]] = []
    for p in rows_with_url:
        payload = {
            "project_id": project_id,
            "post_url": p["url"],
            "published_date": p.get("published"),
            "impressions": int(p.get("impressions") or 0),
            "engagements": int(p.get("engagements") or 0),
        }
        if p["url"] in id_by_url:
            resp = (
                supabase.table("post_performance")
                .update(payload)
                .eq("id", id_by_url[p["url"]])
                .execute()
            )
        else:
            resp = supabase.table("post_performance").insert(payload).execute()
        if resp.data:
            saved.append(resp.data[0])
    return saved


def load_post_performance(project_id: str, limit: int = 20) -> list[dict[str, Any]]:
    """Real post outcomes for a project, best-performing first — feeds the Analyst and Librarian."""
    resp = (
        get_supabase()
        .table("post_performance")
        .select("*")
        .eq("project_id", project_id)
        .order("impressions", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []


def map_performance_to_post(perf_id: str, post_code: Optional[str]) -> dict[str, Any]:
    """Link (or unlink) a real post URL to one of our drafted posts by post_code."""
    resp = (
        get_supabase()
        .table("post_performance")
        .update({"post_code": post_code})
        .eq("id", perf_id)
        .execute()
    )
    if not resp.data:
        raise RuntimeError("post_performance row not found")
    return resp.data[0]
