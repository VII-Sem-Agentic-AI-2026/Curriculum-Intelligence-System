# Lab 1 — Agent vs Chatbot

**Concept (book spec):** Establish the agent loop (clarify -> plan -> revise) instead of a one-shot chatbot answer.

## 1. Concept applied
The Coordinator's clarify_node checks for missing required fields and asks specific questions instead of guessing; plan_node drafts an 8-step plan; revise_node applies human feedback rounds. These are real LangGraph nodes operating on a shared GraphState, not a simulated while-loop.

## 2. Technical stack

| Item | Used |
|---|---|
| Language | Python 3.12 |
| Framework | LangGraph StateGraph |
| LLM | Deterministic MockLLM (no API key needed) |

## 3. Code

- `code/graph.py` (full copy of `app/graph.py` in the main codebase)
- `code/llm_client.py` (full copy of `app/llm_client.py` in the main codebase)

**app/graph.py** (excerpt):
```python
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

tests/test_governance_graph.py::test_pipeline_pauses_at_gate_with_parallel_speedup_and_passing_suite PASSED 

```
