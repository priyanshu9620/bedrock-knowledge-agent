"""`ka` CLI: ask the agent, retrieve from the KB, sync the KB, serve the demo page."""

import json
import subprocess

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from ka.config import settings

app = typer.Typer(no_args_is_help=True, help="Bedrock Knowledge Agent")
console = Console()


@app.command()
def ask(
    question: str, session: str = "", confirm: bool = typer.Option(False, help="auto-confirm mutating tools")
) -> None:
    """Ask the agent one question; prints the answer, citations, tool calls and usage."""
    from ka.client import AgentClient

    a = AgentClient().ask(question, session_id=session or None, auto_confirm=confirm)
    console.print(f"[bold green]answer>[/bold green] {a.text}")
    for c in a.citations:
        console.print(f"  [dim]cite {c['doc']}: {c['snippet'][:90]}…[/dim]")
    for t in a.tool_calls:
        console.print(
            f"  [cyan]tool {t['method']} {t['api']} {t['params']}[/cyan] → [dim]{(t['result'] or '')[:120]}[/dim]"
        )
    if a.confirmation_requested and not confirm:
        console.print(
            "  [yellow]the agent asked for confirmation before a mutating tool; re-run with --confirm[/yellow]"
        )
    console.print(
        f"  [dim]{a.latency_s}s · {a.llm_calls} LLM calls · {a.input_tokens}/{a.output_tokens} tokens · session {a.session_id}[/dim]"
    )


@app.command()
def retrieve(question: str, top_k: int = 5) -> None:
    """Raw Knowledge Base retrieval: top chunks with scores (no agent, no generation)."""
    from ka.client import retrieve as _retrieve

    t = Table(title=f"retrieve · top {top_k}")
    for col in ("score", "doc", "text"):
        t.add_column(col)
    for r in _retrieve(question, top_k=top_k):
        t.add_row(str(r["score"]), r["doc"], r["text"][:120].replace("\n", " "))
    console.print(t)


@app.command("kb-sync")
def kb_sync_cmd() -> None:
    """Start a KB ingestion job (reads data_source_id from tofu output) and wait."""
    from ka.client import kb_sync

    out = json.loads(subprocess.check_output(["tofu", "-chdir=infra", "output", "-json"]))
    res = kb_sync(out["knowledge_base_id"]["value"], out["data_source_id"]["value"])
    console.print(res)


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8001) -> None:
    """Demo API + page at /ui."""
    uvicorn.run("ka.api:app", host=host, port=port)


@app.command()
def config() -> None:
    console.print(settings.model_dump())
