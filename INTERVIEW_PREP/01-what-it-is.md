# 01 · What it is

**Problem.** People ask the same policy questions over and over, and the real answers mix a rule ("meals are capped at
₹800/day") with live data ("how much of *my* ₹1,200 claim is reimbursed?"). A plain chatbot invents numbers; a plain
search cannot do arithmetic or look up a balance.

**Solution.** A grounded assistant: the handbook (13 Markdown docs) lives in S3 and is indexed as Gemini embeddings in
Amazon S3 Vectors; a Gemini tool-calling agent retrieves passages and cites them, and calls four people-ops tools
running in Lambda (leave balance, reimbursement calculation, holiday calendar, helpdesk ticket). The tool definitions
come from one OpenAPI file — the same file a Bedrock action group would consume — and the Lambda receives the Bedrock
action-group event shape, so the parked Bedrock version (v2) swaps only the orchestrator. The mutating tool (ticket)
is gated by a code-enforced confirmation. A second Lambda behind a Function URL serves the same agent publicly with a
token. Everything is OpenTofu; the stack is created, evaluated and destroyed in one session on the AWS Free plan.

**Why Gemini and not Bedrock.** The account is on the AWS Free plan, which sets every Bedrock invocation quota to zero
and makes them non-adjustable. I kept every AWS piece the plan allows and moved only the model calls. The Bedrock
Terraform is written, validated and planned (31 resources) in `infra-bedrock-v2/` with a step-by-step upgrade doc.

**Numbers (measured, `eval/report.md`).** 40 questions in four classes scored by deterministic rules — see the report
for pass counts by class, retrieval top-3 hit rate, p50/p95 latency and tokens per question.

**2-minute demo.** `DEMO.md`: policy question with citation → tool question through Lambda → both → refusal → ticket with
confirmation. Say: "retrieve, cite, call tools, confirm before mutating, measure, destroy."
