"""
Lab 5 — MCP-Style Connector, implemented as a REAL MCP server.

This is not "MCP-style" in name only: it's an actual Model Context Protocol
server (using Anthropic's `mcp` Python SDK), speaking MCP over stdio. It
exposes four **tools** — one per governed data source, plus one static
**resource** for the accreditation reference pointers — so any MCP-aware
client (our LangChain/LangGraph agent, or Claude Desktop, or any other MCP
host) reaches curriculum data the exact same governed way.

Run standalone for testing:
    python -m mcp_server.server

Run via the MCP Inspector (visual debugging):
    npx @modelcontextprotocol/inspector python -m mcp_server.server

Every tool call is what Lab 5's guardrail ("no agent should touch a source
directly") is enforcing in this build: `app/mcp_client.py` is the ONLY file
on the agent side allowed to talk to this server, and this server is the
ONLY thing allowed to open the JSON files under `data/`.
"""
from __future__ import annotations

import json
import os
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

mcp = FastMCP(
    name="curriculum-intelligence-connector",
    instructions=(
        "Governed data connector for the Curriculum Intelligence System (Worklet-5). "
        "Exposes the department's curriculum, real industry-demand signals, and "
        "student-performance/revision-history data as typed MCP tools. Agents must "
        "call these tools instead of reading any file directly."
    ),
)


def _load(filename: str) -> Any:
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


@mcp.tool()
def read_curriculum(course_code: str | None = None) -> dict:
    """Read the department's official curriculum structure (real KLE Tech
    CSE-AI Curriculum Structure-Overall document: courses, credits, L-T-P,
    semester). Pass course_code to filter to one course, or omit for all."""
    data = _load("curriculum.json")
    if course_code:
        matches = [c for c in data["courses"] if c["course_code"] == course_code]
        return matches[0] if matches else {"error": f"No course '{course_code}' found."}
    return data


@mcp.tool()
def read_industry_signals() -> dict:
    """Read current industry-demand signals: real job postings and
    aggregated skill-demand trends gathered from live job boards and company
    career pages (Infosys, TCS, Razorpay, Siemens, ASAPP, etc.), each with a
    source URL, plus ACM/APNI accreditation reference pointers."""
    return _load("industry_signals.json")


@mcp.tool()
def read_student_performance(course_code: str | None = None) -> dict:
    """Read student course-outcome attainment and placement-interview
    feedback signals. NOTE: this dataset is simulated for the demo (real
    attainment data is private student/exam-cell records not provided to
    this system) but keyed to the department's real course codes."""
    data = _load("student_performance.json")
    if course_code:
        matches = [c for c in data["course_attainment"] if c["course_code"] == course_code]
        return {"course_attainment": matches, "placement_feedback": data["placement_feedback"]}
    return data


@mcp.tool()
def read_revision_history(tag: str | None = None) -> dict:
    """Read the long-term store of prior curriculum-revision decisions
    (Lab 4's memory store), optionally filtered by tag."""
    data = _load("history_store.json")
    if tag:
        data = [item for item in data if tag.lower() in [t.lower() for t in item.get("tags", [])]]
    return {"items": data}


@mcp.tool()
def read_accreditation_reference() -> dict:
    """Read the accreditation benchmark: ACM/IEEE-CS CS2023 knowledge areas
    (with curated keyword mapping) and the department's PEO/PO/PSO statements
    transcribed from the official curriculum document. APNI clause text was
    not supplied and is intentionally absent."""
    return _load("accreditation_reference.json")


@mcp.resource("cis://accreditation-standards")
def accreditation_standards() -> str:
    """Static resource: the ACM/APNI accreditation reference pointers."""
    signals = _load("industry_signals.json")
    return json.dumps(signals["accreditation_signals"], indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
