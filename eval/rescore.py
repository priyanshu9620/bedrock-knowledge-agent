"""Re-apply eval/score.py to a stored run (answers are kept verbatim), e.g. after fixing a scorer bug.
Usage: uv run python eval/rescore.py [eval/out/eval-<ts>.json]  (default: newest). Rewrites the file in place and
records `rescored_at`; the model answers, tool calls and latencies are untouched."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from score import score  # noqa: E402

path = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted(HERE.glob("out/eval-*.json"))[-1]
d = json.loads(path.read_text())
import yaml  # noqa: E402

qs = {q["id"]: q for q in yaml.safe_load((HERE / "questions.yml").read_text())}
changed = 0
for r in d["rows"]:
    answer = {
        "text": r["answer"],
        "citations": r["citations"],
        "tool_calls": r["tool_calls"],
        "confirmation_requested": r.get("confirmation_requested"),
    }
    new = score(qs[r["id"]]["expect"], answer)
    if new != r["checks"]:
        changed += 1
    r["checks"] = new
rows = d["rows"]
d["passed"] = sum(r["checks"]["pass"] for r in rows)
for c, v in d["by_class"].items():
    v["passed"] = sum(r["checks"]["pass"] for r in rows if r["class"] == c)
names = sorted({k for r in rows for k in r["checks"] if k != "pass"})
d["per_check_pass_rate"] = {
    k: round(sum(1 for r in rows if r["checks"].get(k, True)) / sum(1 for r in rows if k in r["checks"]), 3)
    for k in names
}
d["rescored_at"] = datetime.now(UTC).isoformat(timespec="seconds")
path.write_text(json.dumps(d, indent=1, ensure_ascii=False))
print(
    f"{path.name}: {changed} row(s) changed → {d['passed']}/{d['completed']} passed, by class {d['by_class']}"
)
