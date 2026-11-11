# 02 · Features — what, how, where

| feature | how | file |
|---|---|---|
| Corpus with ground truth | 13 handbook docs + `facts.yml`; `eval/corpus_check.py` asserts every fact is verbatim in its doc | `corpus/` |
| Chunking | paragraph-aware, ≈1,200 chars, 200 overlap, doc title prefixed to each chunk | `src/ka/ingest.py` |
| Embeddings | `gemini-embedding-001`, 768-d, batched 50/call, task types `RETRIEVAL_DOCUMENT` / `RETRIEVAL_QUERY` | `src/ka/gemini.py` |
| Vector store | Amazon S3 Vectors (`put_vectors` / `query_vectors`, cosine, metadata doc+text) with a numpy local twin | `src/ka/index.py` |
| Tools from OpenAPI | `operationId` → Gemini function declaration (types, required, descriptions); `x-requireConfirmation` → gate | `src/ka/tools.py`, `lambda/openapi.yml` |
| Bedrock-shaped Lambda contract | executor builds `{apiPath, httpMethod, parameters, requestBody}`; handler returns the action-group response | `src/ka/tools.py`, `lambda/handler.py` |
| Agent loop | system instruction + declarations → function calls → results → final text; step cap; usage summed | `src/ka/agent.py`, `src/ka/instruction.txt` |
| Citations | docs of the passages retrieved during the answer, with scores and snippets | `src/ka/agent.py` |
| Confirmation gate | mutating tool → loop stops with `confirmation_requested`; `yes` on the session executes; `confirm` flag for eval | `src/ka/agent.py` |
| Resilience | retry 429/5xx with backoff; automatic fallback model | `src/ka/gemini.py` |
| Public API | Lambda Function URL handler, `X-Api-Token` from SSM, Gemini key from SSM at cold start | `src/ka/lambda_api.py`, `infra/main.tf` |
| CLI / local API / page | `ka ingest/retrieve/ask/serve`; FastAPI `/ask`; one static page | `src/ka/cli.py`, `api.py`, `ui/index.html` |
| Evaluation | 40 questions × deterministic checks; retrieval top-3; abort on 3 consecutive errors; generated report | `eval/` |
| Infra as code | S3 docs + objects, S3 Vectors bucket/index, 2 Lambdas, Function URL, SSM, least-privilege roles | `infra/` |
| Parked Bedrock v2 | KB + Agent + action group + alias Terraform, validated, planned | `infra-bedrock-v2/`, `docs/V2-BEDROCK.md` |
| Portability | notes + memory in repo, encrypted secrets archive | `notes/`, `scripts/secrets.sh` |
