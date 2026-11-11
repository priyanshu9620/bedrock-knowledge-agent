# Fresh laptop → working Knowledge Agent + a Claude session that knows everything

Repo = code + results + notes (`notes/`) + Claude memory note (`notes/claude-memory/`) + encrypted secrets (`secrets.tar.enc`).

## 1. Tools
`brew install uv tofu awscli gh git` · `uv python install 3.11` · `gh auth login` (personal account `priyanshu9620`).
OpenTofu's AWS provider 6.72.0 may need the local mirror (`~/.tofurc`, see ShopEase notes P-20) on networks where GitHub
release assets hang.

## 2. Clone and restore
```
git clone https://github.com/priyanshu9620/bedrock-knowledge-agent ~/Desktop/bedrock-knowledge-agent && cd $_
git config user.name "Priyanshu Gupta" && git config user.email "guptapriyanshu1822@gmail.com"
SECRETS_PASSPHRASE='<passphrase>' make secrets-unpack     # .env (Gemini key), infra/terraform.tfvars, tfstate, aws-credentials
cp aws-credentials ~/.aws/credentials                        # (merge if you have others) + [profile shopease] region=ap-southeast-2 in ~/.aws/config
uv sync && make test && uv run ka ingest && uv run ka ask "How long is maternity leave?"
```

## 3. Start a Claude Code session that resumes the work
In `~/Desktop/bedrock-knowledge-agent`, paste:
> Read notes/BOOTSTRAP.md, then notes/session/HANDOFF.md, DECISIONS.md, BUILD-PLAN.md, PROGRESS.md, PROBLEMS.md and
> notes/handoff-prompt-template.md. Save notes/claude-memory/bedrock-knowledge-agent-project.md into your memory directory and
> index it. Continue from HANDOFF's "Single next command". Rules: commit to main directly, never run tofu apply/destroy or
> anything billable yourself, nothing from any employer. For the Bedrock version read docs/V2-BEDROCK.md first.

## 4. Keep it portable
After each session: `make secrets-pack` if a secret/state changed, update `notes/session/*`, copy the memory note back,
commit, push.
