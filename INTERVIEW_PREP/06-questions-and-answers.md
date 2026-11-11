# 06 · Likely questions — answers in my voice

**Walk me through what happens when I ask "how much of my ₹1,200 meal claim is reimbursed?"**
Gemini gets the question plus five tool declarations. It calls `retrieve_handbook("meal reimbursement limit")`; I embed
the query, query S3 Vectors, and return the top passages with their doc names. It then calls `calculateReimbursement`
with category, amount and receipt flag; my executor turns that into the Bedrock-style action-group event and invokes
the Lambda, which applies the cap. The model writes the answer with the limit from the handbook and the number from
the tool; the expense policy doc is the citation.

**Why not just put the whole handbook in the prompt?**
Thirteen docs fit today, but the design has to work for thousands; retrieval keeps the prompt small, gives citations,
and makes "the model answered from this passage" checkable. The eval measures retrieval separately (top-3 hit rate).

**Why S3 Vectors?**
Zero idle cost, created and destroyed with Terraform in seconds, and it lives in the same account as the documents. An
OpenSearch cluster would cost more per day than this whole project.

**Where does Bedrock come in?**
It doesn't, in v1 — the Free plan zero-quotas Bedrock. I built and planned the Bedrock Knowledge Base + Agent version
(31 resources) and parked it with an upgrade doc. The Lambda contract and the OpenAPI schema are the Bedrock ones, so
the swap is the orchestrator only.

**How do you stop the model from doing something harmful?**
Only one tool mutates (file a ticket). It is flagged in the schema and the loop stops and asks before calling it; the
prompt also says so, but the gate is code. Everything else is read-only.

**How did you evaluate it?**
Forty questions, four classes. Each has expected facts, an expected cited doc, an expected tool and arguments, or a
refusal flag; a scorer checks them deterministically, and raw retrieval is checked for top-3 hits. The report lists
per-class pass counts, per-check pass rates, latency, tokens, and what it does not prove.

**What broke?**
The Lambda handler path in the zip; Gemini 503s and 40-second responses on the free tier; the daily quota shared with
another project; a YAML colon in the OpenAPI file. Each is in 04 with the fix and the lesson.

**What next?**
Bedrock v2 when the account is paid; hybrid search (keyword + vector); an LLM-judge for answer quality next to the
structural checks; streaming answers on the Function URL.
