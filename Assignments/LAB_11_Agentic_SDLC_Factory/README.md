# Lab 11 — Agentic SDLC Factory

**Concept (book spec):** Treat the plan as a spec and the output as a tested implementation.

## 1. Concept applied
No draft reaches the human gate without first passing 8 checks: credit totals, CO/PO-to-PSO consistency, every gap grounded, every recommendation grounded and in-scope, every high-severity gap covered, reproducibility of the gap analysis, and no premature approval status.

## 2. Technical stack

| Item | Used |
|---|---|
| Gate | An 8-check acceptance suite, analysis.validate() |

## 3. Code

- `code/analysis.py` (full copy of `app/analysis.py` in the main codebase)

**app/analysis.py** (excerpt):
```python
def validate(gaps, recs, curriculum, tool_checks: dict, recompute_fn) -> dict:
```

## 4. Evidence

See `evidence.txt` in this folder — output of:

```
python -m pytest tests/test_tools_analysis.py::test_recommendations_validate_and_fault_is_detected tests/test_tools_analysis.py::test_out_of_scope_recommendation_is_rejected -v
```

```
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/claude/cis3
plugins: platformdirs-4.13.0, anyio-4.16.0, langsmith-0.14.17
collecting ... collected 2 items

tests/test_tools_analysis.py::test_recommendations_validate_and_fault_is_detected PASSED [ 50%]
tests/test_tools_analysis.py::test_out_of_scope_recommendation_is_rejected PASSED [100%]

============================== 2 passed in 2.13s ===============================
```
