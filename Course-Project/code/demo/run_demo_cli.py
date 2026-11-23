"""Terminal demo (fallback if Streamlit is unavailable): python demo/run_demo_cli.py"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from langgraph.types import Command
from app.audit_callback import AuditLogCallbackHandler
from app.graph import build_graph_builder, get_checkpointer_cm


def h(t): print("\n" + "=" * 78 + "\n" + t + "\n" + "=" * 78)


run_id = "cli-demo"
audit = AuditLogCallbackHandler(run_id)
h("RUN: LangGraph + LangChain tools + real MCP server (2 injected faults to show self-repair)")
with get_checkpointer_cm() as cp:
    g = build_graph_builder().compile(checkpointer=cp)
    cfg = {"configurable": {"thread_id": run_id, "audit": audit}}
    r = g.invoke({"run_id": run_id, "user_request": {"department": "CSE (AI)", "scope": "full curriculum", "cycle": "annual", "pack": "ug_cse_ai"},
                   "feedback_rounds": ["Prioritise agentic AI, RAG and MLOps."], "budget_used": 0, "force_fail_countdown": 2}, config=cfg)
t = r["worker_timing"]
print(f"Parallel swarm: {t['parallel_wall_seconds']}s wall vs {t['sequential_estimate_seconds']}s sequential  {t['workers_seconds']}")
cov = r["skill_coverage"]["value"]
print(f"Skill coverage {cov['coverage_pct']}% (syllabus-verified {cov['strict_coverage_pct']}%)  counts={cov['counts']}")
print("Missing:", cov["missing_skills"])
print(f"ACM CS2023 alignment {r['benchmark_view']['value']['alignment_pct']}%  counts={r['benchmark_view']['value']['counts']}")
print("Recently revised by the department:", [c['title'] for c in r['evolution']['value']['recent_courses']])
h(f"VALIDATION: passed={r['validation']['passed']} after {r['attempts']} attempt(s) (targeted repair)")
for c in r["validation"]["checks"]: print(("  PASS  " if c["passed"] else "  FAIL  ") + c["check"])
h("GAPS")
for gp in r["gaps"][:10]: print(f"  {gp['id']} [{gp['severity']}] {gp['title']}")
h("RECOMMENDATIONS (each tied to gaps and evidence)")
for rc in r["recommendations"]: print(f"  {rc['id']} {rc['title']}  gaps={rc['gap_ids']}  evidence={len(rc['evidence'])}")
assert r.get("__interrupt__")
h("HARD STOP at the human gate (LangGraph interrupt). Resuming from a fresh checkpointer as the HoD")
with get_checkpointer_cm() as cp2:
    g2 = build_graph_builder().compile(checkpointer=cp2)
    r2 = g2.invoke(Command(resume={"approved": True, "role": "HoD", "name": "Demo HoD"}), config=cfg)
print("decision:", r2["gate_decision"], " published version: v%s" % r2["published_version"])
h("AUDIT LOG (tool calls auto-logged by a LangChain callback)")
for e in audit.all_entries()[:40]: print(f"  [{e['kind']:5s}] {e['name']:34s} {str(e['result'])[:60]}")
