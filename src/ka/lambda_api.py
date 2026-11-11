"""Lambda Function URL handler: the same Agent behind HTTPS. GET /healthz, GET /ui, POST /ask (X-Api-Token).
Gemini key + token come from SSM at cold start; everything else from the function's environment."""

import base64
import json
import os
from pathlib import Path

_agent = None
_token = None


def _bootstrap():
    global _agent, _token
    if _agent is not None:
        return
    import boto3

    name, region = os.environ["KA_NAME"], os.environ["KA_REGION"]
    ssm = boto3.client("ssm", region_name=region)
    key = ssm.get_parameter(Name=f"/{name}/GOOGLE_API_KEY", WithDecryption=True)["Parameter"]["Value"]
    _token = ssm.get_parameter(Name=f"/{name}/API_TOKEN", WithDecryption=True)["Parameter"]["Value"]
    os.environ.setdefault("GOOGLE_API_KEY", key)
    os.environ.setdefault("AWS_REGION", region)
    from ka import config

    config.settings = config.Settings(
        google_api_key=key,
        aws_region=region,
        vector_bucket=os.environ["VECTOR_BUCKET"],
        vector_index=os.environ["VECTOR_INDEX"],
        tools_lambda=os.environ["TOOLS_LAMBDA"],
        gemini_model=os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        gemini_fallback_model=os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-3.1-flash-lite"),
        embedding_model=os.environ.get("EMBEDDING_MODEL", "gemini-embedding-001"),
        embedding_dimension=int(os.environ.get("EMBEDDING_DIMENSION", "768")),
    )
    import ka.agent as agent_mod
    import ka.index as index_mod
    import ka.tools as tools_mod

    index_mod.settings = config.settings
    tools_mod.settings = config.settings
    agent_mod.settings = config.settings
    _agent = agent_mod.Agent()


def _resp(status: int, body, ctype: str = "application/json") -> dict:
    return {
        "statusCode": status,
        "headers": {"content-type": ctype},
        "body": body if isinstance(body, str) else json.dumps(body, ensure_ascii=False),
    }


def handler(event, context=None):
    method = (event.get("requestContext") or {}).get("http", {}).get("method", "GET")
    path = event.get("rawPath", "/")
    if method == "GET" and path == "/healthz":
        return _resp(
            200, {"ok": True, "service": "knowledge-agent", "vector_index": os.environ.get("VECTOR_INDEX")}
        )
    if method == "GET" and path in {"/", "/ui"}:
        return _resp(
            200, (Path(__file__).parent / "ui" / "index.html").read_text(), "text/html; charset=utf-8"
        )
    if method == "POST" and path == "/ask":
        _bootstrap()
        headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
        if headers.get("x-api-token") != _token:
            return _resp(401, {"error": "bad or missing X-Api-Token"})
        raw = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(raw).decode()
        body = json.loads(raw)
        a = _agent.ask(
            body.get("question", ""),
            session_id=body.get("session_id"),
            auto_confirm=bool(body.get("confirm")),
        )
        return _resp(200, a.as_dict())
    return _resp(404, {"error": "not found"})
