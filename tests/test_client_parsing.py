"""Trace/citation parsing against canned Bedrock event shapes (no network)."""

from ka.client import AgentClient, Answer, _api_params


def test_trace_parsing_accumulates_usage_tools_and_kb_docs():
    a = Answer(question="q")
    AgentClient._parse_trace(
        a,
        {
            "orchestrationTrace": {
                "modelInvocationOutput": {"metadata": {"usage": {"inputTokens": 100, "outputTokens": 20}}}
            }
        },
    )
    AgentClient._parse_trace(
        a,
        {
            "orchestrationTrace": {
                "invocationInput": {
                    "actionGroupInvocationInput": {
                        "apiPath": "/holidays",
                        "verb": "GET",
                        "parameters": [{"name": "year", "value": "2026"}],
                    }
                }
            }
        },
    )
    AgentClient._parse_trace(
        a, {"orchestrationTrace": {"observation": {"actionGroupInvocationOutput": {"text": '{"ok": true}'}}}}
    )
    AgentClient._parse_trace(
        a,
        {
            "orchestrationTrace": {
                "observation": {
                    "knowledgeBaseLookupOutput": {
                        "retrievedReferences": [
                            {"location": {"s3Location": {"uri": "s3://b/docs/01-leave-policy.md"}}}
                        ]
                    }
                }
            }
        },
    )
    AgentClient._parse_trace(
        a,
        {
            "postProcessingTrace": {
                "modelInvocationOutput": {"metadata": {"usage": {"inputTokens": 5, "outputTokens": 1}}}
            }
        },
    )
    assert a.llm_calls == 2 and a.input_tokens == 105 and a.output_tokens == 21
    assert a.tool_calls == [
        {"api": "/holidays", "method": "GET", "params": {"year": "2026"}, "result": '{"ok": true}'}
    ]
    assert a.retrieved_docs == ["01-leave-policy.md"]


def test_confirm_state_and_body_params():
    rc = {
        "invocationId": "inv-1",
        "invocationInputs": [
            {
                "apiInvocationInput": {
                    "actionGroup": "people-ops",
                    "apiPath": "/helpdesk/ticket",
                    "httpMethod": "POST",
                    "requestBody": {
                        "content": {
                            "application/json": {"properties": [{"name": "summary", "value": "VPN down"}]}
                        }
                    },
                }
            }
        ],
    }
    st = AgentClient._confirm_state(rc)
    assert (
        st["invocationId"] == "inv-1"
        and st["returnControlInvocationResults"][0]["apiResult"]["confirmationState"] == "CONFIRM"
    )
    assert _api_params(rc["invocationInputs"][0]["apiInvocationInput"]) == {"summary": "VPN down"}
