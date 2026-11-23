# Lab 10 — Ops Resilience / Self-Healing

**Concept (book spec):** Make the pipeline self-healing when validation fails.

## 1. Concept applied
A fault-injection slider strips evidence from one recommendation; validate_node diagnoses exactly which recommendation failed and regenerate_node repairs only that one, leaving the others untouched.

## 2. Technical stack

| Item | Used |
|---|---|
| Mechanism | validate_node / regenerate_node bounded loop |

## 3. Code

- `code/analysis.py` (full copy of `app/analysis.py` in the main codebase)

**app/graph.py** (excerpt):
```python
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
```

## 4. Evidence

See `evidence.txt` in this folder — output of:

```
python -m pytest tests/test_governance_graph.py::test_targeted_self_repair_after_injected_faults -v
```

```
cachedir: .pytest_cache
rootdir: /home/claude/cis3
plugins: platformdirs-4.13.0, anyio-4.16.0, langsmith-0.14.17
collecting ... collected 1 item

tests/test_governance_graph.py::test_targeted_self_repair_after_injected_faults PASSED [100%]


```
