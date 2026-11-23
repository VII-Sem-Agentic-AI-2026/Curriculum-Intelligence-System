# Lab 8 — Parallel Swarm

**Concept (book spec):** Parallelise the per-unit work across multiple workers and merge the best results.

## 1. Concept applied
curriculum_mapping_agent, industry_skills_agent and acm_apni_benchmarking_agent are three graph nodes with no edge between them, so LangGraph runs them in the same superstep concurrently. fan_in_specialists is the merge node the book names, and waits on all three.

## 2. Technical stack

| Item | Used |
|---|---|
| Scheduler | LangGraph's own Pregel scheduler (no manual thread pool) |

## 3. Code

- `code/graph.py` (full copy of `app/graph.py` in the main codebase)

**app/graph.py** (excerpt):
```python
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
    ...
```

## 4. Evidence

See `evidence.txt` in this folder — output of:

```
python -m pytest tests/test_governance_graph.py::test_three_specialist_agents_are_distinct_graph_nodes_with_real_speedup -v
```

```
cachedir: .pytest_cache
rootdir: /home/claude/cis3
plugins: platformdirs-4.13.0, anyio-4.16.0, langsmith-0.14.17
collecting ... collected 1 item

tests/test_governance_graph.py::test_three_specialist_agents_are_distinct_graph_nodes_with_real_speedup PASSED [100%]

```
