---
name: bedrock-knowledge-agent-project
description: Bedrock Knowledge Agent resume project #4 (RAG on AWS Bedrock KB + Agent + Lambda tools) — repo ~/Desktop/bedrock-knowledge-agent with notes inside; planning done 2026-11-11, awaiting user's answers + "go"
metadata:
  type: project
---

Fourth "make my resume project real" project, started 2026-11-11 right after TripMate. Lines borrowed as writeup; nothing existed. Repo `~/Desktop/bedrock-knowledge-agent` (notes in `notes/`, read `notes/session/HANDOFF.md` first); GitHub `priyanshu9620/bedrock-knowledge-agent` (to be created, private at first).

Status 2026-11-12: Phases 0+1 done + pushed (private); plan = 31 resources. BLOCKED: account is on AWS Free plan → Bedrock quotas 0, not adjustable (P-1); user must upgrade to Paid plan then make infra-apply; then Claude: make env, kb-sync, eval, report. Key facts: account allows bedrock/bedrock-agent/lambda/s3/s3vectors/opensearchserverless in ap-southeast-2; Nova 2 Lite + Titan Embed v2 authorized, Claude models NOT_AVAILABLE; vector store = S3 Vectors (OpenSearch Serverless fallback, costly); corpus = synthetic company handbook; 4 Lambda tools; eval = ~40 questions, deterministic scoring. Budget < $2, one AWS session then destroy.

**Why:** same method as [[tripmate-project]]; user wants everything portable in the repo.
**How to apply:** reuse TripMate conventions (commit to main, token-header push, secrets.tar.enc, Claude never applies/destroys). Open questions for the user: corpus domain OK?, tool list OK?, budget OK?, repo name, "go".
