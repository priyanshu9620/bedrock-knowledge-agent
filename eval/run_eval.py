"""Ask every question in eval/questions.yml against the live agent; score; write eval/out/eval-<ts>.json.
Also runs raw retrieval for kb/both questions (retrieval top-3 hit rate). Aborts after 3 consecutive errors."""

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))
from score import retrieval_hit, score  # noqa: E402

from ka.agent import Agent  # noqa: E402
from ka.config import settings  # noqa: E402

# USD per 1M tokens (input, output) — Gemini 3.5 flash-lite list price; the free tier costs 0 within quota
PRICES = {"gemini-3.5-flash-lite": (0.10, 0.40)}


def main() -> int:
    qs = yaml.safe_load((HERE / "questions.yml").read_text())
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    if limit:
        qs = qs[:limit]
    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    client = Agent()
    where = "S3 Vectors + Lambda" if settings.vector_bucket else "local index + in-process tools"
    print(
        f"eval · {settings.gemini_model} / {settings.embedding_model} · {where} · {len(qs)} questions · run {run_id}"
    )
    rows, errors, streak = [], [], 0
    for q in qs:
        try:
            a = client.ask(q["q"], auto_confirm=bool(q["expect"].get("confirm")))
            ret = client.retrieve(q["q"], k=3) if q["class"] in {"kb", "both"} else []
            streak = 0
        except Exception as e:  # noqa: BLE001
            streak += 1
            errors.append({"id": q["id"], "error": f"{type(e).__name__}: {str(e)[:300]}"})
            print(f"  {q['id']} ERROR {type(e).__name__}: {str(e)[:160]}")
            if streak >= 3:
                print("3 consecutive errors — aborting, no results file written.")
                return 2
            continue
        checks = score(q["expect"], a.as_dict())
        hit = retrieval_hit(q["expect"], ret)
        row = {
            "id": q["id"],
            "class": q["class"],
            "question": q["q"],
            "answer": a.text,
            "citations": a.citations,
            "tool_calls": a.tool_calls,
            "retrieved_docs": a.retrieved_docs,
            "retrieval_top3": [r["doc"] for r in ret],
            "retrieval_hit_top3": hit,
            "checks": checks,
            "latency_s": a.latency_s,
            "llm_calls": a.llm_calls,
            "input_tokens": a.input_tokens,
            "output_tokens": a.output_tokens,
            "confirmation_requested": a.confirmation_requested,
        }
        rows.append(row)
        failed = [k for k, v in checks.items() if not v and k != "pass"]
        print(
            f"  {q['id']} {q['class']:<4} {'PASS' if checks['pass'] else 'FAIL'} {a.latency_s:>5.1f}s {a.llm_calls} llm {a.input_tokens}/{a.output_tokens} tok"
            + (f"  ✗ {', '.join(failed)}" if failed else "")
        )
        time.sleep(0.5)
    if not rows:
        return 2
    by_class = {}
    for c in ("kb", "tool", "both", "oos"):
        rs = [r for r in rows if r["class"] == c]
        if rs:
            by_class[c] = {"n": len(rs), "passed": sum(r["checks"]["pass"] for r in rs)}
    lat = sorted(r["latency_s"] for r in rows)
    tin, tout = sum(r["input_tokens"] for r in rows), sum(r["output_tokens"] for r in rows)
    hits = [r["retrieval_hit_top3"] for r in rows if r["retrieval_hit_top3"] is not None]
    check_names = sorted({k for r in rows for k in r["checks"] if k != "pass"})
    summary = {
        "run_id": run_id,
        "model": settings.gemini_model,
        "embeddings": settings.embedding_model,
        "backend": where,
        "questions": len(qs),
        "completed": len(rows),
        "errors": errors,
        "passed": sum(r["checks"]["pass"] for r in rows),
        "by_class": by_class,
        "per_check_pass_rate": {
            k: round(
                sum(1 for r in rows if r["checks"].get(k, True)) / sum(1 for r in rows if k in r["checks"]), 3
            )
            for k in check_names
        },
        "retrieval_top3_hit_rate": round(sum(hits) / len(hits), 3) if hits else None,
        "latency_s": {
            "p50": lat[len(lat) // 2],
            "p95": lat[min(len(lat) - 1, int(len(lat) * 0.95))],
            "mean": round(sum(lat) / len(lat), 2),
        },
        "llm_calls_per_question": round(sum(r["llm_calls"] for r in rows) / len(rows), 2),
        "tokens_per_question": {"input": round(tin / len(rows)), "output": round(tout / len(rows))},
        "est_cost_usd_per_question_at_list_price": round(
            (tin * PRICES["gemini-3.5-flash-lite"][0] + tout * PRICES["gemini-3.5-flash-lite"][1])
            / 1e6
            / len(rows),
            5,
        ),
        "rows": rows,
    }
    (HERE / "out").mkdir(exist_ok=True)
    path = HERE / "out" / f"eval-{run_id}.json"
    path.write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    print(
        f"\n{summary['passed']}/{len(rows)} passed · by class {by_class} · retrieval top-3 hit {summary['retrieval_top3_hit_rate']} · p50 {summary['latency_s']['p50']}s p95 {summary['latency_s']['p95']}s · {summary['tokens_per_question']['input']}/{summary['tokens_per_question']['output']} tok/q\n→ {path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
