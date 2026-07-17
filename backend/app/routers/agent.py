import json
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.agent.runner import (
    PLANS_DIR,
    AgentRunError,
    run_weekly_agent,
    stream_weekly_agent,
)
from app.rate_limit import enforce_rate_limit

router = APIRouter(prefix="/projects/{project_id}", tags=["agent"])

# Weekly runs are expensive (many LLM + search calls). Cap re-runs to protect free quotas.
_RUN_MAX_CALLS = 5
_RUN_PER_SECONDS = 300  # 5 runs per 5 minutes per project


class RunWeeklyRequest(BaseModel):
    snapshot_id: Optional[str] = None


@router.post("/run-weekly")
async def run_weekly(project_id: str, body: RunWeeklyRequest = RunWeeklyRequest()):
    enforce_rate_limit(f"run:{project_id}", max_calls=_RUN_MAX_CALLS, per_seconds=_RUN_PER_SECONDS)
    try:
        return await run_weekly_agent(project_id, snapshot_id=body.snapshot_id)
    except AgentRunError as e:
        raise HTTPException(status_code=400, detail=e.message) from e


@router.post("/run-weekly/stream")
async def run_weekly_stream(project_id: str, body: RunWeeklyRequest = RunWeeklyRequest()):
    """Server-Sent Events: emits one 'progress' event per specialist, then a 'done' event."""
    enforce_rate_limit(f"run:{project_id}", max_calls=_RUN_MAX_CALLS, per_seconds=_RUN_PER_SECONDS)

    async def event_stream():
        try:
            async for event in stream_weekly_agent(project_id, snapshot_id=body.snapshot_id):
                yield f"data: {json.dumps(event)}\n\n"
        except AgentRunError as e:
            yield f"data: {json.dumps({'type': 'error', 'message': e.message})}\n\n"
        except Exception as e:  # surface the real error to the UI, never a silent hang
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/plans/{filename}")
async def download_plan(project_id: str, filename: str):
    path = PLANS_DIR / filename
    if project_id not in filename or not path.exists():
        raise HTTPException(status_code=404, detail="Plan not found")
    return FileResponse(path, media_type="text/markdown", filename=filename)
