import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
from score import contains, retrieval_hit, score  # noqa: E402


def test_contains_is_number_and_currency_tolerant():
    assert contains("You get ₹2,500 per day", "2,500")
    assert contains("The cover is Rs. 5,00,000", "5,00,000")
    assert not contains("You get 120 days", "12")  # whole-number match only
    assert contains("Tuesday to Thursday are office days", "Tuesday")
    assert contains("the reimbursement amount is ₹0.", "0")  # sentence-ending period (eval q26)
    assert not contains("costs 0.5 per unit", "0")  # decimal: 0.5 is not 0


def test_kb_question_scoring():
    exp = {"contains": ["12"], "cite": "01-leave-policy.md"}
    good = {
        "text": "Employees get 12 casual leave days.",
        "citations": [{"doc": "01-leave-policy.md"}],
        "tool_calls": [],
    }
    assert score(exp, good)["pass"]
    assert not score(exp, {**good, "citations": []})["cited_right_doc"]
    assert not score(exp, {**good, "tool_calls": [{"api": "/holidays"}]})["no_unneeded_tool"]


def test_tool_question_scoring_with_args_and_confirmation():
    exp = {"contains": ["21.5"], "tool": "/leave-balance/{employee_id}", "args": {"employee_id": "E1001"}}
    ans = {
        "text": "E1001 has 21.5 EL days.",
        "citations": [],
        "tool_calls": [{"api": "/leave-balance/{employee_id}", "params": {"employee_id": "e1001"}}],
    }
    c = score(exp, ans)
    assert c["pass"] and c["tool_args_correct"]
    exp2 = {"tool": "/helpdesk/ticket", "contains": ["HD-"], "confirm": True}
    ans2 = {
        "text": "Filed ticket HD-1A2B3C",
        "citations": [],
        "tool_calls": [{"api": "/helpdesk/ticket", "params": {}}],
        "confirmation_requested": True,
    }
    assert score(exp2, ans2)["pass"]
    assert not score(exp2, {**ans2, "confirmation_requested": False})["confirmation_requested"]


def test_oos_scoring():
    exp = {"refuse": True}
    assert score(
        exp, {"text": "I can only answer questions about the Meridian Labs handbook.", "tool_calls": []}
    )["pass"]
    assert not score(exp, {"text": "Paris.", "tool_calls": []})["refused"]
    assert not score(exp, {"text": "Sorry, I cannot help.", "tool_calls": [{"api": "/holidays"}]})[
        "no_tool_call"
    ]


def test_retrieval_hit():
    assert retrieval_hit({"cite": "a.md"}, [{"doc": "b.md"}, {"doc": "a.md"}]) is True
    assert retrieval_hit({"cite": "a.md"}, [{"doc": "b.md"}] * 3 + [{"doc": "a.md"}]) is False
    assert retrieval_hit({}, []) is None
