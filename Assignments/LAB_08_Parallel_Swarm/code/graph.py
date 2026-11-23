"""
The whole Coordinator as one LangGraph StateGraph (Labs 1-14).

  Lab 1  clarify -> plan -> revise            (agent loop, not a chatbot)
  Lab 2  LangChain @tools called by the workers (typed, computed values)
  Lab 3  lock_plan / format_document use reusable skills
  Lab 4  memory node: tag + similarity retrieval (BaseRetriever)
  Lab 5  every data read goes through the real MCP server
  Lab 6  SqliteSaver checkpoints, interrupt() gate, step budget, audit callback
  Lab 7  explicit node graph with a validate -> regenerate back-edge
  Lab 8  curriculum_mapping_agent / industry_skills_agent / acm_apni_benchmarking_agent
         run as three independent graph nodes LangGraph schedules concurrently,
         fan_in_specialists merges
  Lab 9  gap_analysis: every gap / recommendation carries an evidence record
  Lab 10 validate + regenerate: diagnose the failing item, repair only that item
  Lab 11 validate is the acceptance suite; nothing reaches the human without it
  Lab 12 governance: roles, department scope, versioned publish, rollback, metrics
  Lab 13 specialist packs (UG CSE-AI, PG AI) change recommendation style/targets
  Lab 14 the Streamlit app wires all of this into a dashboard
"""
from __future__ import annotations

import json
import os
import time
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from . import analysis, governance, skills
from .audit_callback import AuditLogCallbackHandler
from .langchain_tools import (
    check_acm_benchmark, check_credit_totals, check_curriculum_evolution, check_pso_alignment,
    check_skill_coverage, check_stale_courses, read_accreditation_reference_via_mcp,
    read_curriculum_via_mcp, read_industry_signals_via_mcp, read_student_performance_via_mcp,
)
from .llm_client import get_llm
from .memory import RevisionHistoryRetriever

MAX_BUDGET = 40
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "checkpoints", "graph_checkpoints.sqlite")


class GraphState(TypedDict, total=False):
    run_id: str
    user_request: dict
    feedback_rounds: list[str]
    clarified_request: dict
    questions: list[str]
    plan_steps: list[str]
    locked_plan: dict
    pack_key: str
    curriculum_json: str
    industry_json: str
    benchmark_view: dict
    worker_timing: dict
    _cm_seconds: float
    _is_seconds: float
    _bm_seconds: float
    credit_check: dict
    stale_flags: dict
    evolution: dict
    pso_check: dict
    skill_coverage: dict
    performance: dict
    gaps: list[dict]
    gaps_fingerprint: str
    tag_hits: list[dict]
    similarity_hits: list[dict]
    recommendations: list[dict]
    evidence_table: list[dict]
    document_markdown: str
    validation: dict
    attempts: int
    force_fail_countdown: int
    budget_used: int
    gate_decision: str
    adjust_target: str
    approver: dict
    published_version: int
    block_reason: str


def _budget_step(state: GraphState, name: str) -> int:
    used = state.get("budget_used", 0) + 1
    if used > MAX_BUDGET:
        raise RuntimeError(f"Runtime budget of {MAX_BUDGET} steps exhausted at node '{name}'.")
    return used


def _audit(config) -> AuditLogCallbackHandler | None:
    return (config or {}).get("configurable", {}).get("audit")


def _cb(config) -> list:
    a = _audit(config)
    return [a] if a else []


def _log(config, name, inputs, result):
    a = _audit(config)
    if a:
        a.log_manual(name, inputs=inputs, result=result)


