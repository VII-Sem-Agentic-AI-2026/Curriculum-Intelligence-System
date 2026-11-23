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
    def on_tool_start(self, serialized: dict, input_str: str, *, run_id: UUID,
                       **kwargs: Any) -> None:
        self._write(AuditEntry(
            entry_id=str(uuid.uuid4())[:8], run_id=self.run_id, timestamp=time.time(),
            kind="tool", name=serialized.get("name", "unknown_tool"),
            inputs=self._safe(input_str), result="(pending)"))

    def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        self._write(AuditEntry(
            entry_id=str(uuid.uuid4())[:8], run_id=self.run_id, timestamp=time.time(),
            kind="tool", name="(tool_end)", inputs="(see tool_start)",
            result=self._safe(str(output)[:500])))

    def log_manual(self, name: str, inputs: Any, result: Any) -> None:
        """For graph steps that aren't LangChain tool calls (clarify/plan/
        revise/skills/gate) but still need the same audit trail."""
        self._write(AuditEntry(
            entry_id=str(uuid.uuid4())[:8], run_id=self.run_id, timestamp=time.time(),
            kind="chain", name=name, inputs=self._safe(inputs), result=self._safe(result)))

    def all_entries(self) -> list[dict]:
        return [asdict(e) for e in self.entries]

    @staticmethod
    def _safe(value: Any) -> Any:
        try:
            json.dumps(value)
            return value
        except TypeError:
            return str(value)

    @classmethod
    def read_log(cls, run_id: str, log_dir: str = "audit_logs") -> list[dict]:
        path = os.path.join(log_dir, f"{run_id}.jsonl")
        if not os.path.exists(path):
            return []
        with open(path) as f:
            return [json.loads(line) for line in f if line.strip()]
