"""
LLM abstraction layer — see Phase-1 README for why this is mocked.
Swapping in a real model is one new class + one line in get_llm().
"""
from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str, *, system: str | None = None) -> str: ...


class MockLLM(LLMClient):
    """Deterministic stand-in so every demo run is 100% reproducible."""

    def complete(self, prompt: str, *, system: str | None = None) -> str:
        p = prompt.lower()
        if "clarifying question" in p:
            return self._clarifying_questions(prompt)
        if "generate a plan" in p:
            return self._plan(prompt)
        if "revise the plan" in p:
            return self._revise(prompt)
        return "[mock-llm] no rule matched; empty completion."

    def _clarifying_questions(self, prompt: str) -> str:
        questions = []
        if "department" not in prompt.lower():
            questions.append("Which department / program is this curriculum review for?")
        if "scope" not in prompt.lower():
            questions.append("Should the review cover the whole curriculum, or specific semesters/courses?")
        if "cycle" not in prompt.lower():
            questions.append("Is this a routine annual review, or triggered by a specific concern (e.g. placement feedback)?")
        if not questions:
            questions = ["Any specific course to prioritize?", "Any constraint on adding new electives?"]
        return "\n".join(f"- {q}" for q in questions[:3])

    def _plan(self, prompt: str) -> str:
        return (
            "1. Apply the program specialist pack and check department data scope\n"
            "2. In parallel: map the curriculum, aggregate industry skill demand, benchmark against ACM CS2023 (via MCP)\n"
            "3. Merge the three views and compute coverage, staleness and PSO consistency with typed tools\n"
            "4. Build the evidence-linked gap analysis\n"
            "5. Retrieve related prior revision decisions from memory\n"
            "6. Draft recommendations tied to each gap and its evidence\n"
            "7. Validate with the acceptance suite; repair only failing items\n"
            "8. Pause at the HoD / Dean / Board of Studies gate before any publish"
        )

    def _revise(self, prompt: str) -> str:
        m = re.search(r"feedback:\s*(.+)$", prompt, re.IGNORECASE | re.DOTALL)
        feedback = m.group(1).strip() if m else "(no feedback text found)"
        return f"Revised plan incorporating feedback -> '{feedback}'. Added a step to address this before proceeding."


def get_llm() -> LLMClient:
    provider = os.environ.get("LLM_PROVIDER", "mock").lower()
    if provider == "mock":
        return MockLLM()
    raise NotImplementedError(f"LLM provider '{provider}' not wired up yet.")
