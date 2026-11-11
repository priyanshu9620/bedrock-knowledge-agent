"""The agent: a Gemini tool-calling loop over `retrieve_handbook` (vector index) + the people-ops tools (Lambda).
Citations = the docs whose chunks were retrieved in this answer. Mutating tools are gated by code: the loop stops
and asks for confirmation unless auto_confirm, or the session was confirmed."""

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from ka.config import settings
from ka.gemini import Gemini
from ka.index import make_index
from ka.tools import ToolExecutor

INSTRUCTION = (Path(__file__).parent / "instruction.txt").read_text()
RETRIEVE = {
    "name": "retrieve_handbook",
    "description": "Search the Meridian Labs employee handbook. Use for ANY policy question (leave, expenses, travel, security, onboarding, devices, remote work, holidays, benefits, conduct, incidents, glossary). Returns the most relevant passages with their source document.",
    "parameters": {
        "type": "OBJECT",
        "properties": {"query": {"type": "STRING", "description": "what to search for"}},
        "required": ["query"],
    },
}
CONFIRM_WORDS = {"yes", "y", "confirm", "ok", "okay", "go ahead", "please do", "sure", "yes please", "do it"}


@dataclass
class Answer:
    question: str
    text: str = ""
    citations: list[dict] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    retrieved_docs: list[str] = field(default_factory=list)
    confirmation_requested: bool = False
    input_tokens: int = 0
    output_tokens: int = 0
    llm_calls: int = 0
    latency_s: float = 0.0
    session_id: str = ""
    steps: int = 0

    def as_dict(self) -> dict:
        return dict(self.__dict__)


class Agent:
    def __init__(
        self,
        gemini: Gemini | None = None,
        index=None,
        executor: ToolExecutor | None = None,
        max_steps: int | None = None,
    ):
        self.gemini = gemini or Gemini(
            settings.google_api_key,
            settings.gemini_model,
            settings.embedding_model,
            settings.embedding_dimension,
        )
        self.index = index if index is not None else make_index()
        self.executor = executor or ToolExecutor()
        self.max_steps = max_steps or settings.max_steps
        self.tools = [RETRIEVE] + self.executor.declarations()
        self.sessions: dict[str, dict] = {}  # session_id → {"contents": [...], "pending": {...}|None}

    # ---- public ----
    def ask(self, question: str, session_id: str | None = None, auto_confirm: bool = False) -> Answer:
        sid = session_id or uuid.uuid4().hex
        sess = self.sessions.setdefault(sid, {"contents": [], "pending": None})
        ans = Answer(question=question, session_id=sid)
        t0 = time.perf_counter()
        if sess["pending"] and question.strip().lower().rstrip(".!") in CONFIRM_WORDS:
            # the user confirmed the pending mutating tool → execute it and let the model finish
            pend = sess.pop("pending")
            sess["pending"] = None
            result = self.executor.call(pend["name"], pend["args"])
            ans.tool_calls.append(
                {
                    "api": pend["path"],
                    "method": pend["method"],
                    "params": pend["args"],
                    "result": _short(result),
                }
            )
            sess["contents"].append(self.gemini.tool_results([(pend["name"], result)]))
            self._loop(ans, sess, auto_confirm=True)
        else:
            sess["contents"].append(self.gemini.user(question))
            self._loop(ans, sess, auto_confirm)
        ans.latency_s = round(time.perf_counter() - t0, 2)
        return ans

    def retrieve(self, query: str, k: int | None = None) -> list[dict]:
        v = self.gemini.embed([query], task="RETRIEVAL_QUERY")[0]
        return self.index.query(v, k or settings.retrieve_top_k)

    # ---- the loop ----
    def _loop(self, ans: Answer, sess: dict, auto_confirm: bool) -> None:
        for _ in range(self.max_steps):
            turn = self.gemini.chat(INSTRUCTION, sess["contents"], self.tools)
            ans.llm_calls += 1
            ans.input_tokens += turn.input_tokens
            ans.output_tokens += turn.output_tokens
            ans.steps += 1
            sess["contents"].append(self.gemini.model_turn(turn))
            if not turn.function_calls:
                ans.text = turn.text
                return
            results = []
            for fc in turn.function_calls:
                name, args = fc["name"], fc["args"]
                if name == "retrieve_handbook":
                    hits = self.retrieve(str(args.get("query", ans.question)))
                    for h in hits:
                        if h["doc"] not in ans.retrieved_docs:
                            ans.retrieved_docs.append(h["doc"])
                        ans.citations.append(
                            {"doc": h["doc"], "snippet": h["text"][:200], "score": h["score"]}
                        )
                    results.append((name, {"passages": [{"doc": h["doc"], "text": h["text"]} for h in hits]}))
                    continue
                spec = self.executor.specs.get(name)
                if spec is None:
                    results.append((name, {"ok": False, "error": f"unknown tool {name}"}))
                    continue
                if spec.requires_confirmation and not auto_confirm:
                    sess["pending"] = {"name": name, "args": args, "path": spec.path, "method": spec.method}
                    ans.confirmation_requested = True
                    ans.tool_calls.append(
                        {
                            "api": spec.path,
                            "method": spec.method,
                            "params": args,
                            "result": "CONFIRMATION_REQUESTED",
                        }
                    )
                    ans.text = (
                        f"Before I do that, please confirm: {name} with {args}. Reply 'yes' to proceed."
                    )
                    return
                if spec.requires_confirmation:
                    ans.confirmation_requested = True  # gate recognised; auto-confirmed by the caller
                result = self.executor.call(name, args)
                ans.tool_calls.append(
                    {"api": spec.path, "method": spec.method, "params": args, "result": _short(result)}
                )
                results.append((name, result))
            sess["contents"].append(self.gemini.tool_results(results))
        ans.text = ans.text or "(stopped: too many steps)"


def _short(result: dict) -> str:
    import json

    return json.dumps(result, ensure_ascii=False)[:500]


def build_agent() -> Agent:
    return Agent()
