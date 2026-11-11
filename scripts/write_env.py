"""`make env`: copy KB / agent ids from the Terraform outputs into .env (creating it from .env.example if needed)."""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
out = json.loads(subprocess.check_output(["tofu", "-chdir=infra", "output", "-json"], cwd=ROOT))
env = ROOT / ".env"
text = env.read_text() if env.exists() else (ROOT / ".env.example").read_text()
for key, tf in (
    ("KNOWLEDGE_BASE_ID", "knowledge_base_id"),
    ("AGENT_ID", "agent_id"),
    ("AGENT_ALIAS_ID", "agent_alias_id"),
):
    val = out[tf]["value"]
    text = (
        re.sub(rf"^{key}=.*$", f"{key}={val}", text, flags=re.M)
        if re.search(rf"^{key}=", text, re.M)
        else text + f"\n{key}={val}"
    )
env.write_text(text)
print("wrote", env, {k: out[k]["value"] for k in ("docs_bucket", "vector_bucket", "tools_lambda", "api_url")})
