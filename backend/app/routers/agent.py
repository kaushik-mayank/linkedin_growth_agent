from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.agent.runner import PLANS_DIR, AgentRunError, run_weekly_agent

router = APIRouter(prefix="/projects/{project_id}", tags=["agent"])


class RunWeeklyRequest(BaseModel):
    snapshot_id: Optional[str] = None


@router.post("/run-weekly")
async def run_weekly(project_id: str, body: RunWeeklyRequest = RunWeeklyRequest()):
    try:
        return await run_weekly_agent(project_id, snapshot_id=body.snapshot_id)
    except AgentRunError as e:
        raise HTTPException(status_code=400, detail=e.message) from e


@router.get("/plans/{filename}")
async def download_plan(project_id: str, filename: str):
    path = PLANS_DIR / filename
    if project_id not in filename or not path.exists():
        raise HTTPException(status_code=404, detail="Plan not found")
    return FileResponse(path, media_type="text/markdown", filename=filename)
