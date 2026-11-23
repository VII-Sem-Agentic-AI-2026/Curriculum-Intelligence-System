"""
Lab 12 -- Safety and Governance: role permissions, department confidentiality,
versioned publish, one-click rollback, evaluation metrics.

Publishing never overwrites: every approved release becomes an immutable
version file; the ledger only moves a 'current' pointer, so rollback is just
moving the pointer back (and is itself recorded).
"""
from __future__ import annotations

import json
import os
import time

APPROVER_ROLES = {"HoD", "Dean (Academics)", "Board of Studies"}
GOV_DIR = os.environ.get("CIS_GOVERNANCE_DIR", os.path.join(os.path.dirname(__file__), "..", "governance_store"))


class PermissionDenied(PermissionError):
    pass


def _paths():
    os.makedirs(os.path.join(GOV_DIR, "versions"), exist_ok=True)
    return os.path.join(GOV_DIR, "ledger.json")


def _load() -> dict:
    p = _paths()
    if not os.path.exists(p):
        return {"current": None, "history": [], "metrics": []}
    return json.load(open(p))


def _save(ledger: dict) -> None:
    json.dump(ledger, open(_paths(), "w"), indent=2)


def check_approver(role: str) -> None:
    if role not in APPROVER_ROLES:
        raise PermissionDenied(f"Role '{role}' may not approve. Allowed: {sorted(APPROVER_ROLES)}")


def check_department_scope(requesting_department: str, data_department_tag: str = "CSE (AI)") -> None:
    """One department's curriculum data must not be released to another."""
    norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
    if norm(data_department_tag) not in norm(requesting_department) and norm(requesting_department) not in norm(data_department_tag):
        raise PermissionDenied(
            f"Department '{requesting_department}' is not authorised for '{data_department_tag}' curriculum data.")


def publish(document_markdown: str, payload: dict, approver_role: str, approver_name: str, run_id: str) -> int:
    check_approver(approver_role)
    ledger = _load()
    version = (ledger["history"][-1]["version"] + 1) if ledger["history"] else 1
    path = os.path.join(GOV_DIR, "versions", f"v{version}.json")
    json.dump({"version": version, "document_markdown": document_markdown, "payload": payload}, open(path, "w"), indent=2)
    ledger["history"].append({"version": version, "run_id": run_id, "approved_by": approver_name, "role": approver_role,
                               "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "event": "publish"})
    ledger["current"] = version
    _save(ledger)
    return version


def rollback(to_version: int, actor_role: str, actor_name: str) -> int:
    check_approver(actor_role)
    ledger = _load()
    if to_version not in {h["version"] for h in ledger["history"] if h["event"] == "publish"}:
        raise ValueError(f"Version {to_version} does not exist.")
    ledger["current"] = to_version
    ledger["history"].append({"version": to_version, "run_id": "-", "approved_by": actor_name, "role": actor_role,
                               "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "event": "rollback"})
    _save(ledger)
    return to_version


def current_version() -> int | None:
    return _load()["current"]


def list_history() -> list[dict]:
    return _load()["history"]


def read_version(version: int) -> dict:
    return json.load(open(os.path.join(GOV_DIR, "versions", f"v{version}.json")))


def record_metrics(run_id: str, metrics: dict) -> None:
    ledger = _load()
    ledger["metrics"].append({"run_id": run_id, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), **metrics})
    _save(ledger)


def list_metrics() -> list[dict]:
    return _load()["metrics"]
