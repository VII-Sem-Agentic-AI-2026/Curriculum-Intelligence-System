import uuid
import pytest
from langgraph.types import Command
from app import governance
from app.audit_callback import AuditLogCallbackHandler
from app.graph import build_graph_builder, get_checkpointer_cm


def run(force=0, dept="CSE (AI)", pack="ug_cse_ai"):
    rid = f"pytest-{uuid.uuid4().hex[:8]}"
    audit = AuditLogCallbackHandler(rid)
    cm = get_checkpointer_cm()
    with cm as cp:
        g = build_graph_builder().compile(checkpointer=cp)
        cfg = {"configurable": {"thread_id": rid, "audit": audit}}
        out = g.invoke({"run_id": rid, "user_request": {"department": dept, "scope": "full", "cycle": "annual", "pack": pack},
                         "feedback_rounds": [], "budget_used": 0, "force_fail_countdown": force}, config=cfg)
    return rid, audit, out


def resume(rid, audit, payload):
    with get_checkpointer_cm() as cp:
        g = build_graph_builder().compile(checkpointer=cp)
        return g.invoke(Command(resume=payload), config={"configurable": {"thread_id": rid, "audit": audit}})


def test_pipeline_pauses_at_gate_with_parallel_speedup_and_passing_suite():
    rid, audit, out = run()
    assert out.get("__interrupt__") and out["validation"]["passed"]
    t = out["worker_timing"]
    assert t["parallel_wall_seconds"] < t["sequential_estimate_seconds"]
    assert out["gaps"] and out["recommendations"] and out["evidence_table"]


def test_resume_in_fresh_checkpointer_and_versioned_publish():
    rid, audit, _ = run()
    out = resume(rid, audit, {"approved": True, "role": "HoD", "name": "Test HoD"})
    assert out["gate_decision"] == "approved" and out["published_version"] >= 1
    assert governance.current_version() == out["published_version"]
    assert all(r["status"].startswith("approved") for r in out["recommendations"])


def test_unauthorised_role_cannot_publish():
    rid, audit, _ = run()
    before = governance.current_version()
    out = resume(rid, audit, {"approved": True, "role": "Faculty", "name": "Someone"})
    assert out["gate_decision"] == "denied_permission" and governance.current_version() == before


def test_denied_gate_publishes_nothing():
    rid, audit, _ = run()
    before = governance.current_version()
    assert resume(rid, audit, {"approved": False, "role": "HoD", "name": "x"})["gate_decision"] == "denied"
    assert governance.current_version() == before


def test_targeted_self_repair_after_injected_faults():
    rid, audit, out = run(force=2)
    assert out["attempts"] == 3 and out["validation"]["passed"]
    entries = [e for e in audit.all_entries() if e["name"] == "regenerate (targeted)"]
    assert len(entries) == 2 and entries[0]["result"]["untouched"] >= 1


def test_budget_exhaustion_escalates():
    rid, audit, out = run(force=999)
    assert out["gate_decision"] == "budget_exceeded" and not out.get("__interrupt__")


def test_other_department_is_blocked_before_any_data_is_read():
    rid, audit, out = run(dept="ECE")
    assert out["gate_decision"] == "blocked_scope"
    assert not [e for e in audit.all_entries() if e["kind"] == "tool"]


def test_every_mcp_tool_call_is_audit_logged_including_parallel_workers():
    rid, audit, out = run()
    names = {e["name"] for e in audit.all_entries() if e["kind"] == "tool"}
    assert {"read_curriculum_via_mcp", "read_industry_signals_via_mcp", "read_accreditation_reference_via_mcp", "check_acm_benchmark"} <= names


def test_three_specialist_agents_are_distinct_graph_nodes_with_real_speedup():
    rid, audit, out = run()
    agent_names = {e["name"] for e in audit.all_entries()
                    if e["name"] in {"curriculum_mapping_agent", "industry_skills_agent", "acm_apni_benchmarking_agent"}}
    assert agent_names == {"curriculum_mapping_agent", "industry_skills_agent", "acm_apni_benchmarking_agent"}
    t = out["worker_timing"]
    assert t["parallel_wall_seconds"] < t["sequential_estimate_seconds"]


def test_adjust_resumes_the_relevant_agent_and_reaches_a_fresh_gate():
    # Agent Roster row 6: "approves, adjusts, or rejects... AURA then resumes the relevant agent
    # for corrections." This exercises the "adjust" action end to end across three separate
    # invoke() calls against the same checkpointed thread.
    rid, audit, out = run()
    assert out.get("__interrupt__")
    with get_checkpointer_cm() as cp:
        g = build_graph_builder().compile(checkpointer=cp)
        cfg = {"configurable": {"thread_id": rid, "audit": audit}}
        out2 = g.invoke(Command(resume={"action": "adjust", "adjust_target": "recommendations",
                                          "role": "HoD", "name": "Prof Adjust", "note": "test note"}), config=cfg)
    assert out2.get("__interrupt__") and out2["gate_decision"] == "adjust"
    assert out2["budget_used"] > out["budget_used"]
    with get_checkpointer_cm() as cp:
        g = build_graph_builder().compile(checkpointer=cp)
        cfg = {"configurable": {"thread_id": rid, "audit": audit}}
        out3 = g.invoke(Command(resume={"action": "approve", "role": "HoD", "name": "Prof Adjust"}), config=cfg)
    assert out3["gate_decision"] == "approved" and out3["published_version"] >= 1
    assert any(e["name"] == "human_gate" and "ADJUST" in str(e["result"]) for e in audit.all_entries())


def test_rollback_moves_pointer_and_is_recorded():
    v1 = governance.publish("doc1", {}, "HoD", "A", "r1")
    v2 = governance.publish("doc2", {}, "HoD", "A", "r2")
    assert governance.current_version() == v2
    governance.rollback(v1, "Dean (Academics)", "B")
    assert governance.current_version() == v1 and governance.list_history()[-1]["event"] == "rollback"
    with pytest.raises(governance.PermissionDenied):
        governance.rollback(v2, "Faculty", "C")
