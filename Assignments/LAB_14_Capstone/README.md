# Lab 14 — Capstone — Team-Owned System

**Concept (book spec):** Integrate everything into a deployed, team-owned system.

## 1. Concept applied
The full worklet -- connector, runtime, node graph, parallel swarm, grounding, self-healing, governance, specialist packs -- delivered as a working Streamlit dashboard and a CLI fallback, demonstrated end to end on the real 2023-27 curriculum.

## 2. Technical stack

| Item | Used |
|---|---|
| Interface | Streamlit (streamlit_app.py) |
| Fallback | CLI (demo/run_demo_cli.py) |

## 3. Code

- `code/streamlit_app.py` (full copy of `streamlit_app.py` in the main codebase)

**demo/run_demo_cli.py** (excerpt):
```python
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
print("Rece
```

## 4. Evidence

See `evidence.txt` in this folder — output of:

```
python -m pytest tests/ -v   (33 tests, full suite)
```

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/claude/cis3
plugins: platformdirs-4.13.0, anyio-4.16.0, langsmith-0.14.17
collecting ... collected 33 items

tests/test_governance_graph.py::test_pipeline_pauses_at_gate_with_parallel_speedup_and_passing_suite PASSED [  3%]
tests/test_governance_graph.py::test_resume_in_fresh_checkpointer_and_versioned_publish PASSED [  6%]
tests/test_governance_graph.py::test_unauthorised_role_cannot_publish PASSED [  9%]
tests/test_governance_graph.py::test_denied_gate_publishes_nothing PASSED [ 12%]
tests/test_governance_graph.py::test_targeted_self_repair_after_injected_faults PASSED [ 15%]
tests/test_governance_graph.py::test_budget_exhaustion_escalates PASSED  [ 18%]
tests/test_governance_graph.py::test_other_department_is_blocked_before_any_data_is_read PASSED [ 21%]
tests/test_governance_graph.py::test_every_mcp_tool_call_is_audit_logged_including_parallel_workers PASSED [ 24%]
tests/test_governance_graph.py::test_three_specialist_agents_are_distinct_graph_nodes_with_real_speedup PASSED [ 27%]
tests/test_governance_graph.py::test_adjust_resumes_the_relevant_agent_and_reaches_a_fresh_gate PASSED [ 30%]
tests/test_governance_graph.py::test_rollback_moves_pointer_and_is_recorded PASSED [ 33%]
tests/test_langchain_memory_skills.py::test_langchain_tool_chain_through_mcp PASSED [ 36%]
tests/test_langchain_memory_skills.py::test_retriever_is_langchain_and_ranks_relevant_first PASSED [ 39%]
tests/test_langchain_memory_skills.py::test_run_state_is_not_persistent PASSED [ 42%]
tests/test_langchain_memory_skills.py::test_skills_reusable_across_departments PASSED [ 45%]
tests/test_mcp.py::test_
```
