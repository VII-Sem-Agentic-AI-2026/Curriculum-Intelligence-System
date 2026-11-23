"""
Labs 7-11 analysis logic: gap analysis, recommendations, grounding (evidence
table), validation / acceptance suite, and failure-injection helpers.

Pure, deterministic functions (no LLM): the same inputs always produce the
same gaps, which is what makes the "gap analysis is reproducible" check real.
Every gap and every recommendation carries evidence records (job-posting
URLs, course codes, ACM knowledge areas, catalog years) -- ungrounded items
are rejected by validate().
"""
from __future__ import annotations

import copy
import hashlib
import json

SEV_ORDER = {"high": 0, "medium": 1, "low": 2}


# ----------------------------------------------------------------- Lab 9/7
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


def gaps_fingerprint(gaps: list[dict]) -> str:
    return hashlib.sha256(json.dumps(gaps, sort_keys=True).encode()).hexdigest()[:16]


def evidence_table(gaps: list[dict], recs: list[dict]) -> list[dict]:
    rows = []
    for g in gaps:
        for e in g["evidence"]:
            rows.append({"item": g["id"], "item_type": "gap", **e})
    for r in recs:
        for e in r["evidence"]:
            rows.append({"item": r["id"], "item_type": "recommendation", **e})
    return rows


# ----------------------------------------------------------------- Lab 13
SPECIALIST_PACKS = {
    "ug_cse_ai": {"label": "UG B.E. CSE (AI)", "elective_semesters": ["VII", "VIII"], "new_elective_credits": 3,
                   "style": "Professional elective in the 4th-year slots (PE-4/PE-5/PE-6); lab-heavy, project-assessed.",
                   "extra_outcome": "Demonstrate the skill in a deployed mini-project."},
    "pg_ai": {"label": "PG M.Tech AI (illustrative pack, no PG curriculum supplied)", "elective_semesters": ["II", "III"], "new_elective_credits": 4,
               "style": "Research-oriented elective with a seminar and a reading list of recent papers.",
               "extra_outcome": "Critically review and reproduce one recent research paper."},
}

_REC_TEMPLATES = [
    {"key": "rag", "gap_skill_ids": ["rag_vector"], "action": "new_elective",
     "title": "New elective: Applied RAG Systems and Vector Databases",
     "host": "Program elective cluster: Data Intelligence (alongside 24ECAE406 Information Retrieval)",
     "prereq": ["22ECAC204", "24ECAC210", "25ECAC307"],
     "outcomes": ["Build a retrieval-augmented generation pipeline with chunking, embedding and metadata filtering.",
                  "Index, query and tune a vector database (FAISS / Chroma / pgvector class).",
                  "Evaluate retrieval quality and answer faithfulness."]},
    {"key": "mlops", "gap_skill_ids": ["mlops_deploy", "cloud_native", "ai_eval_observability"], "action": "new_elective",
     "title": "New elective: MLOps, LLMOps and Cloud-Native AI Deployment",
     "host": "Program elective cluster: Systems and Software Development (alongside 22ECAE415 Scalable AI)",
     "prereq": ["22ECAC303", "22ECAC301", "24ECAC302"],
     "outcomes": ["Containerise a model service and deploy it on a cloud platform (Docker, Kubernetes class).",
                  "Build a CI/CD pipeline that tests, evaluates and releases an ML or LLM application.",
                  "Monitor a deployed model and add guardrails and evaluation checks."]},
    {"key": "mcp", "gap_skill_ids": ["mcp_tool_calling"], "action": "extend_course",
     "title": "Extend Agentic AI with a tool-calling and MCP server laboratory",
     "host": "26ECAC401", "prereq": ["25ECAC307"],
     "outcomes": ["Expose data sources to an agent through a typed MCP server.",
                  "Implement tool calling with validated schemas and audit logging.",
                  "Orchestrate a multi-step agent with a state graph and a human approval gate."]},
    {"key": "verify_agentic", "gap_skill_ids": ["agentic_frameworks"], "action": "verify_syllabus",
     "title": "Confirm the Agentic AI syllabus covers orchestration frameworks, RAG and tool calling",
     "host": "26ECAC401", "prereq": [],
     "outcomes": ["Board of Studies confirms the approved syllabus names agent orchestration (state graphs / multi-agent), memory and tool use.",
                  "Record the confirmed topic list in the curriculum content document."]},
    {"key": "verify_genai", "gap_skill_ids": ["genai_llm"], "action": "verify_syllabus",
     "title": "Confirm the Generative AI syllabus covers LLM APIs, prompting, fine-tuning and evaluation",
     "host": "25ECAC307", "prereq": [],
     "outcomes": ["Confirm LLM API integration, prompt engineering and evaluation appear in the approved syllabus.",
                  "Move retrieval-augmented generation depth to the proposed RAG elective or a defined module."]},
    {"key": "secai", "gap_skill_ids": ["ai_security"], "action": "extend_course",
     "title": "Add an AI security module (prompt injection, data exposure, responsible AI)",
     "host": "24ECAC403", "prereq": ["24ECAC302"],
     "outcomes": ["Identify prompt-injection and data-exposure risks in an LLM application.",
                  "Apply mitigations and document residual risk."]},
    {"key": "hci", "gap_skill_ids": [], "gap_titles": ["Human-Computer Interaction"], "action": "extend_course",
     "title": "Add a human-computer interaction module to the Web Technologies Lab",
     "host": "24ECAP304", "prereq": [],
     "outcomes": ["Apply usability heuristics and evaluate a user interface with a short user study."]},
]


