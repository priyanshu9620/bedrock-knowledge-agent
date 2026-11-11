"""Deterministic scoring of one agent answer against a question's `expect` block. No LLM judge."""

import re

REFUSAL_CUES = (
    "not able to",
    "cannot",
    "can't",
    "unable",
    "don't have",
    "do not have",
    "not covered",
    "outside",
    "only answer",
    "not available",
    "sorry",
    "no information",
    "does not contain",
    "doesn't contain",
    "not in the handbook",
    "not part of",
)


def norm(s: str) -> str:
    s = (s or "").lower().replace("₹", "").replace("rs.", "").replace("inr", "")
    s = re.sub(r"(?<=\d),(?=\d)", "", s)  # 2,500 → 2500 ; 5,00,000 → 500000
    return re.sub(r"\s+", " ", s)


def contains(answer: str, needle: str) -> bool:
    a, n = norm(answer), norm(needle)
    if re.fullmatch(r"[\d.]+", n):  # bare number: must appear as a whole number token
        return re.search(rf"(?<![\d.]){re.escape(n)}(?![\d.])", a) is not None
    return n in a


def score(expect: dict, answer: dict) -> dict:
    """answer: dict from Answer.as_dict(). Returns {check: bool} plus 'pass'."""
    text = answer.get("text") or ""
    cited = {c["doc"] for c in answer.get("citations") or []}
    tools = answer.get("tool_calls") or []
    checks: dict[str, bool] = {}
    if expect.get("refuse"):
        checks["refused"] = any(c in text.lower() for c in REFUSAL_CUES)
        checks["no_tool_call"] = not tools
    else:
        if expect.get("contains"):
            checks["facts_present"] = all(contains(text, n) for n in expect["contains"])
        if expect.get("cite"):
            checks["cited_right_doc"] = expect["cite"] in cited
        if expect.get("tool"):
            calls = [t for t in tools if t.get("api") == expect["tool"]]
            checks["right_tool_called"] = bool(calls)
            if expect.get("args"):
                want = {k: str(v) for k, v in expect["args"].items()}
                checks["tool_args_correct"] = any(
                    all(
                        str((t.get("params") or {}).get(k, "")).strip().lower() == v.lower()
                        for k, v in want.items()
                    )
                    for t in calls
                )
            if expect.get("confirm"):
                checks["confirmation_requested"] = bool(answer.get("confirmation_requested"))
        if not expect.get("tool"):
            checks["no_unneeded_tool"] = not tools
    checks["pass"] = all(v for k, v in checks.items() if k != "pass")
    return checks


def retrieval_hit(expect: dict, retrieved: list[dict], k: int = 3) -> bool | None:
    """Did the expected doc appear in the top-k raw KB retrieval? None when the question has no cite."""
    if not expect.get("cite"):
        return None
    return expect["cite"] in [r["doc"] for r in retrieved[:k]]
