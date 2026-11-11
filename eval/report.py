"""eval/report.md + results.json + README numbers from the newest eval run per backend in eval/out/. Never hand-edit."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
README = HERE.parent / "README.md"


def runs() -> dict[str, dict]:
    out = {}
    for f in sorted(HERE.glob("out/eval-*.json")):
        d = json.loads(f.read_text())
        out[d.get("backend", "unknown")] = d
    return out


def bar(title, labels, values, unit=""):
    if not values:
        return ""
    vmax = max(values) or 1
    bw, gap, left, top, h = 90, 30, 60, 40, 180
    w = max(640, left + len(values) * (bw + gap) + 20)
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h + 70}" font-family="sans-serif" font-size="12">',
        f'<text x="{left}" y="20" font-size="14" font-weight="bold">{title}</text>',
    ]
    for i, (lab, v) in enumerate(zip(labels, values, strict=True)):
        x, bh = left + i * (bw + gap), int(h * v / vmax)
        p += [
            f'<rect x="{x}" y="{top + h - bh}" width="{bw}" height="{bh}" fill="#2563eb"/>',
            f'<text x="{x + bw / 2}" y="{top + h - bh - 4}" text-anchor="middle">{v:g}{unit}</text>',
            f'<text x="{x + bw / 2}" y="{top + h + 16}" text-anchor="middle">{lab}</text>',
        ]
    return "\n".join(p + ["</svg>"])


def main() -> None:
    rs = runs()
    md = [
        "# Knowledge Agent — evaluation report",
        "",
        f"_Generated {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')} by `eval/report.py` from the newest run per backend in `eval/out/`. Do not edit by hand._",
        "",
    ]
    md += [
        "## Method",
        "",
        "40 fixed questions (`eval/questions.yml`) in four classes — **kb** (handbook only), **tool** (Lambda only), **both** (handbook + tool), **oos** (out of scope). Each answer is scored by deterministic rules (`eval/score.py`): the expected fact appears, the right document is cited, the right tool was called with the right arguments, confirmation was requested before the mutating tool, no tool for pure policy questions, and refusal + no tool for out-of-scope. Raw retrieval (top-3) is checked separately for kb/both questions. No LLM judge.",
        "",
    ]
    md += [
        "## Results",
        "",
        "| backend | passed | kb | tool | both | oos | retrieval top-3 hit | p50 | p95 | LLM calls/q | tokens in/out per q | est. $/q at list price | errors |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    results = {"generated": datetime.now(UTC).isoformat(timespec="seconds"), "backends": {}}
    for b, d in rs.items():
        bc = d["by_class"]

        def cell(c, bc=bc):
            return f"{bc[c]['passed']}/{bc[c]['n']}" if c in bc else "—"

        md.append(
            f"| {b} ({d['model']}) | **{d['passed']}/{d['completed']}** | {cell('kb')} | {cell('tool')} | {cell('both')} | {cell('oos')} | {d['retrieval_top3_hit_rate']} | {d['latency_s']['p50']} s | {d['latency_s']['p95']} s | {d['llm_calls_per_question']} | {d['tokens_per_question']['input']} / {d['tokens_per_question']['output']} | ${d['est_cost_usd_per_question_at_list_price']} | {len(d['errors'])} |"
        )
        results["backends"][b] = {
            k: d[k]
            for k in (
                "run_id",
                "model",
                "embeddings",
                "questions",
                "completed",
                "passed",
                "by_class",
                "per_check_pass_rate",
                "retrieval_top3_hit_rate",
                "latency_s",
                "llm_calls_per_question",
                "tokens_per_question",
                "est_cost_usd_per_question_at_list_price",
            )
        }
    md.append("")
    if rs:
        names = list(rs)
        md += [
            bar("questions passed (of 40)", names, [rs[n]["passed"] for n in names]),
            "",
            bar("p50 latency (s)", names, [rs[n]["latency_s"]["p50"] for n in names], " s"),
            "",
        ]
        md += [
            "### Per-check pass rate",
            "",
            "| check | " + " | ".join(names) + " |",
            "|---|" + "---|" * len(names),
        ]
        checks = sorted({k for n in names for k in rs[n]["per_check_pass_rate"]})
        for c in checks:
            md.append(
                f"| {c} | "
                + " | ".join(f"{100 * rs[n]['per_check_pass_rate'].get(c, 0):.0f} %" for n in names)
                + " |"
            )
        md.append("")
        for n in names:
            failed = [
                (
                    r["id"],
                    r["class"],
                    [k for k, v in r["checks"].items() if not v and k != "pass"],
                    r["answer"][:160],
                )
                for r in rs[n]["rows"]
                if not r["checks"]["pass"]
            ]
            if failed:
                md += [f"<details><summary>{n}: failed questions ({len(failed)})</summary>", ""]
                md += [f"- `{i}` ({c}): {', '.join(ks)} — _{a}_" for i, c, ks, a in failed]
                md += ["", "</details>", ""]
    md += [
        "## What this does NOT prove",
        "",
        "- **The corpus is synthetic** (13 short handbook docs we wrote); retrieval over thousands of real, messy documents is a different problem.",
        "- **The checks are structural**: the expected number/word is present, the right doc is cited, the right tool ran. They do not judge tone, completeness or hallucinated extras beyond the checked facts.",
        "- **One run per backend, free-tier model**; model non-determinism moves pass counts by ±1–2. Latency includes Google API round trips from one laptop (or one Lambda cold/warm mix).",
        "- **Tools are a demo Lambda over a JSON table**, not an HR system; the ticket tool returns a deterministic id.",
        "- **v1 is Gemini, not Bedrock** (AWS Free plan); see `docs/V2-BEDROCK.md`.",
        "",
    ]
    (HERE / "report.md").write_text("\n".join(md))
    (HERE / "results.json").write_text(json.dumps(results, indent=1))
    if README.exists() and rs:
        rows = [
            "| backend | passed | retrieval top-3 hit | p50 / p95 | per question |",
            "|---|---|---|---|---|",
        ]
        for b, d in rs.items():
            by_class = ", ".join(f"{c} {v['passed']}/{v['n']}" for c, v in d["by_class"].items())
            rows.append(
                f"| {b} · {d['model']} + {d['embeddings']} | **{d['passed']}/{d['completed']}** ({by_class}) | {d['retrieval_top3_hit_rate']} | {d['latency_s']['p50']} s / {d['latency_s']['p95']} s | {d['llm_calls_per_question']} LLM calls, {d['tokens_per_question']['input']}/{d['tokens_per_question']['output']} tokens |"
            )
        table = (
            "\n".join(rows)
            + "\n\nFull report with per-check table, failed questions and what the numbers do **not** prove: [`eval/report.md`](eval/report.md) · raw: [`eval/results.json`](eval/results.json)."
        )
        s = README.read_text()
        s = re.sub(
            r"<!-- numbers:start -->.*?<!-- numbers:end -->",
            f"<!-- numbers:start -->\n{table}\n<!-- numbers:end -->",
            s,
            flags=re.S,
        )
        README.write_text(s)
    print(f"report → {HERE / 'report.md'} ({len(rs)} backend(s))")


if __name__ == "__main__":
    main()
