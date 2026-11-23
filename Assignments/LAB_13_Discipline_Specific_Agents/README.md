# Lab 13 — Discipline-Specific Agents

**Concept (book spec):** Specialise the worklet to its domain variants.

## 1. Concept applied
The UG B.E. CSE (AI) pack and an illustrative PG AI pack change which semesters a new elective targets and its delivery style, while the same recommendation-building code produces both.

## 2. Technical stack

| Item | Used |
|---|---|
| Packs | SPECIALIST_PACKS dict: ug_cse_ai, pg_ai |

## 3. Code

- `code/analysis.py` (full copy of `app/analysis.py` in the main codebase)

**app/analysis.py** (excerpt):
```python
SPECIALIST_PACKS = {
    "ug_cse_ai": {"label": "UG B.E. CSE (AI)", "elective_semesters": ["VII", "VIII"], "new_elective_credits": 3,
                   "style": "Professional elective in the 4th-year slots (PE-4/PE-5/PE-6); lab-heavy, project-assessed.",
                   "extra_outcome": "Demonstrate the skill in a deployed mini-project."},
    "pg_ai": {"label": "PG M.Tech AI (illustrative pack, no PG curriculum supplied)", "elective_semesters": ["II", "III"], "new_elective_credits": 4,
               "style": "Research-oriented elective with a seminar and a reading list of recent papers.",
               "extra_outcome": "Critically review and reproduce one recent research paper."},}
```

## 4. Evidence

See `evidence.txt` in this folder — output of:

```
python -m pytest tests/test_tools_analysis.py::test_pg_pack_changes_recommendation_style -v
```

```
cachedir: .pytest_cache
rootdir: /home/claude/cis3
plugins: platformdirs-4.13.0, anyio-4.16.0, langsmith-0.14.17
collecting ... collected 1 item

tests/test_tools_analysis.py::test_pg_pack_changes_recommendation_style PASSED [100%]

```
