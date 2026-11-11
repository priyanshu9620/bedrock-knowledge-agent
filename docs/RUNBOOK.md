# Runbook — one AWS session: create, ingest, evaluate, demo, destroy (Free plan, ≈ ₹0)

Normal days: nothing exists on AWS. Local mode (`.env` with only `GOOGLE_API_KEY`) works any time:
`uv run ka ingest` → `uv run ka ask "…"` against a local numpy index with the tools in-process.

## Up (≈ 5 min)
```
cd ~/Desktop/bedrock-knowledge-agent && git pull
make cost                              # spend before
make infra-plan && make infra-apply    # 28 resources: docs bucket + files, S3 Vectors index, tools + api Lambdas, Function URL, SSM (≈ 2 min)
make env                               # bucket / index / lambda / url / token → .env
make ingest-s3                         # S3 docs → chunks → Gemini embeddings → S3 Vectors (one embed batch)
uv run ka retrieve "casual leave"      # S3 Vectors query works?
uv run ka ask "How many casual leave days do I get?"      # cites 01-leave-policy.md
uv run ka ask "What is the leave balance of E1001?"       # calls the tools Lambda
```
Public demo: `$(tofu -chdir=infra output -raw api_url)ui?token=<API_TOKEN from .env>` — or curl:
```
curl -s -X POST "$API_URL/ask" -H "content-type: application/json" -H "x-api-token: $API_TOKEN" -d '{"question":"How long is maternity leave?"}'
```

## Evaluate
```
make eval                              # 40 questions through S3 Vectors + Lambda → eval/out/eval-<ts>.json (≈ 3–5 min)
make report                            # eval/report.md + results.json + README numbers
```

## Down (≈ 2 min)
```
make infra-destroy                     # removes everything incl. objects and vectors
make cost
AWS_PROFILE=shopease AWS_REGION=ap-southeast-2 aws s3api list-buckets --query 'length(Buckets)'                # 0
AWS_PROFILE=shopease AWS_REGION=ap-southeast-2 aws s3vectors list-vector-buckets --query 'length(vectorBuckets)' # 0
AWS_PROFILE=shopease AWS_REGION=ap-southeast-2 aws lambda list-functions --query 'length(Functions)'           # 0
SECRETS_PASSPHRASE='…' make secrets-pack && git add secrets.tar.enc && git commit -m "chore: secrets" && git push
```

## If something is off
| symptom | do |
|---|---|
| `ResourceNotFoundException` from s3vectors | `.env` ids stale → `make env` |
| `AccessDenied` on `s3vectors:PutVectors` | the CLI uses your profile (admin); the api Lambda only queries — ingest from the laptop |
| Gemini `429 RESOURCE_EXHAUSTED` | free tier: ~500 requests/day/model; the eval needs ~120; wait for the reset (~13:30 IST) |
| api Lambda 401 | `X-Api-Token` must equal `API_TOKEN` in `.env` (= `api_token` in `infra/terraform.tfvars`) |
| api Lambda timeout | first call is a cold start (~3 s) + Gemini; the limit is 60 s |
| `tofu init` hangs | provider mirror in `~/.tofurc` (aws 6.72.0 placed by hand) |
| Bedrock errors | not used in v1; see `docs/V2-BEDROCK.md` |
