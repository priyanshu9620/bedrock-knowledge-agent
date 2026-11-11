# Demo — 2 minutes

**Local (no AWS):** `uv run ka ingest && make serve` → http://127.0.0.1:8001/ui
**AWS:** after the runbook's "Up": open `<API_URL>ui?token=<API_TOKEN>`.

Ask, in this order, and say:
1. `How many casual leave days do I get per year?` — "Policy question: the agent searched the handbook, answered with the
   number and cited the leave policy. Retrieval is Gemini embeddings in Amazon S3 Vectors."
2. `What is the leave balance of employee E1001?` — "Live data: the model chose the tool; the call went to a Lambda with the
   exact event shape a Bedrock action group would send. The tool definitions come from one OpenAPI file."
3. `I claimed ₹3,000 for one day of international meals with receipts. What's the limit and how much do I get?` —
   "Both: the limit from the handbook, the arithmetic from the tool. Capped at ₹2,500."
4. `What is the capital of France?` — "Out of scope: it refuses instead of answering; scored in the eval."
5. `Please file a P2 helpdesk ticket for E1002: VPN cannot connect from home.` → it asks to confirm → `yes` —
   "Mutating action: code-enforced confirmation gate, then the ticket id."
Close with `eval/report.md`: 40 questions, four classes, deterministic checks, and what the numbers do not prove.
