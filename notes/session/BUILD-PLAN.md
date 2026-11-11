# Build plan — Bedrock Knowledge Agent

Order chosen so everything that costs nothing comes first and the AWS stack lives for one short session.

## Phase 0 — Skeleton + corpus + Lambda, all local  ☑ 2026-11-11
- [x] repo (`uv`, pinned deps, Makefile, `.env.example`, CI), `ka` CLI skeleton, secrets tooling copied from TripMate
- [x] `corpus/` 12 handbook docs (fictional company) with a `facts.yml` ground-truth sheet (every number/rule we will ask about)
- [x] `lambda/handler.py`: 4 tools over a bundled JSON table; `lambda/openapi.yml` action-group schema; unit tests
- [x] `eval/questions.yml` (~40) + `eval/score.py` with unit tests on canned agent outputs
- Exit: `make test` green offline; `make corpus-check` proves every fact in questions.yml appears in the corpus.

## Phase 1 — Infra as code (planned, not applied)  ☑ 2026-11-11 (plan: 31 to add)
- [x] `infra/`: S3 docs bucket (+ upload of `corpus/`), S3 Vectors bucket + index, KB (Titan v2) + S3 data source, Lambda + role, Agent (Nova 2 Lite) + action group + alias, IAM roles/policies with least privilege, outputs
- [x] `make infra-plan` clean; `make kb-sync` (start ingestion job + wait), `make cost`
- Exit: `tofu plan` shows the full stack; cost estimate documented in RUNBOOK.

## Phase 2 — The one AWS session (billable, ~1 h)  ☐
- [ ] user: `make infra-apply` → Claude: `make kb-sync`, `ka retrieve`, `ka ask` smoke for each question class, fix prompts/schema as needed (re-apply is in-place)
- [ ] `make eval` → `eval/report.md` + `results.json`; screenshots/traces into `docs/`
- [ ] user: `make infra-destroy`; Claude verifies the account is empty and `make cost` after
- Exit: measured numbers in the README; evidence in `docs/aws-evidence.md`.

## Phase 3 — Interview material + resume rewrite  ☐
- [ ] `docs/GUIDE.md`, `docs/RUNBOOK.md`, `INTERVIEW_PREP/01–06`, `DEMO.md`, `notes/BOOTSTRAP.md`, resume lines with numbers
- Exit: user can explain and re-run everything from the repo alone.
