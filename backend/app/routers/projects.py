from fastapi import APIRouter, HTTPException

from app.db.supabase_client import get_supabase
from app.models.project import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut)
async def create_project(body: ProjectCreate):
    try:
        supabase = get_supabase()
        resp = supabase.table("projects").insert(body.model_dump(exclude_none=True)).execute()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase error creating project: {e}") from e
    if not resp.data:
        raise HTTPException(status_code=502, detail="Supabase returned no data after insert")
    return resp.data[0]


@router.get("", response_model=list[ProjectOut])
async def list_projects():
    try:
        supabase = get_supabase()
        resp = supabase.table("projects").select("*").order("created_at", desc=True).execute()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase error listing projects: {e}") from e
    return resp.data


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str):
    try:
        supabase = get_supabase()
        resp = supabase.table("projects").select("*").eq("id", project_id).execute()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase error fetching project: {e}") from e
    if not resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    return resp.data[0]


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: str, body: ProjectUpdate):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update")
    try:
        supabase = get_supabase()
        resp = supabase.table("projects").update(updates).eq("id", project_id).execute()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase error updating project: {e}") from e
    if not resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    return resp.data[0]


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    try:
        supabase = get_supabase()
        resp = supabase.table("projects").delete().eq("id", project_id).execute()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase error deleting project: {e}") from e
    if not resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"deleted": True, "id": project_id}
