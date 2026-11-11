---
name: bedrock-knowledge-agent-project
description: Bedrock Knowledge Agent resume project #4 (RAG on AWS Bedrock KB + Agent + Lambda tools) — repo ~/Desktop/bedrock-knowledge-agent with notes inside; planning done 2026-11-11, awaiting user's answers + "go"
metadata:
  type: project
---

Fourth "make my resume project real" project, started 2026-11-11 right after TripMate. Lines borrowed as writeup; nothing existed. Repo `~/Desktop/bedrock-knowledge-agent` (notes in `notes/`, read `notes/session/HANDOFF.md` first); GitHub `priyanshu9620/bedrock-knowledge-agent` (to be created, private at first).

Status 2026-11-12 night: PIVOTED to v1 = Gemini (3.5-flash-lite + gemini-embedding-001) + Amazon S3 Vectors + Lambda tools + Lambda Function URL, because the AWS Free plan zero-quotas Bedrock (user declined adding a card). Deployed, evaluated 40/40 (retrieval top-3 1.0, p50 7.4 s), documented (GUIDE/RUNBOOK/DEMO/INTERVIEW_PREP/RESUME). Pending: user `make infra-destroy` + secrets-pack + push; flip repo public. Bedrock v2 parked in infra-bedrock-v2/ + docs/V2-BEDROCK.md.

**Why:** same method as [[tripmate-project]]; user wants everything portable in the repo.
**How to apply:** reuse TripMate conventions (commit to main, token-header push, secrets.tar.enc, Claude never applies/destroys). Open questions for the user: corpus domain OK?, tool list OK?, budget OK?, repo name, "go".
