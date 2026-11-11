"""`make env`: copy the Terraform outputs (bucket, index, lambda, url) + the api token into .env."""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
out = json.loads(subprocess.check_output(["tofu", "-chdir=infra", "output", "-json"], cwd=ROOT))
env = ROOT / ".env"
text = env.read_text() if env.exists() else (ROOT / ".env.example").read_text()
tfvars = ROOT / "infra" / "terraform.tfvars"
m = re.search(r'api_token\s*=\s*"([^"]+)"', tfvars.read_text()) if tfvars.exists() else None
values = {
    "DOCS_BUCKET": out["docs_bucket"]["value"],
    "VECTOR_BUCKET": out["vector_bucket"]["value"],
    "VECTOR_INDEX": out["vector_index"]["value"],
    "TOOLS_LAMBDA": out["tools_lambda"]["value"],
    "API_URL": out["api_url"]["value"],
}
if m:
    values["API_TOKEN"] = m.group(1)
for key, val in values.items():
    if re.search(rf"^{key}=", text, re.M):
        text = re.sub(rf"^{key}=.*$", f"{key}={val}", text, flags=re.M)
    else:
        text += f"\n{key}={val}"
env.write_text(text)
print("wrote .env:", {k: v for k, v in values.items() if k != "API_TOKEN"})
