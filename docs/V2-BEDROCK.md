# v2 — the Bedrock version (parked; build when the account is on the AWS Paid plan)

**Read this first in a future session.** v1 (this repo's `src/ka`, `infra/`) runs the model side on Gemini because the
AWS Free plan sets all Bedrock invocation quotas to 0 (notes P-1). Everything below is ready for the day the account is
upgraded (Billing → Account plan → Upgrade; credits keep applying).

## What is already done for v2
- `infra-bedrock-v2/` — complete OpenTofu for: S3 docs bucket, S3 Vectors index (1024-d for Titan v2), Bedrock
  Knowledge Base (Titan Embeddings v2) + S3 data source (300-token chunks), the tools Lambda, the Bedrock Agent
  (Nova 2 Lite via the `global.` inference profile — it is INFERENCE_PROFILE-only in ap-southeast-2) + action group
  (`lambda/openapi.yml`) + KB association + alias, least-privilege roles. `tofu validate` passed; `tofu plan` = 31 to add
  (2026-11-11, provider aws 6.72.0 from the local mirror). Never applied.
- `infra-bedrock-v2/instruction.txt` — the agent instruction.
- `lambda/handler.py` + `lambda/openapi.yml` — identical for v1 and v2 (the Lambda receives the Bedrock action-group
  event shape in both).
- `eval/questions.yml` + `eval/score.py` — identical; the scorer reads `Answer.as_dict()`.
- `git show <phase-1 commit>:src/ka/client.py` — the Bedrock Agent Runtime client (invoke_agent trace parsing:
  usage, tool calls, KB lookups, citations; return-control confirmation; `retrieve`; `kb_sync`). It was removed from
  `src/ka` in the pivot; restore it as `src/ka/bedrock_client.py`.

## Steps for the future session
1. Confirm quotas: `aws bedrock-runtime converse --model-id global.amazon.nova-2-lite-v1:0 …` must not throttle;
   `aws bedrock get-foundation-model-availability --model-id amazon.titan-embed-text-v2:0` → AUTHORIZED.
2. `cd infra-bedrock-v2 && tofu init && tofu plan` (mirror in `~/.tofurc`); user applies.
3. `make env` equivalent: write `KNOWLEDGE_BASE_ID`, `AGENT_ID`, `AGENT_ALIAS_ID` to `.env`; `kb_sync()` → ingestion job.
4. Add a `--backend bedrock|gemini` switch to `ka ask` / `eval/run_eval.py` that selects `bedrock_client.AgentClient`
   vs the v1 `agent.Agent`; both return the same `Answer` shape, so the scorer and report need no change.
5. Run `make eval` for both backends → the report gets a second row; rewrite the resume line to claim Bedrock.
6. Destroy; verify `list-agents` and `list-knowledge-bases` are empty; `make cost`.

Expected cost: embedding 13 docs + ~60 agent questions on Nova 2 Lite ≈ $0.30–0.50 against credits.
