from fastapi import APIRouter, HTTPException

from app.db.supabase_client import get_supabase

router = APIRouter(prefix="/projects/{project_id}/weeks", tags=["weeks"])


@router.get("")
async def list_weeks(project_id: str):
    """All weeks for a project, newest first — powers the History page and 'latest plan' on the dashboard."""
    try:
        resp = (
            get_supabase()
            .table("weeks")
            .select("*")
            .eq("project_id", project_id)
            .order("week_number", desc=True)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase error listing weeks: {e}") from e
    return resp.data


@router.get("/{week_id}")
async def get_week(project_id: str, week_id: str):
    """A single week plus its posts — powers the Weekly Plan view."""
    try:
        supabase = get_supabase()
        week_resp = supabase.table("weeks").select("*").eq("id", week_id).execute()
        if not week_resp.data:
            raise HTTPException(status_code=404, detail="Week not found")
        posts_resp = (
            supabase.table("posts")
            .select("*")
            .eq("week_id", week_id)
            .order("post_code", desc=False)
            .execute()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase error fetching week: {e}") from e
    return {"week": week_resp.data[0], "posts": posts_resp.data}
