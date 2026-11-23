# Curriculum Intelligence System (Worklet-5), Labs 1 to 14

Agentic AI (26ECAC401), KLE Technological University, CSE (AI). Team 09.

It continuously maps the CSE-AI curriculum against real industry demand and ACM CS2023, finds gaps,
drafts evidence-linked revision recommendations, and stops at a human approval gate (HoD / Dean / Board of Studies).

## Run it

```bash
python3 -m venv venv && source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py                            # main demo (white theme, no emoji)
python demo/run_demo_cli.py                               # terminal fallback
python -m pytest tests/ -q                                # 29 tests, about 50 seconds
npx @modelcontextprotocol/inspector python -m mcp_server.server   # optional: official MCP Inspector
```
No API key is needed. The LLM is a deterministic mock (see Limitations).

## Architecture

```
Streamlit (streamlit_app.py)
  -> LangGraph StateGraph (app/graph.py), SqliteSaver checkpoints, interrupt() gate, step budget
       clarify -> plan -> revise -> lock_plan -> specialist_pack
       -> parallel_specialists (3 agents run concurrently) -> gap_analysis -> memory -> recommend -> format
       -> validate --fail--> regenerate (only failing items) -> format -> validate ...
       -> human_gate (hard stop) -> publish (versioned) | END
  -> LangChain: @tool wrappers, BaseCallbackHandler audit log, BaseRetriever memory
  -> MCP client (app/mcp_client.py) --stdio--> MCP server (mcp_server/server.py) -> mcp_server/data/*.json
```

## Where MCP, LangChain and LangGraph are used (teacher question)

* **MCP**: `mcp_server/server.py` is a real MCP server (Anthropic `mcp` SDK, FastMCP, stdio). Five tools and one resource.
  `app/mcp_client.py` is the only code that talks to it, and the only code path to the data files. The app's last tab
  runs live `tools/list` and `resources/list` against it.
* **LangChain**: `@tool` functions (`app/langchain_tools.py`), the audit log as a `BaseCallbackHandler`
  (`app/audit_callback.py`), and the memory store as a `BaseRetriever` (`app/memory.py`).
* **LangGraph**: the whole coordinator is one `StateGraph`. It provides checkpoint/resume (`SqliteSaver`) and the
  human gate (`interrupt()`), and the bounded validate to regenerate loop.

## The 14 labs

| Lab | What was built | Where |
|---|---|---|
| 1 | Clarify, plan, revise agent loop | graph.py clarify/plan/revise |
| 2 | Typed tools computing real values | tools.py, langchain_tools.py |
| 3 | Reusable skills plan(), format_curriculum() | skills.py |
| 4 | Run state vs long-term store, tag and similarity retrieval | memory.py |
| 5 | Real MCP server and client | mcp_server/, mcp_client.py |
| 6 | Runtime: checkpoints, gate, budget, audit | graph.py, audit_callback.py |
| 7 | Explicit node graph with back-edge | graph.py |
| 8 | Parallel swarm: `curriculum_mapping_agent`, `industry_skills_agent`, `acm_apni_benchmarking_agent` are three independent graph nodes with no edge between them, so LangGraph's scheduler runs them in the same superstep (concurrently); `fan_in_specialists` is the merge/selector, waiting on all three. Measured wall-clock vs sequential (about 2x in testing) | graph.py |
| 9 | Grounding: every gap and recommendation carries evidence records (URLs with collection dates, course codes, ACM areas); low-confidence/single-source trends are explicitly flagged; evidence table | analysis.py |
| 10 | Self-healing: diagnose the failing recommendation, regenerate only that one; fault injection slider | validate_node, regenerate_node |
| 11 | Acceptance suite of 8 checks (including an explicit CO/PO-mapping check, substituted with PSO alignment since no CO data was supplied) that must pass before a human sees the draft | analysis.validate() |
| 12 | Roles, department confidentiality guard, versioned publish, rollback, metrics, and an approve/adjust/reject gate (adjust resumes Group E alone, or Groups A-C together) | governance.py, graph.py human_gate_node |
| 13 | Specialist packs: UG CSE-AI and an illustrative PG AI pack change targets and style | analysis.SPECIALIST_PACKS |
| 14 | Streamlit capstone: dashboard, gap report, governance, audit, MCP discovery | streamlit_app.py |

## Data: real, simulated, not supplied

