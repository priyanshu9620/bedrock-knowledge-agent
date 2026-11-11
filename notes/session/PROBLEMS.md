# Problems (real ones only)

(none yet)
- **P-1 · 2026-11-11 · Every Bedrock invocation throttled: "Too many tokens per day" — quotas are 0.** `get-account-plan-state` → `FREE`; Service Quotas shows e.g. "Global cross-region model inference tokens per day for Amazon Nova 2 Lite = 0", "On-demand model inference requests per minute for Titan Text Embeddings V2 = 0", **Adjustable = False**. Even the embeddings call (needed for KB ingestion) is blocked. Fix: the account must be upgraded to the Paid plan (credits keep applying). Lesson: probe the *invocation* path (one tiny converse call) before designing around a service — "allowed by the SCP" and "has quota" are different questions.
- **P-2 · 2026-11-11 · Nova 2 Lite is INFERENCE_PROFILE-only in Sydney** (no on-demand). The agent's `foundation_model` must be the inference-profile ARN (`global.amazon.nova-2-lite-v1:0`), and the agent role needs both the profile ARN and `foundation-model/*` ARNs because a global profile routes to other regions.
- **P-3 · 2026-11-11 · Provider 5.82.2 has no S3 Vectors; 6.72.0 downloaded from releases.hashicorp.com (SHA256-verified) into the local mirror** (GitHub release assets hang on this network, ShopEase P-20).
- **P-4 · 2026-11-11 · `uv add` failed after I deleted `src/ka` created by `uv init`** (Pager-Zero P-3 again). Recreate the package first.
