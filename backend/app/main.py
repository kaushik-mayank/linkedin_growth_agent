from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import config
from app.llm.base import LLMError
from app.llm.factory import get_default_provider, get_other_provider_name, get_provider
from app.routers import projects

app = FastAPI(title="LinkedIn Growth Agent — Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


class TestLLMRequest(BaseModel):
    prompt: str = "Say hello in one short sentence."


@app.post("/test-llm")
async def test_llm(body: TestLLMRequest):
    primary = get_default_provider()
    errors: dict[str, str] = {}

    try:
        reply = await primary.generate(body.prompt)
        return {"provider": primary.name, "reply": reply}
    except LLMError as e:
        errors[e.provider] = e.message

    # Primary failed — try the other configured provider and surface BOTH real errors
    # if it also fails. Never collapse this into a generic "all providers failed".
    fallback_name = get_other_provider_name(primary.name)
    try:
        fallback = get_provider(fallback_name)
        reply = await fallback.generate(body.prompt)
        return {
            "provider": fallback.name,
            "reply": reply,
            "note": f"primary provider '{primary.name}' failed, used fallback",
        }
    except LLMError as e:
        errors[e.provider] = e.message

    raise HTTPException(status_code=502, detail={"message": "All providers failed", "errors": errors})
