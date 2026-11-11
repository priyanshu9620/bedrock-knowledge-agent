# Progress (newest first)

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
