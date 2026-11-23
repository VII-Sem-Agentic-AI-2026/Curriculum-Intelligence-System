"""
Curriculum Intelligence System (Worklet-5) -- Streamlit demo, Labs 1-14.

Run:  streamlit run streamlit_app.py
White background, no emoji. Every figure on screen is computed by the
LangGraph pipeline from real data reached through the MCP server.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

import streamlit as st
from langgraph.types import Command

sys.path.insert(0, str(Path(__file__).parent))

from app import analysis, governance
from app.audit_callback import AuditLogCallbackHandler
from app.graph import ADJUST_TARGETS, MAX_BUDGET, build_graph_builder, get_checkpointer_cm
from app.mcp_client import list_mcp_capabilities, mcp_read_curriculum, mcp_read_industry_signals

st.set_page_config(page_title="Curriculum Intelligence System", layout="wide")
st.markdown("""<style>
.stApp {background-color:#FFFFFF;} section[data-testid="stSidebar"] {background-color:#F4F6F9;}
h1,h2,h3 {color:#1F3A5F;} .small {color:#55637a;font-size:0.9rem;}
</style>""", unsafe_allow_html=True)

SEV = {"high": "HIGH", "medium": "MEDIUM", "low": "LOW"}


@st.cache_data(show_spinner=False)
def _curriculum():
    return mcp_read_curriculum()


@st.cache_data(show_spinner=False)
def _industry():
    return mcp_read_industry_signals()


def _new_session():
    for k in list(st.session_state.keys()):
        del st.session_state[k]


def _init():
    if "run_id" not in st.session_state:
        st.session_state.run_id = f"run-{uuid.uuid4().hex[:8]}"
        st.session_state.audit = AuditLogCallbackHandler(st.session_state.run_id)
        st.session_state.stage = "form"
        st.session_state.result = None


_init()

st.title("Curriculum Intelligence System")
st.markdown('<div class="small">Worklet-5 | Agentic AI (26ECAC401) | KLE Technological University, CSE (AI) | '
            'Continuous curriculum, industry and accreditation mapping with human-approved revision recommendations</div>',
            unsafe_allow_html=True)

with st.sidebar:
    st.header("What is real in this demo")
    st.markdown(
        "**Real data**\n- KLE Tech CSE-AI 2023-27 curriculum, semesters I to VIII, including the 2026-27 revision "
        "(Agentic AI, Cryptography and Network Security)\n"
        "- Real unit-wise topics for Agentic AI, Generative AI and others, from the lesson-plan document\n"
        "- Real Board of Studies resolutions (18 April 2026), including points raised but not yet adopted\n"
        "- Department PEO/PO/PSO statements\n- Industry demand collected on 2026-10-20 from LinkedIn-hosted postings, "
        "Naukri Campus, and company career pages (each skill has source URLs)\n\n"
        "**Simulated and labelled**\n- Student attainment and placement feedback\n"
        "- A few illustrative committee notes, shown alongside the real resolutions and marked separately\n\n"
        "**Not supplied**\n- APNI clause text (benchmark is a documented stub)")
    st.divider()
    st.markdown("**Stack**\n- MCP server (Anthropic mcp SDK, stdio)\n- LangChain tools, callback audit log, retriever\n"
                "- LangGraph state graph, SQLite checkpoints, interrupt() approval gate")
    if st.button("Start a new run"):
        _new_session()
        st.rerun()

tabs = st.tabs(["Run pipeline", "Dashboard", "Gaps and recommendations", "Curriculum and industry data",
                "Governance", "Audit log", "Agent roster", "MCP and architecture"])
T_RUN, T_DASH, T_GAPS, T_DATA, T_GOV, T_AUDIT, T_ROSTER, T_MCP = tabs

AGENT_ROSTER = [
    {"order": 0, "agent": "apniLeap AURA Coordinator", "node(s)": "clarify, plan, revise, lock_plan, specialist_pack, publish",
     "role_and_communication": "Receives the request, checks permissions, creates the run plan, initialises agents with scoped instructions, monitors state.",
     "guardrails": "Never bypass human approval; enforce data scope, audit logging, source citation, exception routing."},
    {"order": 1, "agent": "Group A: Curriculum Mapping Agent", "node(s)": "curriculum_mapping_agent",
     "role_and_communication": "Maps courses, credit structure and unit-wise content. Task packet from AURA, runs in parallel with Groups B and C, returns the structured curriculum map.",
     "guardrails": "Use only the approved curriculum document and syllabus; never infer an unstated course outcome; flag outdated or missing syllabus sections."},
    {"order": 2, "agent": "Group B: Industry Skills Agent", "node(s)": "industry_skills_agent",
     "role_and_communication": "Aggregates industry-demanded skills. Task packet from AURA, runs in parallel with Groups A and C, returns a ranked skills list.",
     "guardrails": "Pull only from authorised sources; cite source and date for every trend; flag low-confidence or single-source trends."},
    {"order": 3, "agent": "Group C: ACM/APNI Benchmarking Agent", "node(s)": "acm_apni_benchmarking_agent",
     "role_and_communication": "Benchmarks against ACM and APNI. Task packet from AURA, runs in parallel with Groups A and B, returns a benchmarking report.",
     "guardrails": "Use only the current approved version; cite the specific clause behind every comparison; never claim compliance without a matched clause."},
    {"order": 4, "agent": "Group D: Gap Analysis Agent", "node(s)": "gap_analysis (fan_in_specialists merges A/B/C first)",
     "role_and_communication": "Compares the three views. Receives the combined A/B/C output via AURA, returns a severity-and-evidence gap report.",
     "guardrails": "Tie every gap to evidence from at least one of A/B/C; never invent a gap; flag conflicting signals for human interpretation."},
    {"order": 5, "agent": "Group E: Recommendation Agent", "node(s)": "recommend",
     "role_and_communication": "Proposes revisions tied to each gap. Receives the gap report via AURA, returns evidence-linked recommendations.",
     "guardrails": "Tie every recommendation to a gap and its evidence; never propose outside approved program scope; flag significant credit/structure impact."},
    {"order": 6, "agent": "HoD / Dean (Academics) / Board of Studies Review", "node(s)": "human_gate",
     "role_and_communication": "Approves, adjusts, or rejects. AURA then resumes the relevant agent (Group E, or Groups A-C) for corrections.",
     "guardrails": "Board of Studies decision is the final authority for adopting a curriculum revision."},
]
res = st.session_state.result


def _invoke(payload_or_command):
    with get_checkpointer_cm() as cp:
        graph = build_graph_builder().compile(checkpointer=cp)
        cfg = {"configurable": {"thread_id": st.session_state.run_id, "audit": st.session_state.audit}}
        return graph.invoke(payload_or_command, config=cfg)


# ------------------------------------------------------------------ RUN
with T_RUN:
    stage = st.session_state.stage
    if stage == "form":
        st.subheader("Step 1. Submit a curriculum review request")
        c1, c2, c3, c4 = st.columns(4)
        department = c1.text_input("Department", value="CSE (AI)")
        pack = c2.selectbox("Specialist pack (Lab 13)", list(analysis.SPECIALIST_PACKS),
                             format_func=lambda k: analysis.SPECIALIST_PACKS[k]["label"])
        scope = c3.selectbox("Scope", ["full curriculum", "semesters V to VIII", "electives only"])
        cycle = c4.selectbox("Cycle", ["annual review", "triggered by placement feedback"])
        feedback = st.text_area("Planning feedback (applied in the revise step)",
                                 value="Prioritise agentic AI, RAG and MLOps skills, and include emerging skills.")
        force = st.slider("Inject N validation faults to demonstrate targeted self-repair (Lab 10). 0 = normal run.", 0, 3, 0)
        st.caption("Try department 'ECE' to see the confidentiality guard block the request (Lab 12).")
        if st.button("Run pipeline", type="primary"):
            with st.spinner("Running the LangGraph pipeline (MCP reads, parallel specialists, gap analysis, validation)..."):
                try:
                    out = _invoke({"run_id": st.session_state.run_id,
                                    "user_request": {"department": department, "scope": scope, "cycle": cycle, "pack": pack},
                                    "feedback_rounds": [feedback] if feedback.strip() else [],
                                    "budget_used": 0, "force_fail_countdown": force})
                except RuntimeError as e:
                    out = {"gate_decision": "budget_exceeded", "block_reason": str(e)}
            st.session_state.result = out
            if out.get("__interrupt__"):
                st.session_state.stage = "awaiting"
                st.session_state.payload = out["__interrupt__"][0].value
            elif out.get("gate_decision") == "blocked_scope":
                st.session_state.stage = "blocked"
            else:
                st.session_state.stage = "budget"
            st.rerun()

    elif stage == "blocked":
        st.error("Request blocked by the department-confidentiality guard. " + st.session_state.result.get("block_reason", ""))
    elif stage == "budget":
        r = st.session_state.result
        st.error("Run escalated: the step budget was exhausted before validation passed. "
                  + (r.get("validation", {}).get("diagnosis") or r.get("block_reason", "")))
        st.info("This is the bounded-retry guardrail working as designed; nothing was published.")
    elif stage in ("awaiting", "done", "denied"):
        st.subheader("Step 2. Pipeline result")
        v = res["validation"]
        a, b, c, d = st.columns(4)
        a.metric("Acceptance suite", "PASS" if v["passed"] else "FAIL", f"{res.get('attempts', 1)} attempt(s)")
        b.metric("Skill coverage", f"{res['skill_coverage']['value']['coverage_pct']}%")
        c.metric("ACM CS2023 alignment", f"{res['benchmark_view']['value']['alignment_pct']}%")
        d.metric("Gaps / recommendations", f"{len(res['gaps'])} / {len(res['recommendations'])}")
        tm = res["worker_timing"]
        st.markdown(f"Parallel swarm (Lab 8): wall-clock **{tm['parallel_wall_seconds']} s** versus "
                    f"**{tm['sequential_estimate_seconds']} s** if the three agents ran one after another. Workers: {tm['workers_seconds']}")
        st.markdown("**Acceptance suite checks**")
        st.dataframe([{"check": x["check"], "result": "PASS" if x["passed"] else "FAIL", "detail": x["detail"]} for x in v["checks"]],
                      width="stretch", hide_index=True)
        if res.get("attempts", 1) > 1:
            st.success(f"Self-repair: validation failed {res['attempts'] - 1} time(s); only the failing recommendation was regenerated each time.")

        if stage == "awaiting":
            st.divider()
            st.subheader("Step 3. Human approval gate (hard stop)")
            st.warning(st.session_state.payload["message"] + " Nothing is published until an authorised person decides.")
            st.code(st.session_state.payload["document_preview"], language="markdown")
            g1, g2 = st.columns(2)
            role = g1.selectbox("Your role", ["HoD", "Dean (Academics)", "Board of Studies", "Faculty"])
            name = g2.text_input("Your name", value="")
            st.caption("Approve publishes a versioned release. Adjust sends the draft back to the named agent "
                       "for correction and returns to this gate. Reject ends the run with nothing published.")
            adjust_target = st.selectbox(
                "If adjusting, resume which agent", list(ADJUST_TARGETS),
                format_func=lambda k: "Group E: Recommendation Agent only" if k == "recommendations"
                else "Groups A to C: Curriculum Mapping / Industry Skills / ACM-APNI Benchmarking Agents")
            note = st.text_input("Note for the resumed agent (optional)", value="")
            b1, b2, b3 = st.columns(3)
            if b1.button("Approve and publish", type="primary"):
                with st.spinner("Publishing a versioned release..."):
                    out = _invoke(Command(resume={"action": "approve", "role": role, "name": name or "unnamed"}))
                st.session_state.result = out
                st.session_state.stage = "done" if out.get("gate_decision") == "approved" else "denied"
                st.rerun()
            if b2.button("Adjust"):
                with st.spinner("Resuming the selected agent..."):
                    out = _invoke(Command(resume={"action": "adjust", "adjust_target": adjust_target,
                                                    "role": role, "name": name or "unnamed", "note": note}))
                st.session_state.result = out
                if out.get("__interrupt__"):
                    st.session_state.payload = out["__interrupt__"][0].value
                    st.session_state.stage = "awaiting"
                else:
                    st.session_state.stage = "budget"
                st.rerun()
            if b3.button("Reject"):
                out = _invoke(Command(resume={"action": "reject", "role": role, "name": name or "unnamed"}))
                st.session_state.result = out
                st.session_state.stage = "denied"
                st.rerun()
        elif stage == "done":
            st.success(f"Approved by {res['approver']['name']} ({res['approver']['role']}). Published as version v{res['published_version']}.")
            st.download_button("Download the published document (Markdown)", res["document_markdown"], file_name="curriculum_revision_recommendation.md")
        else:
            gd = res.get("gate_decision")
            st.error("Not published. " + ("The role is not authorised to approve." if gd == "denied_permission" else "The draft was denied."))

# ------------------------------------------------------------------ DASHBOARD
with T_DASH:
    if not res or "gaps" not in res:
        st.info("Run the pipeline to populate the dashboard.")
    else:
        st.subheader("Curriculum committee dashboard (Lab 14)")
        cov, bench = res["skill_coverage"]["value"], res["benchmark_view"]["value"]
        m = st.columns(5)
        m[0].metric("Courses", res["evolution"]["value"]["concrete_course_count"])
        m[1].metric("Recently revised (2025+)", res["evolution"]["value"]["recent_count"])
        m[2].metric("Syllabus-verified coverage", f"{cov['strict_coverage_pct']}%")
        m[3].metric("High-severity gaps", sum(1 for g in res["gaps"] if g["severity"] == "high"))
        m[4].metric("Credit check", "PASS" if res["credit_check"]["valid"] else "FAIL")
        st.markdown("**Curriculum map (semester by semester)**")
        cur = json.loads(res["curriculum_json"])
        by_sem: dict[int, list[str]] = {}
        for c in cur["courses"]:
            by_sem.setdefault(c["semester"], []).append(f"{c['title']} ({c['course_code']})")
        st.dataframe([{"semester": s, "credits (declared)": cur["declared_semester_credits"][["I","II","III","IV","V","VI","VII","VIII"][s-1]],
                        "courses": "; ".join(v)} for s, v in sorted(by_sem.items())], width="stretch", hide_index=True)
        st.markdown("**Benchmarking status: ACM CS2023 knowledge areas**")
        st.dataframe([{"area": f"{r['ka_code']} {r['ka_name']}", "status": r["status"].upper(), "core courses": ", ".join(r["core_courses"]),
                        "elective options": ", ".join(r["elective_options"])} for r in bench["rows"]], width="stretch", hide_index=True)
        st.markdown("**Gap report**")
        st.dataframe([{"id": g["id"], "severity": SEV[g["severity"]], "type": g["type"], "gap": g["title"], "horizon": g["horizon"],
                        "evidence records": len(g["evidence"]), "conflicting signal": g["conflicting"]} for g in res["gaps"]],
                      width="stretch", hide_index=True)
        st.markdown("**Revision recommendations and approval status**")
        st.dataframe([{"id": r["id"], "type": r["action_type"], "recommendation": r["title"], "host": r["host"],
                        "closes gaps": ", ".join(r["gap_ids"]), "status": r["status"]} for r in res["recommendations"]],
                      width="stretch", hide_index=True)

# ------------------------------------------------------------------ GAPS
with T_GAPS:
    if not res or "gaps" not in res:
        st.info("Run the pipeline first.")
    else:
        st.subheader("Evidence-linked recommendations")
        st.caption("Each recommendation names the gaps it closes, the host course, real prerequisite course codes and the evidence behind it.")
        for r in res["recommendations"]:
            with st.expander(f"{r['id']}  {r['title']}"):
                st.markdown(f"**Action:** {r['action_type']}  |  **Host:** {r['host']}  |  **Pack:** {r['pack']}")
                st.markdown(f"**Target semesters:** {', '.join(r['target_semesters'])}  |  **Credits:** {r['credits'] or 'n/a'}  |  "
                            f"**Board of Studies approval required:** {r['needs_board_of_studies']}  |  **High impact:** {r['high_impact']}")
                st.markdown("**Prerequisites:** " + (", ".join(r["prerequisites"]) or "none"))
                st.markdown("**Learning outcomes**")
                for o in r["learning_outcomes"]:
                    st.markdown(f"- {o}")
                st.markdown("**Closes gaps:** " + ", ".join(r["gap_ids"]))
                st.markdown("**Evidence**")
                for e in r["evidence"]:
                    st.markdown(f"- {e['kind']}: {e['ref']} ({e['detail']})")
        st.subheader("Evidence table (Lab 9)")
        st.dataframe(res["evidence_table"], width="stretch", hide_index=True)

# ------------------------------------------------------------------ DATA
with T_DATA:
    st.subheader("Real industry demand collected from LinkedIn, Naukri and company career pages")
    ind = _industry()
    st.caption(ind["_source"])
    rows = []
    for s in ind["aggregated_skill_demand"]:
        status = ""
        if res and "skill_coverage" in res:
            status = next(d["status"] for d in res["skill_coverage"]["value"]["detail"] if d["id"] == s["id"])
        rows.append({"skill": s["skill"], "horizon": s["horizon"], "trend": s["trend"], "confidence": s["confidence"],
                      "sources": len(s["sources"]), "curriculum status": status})
    st.dataframe(rows, width="stretch", hide_index=True)
    st.markdown("**Postings and pages read**")
    st.dataframe([{"company": p["company"], "role": p["role"], "channel": p["channel"], "skills": ", ".join(p["skills"]), "url": p["source_url"]}
                   for p in ind["job_postings_sample"]], width="stretch", hide_index=True)
    st.subheader("Elective catalog from the 2026 VII-VIII scheme")
    cat = _curriculum()["elective_catalog"]
    st.dataframe([{"kind": "open elective", "code": e["code"], "title": e["title"]} for e in cat["open_electives"]] +
                  [{"kind": "program elective: " + e["cluster"], "code": e["code"], "title": e["title"]} for e in cat["program_electives"]],
                  width="stretch", hide_index=True)

# ------------------------------------------------------------------ GOVERNANCE
with T_GOV:
    st.subheader("Versioned releases and rollback (Lab 12)")
    cur_v = governance.current_version()
    st.markdown(f"**Current published version:** {'v' + str(cur_v) if cur_v else 'none yet'}")
    hist = governance.list_history()
    if hist:
        st.dataframe(hist, width="stretch", hide_index=True)
        versions = sorted({h["version"] for h in hist if h["event"] == "publish"})
        g1, g2, g3 = st.columns(3)
        target = g1.selectbox("Roll back to version", versions)
        role = g2.selectbox("Role", ["HoD", "Dean (Academics)", "Board of Studies", "Faculty"], key="rb_role")
        who = g3.text_input("Name", key="rb_name")
        if st.button("Roll back"):
            try:
                governance.rollback(target, role, who or "unnamed")
                st.success(f"Current version is now v{target}. The rollback is recorded in the ledger.")
                st.rerun()
            except governance.PermissionDenied as e:
                st.error(str(e))
        with st.expander("View the currently published document"):
            if governance.current_version():
                st.markdown(governance.read_version(governance.current_version())["document_markdown"])
    else:
        st.info("No release has been approved yet.")
    st.subheader("Evaluation metrics per published run")
    st.dataframe(governance.list_metrics(), width="stretch", hide_index=True)

# ------------------------------------------------------------------ AUDIT
with T_AUDIT:
    st.subheader("Audit log")
    st.caption("Tool calls are logged automatically by a LangChain callback handler; graph steps are logged by the nodes.")
    ent = st.session_state.audit.all_entries()
    if ent:
        st.dataframe([{"kind": e["kind"], "name": e["name"], "inputs": str(e["inputs"])[:160], "result": str(e["result"])[:160]} for e in ent],
                      width="stretch", hide_index=True)
    else:
        st.info("Run the pipeline to populate the audit log.")

# ------------------------------------------------------------------ ROSTER
with T_ROSTER:
    st.subheader("Agent roster: specification versus this build")
    st.caption("Order 0-6, exactly as specified. 'Node(s)' names the actual code each row maps to.")
    st.dataframe(AGENT_ROSTER, width="stretch", hide_index=True)
    st.markdown(
        "**Where this is exact:** rows 0, 1, 2, 3, 5 and 6 are implemented node-for-node, including the "
        "fan-out to three independent agents that LangGraph schedules concurrently (Lab 8), and the "
        "approve/adjust/reject gate with role checking (Lab 12).\n\n"
        "**One documented approximation:** row 4 (Group D) is a single `gap_analysis` node rather than a "
        "separate agent process, because its input is simply \"the combined output of A, B and C\" with no "
        "further parallelism to model; `fan_in_specialists` is the point where that combined output becomes "
        "available, immediately before `gap_analysis` runs. Every gap it produces is still restricted to "
        "evidence from Groups A, B or C only -- never from the (separate, simulated) student-performance "
        "data -- exactly as Group D's guardrail requires.\n\n"
        "**Adjust granularity:** \"AURA resumes the relevant agent\" is implemented as two selectable targets: "
        "Group E alone (recommendations only), or Groups A-C together (the whole parallel evidence-gathering "
        "layer, since they share one fan-out/fan-in step). Resuming exactly one of A, B or C alone is not "
        "supported, since they are not independently addressable."
    )

# ------------------------------------------------------------------ MCP
with T_MCP:
    st.subheader("Live MCP discovery (in-app equivalent of the MCP Inspector)")
    st.markdown("The button starts the real MCP server as a subprocess and issues the protocol calls tools/list and resources/list.")
    if st.button("Discover MCP server capabilities"):
        with st.spinner("Connecting to the MCP server over stdio..."):
            st.session_state.mcp_caps = list_mcp_capabilities()
    if "mcp_caps" in st.session_state:
        st.dataframe(st.session_state.mcp_caps, width="stretch", hide_index=True)
    st.subheader("Lab to code map")
    st.dataframe([
        {"lab": "1 Agent vs chatbot", "where": "app/graph.py clarify, plan, revise nodes"},
        {"lab": "2 Tool-using agent", "where": "app/tools.py logic, app/langchain_tools.py LangChain tools"},
        {"lab": "3 Skills", "where": "app/skills.py plan(), format_curriculum()"},
        {"lab": "4 Memory and retrieval", "where": "app/memory.py RunState and RevisionHistoryRetriever"},
        {"lab": "5 MCP connector", "where": "mcp_server/server.py and app/mcp_client.py"},
        {"lab": "6 Runtime", "where": "LangGraph SqliteSaver, interrupt(), budget, app/audit_callback.py"},
        {"lab": "7 Node graph", "where": "app/graph.py build_graph_builder()"},
        {"lab": "8 Parallel swarm", "where": "app/graph.py curriculum_mapping_agent, industry_skills_agent, acm_apni_benchmarking_agent, fan_in_specialists"},
        {"lab": "9 Grounding", "where": "app/analysis.py build_gaps(), evidence_table()"},
        {"lab": "10 Self-healing", "where": "validate_node, regenerate_node, inject_fault()"},
        {"lab": "11 Acceptance suite", "where": "app/analysis.py validate()"},
        {"lab": "12 Governance", "where": "app/governance.py roles, scope, versions, rollback, metrics"},
        {"lab": "13 Specialist packs", "where": "app/analysis.py SPECIALIST_PACKS"},
        {"lab": "14 Capstone", "where": "this application and its Dashboard tab"},
    ], width="stretch", hide_index=True)