# ------------------------------------------------------------- Lab 1 + 12
def clarify_node(state: GraphState, config=None) -> dict:
    req = state["user_request"]
    try:
        governance.check_department_scope(req.get("department", ""))
    except governance.PermissionDenied as e:
        _log(config, "scope_check", req, f"BLOCKED: {e}")
        return {"gate_decision": "blocked_scope", "block_reason": str(e), "budget_used": _budget_step(state, "clarify")}
    llm = get_llm()
    missing = [f for f in ("department", "scope", "cycle") if not req.get(f)]
    questions = []
    if missing:
        raw = llm.complete(f"Generate clarifying questions. Known: {req}. Missing: {missing}.")
        questions = [q.strip("- ").strip() for q in raw.splitlines() if q.strip()]
    _log(config, "clarify", req, {"questions": questions, "scope_check": "passed"})
    return {"clarified_request": dict(req), "questions": questions, "budget_used": _budget_step(state, "clarify")}


def route_after_clarify(state: GraphState) -> str:
    return END if state.get("gate_decision") == "blocked_scope" else "plan"


def plan_node(state: GraphState, config=None) -> dict:
    raw = get_llm().complete(f"Generate a plan for this curriculum review: {state['clarified_request']}")
    steps = [line.split(". ", 1)[-1] for line in raw.splitlines() if line.strip()]
    _log(config, "propose_plan", state["clarified_request"], steps)
    return {"plan_steps": steps, "budget_used": _budget_step(state, "plan")}


def revise_node(state: GraphState, config=None) -> dict:
    llm, steps = get_llm(), list(state["plan_steps"])
    for fb in state.get("feedback_rounds", []):
        note = llm.complete(f"Revise the plan given this feedback: {fb}")
        steps.append(note)
        _log(config, "revise_plan", fb, note)
    return {"plan_steps": steps, "budget_used": _budget_step(state, "revise")}


def lock_plan_node(state: GraphState, config=None) -> dict:
    req = state["clarified_request"]
    locked = skills.plan({"department": req.get("department", "Unspecified"), "scope": req.get("scope", "full curriculum"),
                           "plan_steps": state["plan_steps"]})
    _log(config, "lock_plan (skill)", state["plan_steps"], locked.as_dict())
    return {"locked_plan": locked.as_dict(), "budget_used": _budget_step(state, "lock_plan")}


# ------------------------------------------------------------------ Lab 13
def specialist_pack_node(state: GraphState, config=None) -> dict:
    key = state["clarified_request"].get("pack", "ug_cse_ai")
    if key not in analysis.SPECIALIST_PACKS:
        key = "ug_cse_ai"
    _log(config, "specialist_pack", key, analysis.SPECIALIST_PACKS[key]["label"])
    return {"pack_key": key, "budget_used": _budget_step(state, "specialist_pack")}


# ------------------------------------------------------------------ Lab 8
# Three distinct agents (Agent Roster #1-#3 in the book), each a real graph
# node with its own name, its own typed outputs and its own audit identity --
# not one fused function. They share no dependency on each other, so
# LangGraph's Pregel scheduler runs them in the same superstep concurrently
# (a thread per ready node); fan_in_specialists_node is the merge/selector
# the book's Lab 8 names, and only it depends on all three.
def curriculum_mapping_node(state: GraphState, config=None) -> dict:
    t0, cfg = time.time(), {"callbacks": _cb(config)}
    cur = read_curriculum_via_mcp.invoke({"course_code": ""}, config=cfg)
    out = {"curriculum_json": cur,
           "credit_check": json.loads(check_credit_totals.invoke({"curriculum_json": cur}, config=cfg)),
           "stale_flags": json.loads(check_stale_courses.invoke({"curriculum_json": cur}, config=cfg)),
           "evolution": json.loads(check_curriculum_evolution.invoke({"curriculum_json": cur}, config=cfg)),
           "pso_check": json.loads(check_pso_alignment.invoke({"curriculum_json": cur}, config=cfg)),
           "_cm_seconds": round(time.time() - t0, 2)}
    _log(config, "curriculum_mapping_agent", "read_curriculum via MCP", {"seconds": out["_cm_seconds"]})
    return out  # budget charged once, in fan_in_specialists_node (avoids concurrent-write conflict)


