"""Bedrock Agent action-group Lambda: four tools over a bundled JSON table (lambda/data.json).

Event (Bedrock → Lambda): apiPath, httpMethod, parameters[], requestBody.content["application/json"].properties[].
Response: {"messageVersion": "1.0", "response": {..., "httpStatusCode", "responseBody": {"application/json": {"body": str}}}}.
Pure Python, no AWS SDK calls → unit-testable offline."""

import hashlib
import json
from pathlib import Path

DATA = json.loads((Path(__file__).resolve().parent / "data.json").read_text())


# ---- the four tools --------------------------------------------------------------------------------------
def get_leave_balance(employee_id: str) -> dict:
    emp = DATA["employees"].get(employee_id.upper().strip())
    if not emp:
        return {
            "ok": False,
            "error": f"unknown employee_id {employee_id!r}; format is E followed by 4 digits",
        }
    return {
        "ok": True,
        "employee_id": employee_id.upper(),
        "name": emp["name"],
        "grade": emp["grade"],
        "location": emp["location"],
        "leave_balance": emp["leave"],
    }


def calculate_reimbursement(category: str, amount_inr: float, has_receipt: bool, days: int = 1) -> dict:
    cat = category.lower().strip().replace(" ", "_")
    caps = DATA["reimbursement_caps"]
    if cat not in caps:
        return {"ok": False, "error": f"unknown category {category!r}; known: {', '.join(caps)}"}
    rule = caps[cat]
    threshold = DATA["receipt_required_above_inr"]
    if amount_inr > threshold and not has_receipt:
        return {
            "ok": True,
            "category": cat,
            "claimed_inr": amount_inr,
            "approved_inr": 0,
            "reason": f"receipt required above ₹{threshold}",
        }
    cap = rule["cap_inr"]
    limit = cap * max(1, days) if cap is not None and rule["per"] == "day" else cap
    approved = amount_inr if limit is None else min(amount_inr, limit)
    reason = "within limit" if approved == amount_inr else f"capped at ₹{limit:,} ({rule['per']})"
    return {
        "ok": True,
        "category": cat,
        "claimed_inr": amount_inr,
        "approved_inr": approved,
        "excess_inr": round(amount_inr - approved, 2),
        "reason": reason,
    }


def get_holiday_calendar(year: int, region: str = "all") -> dict:
    y = DATA["holidays"].get(str(year))
    if not y:
        return {"ok": False, "error": f"no calendar for {year}; available: {', '.join(DATA['holidays'])}"}
    rows = list(y["all"]) + list(y.get(region.title(), []) if region.lower() != "all" else [])
    rows.sort()
    return {
        "ok": True,
        "year": year,
        "region": region,
        "count": len(rows),
        "holidays": [{"date": d, "name": n} for d, n in rows],
    }


def file_helpdesk_ticket(summary: str, priority: str = "P3", requester_id: str = "unknown") -> dict:
    priority = priority.upper().strip()
    if priority not in {"P1", "P2", "P3", "P4"}:
        return {"ok": False, "error": "priority must be P1..P4"}
    tid = (
        "HD-" + hashlib.sha1(f"{summary.strip()}|{priority}|{requester_id}".encode()).hexdigest()[:6].upper()
    )
    return {
        "ok": True,
        "ticket_id": tid,
        "summary": summary,
        "priority": priority.upper(),
        "requester_id": requester_id,
        "status": "open",
    }


# ---- Bedrock agent event plumbing ----------------------------------------------------------------------
def _params(event: dict) -> dict:
    out = {p["name"]: p.get("value") for p in event.get("parameters") or []}
    body = ((event.get("requestBody") or {}).get("content") or {}).get("application/json") or {}
    for p in body.get("properties") or []:
        out[p["name"]] = p.get("value")
    return out


def _bool(v) -> bool:
    return str(v).strip().lower() in {"true", "1", "yes", "y"}


ROUTES = {
    ("GET", "/leave-balance/{employee_id}"): lambda p: get_leave_balance(p["employee_id"]),
    ("POST", "/reimbursement/calculate"): lambda p: calculate_reimbursement(
        p["category"], float(p["amount_inr"]), _bool(p.get("has_receipt", False)), int(p.get("days") or 1)
    ),
    ("GET", "/holidays"): lambda p: get_holiday_calendar(int(p["year"]), p.get("region") or "all"),
    ("POST", "/helpdesk/ticket"): lambda p: file_helpdesk_ticket(
        p["summary"], p.get("priority") or "P3", p.get("requester_id") or "unknown"
    ),
}


def lambda_handler(event: dict, context=None) -> dict:
    key = (event.get("httpMethod", "").upper(), event.get("apiPath", ""))
    fn = ROUTES.get(key)
    try:
        result = fn(_params(event)) if fn else {"ok": False, "error": f"no route for {key}"}
        status = 200 if result.get("ok") else 400
    except (KeyError, ValueError, TypeError) as e:
        result, status = {"ok": False, "error": f"bad input: {e}"}, 400
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup"),
            "apiPath": event.get("apiPath"),
            "httpMethod": event.get("httpMethod"),
            "httpStatusCode": status,
            "responseBody": {"application/json": {"body": json.dumps(result)}},
        },
    }
