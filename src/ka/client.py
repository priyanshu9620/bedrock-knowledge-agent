"""Client over Bedrock Agent Runtime: invoke_agent with trace parsing, retrieve, confirmation handling."""

import json
import time
import uuid
from dataclasses import dataclass, field

import boto3

from ka.config import settings


@dataclass
class Answer:
    question: str
    text: str = ""
    citations: list[dict] = field(default_factory=list)  # {"doc": "01-leave-policy.md", "snippet": "..."}
    tool_calls: list[dict] = field(
        default_factory=list
    )  # {"api": "/holidays", "method": "GET", "params": {...}, "result": "..."}
    retrieved_docs: list[str] = field(default_factory=list)  # docs the agent's own KB lookup returned
    confirmation_requested: bool = False
    rationale: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    llm_calls: int = 0
    latency_s: float = 0.0
    session_id: str = ""
    raw_trace_count: int = 0

    def as_dict(self) -> dict:
        return self.__dict__


def _session():
    return boto3.Session(profile_name=settings.aws_profile, region_name=settings.aws_region)


def runtime():
    return _session().client("bedrock-agent-runtime")


def _doc(uri: str) -> str:
    return uri.rsplit("/", 1)[-1] if uri else ""


class AgentClient:
    def __init__(self, agent_id: str | None = None, alias_id: str | None = None):
        self.agent_id = agent_id or settings.agent_id
        self.alias_id = alias_id or settings.agent_alias_id
        self.rt = runtime()

    def ask(self, question: str, session_id: str | None = None, auto_confirm: bool = False) -> Answer:
        """One question; re-invokes with CONFIRM if the agent asks to confirm a mutating tool."""
        sid = session_id or uuid.uuid4().hex
        t0 = time.perf_counter()
        ans = Answer(question=question, session_id=sid)
        pending = self._invoke(ans, {"inputText": question})
        if pending and auto_confirm:
            ans.confirmation_requested = True
            self._invoke(ans, {"sessionState": pending})
        elif pending:
            ans.confirmation_requested = True
        ans.latency_s = round(time.perf_counter() - t0, 2)
        return ans

    def _invoke(self, ans: Answer, extra: dict) -> dict | None:
        resp = self.rt.invoke_agent(
            agentId=self.agent_id,
            agentAliasId=self.alias_id,
            sessionId=ans.session_id,
            enableTrace=True,
            **extra,
        )
        pending = None
        for event in resp["completion"]:
            if "chunk" in event:
                ch = event["chunk"]
                ans.text += ch.get("bytes", b"").decode("utf-8")
                for c in (ch.get("attribution") or {}).get("citations", []):
                    for ref in c.get("retrievedReferences", []):
                        uri = ((ref.get("location") or {}).get("s3Location") or {}).get("uri", "")
                        ans.citations.append(
                            {"doc": _doc(uri), "snippet": (ref.get("content") or {}).get("text", "")[:200]}
                        )
            elif "trace" in event:
                ans.raw_trace_count += 1
                self._parse_trace(ans, event["trace"].get("trace", {}))
            elif "returnControl" in event:
                rc = event["returnControl"]
                pending = self._confirm_state(rc)
                for inv in rc.get("invocationInputs", []):
                    api = inv.get("apiInvocationInput") or {}
                    ans.tool_calls.append(
                        {
                            "api": api.get("apiPath"),
                            "method": api.get("httpMethod"),
                            "params": _api_params(api),
                            "result": "CONFIRMATION_REQUESTED",
                        }
                    )
        return pending

    @staticmethod
    def _confirm_state(rc: dict) -> dict:
        results = []
        for inv in rc.get("invocationInputs", []):
            api = inv.get("apiInvocationInput") or {}
            results.append(
                {
                    "apiResult": {
                        "actionGroup": api.get("actionGroup"),
                        "apiPath": api.get("apiPath"),
                        "httpMethod": api.get("httpMethod"),
                        "confirmationState": "CONFIRM",
                    }
                }
            )
        return {"invocationId": rc.get("invocationId"), "returnControlInvocationResults": results}

    @staticmethod
    def _parse_trace(ans: Answer, trace: dict) -> None:
        orch = trace.get("orchestrationTrace") or {}
        if "modelInvocationOutput" in orch:
            usage = ((orch["modelInvocationOutput"].get("metadata") or {}).get("usage")) or {}
            ans.llm_calls += 1
            ans.input_tokens += usage.get("inputTokens", 0)
            ans.output_tokens += usage.get("outputTokens", 0)
        if "rationale" in orch:
            ans.rationale.append(orch["rationale"].get("text", "")[:300])
        if "invocationInput" in orch:
            ag = orch["invocationInput"].get("actionGroupInvocationInput")
            if ag:
                ans.tool_calls.append(
                    {
                        "api": ag.get("apiPath"),
                        "method": ag.get("verb"),
                        "params": _api_params(ag),
                        "result": None,
                    }
                )
        if "observation" in orch:
            obs = orch["observation"]
            ago = obs.get("actionGroupInvocationOutput")
            if ago and ans.tool_calls and ans.tool_calls[-1]["result"] is None:
                ans.tool_calls[-1]["result"] = (ago.get("text") or "")[:500]
            kb = obs.get("knowledgeBaseLookupOutput")
            if kb:
                for ref in kb.get("retrievedReferences", []):
                    uri = ((ref.get("location") or {}).get("s3Location") or {}).get("uri", "")
                    if _doc(uri) and _doc(uri) not in ans.retrieved_docs:
                        ans.retrieved_docs.append(_doc(uri))
        # post-processing / pre-processing traces also carry model usage
        for key in ("preProcessingTrace", "postProcessingTrace"):
            mo = (trace.get(key) or {}).get("modelInvocationOutput")
            if mo:
                usage = (mo.get("metadata") or {}).get("usage") or {}
                ans.llm_calls += 1
                ans.input_tokens += usage.get("inputTokens", 0)
                ans.output_tokens += usage.get("outputTokens", 0)


