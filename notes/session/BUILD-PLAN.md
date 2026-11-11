# Build plan — Knowledge Agent v1 (Gemini + S3 Vectors + Lambda) — supersedes the Bedrock-only plan (kept in git history)

## Phase 0 — Skeleton + corpus + Lambda + eval scorer  ☑ 2026-11-11 (unchanged by the pivot)

## Phase 1 — v1 code + infra  ☐
- [ ] `src/ka`: gemini.py (embed, chat w/ tools, usage), index.py (S3 Vectors store + local numpy fallback), ingest.py (chunk → embed → put), tools.py (openapi.yml → Gemini function declarations; executor → Lambda invoke with the action-group event), agent.py (loop, retrieve tool, citations, confirmation gate), cli/api/ui
- [ ] `infra/` v1: docs bucket + objects, S3 Vectors bucket + index (768-d), tools Lambda, SSM param for the Gemini key, api Lambda + Function URL + token, IAM; `make lambda-zip` builds both zips (api zip bundles google-genai)
- [ ] tests: chunking, schema conversion, agent loop with a fake Gemini, index fallback, confirmation gate
- [ ] `docs/V2-BEDROCK.md`, `infra-bedrock-v2/` preserved
- Exit: `make test` green; `tofu plan` clean; `ka ask` works locally against a local numpy index built from `corpus/` (no AWS) with the real Gemini.

## Phase 2 — The AWS session (Free plan, ≈ ₹0)  ☐
- [ ] user: `make infra-apply` → Claude: `make env`, `make ingest` (S3 → chunks → Gemini → S3 Vectors), `ka retrieve`, `ka ask` smoke for each class
- [ ] `make eval` → `eval/report.md` + `results.json`; demo via the Function URL + `/ui`; evidence to `docs/`
- [ ] user: `make infra-destroy`; Claude verifies the account is empty; `make cost`
- Exit: measured numbers in README; `docs/aws-evidence.md`.

## Phase 3 — Interview material + resume rewrite  ☐
- [ ] `docs/GUIDE.md`, `docs/RUNBOOK.md` (updated), `INTERVIEW_PREP/01–06`, `DEMO.md`, `notes/BOOTSTRAP.md`, `notes/session/RESUME.md`
