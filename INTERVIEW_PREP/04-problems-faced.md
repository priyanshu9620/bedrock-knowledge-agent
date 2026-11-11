# 04 · Problems faced — symptom → cause → fix → lesson

Real errors from building this (source: `notes/session/PROBLEMS.md`), as interview stories.

## P-1 — Every Bedrock invocation throttled: "Too many tokens per day" — quotas are 0
`get-account-plan-state` → `FREE`; Service Quotas shows e.g. "Global cross-region model inference tokens per day for Amazon Nova 2 Lite = 0", "On-demand model inference requests per minute for Titan Text Embeddings V2 = 0", **Adjustable = False**. Even the embeddings call (needed for KB ingestion) is blocked. Fix: the account must be upgraded to the Paid plan (credits keep applying). Lesson: probe the *invocation* path (one tiny converse call) before designing around a service — "allowed by the SCP" and "has quota" are different questions.

## P-2 — Nova 2 Lite is INFERENCE_PROFILE-only in Sydney
(no on-demand). The agent's `foundation_model` must be the inference-profile ARN (`global.amazon.nova-2-lite-v1:0`), and the agent role needs both the profile ARN and `foundation-model/*` ARNs because a global profile routes to other regions.

## P-3 — Provider 5.82.2 has no S3 Vectors; 6.72.0 downloaded from releases.hashicorp.com (SHA256-verified) into the local mirror
(GitHub release assets hang on this network, ShopEase P-20).

## P-4 — `uv add` failed after I deleted `src/ka` created by `uv init`
(Pager-Zero P-3 again). Recreate the package first.

## P-5 — Local eval died at q18 with Gemini `429 RESOURCE_EXHAUSTED`
— the `gemini-3.5-flash-lite` daily request quota was already spent by TripMate's benchmark + demos earlier the same day (shared key, per-model ~500 req/day, reset ≈ 13:30 IST). 17/17 questions had passed before that, which is what the local run was for (scorer validation). `gemini-2.5-flash-lite` hung (>60 s); **`gemini-3.1-flash-lite` works with tool calling and has its own bucket** → used for the AWS session (`.env` + `infra/terraform.tfvars`). Lesson (again, Pager-Zero P-29): the free-tier unit is requests per model per day; keep one model's bucket untouched for the run that matters, and make the model a one-line config.

## P-6 — Public Function URL returned "Internal Server Error" even on /healthz
CloudWatch: `Runtime.ImportModuleError: No module named 'lambda_api'` — the zip puts the file at `ka/lambda_api.py`, so the handler must be `ka.lambda_api.handler`. Fixed live (`aws lambda update-function-configuration`) and in `main.tf`. Lesson: check a Lambda's import path against the zip layout, and smoke `/healthz` right after apply — the log told the whole story in one line.

## P-7 — Gemini `503 UNAVAILABLE` / slow responses (10–50 s) during the evening
The tool question failed once in the CLI and once via the Function URL with the same ServerError. Fix: `_retry` with exponential backoff on 429/5xx (2,4,8,16 s) and an automatic fallback model (`GEMINI_FALLBACK_MODEL`, 3.1-flash-lite) when the primary keeps failing; counted in `fallbacks_used`. Lesson: on a free tier the model is the least reliable component — the client must own retries and a fallback, not the caller.

## The three I'd lead with

1. **P-1, Bedrock quotas are zero on the AWS Free plan.** Discovered by a one-token smoke call, not by reading docs. It changed the architecture: keep S3, S3 Vectors and Lambda, move the model to Gemini, park Bedrock as a planned v2. Probe the invocation path before designing around a service.
2. **P-6, the Lambda handler path.** `/healthz` said Internal Server Error; one CloudWatch line said `No module named 'lambda_api'`. The zip layout and the handler string must agree. Smoke the health route right after apply.
3. **P-7, free-tier model reliability.** 503s and 40-second answers in the evening. Retries with backoff and an automatic fallback model belong in the client; the eval runner also aborts on three consecutive errors so a quota outage never produces a fake result.
