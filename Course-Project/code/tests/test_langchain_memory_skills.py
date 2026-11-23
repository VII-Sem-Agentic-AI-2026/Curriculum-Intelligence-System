import json
from langchain_core.retrievers import BaseRetriever
from app import skills
from app.langchain_tools import check_credit_totals, check_skill_coverage, read_curriculum_via_mcp, read_industry_signals_via_mcp
from app.memory import RevisionHistoryRetriever, RunState


def test_langchain_tool_chain_through_mcp():
    cur = read_curriculum_via_mcp.invoke({"course_code": ""})
    assert json.loads(check_credit_totals.invoke({"curriculum_json": cur}))["valid"]
    ind = read_industry_signals_via_mcp.invoke({})
    cov = json.loads(check_skill_coverage.invoke({"curriculum_json": cur, "industry_signals_json": ind}))
    assert 0 <= cov["value"]["coverage_pct"] <= 100


def test_retriever_is_langchain_and_ranks_relevant_first():
    r = RevisionHistoryRetriever(k=3)
    assert isinstance(r, BaseRetriever)
    docs = r.invoke("agentic AI new course added in 2026 revision autonomous decision-making")
    assert docs and docs[0].metadata["course_code"] == "26ECAC401"
    assert r.retrieve_by_tags(["rag"])


def test_run_state_is_not_persistent():
    assert not hasattr(RunState(run_id="x"), "save")


def test_skills_reusable_across_departments():
    a = skills.plan({"department": "CSE (AI)", "scope": "full", "plan_steps": ["a"]})
    b = skills.plan({"department": "ECE", "scope": "electives", "plan_steps": ["x", "y"]})
    assert a.locked and b.locked and len(b.steps) == 2
    assert "# T" in skills.format_curriculum({"title": "T", "sections": {"S": ["x"]}}).as_markdown()