def industry_skills_node(state: GraphState, config=None) -> dict:
    t0, cfg = time.time(), {"callbacks": _cb(config)}
    ind = read_industry_signals_via_mcp.invoke({}, config=cfg)
    perf = read_student_performance_via_mcp.invoke({"course_code": ""}, config=cfg)
    out = {"industry_json": ind, "performance": json.loads(perf), "_is_seconds": round(time.time() - t0, 2)}
    _log(config, "industry_skills_agent", "read_industry_signals + read_student_performance via MCP",
         {"seconds": out["_is_seconds"]})
    return out


def acm_apni_benchmarking_node(state: GraphState, config=None) -> dict:
    t0, cfg = time.time(), {"callbacks": _cb(config)}
    cur = read_curriculum_via_mcp.invoke({"course_code": ""}, config=cfg)
    ref = read_accreditation_reference_via_mcp.invoke({}, config=cfg)
    bench = json.loads(check_acm_benchmark.invoke({"curriculum_json": cur, "reference_json": ref}, config=cfg))
    out = {"benchmark_view": bench, "_bm_seconds": round(time.time() - t0, 2)}
    _log(config, "acm_apni_benchmarking_agent", "read_curriculum + read_accreditation_reference via MCP (APNI: not supplied)",
         {"seconds": out["_bm_seconds"]})
    return out


def fan_in_specialists_node(state: GraphState, config=None) -> dict:
    """Lab 8 merge/selector: all three parallel views are in by the time this
    node's dependencies (all three above) are satisfied."""
    cfg = {"callbacks": _cb(config)}
    coverage = json.loads(check_skill_coverage.invoke(
        {"curriculum_json": state["curriculum_json"], "industry_signals_json": state["industry_json"]}, config=cfg))
    per_agent = {"curriculum_mapping": state["_cm_seconds"], "industry_skills": state["_is_seconds"],
                 "acm_apni_benchmarking": state["_bm_seconds"]}
    timing = {"workers_seconds": per_agent, "sequential_estimate_seconds": round(sum(per_agent.values()), 2),
              "parallel_wall_seconds": round(max(per_agent.values()), 2)}
    _log(config, "fan_in_specialists (merge)", list(per_agent), timing)
    used = state.get("budget_used", 0) + 4  # charges for the 3 parallel agents + this merge
    if used > MAX_BUDGET:
        raise RuntimeError(f"Runtime budget of {MAX_BUDGET} steps exhausted at node 'fan_in_specialists'.")
    return {"skill_coverage": coverage, "worker_timing": timing, "budget_used": used}


# ------------------------------------------------------------- Lab 7 / 9
def _build_gaps(state: GraphState) -> list[dict]:
    return analysis.build_gaps(state["skill_coverage"]["value"], state["benchmark_view"]["value"],
                                state["stale_flags"]["value"], json.loads(state["curriculum_json"]), state["performance"])


def gap_analysis_node(state: GraphState, config=None) -> dict:
    gaps = _build_gaps(state)
    fp = analysis.gaps_fingerprint(gaps)
    _log(config, "gap_analysis", {"coverage_pct": state["skill_coverage"]["value"]["coverage_pct"]},
          {"gaps": len(gaps), "fingerprint": fp})
    return {"gaps": gaps, "gaps_fingerprint": fp, "budget_used": _budget_step(state, "gap_analysis")}


def memory_node(state: GraphState, config=None) -> dict:
    retriever = RevisionHistoryRetriever(k=3)
    tag_hits = retriever.retrieve_by_tags(["cloud", "attainment-gap", "agentic-ai"])
    missing = state["skill_coverage"]["value"]["missing_skills"]
    query = "industry expectations gap " + " ".join(missing[:3])
    docs = retriever.invoke(query)
    sims = [{"text": d.page_content, **d.metadata} for d in docs]
    _log(config, "memory_retrieve", query, {"tag_hits": len(tag_hits), "similarity_hits": len(sims)})
    return {"tag_hits": tag_hits, "similarity_hits": sims, "budget_used": _budget_step(state, "memory")}