| Data | Status |
|---|---|
| Curriculum I to VIII, 2023-27, including the 2026 revision (Agentic AI 26ECAC401, Cryptography 26ECAC402, Big Data 26ECAE417, Generative AI 25ECAC307) | Real, from your documents |
| Elective catalog (open and program electives, SWAYAM MOOC) | Real, from the 2026 scheme |
| Topic lists for every core Semester I-VIII course, plus Agentic AI, Generative AI, Cryptography & Network Security, Big Data Analytics, Cloud Computing, Cyber Security, Software Testing and Wireless & Mobile Networks | Real: Agentic AI/Generative AI/Cryptography/the electives from `All_Lesson_Plans_Merged_Sequence_Wise.pdf` and `CSE_AI-BOS-MOM.docx` (2023-27 batch); the remaining core courses carried from the 2025-29 master document for same-titled courses (recorded per course in `topics_source`) |
| PEO / PO / PSO | Real, from the 2025-29 master document |
| Industry demand | Real, collected 2026-10-20 via web search: LinkedIn-hosted and syndicated postings, Naukri Campus guides, company career pages. 15 skills, each with source URLs. A small sample, not a labour-market census |
| ACM CS2023 knowledge areas | Real area list; the keyword mapping to courses is this project's own |
| Student attainment, placement feedback, committee notes | **Simulated**, labelled in the files |
| APNI clauses | **Not supplied**. Stub only |

## Real findings (from the real data)

* Using the real unit-wise topics (from the lesson-plan document) and the real Board of Studies
  resolution of 18 April 2026: Agentic AI (26ECAC401) already teaches LangChain, LangGraph, AutoGen,
  the Model Context Protocol and multi-agent orchestration; Generative AI already teaches
  Retrieval-Augmented Generation with a vector-database lab; Cryptography & Network Security covers
  symmetric/asymmetric crypto, PKI, TLS/Kerberos/OAuth and 5G/Wi-Fi security. The system reports all
  of these as **covered_topic** (verified by syllabus), not a title-only guess -- real-data coverage
  is 66.7%, and every one of those covered skills is now syllabus-verified (the "depth unverified"
  category that existed before the lesson plans were supplied is now empty).
* Still genuinely missing from the core curriculum: MLOps / model deployment and monitoring, and
  LLM evaluation and observability. ACM CS2023 Human-Computer Interaction has no course at all.
* Cloud-native deployment, AI security, and big-data platforms are real, detailed electives (Cloud
  Computing 24ECAE317 covers Docker/Kubernetes/Ansible; Cyber Security 24ECSE318 covers SOC/SIEM;
  Big Data Analytics 26ECAE417 covers Hadoop/Spark/NoSQL) -- but electives are not guaranteed for
  every graduate, which is exactly why the system reports them as elective_only rather than covered.
* A real, independent cross-check: a Board of Studies member raised introducing Responsible AI and
  Ethics as a **core** course on 18 April 2026; that proposal was not adopted, and the system's own
  gap analysis separately flags AI security/responsible-AI as elective-only -- two independent
  sources (a human committee discussion, and this system's keyword-grounded analysis) converge on
  the same real gap.
* Course codes are not fully consistent across the university's own documents for the same course
  (for example Computer Organization and Architecture is 24ECAC202 in the structure sheet and
  21ECSC201 in the lesson-plan document). Both codes are recorded rather than silently picked.

## Limitations (say these before you are asked)

1. The LLM is a deterministic mock. Everything else (MCP, LangChain, LangGraph, analysis) is real. One class swaps it.
2. Student attainment and a few committee notes are simulated, and are explicitly labelled as such inside the
   data files, separate from the real Board of Studies resolutions. APNI clause text was never supplied, so
   that half of the benchmark is a documented stub, not a real evaluation.
3. Coverage uses curated keyword matching on real course titles and real unit-wise topics. It is auditable,
   not semantic -- a human should still read the matched course before relying on the result.
4. Nothing is "trained": no model weights are learned. The system reasons from data served by MCP and computed by tools.
5. Real unit-wise topics are loaded for every core Semester I-VIII course and for 7 elective/SWAYAM courses
   (Agentic AI, Generative AI, Cryptography & Network Security, Big Data Analytics, Cloud Computing, Cyber
   Security, Software Testing, Wireless and Mobile Networks), taken from
   `All_Lesson_Plans_Merged_Sequence_Wise.pdf` and `CSE_AI-BOS-MOM.docx`. The remaining electives in the
   catalog (placeholder PE-1 to PE-6 slots not yet selected by a student, plus a few open electives) have a
   title only, since no student has chosen a specific option yet.
6. Course codes are not fully consistent across the university's own documents for the same course -- for
   example Cryptography & Network Security appears as 26ECAC402 in one structure draft, 24ECAC403 in the
   Board-of-Studies-approved table, and 26ECAC305 in the course-content document. All variants seen are
   recorded against the course rather than silently picking one.
