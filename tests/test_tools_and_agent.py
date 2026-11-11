"""Offline: OpenAPI → tool specs, the Bedrock-shaped event, chunking, the local index, and the agent loop with a fake Gemini."""

import sys
from pathlib import Path

import pytest

from ka.agent import Agent
from ka.gemini import Turn
from ka.index import LocalIndex
from ka.ingest import chunk, ingest, load_docs
from ka.tools import ToolExecutor, action_group_event, load_specs

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lambda"))


def test_openapi_to_tool_specs():
    specs = {t.name: t for t in load_specs()}
    assert set(specs) == {
        "getLeaveBalance",
        "calculateReimbursement",
        "getHolidayCalendar",
        "fileHelpdeskTicket",
    }
    assert specs["getLeaveBalance"].path_params == ["employee_id"] and specs["getLeaveBalance"].required == [
        "employee_id"
    ]
    assert specs["calculateReimbursement"].body_params == ["category", "amount_inr", "has_receipt", "days"]
    assert (
        specs["fileHelpdeskTicket"].requires_confirmation
        and not specs["getHolidayCalendar"].requires_confirmation
    )
    d = specs["calculateReimbursement"].declaration()
    assert (
        d["parameters"]["properties"]["amount_inr"]["type"] == "NUMBER"
        and "category" in d["parameters"]["required"]
    )


def test_event_shape_matches_bedrock_and_handler_runs_in_process():
    specs = {t.name: t for t in load_specs()}
    ev = action_group_event(
        specs["calculateReimbursement"], {"category": "internet", "amount_inr": 900, "has_receipt": True}
    )
    assert ev["apiPath"] == "/reimbursement/calculate" and ev["httpMethod"] == "POST"
    assert {p["name"] for p in ev["requestBody"]["content"]["application/json"]["properties"]} == {
        "category",
        "amount_inr",
        "has_receipt",
    }
    ex = ToolExecutor(lambda_name="")  # in-process
    assert ex.call("getLeaveBalance", {"employee_id": "E1001"})["name"] == "Asha Rao"
    assert ex.call("nope", {})["ok"] is False


def test_chunking_keeps_title_and_overlap():
    text = "# Title\n\n" + "\n\n".join(f"Paragraph {i} " + "x" * 300 for i in range(8))
    cs = chunk(text, max_chars=1000, overlap=100)
    assert len(cs) >= 3 and all(c.startswith("# Title") for c in cs)
    assert "Paragraph 7" in cs[-1]


class FakeGemini:
    """Scripted replies: embeds by hashing words; chats follow a queue of Turns."""

    def __init__(self, turns):
        self.turns = list(turns)
        self.dims = 512

    def embed(self, texts, task="RETRIEVAL_DOCUMENT"):
        out = []
        for t in texts:
            v = [0.0] * self.dims
            for w in t.lower().split():
                v[hash(w) % self.dims] += 1.0
            out.append(v)
        return out

    def chat(self, system, contents, tools):
        t = self.turns.pop(0)
        t.raw = type("R", (), {"candidates": [type("C", (), {"content": {"role": "model", "turn": t}})()]})()
        return t

    @staticmethod
    def user(text):
        return {"role": "user", "text": text}

    @staticmethod
    def model_turn(turn):
        return turn.raw.candidates[0].content

    @staticmethod
    def tool_results(results):
        return {"role": "tool", "results": results}


@pytest.fixture
def local_index(tmp_path):
    idx = LocalIndex(str(tmp_path / "i.npz"))
    g = FakeGemini([])
    stats = ingest(idx, g, load_docs("local"))
    assert stats["docs"] == 13 and stats["chunks"] >= 13
    return idx


def test_local_index_query_returns_the_right_doc(local_index):
    g = FakeGemini([])
    hits = local_index.query(g.embed(["casual leave 12 days per year credited"])[0], k=3)
    assert hits and hits[0]["doc"] == "01-leave-policy.md"


def test_agent_retrieves_cites_and_answers(local_index):
    g = FakeGemini(
        [
            Turn(
                function_calls=[
                    {"name": "retrieve_handbook", "args": {"query": "casual leave days per year"}}
                ],
                input_tokens=10,
                output_tokens=2,
            ),
            Turn(text="You get 12 casual leave days per year.", input_tokens=50, output_tokens=12),
        ]
    )
    a = Agent(gemini=g, index=local_index, executor=ToolExecutor(lambda_name=""), max_steps=4)
    ans = a.ask("How many casual leave days?")
    assert ans.text.startswith("You get 12") and ans.llm_calls == 2 and ans.input_tokens == 60
    assert "01-leave-policy.md" in ans.retrieved_docs and ans.citations[0]["doc"]
    assert ans.tool_calls == []


def test_agent_calls_lambda_tool_and_gates_confirmation(local_index):
    g = FakeGemini(
        [
            Turn(function_calls=[{"name": "getLeaveBalance", "args": {"employee_id": "E1001"}}]),
            Turn(text="E1001 has 21.5 EL days."),
            Turn(
                function_calls=[
                    {"name": "fileHelpdeskTicket", "args": {"summary": "VPN down", "priority": "P2"}}
                ]
            ),
            Turn(text="Filed ticket HD-XYZ."),
        ]
    )
    a = Agent(gemini=g, index=local_index, executor=ToolExecutor(lambda_name=""), max_steps=4)
    ans = a.ask("What is E1001's balance?")
    assert (
        ans.tool_calls[0]["api"] == "/leave-balance/{employee_id}" and "21.5" in ans.tool_calls[0]["result"]
    )
    ans2 = a.ask("File a P2 ticket: VPN down", session_id="s1")
    assert (
        ans2.confirmation_requested
        and ans2.tool_calls[-1]["result"] == "CONFIRMATION_REQUESTED"
        and "confirm" in ans2.text.lower()
    )
    ans3 = a.ask("yes", session_id="s1")
    assert (
        ans3.tool_calls[0]["api"] == "/helpdesk/ticket"
        and "HD-" in ans3.tool_calls[0]["result"]
        and ans3.text.startswith("Filed")
    )
