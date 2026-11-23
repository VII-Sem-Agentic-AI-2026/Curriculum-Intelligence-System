"""
Lab 2 -- Tool-Using Agent: core typed-tool logic.

Every number here is computed by plain, auditable Python from data reached
through the MCP connector -- never asserted by the LLM. LangChain @tool
wrappers live in langchain_tools.py; this file stays framework-free so it
is directly unit-testable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    valid: bool
    value: Any
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- helpers
def _is_concrete(course: dict) -> bool:
    """Elective/OE placeholder slots (XX-prefixed) are not concrete courses."""
    return not course["course_code"].startswith("XX") and course.get("type") != "audit"


def _corpus(curriculum: dict) -> list[dict]:
    rows = []
    for c in curriculum.get("courses", []):
        if not _is_concrete(c):
            continue
        rows.append({
            "code": c["course_code"], "title": c["title"], "semester": c["semester"],
            "title_text": c["title"].lower(),
            "topic_text": " | ".join(c.get("topics", [])).lower(),
            "has_topics": bool(c.get("topics")),
        })
    return rows


def _elective_titles(curriculum: dict) -> list[dict]:
    cat = curriculum.get("elective_catalog", {})
    def row(e, kind):
        return {"code": e["code"], "title": e["title"], "kind": kind,
                "text": (e["title"] + " | " + " | ".join(e.get("topics", []))).lower()}
    out = [row(e, "open_elective") for e in cat.get("open_electives", [])]
    out += [row(e, "program_elective:" + e["cluster"]) for e in cat.get("program_electives", [])]
    return out


# ------------------------------------------------------------------ checks
def compute_credit_total_check(curriculum: dict) -> ToolResult:
    declared = curriculum["declared_semester_credits"]
    computed_total = round(sum(declared.values()), 2)
    stated_total = curriculum["total_program_credits"]
    errors = [] if computed_total == stated_total else [
        f"Semester totals sum to {computed_total}, document states {stated_total}."]
    return ToolResult(not errors, {"computed_total": computed_total, "stated_total": stated_total,
                                     "per_semester": declared}, errors)


def compute_stale_content_flags(curriculum: dict, threshold_years: int = 5, as_of_year: int = 2026) -> ToolResult:
    """KLE course codes encode the catalog year (24ECAC207 -> 2024); read it directly."""
    flags = []
    for c in curriculum.get("courses", []):
        if not _is_concrete(c) or not c["course_code"][:2].isdigit():
            continue
        year = 2000 + int(c["course_code"][:2])
        age = as_of_year - year
        if age >= threshold_years:
            flags.append({"course_code": c["course_code"], "title": c["title"], "semester": c["semester"],
                           "catalog_year": year, "years_since_revision": age})
    flags.sort(key=lambda f: (-f["years_since_revision"], f["course_code"]))
    return ToolResult(True, flags, [])


def compute_curriculum_evolution(curriculum: dict, recent_from_year: int = 2025) -> ToolResult:
    """What the department has already changed recently (catalog year >= recent_from_year)."""
    recent = []
    for c in curriculum.get("courses", []):
        if _is_concrete(c) and c["course_code"][:2].isdigit() and 2000 + int(c["course_code"][:2]) >= recent_from_year:
            recent.append({"course_code": c["course_code"], "title": c["title"], "semester": c["semester"],
                            "catalog_year": 2000 + int(c["course_code"][:2])})
    concrete = [c for c in curriculum.get("courses", []) if _is_concrete(c)]
    return ToolResult(True, {"recent_courses": recent, "recent_count": len(recent),
                              "concrete_course_count": len(concrete)}, [])


def compute_skill_coverage(curriculum: dict, industry_signals: dict) -> ToolResult:
    """
    Three-state coverage per in-demand skill, each with evidence:
      covered_topic  -- keyword found in a course's syllabus topics
      covered_title  -- keyword found only in a course TITLE (syllabus not supplied: depth unverified)
      elective_only  -- keyword found only in the elective catalog (optional, not guaranteed)
      missing        -- nowhere
    Curated match_keywords per skill avoid false positives from generic words.
    """
    corpus, electives = _corpus(curriculum), _elective_titles(curriculum)
    detail = []
    for skill in industry_signals.get("aggregated_skill_demand", []):
        kws = [k.lower() for k in skill.get("match_keywords") or [skill["skill"].lower()]]
        topic_hits = [r["code"] for r in corpus if any(k in r["topic_text"] for k in kws)]
        title_hits = [r["code"] for r in corpus if any(k in r["title_text"] for k in kws) and r["code"] not in topic_hits]
        elective_hits = [e["code"] for e in electives if any(k in e["text"] for k in kws)]
        if topic_hits:
            status, hits = "covered_topic", topic_hits
        elif title_hits:
            status, hits = "covered_title", title_hits
        elif elective_hits:
            status, hits = "elective_only", elective_hits
        else:
            status, hits = "missing", []
        detail.append({"id": skill["id"], "skill": skill["skill"], "horizon": skill.get("horizon", "present"),
                        "trend": skill["trend"], "confidence": skill["confidence"], "mentions": skill["mentions"],
                        "status": status, "matched_courses": hits, "sources": skill["sources"],
                        "date_collected": skill.get("date_collected"),
                        "low_confidence_or_single_source": skill.get("low_confidence_or_single_source", False)})
    n = max(1, len(detail))
    count = lambda s: sum(1 for d in detail if d["status"] == s)
    return ToolResult(True, {
        "detail": detail,
        "counts": {s: count(s) for s in ("covered_topic", "covered_title", "elective_only", "missing")},
        "coverage_pct": round(100 * (count("covered_topic") + count("covered_title")) / n, 1),
        "strict_coverage_pct": round(100 * count("covered_topic") / n, 1),
        "missing_skills": [d["skill"] for d in detail if d["status"] == "missing"],
        "covered_skills": [d["skill"] for d in detail if d["status"] in ("covered_topic", "covered_title")],
    }, [])


def compute_acm_benchmark(curriculum: dict, reference: dict) -> ToolResult:
    """Benchmark against ACM CS2023 knowledge areas, with matched courses as the clause-level evidence."""
    corpus, electives = _corpus(curriculum), _elective_titles(curriculum)
    rows = []
    for ka in reference["acm_cs2023_knowledge_areas"]:
        kws = ka["keywords"]
        core = sorted({r["code"] for r in corpus if any(k in r["title_text"] or k in r["topic_text"] for k in kws)})
        elec = sorted({e["code"] for e in electives if any(k in e["text"] for k in kws)})
        if len(core) >= ka["min_courses_core"]:
            status = "covered"
        elif core or elec:
            status = "partial"
        else:
            status = "missing"
        rows.append({"ka_code": ka["code"], "ka_name": ka["name"], "status": status,
                      "core_courses": core, "elective_options": elec, "min_core_expected": ka["min_courses_core"]})
    return ToolResult(True, {
        "rows": rows,
        "counts": {s: sum(1 for r in rows if r["status"] == s) for s in ("covered", "partial", "missing")},
        "alignment_pct": round(100 * sum(1 for r in rows if r["status"] == "covered") / max(1, len(rows)), 1),
        "apni": "not evaluated: APNI clause text was not supplied",
    }, [])


def compute_pso_alignment(curriculum: dict) -> ToolResult:
    """Consistency check between the department's PSOs and the courses actually offered."""
    corpus = _corpus(curriculum)
    has = lambda kws: sorted({r["code"] for r in corpus if any(k in r["title_text"] or k in r["topic_text"] for k in kws)})
    groups = {
        "PSO1 (software system construction)": has(["software engineering", "object oriented", "web technologies", "design and analysis of algorithms"]),
        "PSO2 AI": has(["machine learning", "deep learning", "generative ai", "agentic"]),
        "PSO2 data": has(["database", "big data", "exploratory data analysis"]),
        "PSO2 network/system": has(["computer networks", "operating system", "internet of things"]),
    }
    errors = [f"{k} has no supporting course" for k, v in groups.items() if not v]
    return ToolResult(not errors, groups, errors)
