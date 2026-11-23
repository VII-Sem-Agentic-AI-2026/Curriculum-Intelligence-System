# Lab 6 — OpenCLA/OpenClaw Runtime

**Concept (book spec):** Run the agent inside a controlled runtime with a full audit log, step budgets, human-approval gates, and checkpoint/resume.

## 1. Concept applied
LangGraph provides checkpoint/resume and the human gate; the audit log is driven automatically by a LangChain callback attached to every tool call, so no call site can skip logging.

## 2. Technical stack

| Item | Used |
|---|---|
| Checkpointing | LangGraph SqliteSaver |
| Audit log | LangChain BaseCallbackHandler |
| Budget | GraphState counter, MAX_BUDGET=40 |

## 3. Code

- `code/audit_callback.py` (full copy of `app/audit_callback.py` in the main codebase)

**app/audit_callback.py** (excerpt):
```python
"""
Lab 6 audit log, driven by a real LangChain callback handler.

LangChain integration point #3: `AuditLogCallbackHandler` subclasses
`langchain_core.callbacks.BaseCallbackHandler` and is attached to every
tool/chain invocation in the graph (see graph.py's `config={"callbacks": [...]}`).
LangChain calls `on_tool_start`/`on_tool_end`/`on_chain_start`/`on_chain_end`
automatically around every invocation — we don't call the logger by hand at
each call site, which is exactly what makes this a *governed* audit log
rather than a log statement someone could forget to add.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler


@dataclass
class AuditEntry:
    entry_id: str
    run_id: str
    timestamp: float
    kind: str          # "tool" | "chain"
    name: str
    inputs: Any
    result: Any


class AuditLogCallbackHandler(BaseCallbackHandler):
    def __init__(self, run_id: str, log_dir: str = "audit_logs"):
        self.run_id = run_id
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.path = os.path.join(log_dir, f"{run_id}.jsonl")
        self.entries: list[AuditEntry] = []
        self._lock = threading.Lock()

    def _write(self, entry: AuditEntry) -> None:
        with self._lock:
            self.entries.append(entry)
            with open(self.path, "a") as f:
                f.write(json.dumps(asdict(entry), default=str) + "\n")

    # --- LangChain calls these automatically around every tool invocation ---
    def on_tool_start(self, 
```

## 4. Evidence

See `evidence.txt` in this folder — output of:

```
python -m pytest tests/test_governance_graph.py::test_resume_in_fresh_checkpointer_and_versioned_publish tests/test_governance_graph.py::test_every_mcp_tool_call_is_audit_logged_including_parallel_workers -v
```

```
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/claude/cis3
plugins: platformdirs-4.13.0, anyio-4.16.0, langsmith-0.14.17
collecting ... collected 2 items

tests/test_governance_graph.py::test_resume_in_fresh_checkpointer_and_versioned_publish PASSED [ 50%]
tests/test_governance_graph.py::test_every_mcp_tool_call_is_audit_logged_including_parallel_workers PASSED [100%]

```
