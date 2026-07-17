from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.db.supabase_client import get_supabase
from app.parser.linkedin_parser import parse as parse_linkedin_export
from app.performance_store import (
    load_post_performance,
    map_performance_to_post,
    sync_post_performance,
)

router = APIRouter(prefix="/projects/{project_id}/analytics", tags=["analytics"])


@router.get("/snapshots")
async def list_snapshots(project_id: str):
    """All snapshots for a project, oldest first — powers header stats, deltas, and sparklines."""
    try:
        resp = (
            get_supabase()
            .table("analytics_snapshots")
            .select("*")
            .eq("project_id", project_id)
            .order("period_end", desc=False)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase error listing snapshots: {e}") from e
    return resp.data


@router.post("/preview")
async def preview_analytics(project_id: str, file: UploadFile = File(...)):
    """Parse only — nothing is written to the database. Used for the upload confirmation screen."""
    content = await file.read()
    try:
        parsed = parse_linkedin_export(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse '{file.filename}': {e}") from e
    return {"file_name": file.filename, **parsed}


@router.post("/upload")
async def upload_analytics(project_id: str, file: UploadFile = File(...)):
    """Parse the export and upsert it into analytics_snapshots (same period = update, not duplicate)."""
    content = await file.read()
    try:
        parsed = parse_linkedin_export(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse '{file.filename}': {e}") from e

    period = parsed.get("period") or {}
    period_start, period_end = period.get("start"), period.get("end")
    if not period_start or not period_end:
        raise HTTPException(
            status_code=400,
            detail="Could not detect a date range from the DISCOVERY sheet — refusing to save without a period.",
        )

    totals = parsed["totals"]
    row = {
        "project_id": project_id,
        "period_start": period_start,
        "period_end": period_end,
        "followers_total": parsed.get("followers", {}).get("total", 0),
        "followers_new": parsed.get("followers", {}).get("new_this_period", 0),
        "impressions": totals["impressions"],
        "engagements": totals["engagements"],
        "engagement_rate": totals["engagement_rate"],
        "posts_published": totals["posts_published"],
        "raw": parsed,
        "file_name": file.filename,
    }

    try:
        supabase = get_supabase()
        resp = (
            supabase.table("analytics_snapshots")
            .upsert(row, on_conflict="project_id,period_start,period_end")
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase error saving snapshot: {e}") from e

    if not resp.data:
        raise HTTPException(status_code=502, detail="Supabase returned no data after upsert")

    # Capture real post outcomes (the learning loop). Non-fatal: a failure here must not
    # block saving the snapshot, but we surface it so it isn't silently lost.
    performance_saved = 0
    performance_warning = None
    try:
        performance_saved = len(sync_post_performance(project_id, parsed.get("top_posts", [])))
    except Exception as e:
        performance_warning = f"Saved the snapshot but could not record post performance: {e}"

    return {
        "snapshot": resp.data[0],
        "parsed": parsed,
        "performance_rows_saved": performance_saved,
        "performance_warning": performance_warning,
    }


@router.get("/performance")
async def get_performance(project_id: str):
    """Real post outcomes (impressions/engagements) captured from past exports."""
    try:
        return load_post_performance(project_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase error loading performance: {e}") from e


class MapPerformanceRequest(BaseModel):
    post_code: str | None = None


@router.patch("/performance/{perf_id}")
async def map_performance(project_id: str, perf_id: str, body: MapPerformanceRequest):
    """Link a real post URL to one of our drafted posts (or unlink with post_code=null)."""
    try:
        return map_performance_to_post(perf_id, body.post_code)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase error mapping performance: {e}") from e
