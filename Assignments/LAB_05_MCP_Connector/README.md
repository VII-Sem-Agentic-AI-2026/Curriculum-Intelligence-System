# Lab 5 — MCP-Style Connector

**Concept (book spec):** Place a governed, typed, authenticated boundary between agents and all data sources.

## 1. Concept applied
mcp_server/server.py is a real MCP server, not a renamed function call — it can be inspected live with the official MCP Inspector. app/mcp_client.py is the only code allowed to open an MCP ClientSession, and therefore the only path to any data file under mcp_server/data/.

## 2. Technical stack

| Item | Used |
|---|---|
| MCP SDK | Anthropic mcp Python SDK, mcp<2.0, FastMCP |
| Transport | stdio |
| Tools | 5 real MCP tools + 1 resource |

## 3. Code

- `code/server.py` (full copy of `mcp_server/server.py` in the main codebase)
- `code/mcp_client.py` (full copy of `app/mcp_client.py` in the main codebase)

**mcp_server/server.py** (excerpt):
```python
sys, TCS, Razorpay, Siemens, ASAPP, etc.), each with a
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

```

## 4. Evidence

See `evidence.txt` in this folder — output of:

```
python -m pytest tests/test_mcp.py -v
```

```
cachedir: .pytest_cache
rootdir: /home/claude/cis3
plugins: platformdirs-4.13.0, anyio-4.16.0, langsmith-0.14.17
collecting ... collected 7 items

tests/test_mcp.py::test_mcp_server_advertises_tools_and_resource PASSED  [ 14%]
tests/test_mcp.py::test_curriculum_is_real_2023_27_with_2026_revision PASSED [ 28%]
tests/test_mcp.py::test_filter_by_course_code PASSED                     [ 42%]
tests/test_mcp.py::test_every_industry_skill_has_sources PASSED          [ 57%]
tests/test_mcp.py::test_performance_data_is_labelled_simulated PASSED    [ 71%]
tests/test_mcp.py::test_revision_history_marks_real_bos_entries_separately_from_simulated_ones PASSED [ 85%]
tests/test_mcp.py::test_accreditation_reference_has_17_acm_areas_and_department_outcomes PASSED [100%]


```
