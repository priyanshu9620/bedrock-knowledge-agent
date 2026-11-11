"""Tools from `lambda/openapi.yml` (the same schema a Bedrock action group consumes) → Gemini function declarations,
and an executor that invokes the Lambda with the Bedrock action-group event shape (or runs the handler in-process)."""

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ka.config import settings

_HERE = Path(__file__).resolve()
OPENAPI = next(
    p for p in (_HERE.parents[2] / "lambda" / "openapi.yml", _HERE.parents[1] / "openapi.yml") if p.exists()
)
_TYPES = {"string": "STRING", "integer": "INTEGER", "number": "NUMBER", "boolean": "BOOLEAN"}


@dataclass
class ToolSpec:
    name: str  # operationId
    method: str
    path: str
    description: str
    params: dict = field(default_factory=dict)  # name → {type, description}
    required: list[str] = field(default_factory=list)
    requires_confirmation: bool = False
    path_params: list[str] = field(default_factory=list)
    body_params: list[str] = field(default_factory=list)

    def declaration(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    k: {"type": _TYPES.get(v["type"], "STRING"), "description": v.get("description", "")}
                    for k, v in self.params.items()
                },
                "required": self.required,
            },
        }


def load_specs(path: Path | None = None) -> list[ToolSpec]:
    spec = yaml.safe_load((path or OPENAPI).read_text())
    out = []
    for p, methods in spec["paths"].items():
        for method, op in methods.items():
            t = ToolSpec(
                name=op["operationId"],
                method=method.upper(),
                path=p,
                description=(op.get("summary", "") + " " + op.get("description", "")).strip(),
            )
            t.requires_confirmation = str(op.get("x-requireConfirmation", "")).upper() == "ENABLED"
            for prm in op.get("parameters", []):
                t.params[prm["name"]] = {
                    "type": prm["schema"]["type"],
                    "description": prm.get("description", ""),
                }
                if prm.get("required"):
                    t.required.append(prm["name"])
                if prm.get("in") == "path":
                    t.path_params.append(prm["name"])
            body = (
                ((op.get("requestBody") or {}).get("content") or {}).get("application/json", {}).get("schema")
            )
            if body:
                for k, v in body.get("properties", {}).items():
                    t.params[k] = {"type": v.get("type", "string"), "description": v.get("description", "")}
                    t.body_params.append(k)
                t.required += [r for r in body.get("required", []) if r not in t.required]
            out.append(t)
    return out


def action_group_event(t: ToolSpec, args: dict) -> dict:
    """Exactly what Bedrock sends an action-group Lambda, so lambda/handler.py is shared by v1 and v2."""
    params = [
        {"name": k, "type": "string", "value": str(v)} for k, v in args.items() if k not in t.body_params
    ]
    body = [{"name": k, "type": "string", "value": str(v)} for k, v in args.items() if k in t.body_params]
    ev = {
        "messageVersion": "1.0",
        "actionGroup": "people-ops",
        "apiPath": t.path,
        "httpMethod": t.method,
        "parameters": params,
    }
    if body:
        ev["requestBody"] = {"content": {"application/json": {"properties": body}}}
    return ev


class ToolExecutor:
    def __init__(self, specs: list[ToolSpec] | None = None, lambda_name: str | None = None):
        self.specs = {t.name: t for t in (specs or load_specs())}
        self.lambda_name = settings.tools_lambda if lambda_name is None else lambda_name
        self._lambda = None

    def declarations(self) -> list[dict]:
        return [t.declaration() for t in self.specs.values()]

    def call(self, name: str, args: dict) -> dict:
        t = self.specs.get(name)
        if not t:
            return {"ok": False, "error": f"unknown tool {name}"}
        event = action_group_event(t, args)
        if self.lambda_name:
            import boto3

            if self._lambda is None:
                self._lambda = boto3.Session(
                    profile_name=settings.aws_profile, region_name=settings.aws_region
                ).client("lambda")
            r = self._lambda.invoke(FunctionName=self.lambda_name, Payload=json.dumps(event).encode())
            resp = json.loads(r["Payload"].read())
        else:
            import sys

            sys.path.insert(0, str(OPENAPI.parent))
            import handler  # the same lambda/handler.py, in-process

            resp = handler.lambda_handler(event)
        body = resp["response"]["responseBody"]["application/json"]["body"]
        return json.loads(body)
