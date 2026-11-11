# Progress (newest first)

## 2026-11-12 — PROJECT COMPLETE (v1); AWS destroyed and verified empty
- User ran `make infra-destroy` (28 destroyed). Verified: 0 buckets, 0 vector buckets, 0 Lambdas, 0 SSM params, tofu state
  empty. Spend $0.0000. Secrets repacked (now incl. infra/terraform.tfvars). Remaining user steps: token push, flip public.

## 2026-11-12 — AWS session done: ingest, public URL, eval 40/40; docs + interview prep written; destroy pending
- User applied v1 (28 resources). `make env` (after fixing write_env), `ka ingest --source s3` → S3 Vectors; retrieve ok;
  CLI kb + tool answers via S3 Vectors + Lambda; Function URL fixed (handler path, P-6) → /healthz 200, 401 without token,
  tool question answered publicly (24.7 s). Gemini 503s → retries + fallback model (P-7).
- **Eval (S3 Vectors + Lambda, gemini-3.5-flash-lite): 40/40 after a scorer fix (P-8; 39/40 raw), retrieval top-3 1.0,
  p50 7.4 s / p95 17.7 s, 1.9 LLM calls, 2,497/66 tokens per question, ≈$0.00028/q at list price. Cost Explorer: $0.0000.**
- Docs: GUIDE, RUNBOOK (v1), DEMO, BOOTSTRAP, INTERVIEW_PREP 01–06, aws-evidence, RESUME.md, README rewritten for v1.

## 2026-11-12 — local eval (scorer validation): 17/17 passed before the Gemini daily quota ran out (P-5)
- `eval/run_eval.py` against the local index: q01–q17 (all kb) PASS, p50 ≈ 3.5 s, 2 LLM calls and ~2.7k/50 tokens per
  question; then 429 on gemini-3.5-flash-lite. Switched to gemini-3.1-flash-lite for the AWS run. Report/runbook written.

## 2026-11-12 — PIVOT to v1 (Gemini + S3 Vectors + Lambda); Phase 1 code + infra done
- User declined the Paid-plan upgrade → D-15…D-19. Bedrock Terraform preserved in `infra-bedrock-v2/` + `docs/V2-BEDROCK.md`.
- v1: `src/ka` gemini.py / index.py (S3VectorsIndex + LocalIndex) / ingest.py / tools.py (openapi.yml → Gemini
  declarations; Bedrock-shaped event → Lambda or in-process) / agent.py (loop, retrieve tool, citations, confirmation
  gate in code) / lambda_api.py (Function URL) / cli / api / ui. 16 offline tests. `infra/` v1 plans at 28 resources
  (docs bucket, S3 Vectors 768-d, tools + api Lambdas, Function URL, SSM). api.zip 27.7 MB (google-genai + boto3).
- **Local smoke with real Gemini (local numpy index, in-process tools):** ingest 13 docs → chunks in one embed batch;
  retrieve ranks 01-leave-policy.md first (0.70); kb answer cites it (3.9 s, 2 LLM calls, 2,878/62 tok); tool answer
  calls GET /leave-balance (2.8 s); both-class answer = policy + tool (3.5 s); out-of-scope refused.

## 2026-11-12 — Phases 0 + 1 done; blocked on the Paid-plan upgrade + apply
- Phase 0: 13 handbook docs + 49 facts (verbatim-checked), Lambda with 4 tools + OpenAPI (x-requireConfirmation on the
  ticket tool), boto3 agent client with trace parsing + return-control confirmation, `ka` CLI, demo page, 40 questions
  (22 kb / 8 tool / 6 both / 4 oos) + deterministic scorer; 12 offline tests green; CI; repo pushed (private).
- Phase 1: `infra/` with aws provider 6.72.0 (S3 Vectors support): docs bucket + objects, S3 Vectors bucket + index
  (1024-d cosine), KB (Titan v2) + S3 data source (300-token chunks), Lambda, Agent (Nova 2 Lite via global profile) +
  action group + KB association + alias, least-privilege roles. `tofu validate` ok; `tofu plan` = 31 to add.
- Found: Bedrock quotas are 0 on the Free plan (P-1) → user must upgrade before apply.

## 2026-11-11 — planning
- Account probed (all services allowed; Nova 2 Lite + Titan v2 authorized). D-1…D-14 + plan written. Waiting for answers + "go".
