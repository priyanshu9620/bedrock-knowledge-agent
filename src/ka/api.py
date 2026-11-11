"""Tiny demo API: POST /ask → answer + citations + tool calls; GET /ui."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ka import __version__
from ka.client import AgentClient
from ka.config import settings

app = FastAPI(title="Bedrock Knowledge Agent", version=__version__)
UI = Path(__file__).parent / "ui" / "index.html"


class Ask(BaseModel):
    question: str
    session_id: str | None = None
    confirm: bool = False


@app.get("/healthz")
def healthz() -> dict:
    return {
        "version": __version__,
        "region": settings.aws_region,
        "agent_id": settings.agent_id,
        "kb_id": settings.knowledge_base_id,
    }


@app.post("/ask")
def ask(body: Ask) -> dict:
    return AgentClient().ask(body.question, session_id=body.session_id, auto_confirm=body.confirm).as_dict()


@app.get("/ui")
def ui() -> FileResponse:
    return FileResponse(UI)
