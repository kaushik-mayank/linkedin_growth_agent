from fastapi import APIRouter, File, HTTPException, UploadFile

from app.db.supabase_client import get_supabase
from app.parser.linkedin_parser import parse as parse_linkedin_export

router = APIRouter(prefix="/projects/{project_id}/analytics", tags=["analytics"])


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

    return {"snapshot": resp.data[0], "parsed": parsed}
