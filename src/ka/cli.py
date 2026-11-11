"""`ka` CLI: ingest the corpus, ask, retrieve, serve the local demo, show config."""

import json

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from ka.config import settings

app = typer.Typer(no_args_is_help=True, help="Knowledge Agent (Gemini + S3 Vectors + Lambda)")
console = Console()


def _show(a) -> None:
    console.print(f"[bold green]answer>[/bold green] {a.text}")
    seen = set()
    for c in a.citations:
        if c["doc"] not in seen:
            seen.add(c["doc"])
            console.print(
                f"  [dim]cite {c['doc']} ({c.get('score')}): {c['snippet'][:90].replace(chr(10), ' ')}…[/dim]"
            )
    for t in a.tool_calls:
        console.print(
            f"  [cyan]tool {t['method']} {t['api']} {t['params']}[/cyan] → [dim]{(t['result'] or '')[:120]}[/dim]"
        )
    if a.confirmation_requested and a.tool_calls and a.tool_calls[-1]["result"] == "CONFIRMATION_REQUESTED":
        console.print(f"  [yellow]confirmation needed → ka ask yes --session {a.session_id}[/yellow]")
    console.print(
        f"  [dim]{a.latency_s}s · {a.llm_calls} LLM calls · {a.input_tokens}/{a.output_tokens} tokens · session {a.session_id}[/dim]"
    )


_AGENT = None


def _agent():
    global _AGENT
    if _AGENT is None:
        from ka.agent import Agent

        _AGENT = Agent()
    return _AGENT


@app.command()
def ask(
    question: str, session: str = "", confirm: bool = typer.Option(False, help="auto-confirm mutating tools")
) -> None:
    """Ask one question (local index + in-process tools unless .env points at AWS)."""
    _show(_agent().ask(question, session_id=session or None, auto_confirm=confirm))


@app.command()
def retrieve(question: str, top_k: int = 4) -> None:
    """Raw vector retrieval: top chunks with cosine scores."""
    t = Table(title=f"retrieve · top {top_k} · {'S3 Vectors' if settings.vector_bucket else 'local'}")
    for col in ("score", "doc", "text"):
        t.add_column(col)
    for r in _agent().retrieve(question, top_k):
        t.add_row(str(r["score"]), str(r["doc"]), r["text"][:110].replace("\n", " "))
    console.print(t)


@app.command()
def ingest(source: str = typer.Option("local", help="local (corpus/) | s3 (the docs bucket)")) -> None:
    """Chunk → embed (Gemini) → index (S3 Vectors or local)."""
    from ka.ingest import ingest as _ingest
    from ka.ingest import load_docs

    a = _agent()
    stats = _ingest(a.index, a.gemini, load_docs(source))
    console.print({"source": source, "index": "s3vectors" if settings.vector_bucket else "local", **stats})


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8001) -> None:
    """Local demo API + page at /ui."""
    uvicorn.run("ka.api:app", host=host, port=port)


@app.command()
def config() -> None:
    d = settings.model_dump()
    d["google_api_key"] = "set" if d["google_api_key"] else ""
    d["api_token"] = "set" if d["api_token"] else ""
    console.print(json.dumps(d, indent=1))
