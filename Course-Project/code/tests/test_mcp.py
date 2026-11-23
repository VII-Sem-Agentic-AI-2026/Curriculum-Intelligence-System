from app.mcp_client import (list_mcp_capabilities, mcp_read_accreditation_reference, mcp_read_curriculum,
                            mcp_read_industry_signals, mcp_read_revision_history, mcp_read_student_performance)


def test_mcp_server_advertises_tools_and_resource():
    caps = {c["name"] for c in list_mcp_capabilities()}
    assert {"read_curriculum", "read_industry_signals", "read_student_performance",
            "read_revision_history", "read_accreditation_reference", "cis://accreditation-standards"} <= caps


def test_curriculum_is_real_2023_27_with_2026_revision():
    d = mcp_read_curriculum()
    assert d["batch_year"] == "2023-27" and d["total_program_credits"] == 176
    titles = {c["title"] for c in d["courses"]}
    assert {"Agentic AI", "Generative AI", "Cryptography & Network Security"} <= titles


def test_filter_by_course_code():
    assert mcp_read_curriculum(course_code="26ECAC401")["title"] == "Agentic AI"


def test_every_industry_skill_has_sources():
    for s in mcp_read_industry_signals()["aggregated_skill_demand"]:
        assert s["sources"] and s["horizon"] in ("present", "emerging")


def test_performance_data_is_labelled_simulated():
    assert "SIMULATED" in mcp_read_student_performance()["_source"]


def test_revision_history_marks_real_bos_entries_separately_from_simulated_ones():
    items = mcp_read_revision_history()["items"]
    real = [i for i in items if not i["simulated"]]
    simulated = [i for i in items if i["simulated"]]
    assert real and simulated  # both kinds present, and each is explicitly tagged
    assert any("Board of Studies" in i["text"] for i in real)


def test_accreditation_reference_has_17_acm_areas_and_department_outcomes():
    r = mcp_read_accreditation_reference()
    assert len(r["acm_cs2023_knowledge_areas"]) == 17 and "PSO2" in r["department_outcomes"]["PSO"]
