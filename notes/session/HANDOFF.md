# HANDOFF — read this first

**Project:** Bedrock Knowledge Agent — RAG assistant on AWS: documents in S3 indexed by a Bedrock Knowledge Base, a
Bedrock Agent that answers grounded questions and calls Lambda tools through action groups. Resume project #4 for
Priyanshu Gupta (lines borrowed as a writeup; nothing existed). **Code + notes:** `~/Desktop/bedrock-knowledge-agent`
(this repo; GitHub `priyanshu9620/bedrock-knowledge-agent`, private until the demo works).

## Resume lines this must satisfy (verbatim, 2026-11-11)
Bedrock Knowledge Agent: RAG Assistant | AWS Bedrock, S3, Lambda · 2026
- Designed and delivered grounded question answering over documents, by building a retrieval-augmented assistant on AWS:
  documents in S3 indexed by Bedrock Knowledge Bases, with a Bedrock Agent calling Lambda tools via action groups.
- Tested answer quality on sample questions, by designing tool schemas and prompts, then tore down cloud resources to
  control cost.
Numbers get measured (D-7) and the lines rewritten at the end.

## Where we are
**2026-11-12 night:** v1 (Gemini + S3 Vectors + Lambda, D-15…D-19) built, deployed, evaluated 40/40, documented. AWS destroyed and verified empty; secrets repacked. Remaining: user pushes (token one-off) and flips the repo public.
Bedrock v2 parked: `docs/V2-BEDROCK.md` + `infra-bedrock-v2/`.

## Audit facts (read-only probes, profile `shopease`, ap-southeast-2)
- Allowed by the SCP: bedrock (81 models), bedrock-agent (KBs, agents), lambda, s3, opensearchserverless, s3vectors, iam roles.
- Model access without any form: `amazon.nova-2-lite-v1:0` (agent) and `amazon.titan-embed-text-v2:0` (embeddings) —
  AVAILABLE/AUTHORIZED. `anthropic.claude-haiku-4-5` is NOT_AVAILABLE (marketplace agreement) → not used.
- Cost Explorer readable; month-to-date spend $0. Account currently empty (TripMate + ShopEase destroyed).
- Everything else we need already exists from TripMate: OpenTofu + provider mirror, profile, gh account, secrets tooling.

## How to work
1. `DECISIONS.md` append-only; `BUILD-PLAN.md` phase order; `PROBLEMS.md`/`PROGRESS.md` after every milestone.
2. Commit directly to `main` (D-19 of TripMate carries over). Push with the personal token one-off (TripMate GUIDE §6).
3. Billable = anything that creates AWS resources or invokes Bedrock: Claude prepares + plans, the user applies/runs;
   Claude verifies afterwards. Target total spend for the whole project < $2.

## Single next command
None required after the push. Optional: Bedrock v2 (docs/V2-BEDROCK.md) when the account is on the Paid plan; hybrid search; LLM-judge score.