def recommend_node(state: GraphState, config=None) -> dict:
    cur = json.loads(state["curriculum_json"])
    recs = analysis.build_recommendations(state["gaps"], cur, state["pack_key"])
    countdown = state.get("force_fail_countdown", 0)
    if countdown > 0:
        analysis.inject_fault(recs)   # failure injection (Lab 10 test)
        _log(config, "fault_injection", f"countdown={countdown}", "evidence stripped from first recommendation")
    _log(config, "recommendations", len(state["gaps"]), {"count": len(recs)})
    return {"recommendations": recs, "evidence_table": analysis.evidence_table(state["gaps"], recs),
            "budget_used": _budget_step(state, "recommend")}


# ------------------------------------------------------------- Lab 3 / 14
def format_node(state: GraphState, config=None) -> dict:
    req = state["clarified_request"]
    cov = state["skill_coverage"]["value"]
    bench = state["benchmark_view"]["value"]
    pack = analysis.SPECIALIST_PACKS[state["pack_key"]]["label"]
    doc = skills.format_curriculum({
        "title": f"Curriculum Revision Recommendation (draft) - {req.get('department', '')}",
        "sections": {
            "Request and specialist pack": [f"Department: {req.get('department')}", f"Scope: {req.get('scope')}",
                                              f"Cycle: {req.get('cycle')}", f"Pack: {pack}"],
            "Summary": [
                f"Industry skill coverage (courses exist): {cov['coverage_pct']}%; syllabus-verified: {cov['strict_coverage_pct']}%",
                f"ACM CS2023 knowledge-area alignment: {bench['alignment_pct']}%",
                f"Gaps found: {len(state['gaps'])}; recommendations drafted: {len(state['recommendations'])}",
                "Status: DRAFT. Nothing is adopted without HoD / Dean / Board of Studies approval."],
            "Curriculum evolution already made by the department": [
                f"{c['course_code']} {c['title']} (catalog year {c['catalog_year']})" for c in state["evolution"]["value"]["recent_courses"]],
            "ACM CS2023 benchmark": [f"{r['ka_code']} {r['ka_name']}: {r['status']} (core: {', '.join(r['core_courses'][:3]) or 'none'})" for r in bench["rows"]],
            "Industry skill coverage": [f"[{d['status']}] {d['skill']} ({d['horizon']}, {d['trend']})" for d in cov["detail"]],
            "Gap report": [f"{g['id']} [{g['severity']}] {g['title']} -- {len(g['evidence'])} evidence record(s)" +
                            (f" -- CONFLICTING SIGNAL: {g['conflicting']}" if g["conflicting"] else "") for g in state["gaps"]],
            "Recommendations": [f"{r['id']} ({r['action_type']}, host: {r['host']}) {r['title']} | gaps: {', '.join(r['gap_ids'])} | "
                                  f"prerequisites: {', '.join(r['prerequisites']) or 'none'} | board approval required: {r['needs_board_of_studies']}"
                                  for r in state["recommendations"]],
            "Related prior revisions (memory)": [h["text"] for h in state["tag_hits"]],
            "Student performance context (SIMULATED data; not used as Gap Analysis evidence, see Lab 7/9 guardrail)": [
                f"{a['title']} ({a['course_code']}): {a['avg_co_attainment_pct']}% -- {a['notes']}"
                for a in state["performance"].get("course_attainment", [])],
        },
    })
    _log(config, "format_document (skill)", "assembled sections", doc.title)
    return {"document_markdown": doc.as_markdown(), "budget_used": _budget_step(state, "format")}


