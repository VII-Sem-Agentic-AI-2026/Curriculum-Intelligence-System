# Lab 9 — Deep Research / Grounding

**Concept (book spec):** Ground every output in cited, in-scope evidence.

## 1. Concept applied
Every gap and recommendation carries an evidence list (job-posting URL with collection date, course code, ACM knowledge-area code, or catalog year). Low-confidence or single-source industry trends are explicitly flagged rather than treated as established.

## 2. Technical stack

| Item | Used |
|---|---|
| Logic | app/analysis.py, deterministic, no LLM |

## 3. Code

- `code/analysis.py` (full copy of `app/analysis.py` in the main codebase)

**app/analysis.py** (excerpt):
```python
def build_gaps(coverage: dict, benchmark: dict, stale: list, curriculum: dict, performance: dict) -> list[dict]:
    gaps: list[dict] = []

    def add(gtype, title, severity, horizon, evidence, note="", skill_id=None, conflicting=None):
        gaps.append({"type": gtype, "title": title, "severity": severity, "horizon": horizon,
                      "evidence": evidence, "note": note, "skill_id": skill_id, "conflicting": conflicting or ""})

    for d in coverage["detail"]:
        ev_jobs = [{"kind": "job_source", "ref": u, "detail": f"industry demand source, collected {d.get('date_collected', 'n/a')}"}
                   for u in d["sources"]]
        rising_hi = d["trend"] == "rising" and d["confidence"] == "high"
        conf_flag = ("LOW-CONFIDENCE / SINGLE-SOURCE TREND -- weigh accordingly. "
                     if d.get("low_confidence_or_single_source") else "")
        if d["status"] == "missing":
            sev = "low" if d.get("low_confidence_or_single_source") else (
                "high" if rising_hi else ("medium" if d["trend"] in ("rising", "stable-high") else "low"))
            add("skill_missing", f"No course covers: {d['skill']}", sev, d["horizon"], ev_jobs,
                conf_flag + f"demand trend {d['trend']}, confidence {d['confidence']}, {d['mentions']} source(s), "
                f"collected {d.get('date_collected', 'n/a')}", d["id"])
        elif d["status"] == "elective_only":
            sev = "medium" if d["trend"] == "rising" else "low"
            ev = ev_jobs + [{"kind": "course_code", "ref": c, "detail": "optional elective only"} for c in d["matched_courses"]]
            add("skill_elective_only", f"Only an optional elective covers: {d['skill']}", sev, d["horizon"], ev,
                "students may graduate without this skill", d["id"],
                conflicting="an elective exists, but electives are not guaranteed to be taken")
        elif d["status"] == "covered_title" and rising_hi:
            ev = ev_jobs + [{"kind": "course_code", "ref": c, "detail": "matched by course title only"} for c in d["matched_courses"]]
            add("depth_unverified", f"Course exists but syllabus depth is unverified: {d['skill']}", "medium", d["horizon"], ev,
                "detailed syllabus topics were not supplied, so framework-level depth cannot be confirmed", d["id"],
                conflicting="coverage by title suggests the department already responded; depth unknown")

    for row in benchmark["rows"]:
        if row["status"] in ("missing", "partial"):
            ev = [{"kind": "acm_ka", "ref": row["ka_code"], "detail": f"ACM CS2023 {row['ka_name']}"}]
            ev += [{"kind": "course_code", "ref": c, "detail": "related course"} for c in row["core_courses"] + row["elective_options"]]
            add("acm_" + row["status"], f"ACM CS2023 area '{row['ka_name']}' is {row['status']} in the core curriculum",
                "medium" if row["status"] == "missing" else "low", "present", ev,
                f"expected at least {row['min_core_expected']} core course(s)", None)

    for f in stale:
        code = f["course_code"]
        if "EC" in code[2:4] and f["years_since_revision"] >= 5:
            course = next((c for c in curriculum["courses"] if c["course_code"] == code), {})
            recoded = "recoded" in course.get("topics_source", "")
            add("stale_content", f"{f['title']} ({code}) last revised {f['catalog_year']}", "low", "present",
                [{"kind": "catalog_year", "ref": code, "detail": f"{f['years_since_revision']} years since catalog year"}],
                "the same course was already recoded for the 2025-29 batch" if recoded else "",
                None, conflicting="newer batches already use a refreshed version" if recoded else "")

    # NOTE: student-performance/attainment data is deliberately NOT used to raise a gap here.
    # The Agent Roster defines Group D (Gap Analysis Agent) as comparing exactly three views --
    # Group A's curriculum map, Group B's industry skills list, Group C's benchmarking report --
    # and its guardrail requires every gap to be tied to "evidence from at least one of the three
    # source agents". Attainment data comes from the MCP connector but from none of A/B/C, so it
    # is surfaced separately (see format_node's "Student performance context" section) rather than
    # turned into a gap, to keep this function's evidence strictly within the three-agent model.
    del performance

    gaps.sort(key=lambda g: (SEV_ORDER[g["severity"]], g["type"], g["title"]))
    for i, g in enumerate(gaps, 1):
        g["id"] = f"GAP-{i:02d}"
    return gaps
```

## 4. Evidence

See `evidence.txt` in this folder — output of:

```
python -m pytest tests/test_tools_analysis.py::test_gaps_are_deterministic_and_grounded -v
```

```
cachedir: .pytest_cache
rootdir: /home/claude/cis3
plugins: platformdirs-4.13.0, anyio-4.16.0, langsmith-0.14.17
collecting ... collected 1 item

tests/test_tools_analysis.py::test_gaps_are_deterministic_and_grounded PASSED [100%]


```
