# Resume lines — v1, with measured numbers (2026-11-12)

**Knowledge Agent: RAG Assistant on AWS** | Python, Gemini, Amazon S3 Vectors, Lambda, OpenTofu · 2026 · github.com/priyanshu9620/bedrock-knowledge-agent

- Designed and delivered grounded question answering over documents on AWS: a 13-document handbook in S3 indexed as
  Gemini embeddings in Amazon S3 Vectors, and a Gemini tool-calling agent that retrieves and cites passages and calls 4
  Lambda tools defined by one OpenAPI schema (leave balance, reimbursement math, holidays, ticketing with a code-enforced
  confirmation gate); served publicly from a Lambda Function URL.
- Measured answer quality on a 40-question set with deterministic checks (facts, citations, tool + arguments, refusals):
  40/40 passed, retrieval top-3 hit rate 100%, p50 7.4 s, ≈2 LLM calls and 2.5k tokens per question; whole stack is
  infrastructure-as-code, created and destroyed in one session at $0 (AWS Free plan + Gemini free tier).

v2 (parked, documented): Bedrock Knowledge Base + Bedrock Agent with action groups — `docs/V2-BEDROCK.md`.
Numbers: `eval/report.md`, `eval/results.json`, `docs/aws-evidence.md`.
