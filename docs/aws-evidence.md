# AWS evidence — v1 session (2026-11-12 IST)

Stack: `infra/` (OpenTofu, aws 6.72.0), ap-southeast-2, Free plan, 28 resources applied by the user (`tofu state list` = 29 entries
incl. the data source). Month-to-date spend before the session: $0.0000 (Cost Explorer).

| what | evidence |
|---|---|
| Documents in S3 | bucket `knowledge-agent-docs-3f441effa755cb34eeba7d3afb`, 13 handbook objects under `handbook/` |
| Index in Amazon S3 Vectors | bucket `knowledge-agent-vectors-459514902118`, index `handbook` (768-d, cosine); `ka ingest --source s3` embedded the 13 docs with gemini-embedding-001 in one batch |
| Retrieval from S3 Vectors | `ka retrieve "how many casual leave days"` → 01-leave-policy.md 0.6959, 12-glossary.md 0.6414, 08-holidays.md 0.6292 |
| Policy answer with citation (CLI → S3 Vectors) | "Employees receive 12 casual leave (CL) days per year …" citing 01-leave-policy.md · 2 LLM calls, 2,878/59 tokens |
| Tool call through the tools Lambda | GET /leave-balance/{employee_id} E1001 → Asha Rao, CL 7 / EL 21.5 / SL 9 |
| Public Function URL | `https://znuuwjhl7frajikam23yefio3a0ngujk.lambda-url.ap-southeast-2.on.aws/` — `/healthz` 200; `/ask` without the token → 401; with the token: the E1001 balance question answered via the tools Lambda in 24.7 s (2 LLM calls) |

Fixed during the session (notes P-6, P-7): the api Lambda handler path (`ka.lambda_api.handler`); transient Gemini
503/429 → retry with backoff + automatic fallback model. Both hot-patched with `aws lambda update-function-*` and
mirrored in `infra/main.tf`, so the next `tofu plan` shows no drift.

Evaluation: see `eval/report.md` (filled after `make eval` + `make report`).

## Evaluation (run 20261111-173336, through S3 Vectors + the tools Lambda)
**40/40 questions passed** (kb 22/22 · tool 8/8 · both 6/6 · oos 4/4) · retrieval top-3 hit rate 1.0 · p50 7.4 s / p95 17.7 s ·
1.9 LLM calls and 2,497 in / 66 out tokens per question · ≈ $0.00028/question at list price (free tier: $0).
The run first scored 39/40: q26's answer "the reimbursement amount is ₹0." failed a whole-number match because of the
sentence-ending period — a scorer bug (notes P-8), fixed with a unit test and re-scored from the stored answers
(`eval/rescore.py`); the model outputs were not touched.
Cost Explorer after the session: month-to-date $0.0000.
