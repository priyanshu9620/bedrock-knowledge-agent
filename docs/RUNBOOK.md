# Runbook — one AWS session: create, sync, evaluate, destroy

Normal days: nothing exists on AWS (₹0). Bring it up only to evaluate or demo. Session ≈ 45 min, cost ≈ cents.
Prerequisite (once): the account must be on the **Paid plan** — the Free plan sets every Bedrock model-invocation
quota to 0 and they are not adjustable (notes P-1). Credits still apply after the upgrade.

## Up (≈ 10 min)
```
cd ~/Desktop/bedrock-knowledge-agent && git pull
make cost                          # spend before
make infra-plan && make infra-apply   # 31 resources: S3 docs, S3 Vectors, KB + data source, Lambda, Agent + alias (≈ 3 min)
make env                           # KB / agent ids → .env
make kb-sync                       # ingestion job: embeds 13 docs with Titan v2 (≈ 1–2 min)
uv run ka retrieve "casual leave"  # raw retrieval works?
uv run ka ask "How many casual leave days do I get?"   # agent + citation
uv run ka ask "What is the leave balance of E1001?"    # agent + Lambda tool
```

## Evaluate + demo
```
make eval                          # 40 questions → eval/out/eval-<ts>.json (≈ 5–8 min)
make report                        # eval/report.md + results.json + README numbers
make serve                         # http://127.0.0.1:8001/ui for the screen recording
```

## Down (≈ 3 min)
```
make infra-destroy                 # removes everything incl. bucket objects and vectors
make cost                          # spend after
AWS_PROFILE=shopease AWS_REGION=ap-southeast-2 aws bedrock-agent list-agents --query 'length(agentSummaries)'   # must be 0
AWS_PROFILE=shopease AWS_REGION=ap-southeast-2 aws s3api list-buckets --query 'length(Buckets)'                 # must be 0
SECRETS_PASSPHRASE='…' make secrets-pack && git add secrets.tar.enc && git commit -m "chore: secrets" && git push
```

## If something is off
| symptom | do |
|---|---|
| `ThrottlingException: Too many tokens per day` on any model | account still on the Free plan (quota 0) — upgrade, wait a few minutes, retry |
| ingestion job FAILED | `aws bedrock-agent get-ingestion-job …` failureReasons; usually the KB role or the index metadata config |
| agent answers but never calls tools | check the action group is attached to DRAFT and the alias was created after it (`tofu apply` again re-prepares) |
| `AccessDeniedException` invoking the agent | the agent role needs the inference-profile ARN **and** `foundation-model/*` ARNs (global profile routes cross-region) |
| `tofu init` hangs | provider mirror in `~/.tofurc` (aws 6.72.0 was placed there by hand) |
