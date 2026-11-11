import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lambda"))
import handler  # noqa: E402


def call(method, path, params=None, body=None):
    ev = {
        "actionGroup": "people-ops",
        "apiPath": path,
        "httpMethod": method,
        "parameters": [{"name": k, "value": v} for k, v in (params or {}).items()],
    }
    if body:
        ev["requestBody"] = {
            "content": {
                "application/json": {"properties": [{"name": k, "value": v} for k, v in body.items()]}
            }
        }
    r = handler.lambda_handler(ev)
    return r["response"]["httpStatusCode"], json.loads(
        r["response"]["responseBody"]["application/json"]["body"]
    )


def test_leave_balance_known_and_unknown():
    s, b = call("GET", "/leave-balance/{employee_id}", {"employee_id": "e1001"})
    assert s == 200 and b["name"] == "Asha Rao" and b["leave_balance"]["EL"] == 21.5
    s, b = call("GET", "/leave-balance/{employee_id}", {"employee_id": "E9999"})
    assert s == 400 and "unknown" in b["error"]


def test_reimbursement_caps_receipts_and_days():
    _, b = call(
        "POST",
        "/reimbursement/calculate",
        body={"category": "meals_domestic", "amount_inr": "1200", "has_receipt": "true", "days": "1"},
    )
    assert b["approved_inr"] == 800 and b["excess_inr"] == 400
    _, b = call(
        "POST",
        "/reimbursement/calculate",
        body={"category": "meals_domestic", "amount_inr": "1500", "has_receipt": "true", "days": "2"},
    )
    assert b["approved_inr"] == 1500
    _, b = call(
        "POST",
        "/reimbursement/calculate",
        body={"category": "internet", "amount_inr": "900", "has_receipt": "false"},
    )
    assert b["approved_inr"] == 0 and "receipt" in b["reason"]
    _, b = call(
        "POST",
        "/reimbursement/calculate",
        body={"category": "cab", "amount_inr": "450", "has_receipt": "false"},
    )
    assert b["approved_inr"] == 450
    s, b = call(
        "POST",
        "/reimbursement/calculate",
        body={"category": "yacht", "amount_inr": "10", "has_receipt": "true"},
    )
    assert s == 400


def test_holidays_region_and_year():
    _, b = call("GET", "/holidays", {"year": "2026", "region": "Mumbai"})
    assert b["count"] == 12 and any(h["name"] == "Ganesh Chaturthi" for h in b["holidays"])
    _, b = call("GET", "/holidays", {"year": "2026"})
    assert b["count"] == 11 and b["holidays"][0]["date"] == "2026-01-01"
    s, _ = call("GET", "/holidays", {"year": "2031"})
    assert s == 400


def test_ticket_is_deterministic_and_validates_priority():
    _, a = call(
        "POST", "/helpdesk/ticket", body={"summary": "VPN down", "priority": "p2", "requester_id": "E1001"}
    )
    _, b = call(
        "POST", "/helpdesk/ticket", body={"summary": "VPN down", "priority": "P2", "requester_id": "E1001"}
    )
    assert a["ticket_id"] == b["ticket_id"] and a["ticket_id"].startswith("HD-")
    s, _ = call("POST", "/helpdesk/ticket", body={"summary": "x", "priority": "urgent"})
    assert s == 400


def test_unknown_route_and_bad_input():
    s, b = call("GET", "/nope")
    assert s == 400 and "no route" in b["error"]
    s, b = call("GET", "/holidays", {"year": "abc"})
    assert s == 400 and "bad input" in b["error"]
