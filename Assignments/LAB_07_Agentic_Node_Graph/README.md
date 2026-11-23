# Lab 7 — Agentic Node Graph

**Concept (book spec):** Wire specialist agents into one explicit node graph with state, branching, and a validation -> regenerate back-edge.

## 1. Concept applied
The full pipeline -- clarify, plan, revise, lock_plan, specialist_pack, 3 parallel agents, fan-in, gap analysis, memory, recommend, format, validate, regenerate, human_gate, publish -- is one explicit StateGraph with a bounded retry back-edge, not a sequence of ad-hoc function calls.

## 2. Technical stack

| Item | Used |
|---|---|
| Orchestration | LangGraph StateGraph, 15 nodes |

## 3. Code

- `code/graph.py` (full copy of `app/graph.py` in the main codebase)

**app/graph.py** (excerpt):
```python
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
```

## 4. Evidence

See `evidence.txt` in this folder — output of:

```
python -m pytest tests/test_governance_graph.py::test_pipeline_pauses_at_gate_with_parallel_speedup_and_passing_suite -v
```

```
cachedir: .pytest_cache
rootdir: /home/claude/cis3
plugins: platformdirs-4.13.0, anyio-4.16.0, langsmith-0.14.17
collecting ... collected 1 item

tests/test_governance_graph.py::test_pipeline_pauses_at_gate_with_parallel_speedup_and_passing_suite PASSED [100%]

```
