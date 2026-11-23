# Lab 12 — Safety & Governance

**Concept (book spec):** Add confidentiality, approval, evaluation and rollback.

## 1. Concept applied
Only HoD / Dean (Academics) / Board of Studies may approve. A request for another department's data is blocked before any data is read. Every approval is an immutable, numbered version with one-click rollback and recorded metrics. The gate supports a genuine approve / adjust / reject decision, where adjust resumes either Group E alone or Groups A-C together.

## 2. Technical stack

| Item | Used |
|---|---|
| Access control | role + department-scope guards |
| Versioning | immutable version files + a ledger |

## 3. Code

- `code/governance.py` (full copy of `app/governance.py` in the main codebase)

**app/governance.py** (excerpt):
```python
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
            f"Department '{requesting_department}' is not authorised for '{dat
```

## 4. Evidence

See `evidence.txt` in this folder — output of:

```
python -m pytest tests/test_governance_graph.py::test_unauthorised_role_cannot_publish tests/test_governance_graph.py::test_other_department_is_blocked_before_any_data_is_read tests/test_governance_graph.py::test_adjust_resumes_the_relevant_agent_and_reaches_a_fresh_gate tests/test_governance_graph.py::test_rollback_moves_pointer_and_is_recorded -v
```

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/claude/cis3
plugins: platformdirs-4.13.0, anyio-4.16.0, langsmith-0.14.17
collecting ... collected 4 items

tests/test_governance_graph.py::test_unauthorised_role_cannot_publish PASSED [ 25%]
tests/test_governance_graph.py::test_other_department_is_blocked_before_any_data_is_read PASSED [ 50%]
tests/test_governance_graph.py::test_adjust_resumes_the_relevant_agent_and_reaches_a_fresh_gate PASSED [ 75%]
tests/test_governance_graph.py::test_rollback_moves_pointer_and_is_recorded PASSED [100%]

============================== 4 passed in 8.85s ===============================
```