def _api_params(api: dict) -> dict:
    out = {p.get("name"): p.get("value") for p in api.get("parameters") or []}
    body = ((api.get("requestBody") or {}).get("content") or {}).get("application/json") or {}
    for p in body.get("properties") or []:
        out[p.get("name")] = p.get("value")
    return out


def retrieve(query: str, kb_id: str | None = None, top_k: int | None = None) -> list[dict]:
    """Direct Knowledge Base retrieval (no agent): chunks with score and source doc."""
    rt = runtime()
    resp = rt.retrieve(
        knowledgeBaseId=kb_id or settings.knowledge_base_id,
        retrievalQuery={"text": query},
        retrievalConfiguration={
            "vectorSearchConfiguration": {"numberOfResults": top_k or settings.retrieve_top_k}
        },
    )
    out = []
    for r in resp.get("retrievalResults", []):
        uri = ((r.get("location") or {}).get("s3Location") or {}).get("uri", "")
        out.append(
            {
                "doc": _doc(uri),
                "score": round(r.get("score", 0), 4),
                "text": (r.get("content") or {}).get("text", ""),
            }
        )
    return out


def kb_sync(kb_id: str | None, data_source_id: str, wait: bool = True) -> dict:
    """Start an ingestion job for the S3 data source and wait for it (embeds the corpus into S3 Vectors)."""
    agent = _session().client("bedrock-agent")
    kb = kb_id or settings.knowledge_base_id
    job = agent.start_ingestion_job(knowledgeBaseId=kb, dataSourceId=data_source_id)["ingestionJob"]
    while wait and job["status"] in {"STARTING", "IN_PROGRESS"}:
        time.sleep(5)
        job = agent.get_ingestion_job(
            knowledgeBaseId=kb, dataSourceId=data_source_id, ingestionJobId=job["ingestionJobId"]
        )["ingestionJob"]
    return {
        "status": job["status"],
        "statistics": job.get("statistics"),
        "failureReasons": job.get("failureReasons"),
    }


def dumps(obj) -> str:
    return json.dumps(obj, default=str, ensure_ascii=False)
