# Knowledge Agent — grounded Q&A over documents on AWS (v1: Gemini + S3 Vectors + Lambda)

> A fictional company handbook (13 Markdown docs) lives in S3 and is indexed as Gemini embeddings in **Amazon S3 Vectors**.
> A Gemini tool-calling agent retrieves and cites passages and calls four **Lambda** tools defined by one OpenAPI schema —
> leave balance, reimbursement math, holiday calendar, helpdesk ticket (code-enforced confirmation). A second Lambda
> behind a Function URL serves it publicly. Everything is OpenTofu; the stack lives for one session and is destroyed.
>
> **v2 (parked):** the same thing on Bedrock Knowledge Bases + a Bedrock Agent with action groups — Terraform written,
> validated and planned in [`infra-bedrock-v2/`](infra-bedrock-v2/); the AWS Free plan zero-quotas Bedrock, see
> [`docs/V2-BEDROCK.md`](docs/V2-BEDROCK.md).

```
 corpus/*.md ─► S3 ─► ka ingest: chunk → Gemini embeddings ─► S3 Vectors (768-d cosine)
 question ─► agent (Gemini tool-calling loop) ─► retrieve_handbook ─► cited answer
                      └─► people-ops tools (OpenAPI) ─► Lambda `tools`   ·   public: Lambda `api` + Function URL (token)
```

## Measured numbers
<!-- numbers:start -->
| backend | passed | retrieval top-3 hit | p50 / p95 | per question |
|---|---|---|---|---|
| S3 Vectors + Lambda · gemini-3.5-flash-lite + gemini-embedding-001 | **40/40** (kb 22/22, tool 8/8, both 6/6, oos 4/4) | 1.0 | 7.39 s / 17.73 s | 1.9 LLM calls, 2497/66 tokens |

Full report with per-check table, failed questions and what the numbers do **not** prove: [`eval/report.md`](eval/report.md) · raw: [`eval/results.json`](eval/results.json).
<!-- numbers:end -->

## Run it
```
uv sync && make test && make corpus-check          # offline: 16 tests; every fact verbatim in its doc
uv run ka ingest && uv run ka ask "How many casual leaves do I get?"   # LOCAL: numpy index + tools in-process (only a Gemini key)
make infra-plan && make infra-apply                # AWS (user runs): S3 docs, S3 Vectors, 2 Lambdas, Function URL, SSM
make env && make ingest-s3                         # ids → .env; S3 docs → S3 Vectors
make serve                                         # http://127.0.0.1:8001/ui   (or <API_URL>ui?token=…)
make eval && make report                           # 40 questions → eval/report.md
make infra-destroy && make cost                    # tear down; verify $0
```

## Docs
[`docs/GUIDE.md`](docs/GUIDE.md) · [`docs/RUNBOOK.md`](docs/RUNBOOK.md) · [`DEMO.md`](DEMO.md) · [`docs/aws-evidence.md`](docs/aws-evidence.md) · [`INTERVIEW_PREP/`](INTERVIEW_PREP/) · [`eval/report.md`](eval/report.md) · [`docs/V2-BEDROCK.md`](docs/V2-BEDROCK.md)

## Roadmap
0 skeleton + corpus + Lambda + eval ✔ · 1 v1 code + infra ✔ · 2 AWS session: ingest, eval 40/40, destroy ✔ · 3 docs + interview prep ✔ · next: Bedrock v2 (paid plan), hybrid search, LLM-judge quality score
