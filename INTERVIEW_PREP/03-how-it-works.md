# 03 · Concepts — what, why, trade-offs

**RAG (retrieval-augmented generation).** Embed chunks once, embed the question at query time, take the nearest chunks,
hand them to the model with the question. Why: the model answers from *your* text and can cite it; no fine-tuning.
Trade-offs: chunking and embeddings decide quality; the model can still ignore the passages (hence the fact checks).

**Embeddings + cosine similarity.** Text → 768 numbers; closeness ≈ meaning. We normalise and use cosine. Smaller
dimension (768 vs 3072) = cheaper storage and queries with little loss for short policy text.

**Amazon S3 Vectors.** A vector index as an S3-native resource: pay per request and storage, no cluster, no idle cost —
the reason this project fits a free plan where OpenSearch Serverless (≈$5+/day minimum) does not. Trade-off: higher
query latency than an in-memory index and fewer features (no hybrid search).

**Tool calling (function calling).** The model receives JSON-schema declarations and may reply with a structured call;
our code runs it and returns the result as a function response. Why: live data and arithmetic the model must not guess.
Design rule: one OpenAPI file is the source of truth for the declarations *and* the Lambda contract.

**Agent loop with a step cap.** Model ↔ tools until the model answers, max 6 rounds; usage summed per answer.

**Confirmation gate in code.** `x-requireConfirmation` on the ticket tool → the loop stops and asks; prompts alone are
not a safety mechanism. Same philosophy as TripMate's approval interrupt.

**Deterministic evaluation.** Each question carries expected facts, cited doc, expected tool + args, refusal flag.
Rules, not an LLM judge, so runs are comparable and failures name a field. Limitation: structural only.

**Lambda Function URL.** HTTPS endpoint straight on a Lambda, no API Gateway; auth is our own token check; secrets via
SSM Parameter Store read at cold start. Why: zero-cost public demo. Trade-off: cold starts (~3 s with a 28 MB zip).

**Retries + fallback model.** Free-tier models return 429/503 and get slow; the client retries with backoff and switches
model after repeated failures. Reliability belongs in the client, not in the caller.

**Infra as code, one-session lifecycle.** OpenTofu creates and destroys everything; `make cost` before/after proves ₹0.
