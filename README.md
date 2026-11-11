# Bedrock Knowledge Agent — grounded Q&A over documents on AWS

> A fictional company handbook (13 Markdown docs) lives in S3 and is indexed by an Amazon Bedrock Knowledge Base
> (Titan Embeddings v2, S3 Vectors). A Bedrock Agent (Amazon Nova 2 Lite) answers questions with citations and calls
> four Lambda tools through an action group — leave balance, reimbursement math, holiday calendar, helpdesk ticket
> (confirmation required). Everything is OpenTofu; the stack lives for one evaluation session and is destroyed.

## Measured numbers
<!-- numbers:start -->
_not yet — `make eval` then `make report` during the AWS session_
<!-- numbers:end -->

## Run it
```
uv sync && make test && make corpus-check          # offline: Lambda handler, scorer, corpus ↔ questions
make infra-plan && make infra-apply                # AWS (billable, user runs): S3, S3 Vectors, KB, Lambda, Agent
make env && make kb-sync                           # ids → .env; embed the corpus
uv run ka ask "How many casual leaves do I get?"   # or: make serve → http://127.0.0.1:8001/ui
make eval && make report                           # 40 questions → eval/report.md
make infra-destroy && make cost                    # tear down; verify spend
```

## Roadmap
0 skeleton + corpus + Lambda + eval scorer ✔ · 1 infra as code · 2 the AWS session (sync, eval, report) · 3 docs + interview prep
