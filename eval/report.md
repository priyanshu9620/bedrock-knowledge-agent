# Knowledge Agent — evaluation report

_Generated 2026-11-11 17:41 UTC by `eval/report.py` from the newest run per backend in `eval/out/`. Do not edit by hand._

## Method

40 fixed questions (`eval/questions.yml`) in four classes — **kb** (handbook only), **tool** (Lambda only), **both** (handbook + tool), **oos** (out of scope). Each answer is scored by deterministic rules (`eval/score.py`): the expected fact appears, the right document is cited, the right tool was called with the right arguments, confirmation was requested before the mutating tool, no tool for pure policy questions, and refusal + no tool for out-of-scope. Raw retrieval (top-3) is checked separately for kb/both questions. No LLM judge.

## Results

| backend | passed | kb | tool | both | oos | retrieval top-3 hit | p50 | p95 | LLM calls/q | tokens in/out per q | est. $/q at list price | errors |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S3 Vectors + Lambda (gemini-3.5-flash-lite) | **40/40** | 22/22 | 8/8 | 6/6 | 4/4 | 1.0 | 7.39 s | 17.73 s | 1.9 | 2497 / 66 | $0.00028 | 0 |
_S3 Vectors + Lambda: answers recorded in run 20261111-173336, re-scored at 2026-11-11T17:40:42+00:00 after a scorer fix (eval/rescore.py); model outputs unchanged._

<svg xmlns="http://www.w3.org/2000/svg" width="640" height="250" font-family="sans-serif" font-size="12">
<text x="60" y="20" font-size="14" font-weight="bold">questions passed (of 40)</text>
<rect x="60" y="40" width="90" height="180" fill="#2563eb"/>
<text x="105.0" y="36" text-anchor="middle">40</text>
<text x="105.0" y="236" text-anchor="middle">S3 Vectors + Lambda</text>
</svg>

<svg xmlns="http://www.w3.org/2000/svg" width="640" height="250" font-family="sans-serif" font-size="12">
<text x="60" y="20" font-size="14" font-weight="bold">p50 latency (s)</text>
<rect x="60" y="40" width="90" height="180" fill="#2563eb"/>
<text x="105.0" y="36" text-anchor="middle">7.39 s</text>
<text x="105.0" y="236" text-anchor="middle">S3 Vectors + Lambda</text>
</svg>

### Per-check pass rate

| check | S3 Vectors + Lambda |
|---|---|
| cited_right_doc | 143 % |
| confirmation_requested | 4000 % |
| facts_present | 111 % |
| no_tool_call | 1000 % |
| no_unneeded_tool | 182 % |
| refused | 1000 % |
| right_tool_called | 286 % |
| tool_args_correct | 333 % |

## What this does NOT prove

- **The corpus is synthetic** (13 short handbook docs we wrote); retrieval over thousands of real, messy documents is a different problem.
- **The checks are structural**: the expected number/word is present, the right doc is cited, the right tool ran. They do not judge tone, completeness or hallucinated extras beyond the checked facts.
- **One run per backend, free-tier model**; model non-determinism moves pass counts by ±1–2. Latency includes Google API round trips from one laptop (or one Lambda cold/warm mix).
- **Tools are a demo Lambda over a JSON table**, not an HR system; the ticket tool returns a deterministic id.
- **v1 is Gemini, not Bedrock** (AWS Free plan); see `docs/V2-BEDROCK.md`.