def build_recommendations(gaps: list[dict], curriculum: dict, pack_key: str = "ug_cse_ai", only_keys: set[str] | None = None) -> list[dict]:
    pack = SPECIALIST_PACKS[pack_key]
    recs = []
    for t in _REC_TEMPLATES:
        if only_keys is not None and t["key"] not in only_keys:
            continue
        matched = [g for g in gaps if g["severity"] in ("high", "medium") and (
            (g.get("skill_id") in t["gap_skill_ids"]) or any(x in g["title"] for x in t.get("gap_titles", [])))]
        if not matched:
            continue
        ev, seen = [], set()
        for g in matched:
            for e in g["evidence"]:
                k = (e["kind"], e["ref"])
                if k not in seen:
                    seen.add(k); ev.append(e)
        outcomes = list(t["outcomes"]) + ([pack["extra_outcome"]] if t["action"] == "new_elective" else [])
        recs.append({
            "key": t["key"], "action_type": t["action"], "title": t["title"], "host": t["host"],
            "prerequisites": list(t["prereq"]), "learning_outcomes": outcomes,
            "target_semesters": pack["elective_semesters"] if t["action"] == "new_elective" else ["as per host course"],
            "credits": pack["new_elective_credits"] if t["action"] == "new_elective" else None,
            "delivery_style": pack["style"] if t["action"] == "new_elective" else "",
            "gap_ids": [g["id"] for g in matched], "evidence": ev,
            "high_impact": t["action"] == "new_elective",
            "needs_board_of_studies": t["action"] in ("new_elective", "verify_syllabus"),
            "status": "draft - pending HoD / Dean / Board of Studies approval", "pack": pack["label"],
        })
    sev = lambda r: min(SEV_ORDER[next(g["severity"] for g in gaps if g["id"] == gid)] for gid in r["gap_ids"])
    recs.sort(key=lambda r: (sev(r), r["title"]))
    for i, r in enumerate(recs, 1):
        r["id"] = f"REC-{i:02d}"
    return recs


def inject_fault(recs: list[dict]) -> None:
    """Failure injection for Lab 10 tests: strip the evidence from the first recommendation."""
    if recs:
        recs[0]["evidence"] = []


# --------------------------------------------------------------- Lab 10/11
def validate(gaps, recs, curriculum, tool_checks: dict, recompute_fn) -> dict:
    codes = {c["course_code"] for c in curriculum["courses"]}
    codes |= {e["code"] for e in curriculum.get("elective_catalog", {}).get("open_electives", [])}
    codes |= {e["code"] for e in curriculum.get("elective_catalog", {}).get("program_electives", [])}
    gap_ids = {g["id"] for g in gaps}
    checks, failing_recs = [], []

    checks.append(("credit totals consistent with the official document", tool_checks["credit"], ""))
    # Chapter 5's literal check is "CO/PO mapping stays consistent". The supplied curriculum
    # documents contain no course-outcome (CO) data, so that check is not computable as written.
    # PSO (program-specific outcome) to offered-course consistency is the closest real substitute
    # and is labelled as such rather than silently renamed to the chapter's wording.
    checks.append(("CO/PO mapping stays consistent [substituted: PSO-to-course alignment, "
                    "no CO data was supplied]", tool_checks["pso"], ""))
    bad_gaps = [g["id"] for g in gaps if not g["evidence"]]
    checks.append(("every gap carries evidence", not bad_gaps, ", ".join(bad_gaps)))

    no_ev = [r["id"] for r in recs if not r["evidence"] or not r["gap_ids"] or any(x not in gap_ids for x in r["gap_ids"])]
    failing_recs += no_ev
    checks.append(("every recommendation cites its evidence and a real gap", not no_ev, ", ".join(no_ev)))

    def in_scope(r):
        host_ok = r["host"] in codes or r["host"].startswith("Program elective cluster")
        return host_ok and all(p in codes for p in r["prerequisites"])
    out_scope = [r["id"] for r in recs if not in_scope(r)]
    failing_recs += out_scope
    checks.append(("every recommendation stays within approved program scope", not out_scope, ", ".join(out_scope)))

    covered = {gid for r in recs for gid in r["gap_ids"]}
    uncovered = [g["id"] for g in gaps if g["severity"] == "high" and g["id"] not in covered]
    checks.append(("every high-severity gap has a recommendation", not uncovered, ", ".join(uncovered)))

    reproducible = gaps_fingerprint(gaps) == gaps_fingerprint(recompute_fn())
    checks.append(("gap analysis is reproducible", reproducible, ""))
    checks.append(("no recommendation is marked approved or published before review",
                    all(r["status"].startswith("draft") for r in recs), ""))

    report = [{"check": n, "passed": bool(ok), "detail": d} for n, ok, d in checks]
    failing = [c["check"] for c in report if not c["passed"]]
    return {"passed": not failing, "checks": report, "failing": failing,
            "failing_rec_ids": sorted(set(failing_recs)),
            "diagnosis": "; ".join(f"{c['check']} -> {c['detail'] or 'see check'}" for c in report if not c["passed"])}
