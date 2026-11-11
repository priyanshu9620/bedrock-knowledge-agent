# Knowledge Agent — the manual

Self-contained: configuration, every command, the API, how a question flows, troubleshooting. Related: [`RUNBOOK.md`](RUNBOOK.md)
(the AWS session), [`V2-BEDROCK.md`](V2-BEDROCK.md) (the parked Bedrock version), [`../DEMO.md`](../DEMO.md).

## 1. Two modes, one code path
| | local mode | AWS mode |
|---|---|---|
| documents | `corpus/*.md` | S3 bucket `handbook/*.md` |
| vector index | numpy file `.ka/index.npz` | Amazon S3 Vectors index |
| tools | `lambda/handler.py` in-process | Lambda `knowledge-agent-tools` (invoked with the Bedrock action-group event) |
| agent | Gemini tool-calling loop (`src/ka/agent.py`) | same code, in the CLI or in Lambda `knowledge-agent-api` behind a Function URL |
| switch | `.env` has only `GOOGLE_API_KEY` | `make env` fills `VECTOR_BUCKET`, `TOOLS_LAMBDA`, `API_URL`, `API_TOKEN` |

## 2. Configuration (`.env`, template `.env.example`)
| key | meaning | default |
|---|---|---|
| `GOOGLE_API_KEY` | Gemini key (free tier) | — |
| `GEMINI_MODEL` / `GEMINI_FALLBACK_MODEL` | agent model / used after repeated 429/5xx | `gemini-3.5-flash-lite` / `gemini-3.1-flash-lite` |
| `EMBEDDING_MODEL` / `EMBEDDING_DIMENSION` | embeddings | `gemini-embedding-001` / 768 |
| `AWS_PROFILE` / `AWS_REGION` | boto3 session | `shopease` / `ap-southeast-2` |
| `DOCS_BUCKET`, `VECTOR_BUCKET`, `VECTOR_INDEX`, `TOOLS_LAMBDA`, `API_URL`, `API_TOKEN` | AWS mode ids | empty = local |
| `RETRIEVE_TOP_K` / `MAX_STEPS` | chunks per retrieval / tool-loop cap | 4 / 6 |

## 3. Commands
| command | what |
|---|---|
| `make test` · `make lint` · `make corpus-check` | 16 offline tests · ruff · every fact in `facts.yml` is verbatim in its doc and every cited doc exists |
| `uv run ka ingest [--source s3]` | chunk (≈1,200 chars, 200 overlap, title-prefixed) → embed → index |
| `uv run ka retrieve "…" --top-k 4` | raw vector search with cosine scores |
| `uv run ka ask "…" [--session id] [--confirm]` | one question; prints answer, citations, tool calls, tokens; `--confirm` auto-approves mutating tools |
| `uv run ka ask yes --session <id>` | confirm a pending mutating tool (the ticket) |
| `make serve` → http://127.0.0.1:8001/ui | local demo page (same page the Function URL serves at `/ui?token=…`) |
| `make eval` · `make report` | 40 questions → `eval/out/eval-<ts>.json` · `eval/report.md` + `results.json` + README table |
| `make lambda-zip` | `tools.zip` (handler + data) and `api.zip` (src/ka + google-genai + boto3 for python3.12/x86_64) |
| `make infra-plan/apply/destroy/output` · `make env` · `make cost` | AWS (user applies/destroys) · ids → .env · Cost Explorer MTD |
| `make secrets-pack/unpack` | encrypted archive of `.env`, tfvars, tfstate, AWS profile |

## 4. HTTP API (local `:8001`, or the Function URL)
| endpoint | body → result |
|---|---|
| `POST /ask` | `{question, session_id?, confirm?}` → `{text, citations:[{doc, snippet, score}], tool_calls:[{api, method, params, result}], retrieved_docs, confirmation_requested, input_tokens, output_tokens, llm_calls, latency_s, session_id}` |
| `GET /healthz` | mode / model / index |
| `GET /ui` | chat page; on the Function URL add `?token=<API_TOKEN>` (sent as `X-Api-Token`) |

## 5. How a question flows
1. The agent sends the system instruction (`src/ka/instruction.txt`), the conversation and the tool declarations to Gemini.
   Declarations = `retrieve_handbook` + the four operations from `lambda/openapi.yml` converted by `tools.py`.
2. Gemini returns text, or one or more function calls. `retrieve_handbook` → embed the query → index query → passages
   with their doc names go back as the function response; the docs become the answer's citations. People-ops tools →
   `ToolExecutor` builds the Bedrock action-group event and invokes the Lambda (or the handler in-process).
3. `fileHelpdeskTicket` is marked `x-requireConfirmation` in the schema: the loop stops and asks; `yes` on the same
   session executes it. `--confirm` / `confirm: true` skips the pause but still records that a gate applied.
4. Loop cap `MAX_STEPS`; usage (tokens, LLM calls) is summed per answer.

## 6. Troubleshooting
| symptom | cause / fix |
|---|---|
| `429 RESOURCE_EXHAUSTED` | Gemini free quota (per model, per day/minute); retries + fallback model handle bursts; otherwise wait for the reset (~13:30 IST) or set another `GEMINI_MODEL` |
| `503 UNAVAILABLE` / 20–50 s answers | model overloaded; the client retries 2/4/8/16 s then falls back |
| `ResourceNotFoundException` (s3vectors) | stale ids → `make env` |
| Function URL 401 | `X-Api-Token` ≠ `API_TOKEN` |
| Function URL 502/500 | `aws logs filter-log-events --log-group-name /aws/lambda/knowledge-agent-api` — the first error line says it |
| `make lambda-zip` fails on `uv pip install --target` | needs network; the api zip bundles google-genai + boto3 for x86_64 |
| `git push` rejected | work credential helper → token one-off (see TripMate GUIDE §6) |
