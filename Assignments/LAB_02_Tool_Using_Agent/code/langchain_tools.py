"""
LangChain integration point #1: typed tools.

Every tool below is a real `langchain_core.tools` `@tool`-decorated
function — LangChain validates its args against the auto-generated schema
and the graph's "act" node (see graph.py) invokes them via the standard
LangChain `Tool.invoke()` interface. The tools themselves call through
`app/mcp_client.py`, i.e. through the real MCP server — LangChain is the
calling convention, MCP is the transport to the data.
"""
from __future__ import annotations

import json

from langchain_core.tools import tool

from . import mcp_client, tools as core_tools


@tool
def read_curriculum_via_mcp(course_code: str = "") -> str:
    """Read the department's official curriculum (courses, credits, L-T-P,
    semester) via the MCP connector. Pass a course_code to filter, or leave
    blank for the full curriculum."""
    data = mcp_client.mcp_read_curriculum(course_code or None)
    return json.dumps(data)


@tool
def read_industry_signals_via_mcp() -> str:
    """Read real, cited industry skill-demand signals via the MCP
    connector (job postings + aggregated trends with source URLs)."""
    return json.dumps(mcp_client.mcp_read_industry_signals())


@tool
def read_student_performance_via_mcp(course_code: str = "") -> str:
    """Read student attainment / placement-feedback signals via the MCP
    connector (simulated for demo, real course codes)."""
    return json.dumps(mcp_client.mcp_read_student_performance(course_code or None))


@tool
def check_credit_totals(curriculum_json: str) -> str:
    """Verify the program's declared 176-credit total against the sum of
    its 8 semester totals. Input is the JSON string from
    read_curriculum_via_mcp."""
    curriculum = json.loads(curriculum_json)
    result = core_tools.compute_credit_total_check(curriculum)
    return json.dumps({"valid": result.valid, "value": result.value, "errors": result.errors})


@tool
def check_stale_courses(curriculum_json: str) -> str:
    """Flag courses whose catalog-year code prefix is >=5 years old.
    Input is the JSON string from read_curriculum_via_mcp."""
    curriculum = json.loads(curriculum_json)
    result = core_tools.compute_stale_content_flags(curriculum)
    return json.dumps({"valid": result.valid, "value": result.value, "errors": result.errors})


@tool
def check_skill_coverage(curriculum_json: str, industry_signals_json: str) -> str:
    """Compute % of in-demand skills covered by current course titles.
    Inputs are the JSON strings from read_curriculum_via_mcp and
    read_industry_signals_via_mcp."""
    curriculum = json.loads(curriculum_json)
    industry = json.loads(industry_signals_json)
    result = core_tools.compute_skill_coverage(curriculum, industry)
    return json.dumps({"valid": result.valid, "value": result.value, "errors": result.errors})


@tool
def read_accreditation_reference_via_mcp() -> str:
    """Read ACM CS2023 knowledge areas and the department PEO/PO/PSO
    statements via the MCP connector."""
    return json.dumps(mcp_client.mcp_read_accreditation_reference())


@tool
def check_acm_benchmark(curriculum_json: str, reference_json: str) -> str:
    """Benchmark the curriculum against ACM CS2023 knowledge areas."""
    r = core_tools.compute_acm_benchmark(json.loads(curriculum_json), json.loads(reference_json))
    return json.dumps({"valid": r.valid, "value": r.value, "errors": r.errors})


@tool
def check_pso_alignment(curriculum_json: str) -> str:
    """Check the department PSOs are supported by offered courses."""
    r = core_tools.compute_pso_alignment(json.loads(curriculum_json))
    return json.dumps({"valid": r.valid, "value": r.value, "errors": r.errors})


@tool
def check_curriculum_evolution(curriculum_json: str) -> str:
    """List recently introduced or revised courses (catalog year 2025+)."""
    r = core_tools.compute_curriculum_evolution(json.loads(curriculum_json))
    return json.dumps({"valid": r.valid, "value": r.value, "errors": r.errors})


ALL_TOOLS = [
    read_curriculum_via_mcp,
    read_industry_signals_via_mcp,
    read_student_performance_via_mcp,
    check_credit_totals,
    check_stale_courses,
    check_skill_coverage,
    read_accreditation_reference_via_mcp,
    check_acm_benchmark,
    check_pso_alignment,
    check_curriculum_evolution,
]
