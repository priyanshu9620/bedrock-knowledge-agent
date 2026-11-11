.PHONY: sync test lint fmt corpus-check lambda-zip ask retrieve serve eval report cost infra-init infra-plan infra-apply infra-destroy infra-output ingest ingest-s3 env secrets-pack secrets-unpack

sync:
	uv sync

test:            ## offline tests (lambda handler, scorer, corpus ↔ questions)
	uv run pytest -q -p no:warnings

lint:
	uv run ruff check src tests eval lambda scripts && uv run ruff format --check src tests eval lambda scripts

fmt:
	uv run ruff format src tests eval lambda scripts && uv run ruff check --fix src tests eval lambda scripts

corpus-check:    ## every fact referenced by eval/questions.yml must exist in corpus/facts.yml and the docs
	uv run python eval/corpus_check.py

lambda-zip:      ## tools.zip (handler + data) and api.zip (src/ka + google-genai + boto3 for python3.12 x86_64)
	rm -rf lambda/build && mkdir -p lambda/build/api && cd lambda && zip -q -r build/tools.zip handler.py data.json
	uv pip install --quiet --target lambda/build/api --python-platform x86_64-manylinux2014 --python-version 3.12 --only-binary :all: google-genai==3.1.0 boto3==1.42.6 pydantic==2.14.3 pydantic-settings==2.16.2 python-dotenv==1.2.4 pyyaml==6.0.3
	cp -R src/ka lambda/build/api/ka && cp lambda/openapi.yml lambda/build/api/openapi.yml && cp lambda/handler.py lambda/build/api/handler.py
	cd lambda/build/api && zip -q -r ../api.zip . -x "*.pyc" -x "*__pycache__*"
	@ls -la lambda/build/*.zip | awk '{print $$5, $$9}'

ask:             ## ka ask "question"   (needs the stack + .env ids)
	uv run ka ask "$(Q)"

retrieve:        ## ka retrieve "question"
	uv run ka retrieve "$(Q)"

serve:           ## demo page on http://127.0.0.1:8001/ui
	uv run ka serve

eval:            ## run every question in eval/questions.yml against the live agent → eval/out/eval-<ts>.json
	uv run python eval/run_eval.py

report:          ## eval/report.md + charts + eval/results.json + README numbers from the newest run
	uv run python eval/report.py

cost:            ## month-to-date spend from Cost Explorer (read-only)
	uv run python scripts/cost.py

# ---- AWS (infra/, OpenTofu). Claude plans; the user runs apply/destroy. ----
TOFU = tofu -chdir=infra
infra-init:
	$(TOFU) init -input=false
infra-plan: lambda-zip
	$(TOFU) plan -input=false -out=plan.out
infra-apply:     ## creates the stack (S3 docs, S3 Vectors, 2 Lambdas, Function URL, SSM) — then: make env ingest-s3
	$(TOFU) apply -input=false plan.out
infra-destroy:   ## removes everything; run after every session
	$(TOFU) destroy -input=false
infra-output:
	$(TOFU) output
env:             ## write KB/agent ids from tofu outputs into .env
	uv run python scripts/write_env.py
ingest:          ## chunk → Gemini embeddings → index (S3 Vectors when .env has VECTOR_BUCKET, else local)
	uv run ka ingest --source $(if $(SRC),$(SRC),local)

ingest-s3:       ## same, reading the docs from the S3 bucket
	uv run ka ingest --source s3

secrets-pack:
	scripts/secrets.sh pack
secrets-unpack:
	scripts/secrets.sh unpack
