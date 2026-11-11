.PHONY: sync test lint fmt corpus-check lambda-zip ask retrieve serve eval report cost infra-init infra-plan infra-apply infra-destroy infra-output kb-sync env secrets-pack secrets-unpack

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

lambda-zip:      ## package lambda/ → lambda/build/tools.zip (what Terraform uploads)
	rm -rf lambda/build && mkdir -p lambda/build && cd lambda && zip -q -r build/tools.zip handler.py data.json

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
infra-apply:     ## creates the stack (S3, S3 Vectors, KB, Lambda, Agent) — then: make env kb-sync
	$(TOFU) apply -input=false plan.out
infra-destroy:   ## removes everything; run after every session
	$(TOFU) destroy -input=false
infra-output:
	$(TOFU) output
env:             ## write KB/agent ids from tofu outputs into .env
	uv run python scripts/write_env.py
kb-sync:         ## start a Knowledge Base ingestion job and wait for it
	uv run ka kb-sync

secrets-pack:
	scripts/secrets.sh pack
secrets-unpack:
	scripts/secrets.sh unpack
