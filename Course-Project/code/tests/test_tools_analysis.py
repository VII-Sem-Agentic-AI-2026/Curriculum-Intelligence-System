import pytest
from app import analysis, tools
from app.mcp_client import (mcp_read_accreditation_reference, mcp_read_curriculum, mcp_read_industry_signals,
                            mcp_read_student_performance)


@pytest.fixture(scope="module")
def data():
    cur, ind = mcp_read_curriculum(), mcp_read_industry_signals()
    ref, perf = mcp_read_accreditation_reference(), mcp_read_student_performance()
    cov = tools.compute_skill_coverage(cur, ind).value
    bench = tools.compute_acm_benchmark(cur, ref).value
    stale = tools.compute_stale_content_flags(cur).value
    return dict(cur=cur, ind=ind, cov=cov, bench=bench, stale=stale, perf=perf)


def test_credit_total_is_176(data):
    r = tools.compute_credit_total_check(data["cur"])
    assert r.valid and r.value["computed_total"] == 176


def test_stale_flags_use_catalog_year_codes(data):
    assert "15ECVF101" in {f["course_code"] for f in data["stale"]}


def test_evolution_finds_2026_revision(data):
    titles = {c["title"] for c in tools.compute_curriculum_evolution(data["cur"]).value["recent_courses"]}
    assert "Agentic AI" in titles


def test_real_syllabus_shows_agentic_ai_already_covers_the_frameworks_it_teaches(data):
    # Once the real Agentic AI / Generative AI unit-wise topics are loaded (from the lesson-plan
    # document), these are genuinely "covered_topic", not just "covered_title" -- the department's
    # 2026 revision already teaches LangChain/LangGraph/MCP and RAG, so the system must say so.
    status = {d["id"]: d["status"] for d in data["cov"]["detail"]}
    assert status["agentic_frameworks"] == "covered_topic"
    assert status["rag_vector"] == "covered_topic"
    assert status["mcp_tool_calling"] == "covered_topic"


def test_real_gaps_mlops_and_ai_eval_still_missing(data):
    status = {d["id"]: d["status"] for d in data["cov"]["detail"]}
    assert status["mlops_deploy"] == "missing"
    assert status["ai_eval_observability"] == "missing"
    assert status["cloud_native"] == "elective_only"   # Cloud Computing (24ECAE317) exists but is elective-only
    assert status["cybersecurity"].startswith("covered")


def test_acm_benchmark_flags_hci_missing(data):
    rows = {r["ka_code"]: r["status"] for r in data["bench"]["rows"]}
    assert rows["HCI"] == "missing" and rows["AI"] == "covered"


def test_pso_alignment_valid(data):
    assert tools.compute_pso_alignment(data["cur"]).valid


def test_gaps_are_deterministic_and_grounded(data):
    mk = lambda: analysis.build_gaps(data["cov"], data["bench"], data["stale"], data["cur"], data["perf"])
    g1, g2 = mk(), mk()
    assert analysis.gaps_fingerprint(g1) == analysis.gaps_fingerprint(g2)
    assert all(g["evidence"] for g in g1) and any(g["severity"] == "high" for g in g1)


def test_recommendations_validate_and_fault_is_detected(data):
    mk = lambda: analysis.build_gaps(data["cov"], data["bench"], data["stale"], data["cur"], data["perf"])
    gaps = mk()
    recs = analysis.build_recommendations(gaps, data["cur"])
    ok = {"credit": True, "pso": True}
    assert analysis.validate(gaps, recs, data["cur"], ok, mk)["passed"]
    analysis.inject_fault(recs)
    rep = analysis.validate(gaps, recs, data["cur"], ok, mk)
    assert not rep["passed"] and rep["failing_rec_ids"] == [recs[0]["id"]]


def test_out_of_scope_recommendation_is_rejected(data):
    mk = lambda: analysis.build_gaps(data["cov"], data["bench"], data["stale"], data["cur"], data["perf"])
    gaps = mk()
    recs = analysis.build_recommendations(gaps, data["cur"])
    recs[0]["prerequisites"].append("99FAKE999")
    assert "every recommendation stays within approved program scope" in analysis.validate(gaps, recs, data["cur"], {"credit": True, "pso": True}, mk)["failing"]


def test_pg_pack_changes_recommendation_style(data):
    gaps = analysis.build_gaps(data["cov"], data["bench"], data["stale"], data["cur"], data["perf"])
    ug = analysis.build_recommendations(gaps, data["cur"], "ug_cse_ai")
    pg = analysis.build_recommendations(gaps, data["cur"], "pg_ai")
    assert ug[0]["target_semesters"] != pg[0]["target_semesters"] and len(ug) == len(pg)
