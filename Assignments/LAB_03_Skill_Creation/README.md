# Lab 3 — Skill Creation

**Concept (book spec):** Package repeatable capability as reusable, schema-typed skills.

## 1. Concept applied
plan() and format_curriculum() are case-agnostic, schema-typed functions proven to work for two different departments (CSE (AI) and ECE) with zero code change.

## 2. Technical stack

| Item | Used |
|---|---|
| Language | Python 3.12 |
| Schema | dataclasses: Plan, PlanStep, Document |

## 3. Code

- `code/skills.py` (full copy of `app/skills.py` in the main codebase)

**app/skills.py** (excerpt):
```python
"""Lab 3 — Skill Creation. Reusable, schema-typed, case-agnostic skills."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass
class PlanStep:
    step_no: int
    description: str


@dataclass
class Plan:
    department: str
    scope: str
    steps: list[PlanStep]
    locked: bool = False

    def lock(self) -> "Plan":
        self.locked = True
        return self

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Document:
    title: str
    generated_at: str
    sections: dict[str, Any]

    def as_markdown(self) -> str:
        lines = [f"# {self.title}", f"_Generated: {self.generated_at}_", ""]
        for heading, content in self.sections.items():
            lines.append(f"## {heading}")
            if isinstance(content, list):
                for item in content:
                    lines.append(f"- {item}")
            elif isinstance(content, dict):
                for k, v in content.items():
                    lines.append(f"- **{k}**: {v}")
            else:
                lines.append(str(content))
            lines.append("")
        return "\n".join(lines)


def plan(inputs: dict) -> Plan:
    """skill plan(inputs) -> Plan: return expand(inputs).lock()"""
    department = inputs.get("department", "Unspecified department")
    scope = inputs.get("scope", "full curriculum")
    raw_steps = inputs.get("plan_steps", [])
    steps = [PlanStep(step_no=i + 1, description=s) for i, s in enumerate(raw_steps)]
    return Plan(departme
```

## 4. Evidence

See `evidence.txt` in this folder — output of:

```
python -m pytest tests/test_langchain_memory_skills.py::test_skills_reusable_across_departments -v
```

```
cachedir: .pytest_cache
rootdir: /home/claude/cis3
plugins: platformdirs-4.13.0, anyio-4.16.0, langsmith-0.14.17
collecting ... collected 1 item

tests/test_langchain_memory_skills.py::test_skills_reusable_across_departments PASSED

```
