from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.research.tavily_research import ResearchError
from app.research.tavily_research import search as tavily_search

router = APIRouter(prefix="/research", tags=["research"])


class ResearchRequest(BaseModel):
    query: str
    days: int = 7
    max_results: int = 5


@router.post("/search")
async def research_search(body: ResearchRequest):
    try:
        return await tavily_search(body.query, days=body.days, max_results=body.max_results)
    except ResearchError as e:
        raise HTTPException(status_code=502, detail=f"Tavily error: {e.message}") from e
