"""Local demo API: POST /ask → Answer; GET /ui; GET /healthz. (The AWS version is lambda_api.py.)"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ka import __version__
from ka.config import settings

app = FastAPI(title="Knowledge Agent", version=__version__)
UI = Path(__file__).parent / "ui" / "index.html"
_agent = None


class Ask(BaseModel):
    question: str
    session_id: str | None = None
    confirm: bool = False


@app.get("/healthz")
def healthz() -> dict:
    return {
        "version": __version__,
        "index": "s3vectors" if settings.vector_bucket else "local",
        "tools": settings.tools_lambda or "in-process",
        "model": settings.gemini_model,
    }


@app.post("/ask")
def ask(body: Ask) -> dict:
    global _agent
    if _agent is None:
        from ka.agent import Agent

        _agent = Agent()
    return _agent.ask(body.question, session_id=body.session_id, auto_confirm=body.confirm).as_dict()


@app.get("/ui")
def ui() -> FileResponse:
    return FileResponse(UI)