# ------------------------------------------------------------ Lab 10 / 11
def validate_node(state: GraphState, config=None) -> dict:
    cur = json.loads(state["curriculum_json"])
    report = analysis.validate(state["gaps"], state["recommendations"], cur,
                                {"credit": state["credit_check"]["valid"], "pso": state["pso_check"]["valid"]},
                                lambda: _build_gaps(state))
    attempts = state.get("attempts", 0) + 1
    _log(config, "validate (acceptance suite)", {"attempt": attempts},
          {"passed": report["passed"], "failing": report["failing"], "diagnosis": report["diagnosis"]})
    return {"validation": report, "attempts": attempts, "budget_used": _budget_step(state, "validate")}


def route_after_validate(state: GraphState) -> str:
    if state["validation"]["passed"]:
        return "human_gate"
    if state.get("budget_used", 0) + 3 > MAX_BUDGET:
        return "budget_exceeded"
    return "regenerate"


def regenerate_node(state: GraphState, config=None) -> dict:
    """Repair ONLY the failing recommendations (never rebuild good work)."""
    cur = json.loads(state["curriculum_json"])
    failing = set(state["validation"]["failing_rec_ids"])
    recs = []
    for r in state["recommendations"]:
        if r["id"] in failing:
            fresh = analysis.build_recommendations(state["gaps"], cur, state["pack_key"], only_keys={r["key"]})[0]
            fresh["id"] = r["id"]
            recs.append(fresh)
        else:
            recs.append(r)
    countdown = max(0, state.get("force_fail_countdown", 0) - 1)
    if countdown > 0:
        analysis.inject_fault(recs)
    _log(config, "regenerate (targeted)", sorted(failing), {"repaired": sorted(failing), "untouched": len(state["recommendations"]) - len(failing)})
    return {"recommendations": recs, "evidence_table": analysis.evidence_table(state["gaps"], recs),
            "force_fail_countdown": countdown, "budget_used": _budget_step(state, "regenerate")}


def budget_exceeded_node(state: GraphState, config=None) -> dict:
    _log(config, "escalate", "budget exhausted", state["validation"]["diagnosis"])
    return {"gate_decision": "budget_exceeded"}


# ------------------------------------------------------------- Lab 6 / 12
ADJUST_TARGETS = {
    "recommendations": "recommend",          # Group E only: re-propose recommendations for the same gaps
    "evidence_gathering": "specialist_pack",  # Groups A/B/C: re-run the parallel view-building agents
}


def human_gate_node(state: GraphState, config=None) -> dict:
    decision = interrupt({
        "message": "Approve, adjust, or reject this curriculum revision recommendation?",
        "gaps": len(state["gaps"]), "recommendations": len(state["recommendations"]),
        # Was truncated to 600 chars, which cut the "Curriculum evolution" list off after its
        # first line (e.g. showing Embedded Intelligent Systems but not Generative AI / Agentic
        # AI, which follow it). Widened so that section -- and the one after it -- are visible
        # at the gate instead of only in the downloaded document.
        "document_preview": state["document_markdown"][:2500],
        "adjust_targets": list(ADJUST_TARGETS),
    })
    d = decision if isinstance(decision, dict) else {"action": "approve" if decision else "reject"}
    approver = {"name": d.get("name", "unknown"), "role": d.get("role", "unknown")}
    action = d.get("action", "approve" if d.get("approved") else "reject")  # back-compat with approved: bool

    if action == "adjust":
        target = d.get("adjust_target")
        if target not in ADJUST_TARGETS:
            _log(config, "human_gate", approver, f"ADJUST rejected: unknown target '{target}'")
            return {"gate_decision": "denied", "approver": approver}
        note = d.get("note", "")
        _log(config, "human_gate", approver, f"ADJUST -> resuming {target} ({ADJUST_TARGETS[target]}). Note: {note}")
        return {"gate_decision": "adjust", "approver": approver, "adjust_target": target}

    if action == "reject":
        _log(config, "human_gate", approver, "REJECTED")
        return {"gate_decision": "denied", "approver": approver}

    try:
        governance.check_approver(approver["role"])
    except governance.PermissionDenied as e:
        _log(config, "human_gate", approver, f"REJECTED (permission): {e}")
        return {"gate_decision": "denied_permission", "approver": approver}
    _log(config, "human_gate", approver, "APPROVED")
    return {"gate_decision": "approved", "approver": approver}


