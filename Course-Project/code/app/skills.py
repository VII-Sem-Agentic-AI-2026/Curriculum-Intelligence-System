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
    return Plan(department=department, scope=scope, steps=steps).lock()


def format_curriculum(result: dict, template: str = "standard") -> Document:
    """skill format_curriculum(result, template) -> Document"""
    title = result.get("title", "Curriculum Review Draft")
    sections = result.get("sections", {})
    return Document(title=title, generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     sections=sections)
