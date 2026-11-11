# 05 · Codebase map — and where to add a new X

```
src/ka/        config.py (settings; empty AWS ids = local mode) · gemini.py (embed, chat, retry, fallback)
               index.py (S3VectorsIndex, LocalIndex) · ingest.py (load_docs local|s3, chunk, ingest)
               tools.py (openapi.yml → ToolSpec → declarations; action_group_event; ToolExecutor Lambda|in-process)
               agent.py (Agent.ask/retrieve, loop, citations, confirmation gate) · instruction.txt (system prompt)
               lambda_api.py (Function URL handler) · api.py (local FastAPI) · cli.py (`ka`) · ui/index.html
lambda/        handler.py (4 tools over data.json, Bedrock action-group plumbing) · openapi.yml · data.json · build/ (zips)
corpus/        13 handbook docs + facts.yml       eval/   questions.yml · score.py · corpus_check.py · run_eval.py · report.py · out/
infra/         v1 OpenTofu (S3, S3 Vectors, 2 Lambdas, URL, SSM)     infra-bedrock-v2/  the parked Bedrock stack
tests/         16 offline tests (lambda, scorer, tools/agent with a fake Gemini, local index)
docs/          GUIDE · RUNBOOK · V2-BEDROCK · aws-evidence       notes/  project memory + BOOTSTRAP
```

**Add a tool.** One path in `lambda/openapi.yml` (operationId, params, description; `x-requireConfirmation: ENABLED` if
it mutates) + one function and route in `lambda/handler.py` + a test in `tests/test_lambda.py`. The agent picks it up
automatically; add an eval question with `expect.tool`.
**Add documents.** Drop `.md` files in `corpus/`, add their facts to `facts.yml`, `make corpus-check`, `ka ingest`.
**Change the model.** `.env` (`GEMINI_MODEL`, fallback) and `infra/terraform.tfvars` for the api Lambda.
**Swap the vector store.** Implement `upsert/query/count` in `index.py` and pick it in `make_index()`.
**Go to Bedrock.** `docs/V2-BEDROCK.md`.