def route_after_gate(state: GraphState) -> str:
    gd = state.get("gate_decision")
    if gd == "approved":
        return "publish"
    if gd == "adjust":
        return ADJUST_TARGETS[state["adjust_target"]]
    return END


def publish_node(state: GraphState, config=None) -> dict:
    ap = state["approver"]
    for r in state["recommendations"]:
        r["status"] = f"approved by {ap['name']} ({ap['role']})"
    version = governance.publish(state["document_markdown"],
                                  {"gaps": state["gaps"], "recommendations": state["recommendations"],
                                   "evidence_table": state["evidence_table"]}, ap["role"], ap["name"], state["run_id"])
    gaps = state["gaps"]
    governance.record_metrics(state["run_id"], {
        "version": version, "gaps": len(gaps), "high_severity_gaps": sum(1 for g in gaps if g["severity"] == "high"),
        "recommendations": len(state["recommendations"]), "validation_attempts": state.get("attempts", 1),
        "coverage_pct": state["skill_coverage"]["value"]["coverage_pct"],
        "acm_alignment_pct": state["benchmark_view"]["value"]["alignment_pct"],
        "evidence_records": len(state["evidence_table"])})
    _log(config, "publish (governed)", ap, f"version v{version}")
    return {"published_version": version, "recommendations": state["recommendations"], "budget_used": _budget_step(state, "publish")}


def build_graph_builder() -> StateGraph:
    g = StateGraph(GraphState)
    for name, fn in [("clarify", clarify_node), ("plan", plan_node), ("revise", revise_node), ("lock_plan", lock_plan_node),
                      ("specialist_pack", specialist_pack_node),
                      ("curriculum_mapping_agent", curriculum_mapping_node),
                      ("industry_skills_agent", industry_skills_node),
                      ("acm_apni_benchmarking_agent", acm_apni_benchmarking_node),
                      ("fan_in_specialists", fan_in_specialists_node),
                      ("gap_analysis", gap_analysis_node), ("memory", memory_node), ("recommend", recommend_node),
                      ("format", format_node), ("validate", validate_node), ("regenerate", regenerate_node),
                      ("budget_exceeded", budget_exceeded_node), ("human_gate", human_gate_node), ("publish", publish_node)]:
        g.add_node(name, fn)
    g.add_edge(START, "clarify")
    g.add_conditional_edges("clarify", route_after_clarify, {"plan": "plan", END: END})
    for a, b in [("plan", "revise"), ("revise", "lock_plan"), ("lock_plan", "specialist_pack")]:
        g.add_edge(a, b)
    # fan-out: three independent agents from one plan (Agent Roster #1-#3)
    for worker in ("curriculum_mapping_agent", "industry_skills_agent", "acm_apni_benchmarking_agent"):
        g.add_edge("specialist_pack", worker)
        g.add_edge(worker, "fan_in_specialists")   # fan-in: merge waits on all three
    for a, b in [("fan_in_specialists", "gap_analysis"), ("gap_analysis", "memory"), ("memory", "recommend"),
                  ("recommend", "format"), ("format", "validate")]:
        g.add_edge(a, b)
    g.add_conditional_edges("validate", route_after_validate,
                             {"human_gate": "human_gate", "regenerate": "regenerate", "budget_exceeded": "budget_exceeded"})
    g.add_edge("regenerate", "format")   # re-assemble the document from repaired recommendations
    g.add_edge("budget_exceeded", END)
    g.add_conditional_edges("human_gate", route_after_gate,
                             {"publish": "publish", "recommend": "recommend", "specialist_pack": "specialist_pack", END: END})
    g.add_edge("publish", END)
    return g


def get_checkpointer_cm():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return SqliteSaver.from_conn_string(DB_PATH)
