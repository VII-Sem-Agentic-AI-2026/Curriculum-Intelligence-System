# Curriculum Intelligence System

**Agentic AI (26ECAC401) — Course Project**
Worklet-5 · KLE Technological University, School of Computer Science and Engineering

---

## 1. Team

| SI No. | Name | USN | Division |
|---|---|---|---|
| 1 | Sudeep S S | 01FE23BCI101 | CS(AI)-B |
| 2 | Chetan S H | 01FE23BCI108 | CS(AI)-B |
| 3 | Nandeesh I B | 01FE23BCI092 | CS(AI)-B |
| 4 | B Gurubasavaraja | 01FE23BCI120 | CS(AI)-B |

---

## 2. Repository structure

```
Curriculum-Intelligence-System/
├── README.md                      <- this file
├── Assignments/                    <- Lab 1 to Lab 14, one folder each
│   ├── LAB_01_Agent_vs_Chatbot/
│   ├── LAB_02_Tool_Using_Agent/
│   ├── LAB_03_Skill_Creation/
│   ├── LAB_04_Memory_and_Retrieval/
│   ├── LAB_05_MCP_Connector/
│   ├── LAB_06_LangGraph_Runtime/
│   ├── LAB_07_Agentic_Node_Graph/
│   ├── LAB_08_Parallel_Swarm/
│   ├── LAB_09_Deep_Research_Grounding/
│   ├── LAB_10_Ops_Resilience_Self_Healing/
│   ├── LAB_11_Agentic_SDLC_Factory/
│   ├── LAB_12_Safety_and_Governance/
│   ├── LAB_13_Discipline_Specific_Agents/
│   └── LAB_14_Capstone/
│       (each lab folder: README.md with concept/stack/implementation/evidence,
│        a code/ copy of the real source files that implement it, and evidence.txt
│        with a captured, passing test run)
└── Course-Project/
    ├── Problem_Statement/          <- the chapter shared at the start of the course
    ├── Final_Report/                <- the final course project report (.docx)
    ├── docs/                          <- worklet learning canvas, captured evidence
    │   └── evidence/
    │       ├── full_test_suite_run.txt   (33 tests, all passing)
    │       └── cli_demo_run.txt           (a full, real pipeline run)
    └── code/                              <- the complete, runnable project
        ├── app/                            (graph, tools, skills, memory, MCP client, governance)
        ├── mcp_server/                     (the real MCP server and its data)
        ├── streamlit_app.py                (the demo UI)
        ├── demo/run_demo_cli.py            (terminal fallback)
        ├── tests/                          (33 tests)
        ├── requirements.txt
        ├── README.md                       (setup + run instructions)
        └── DEMO_GUIDE.md                   (what to do manually, what to demo, likely questions)
```

---

## 3. Overview of the 14 assignments

Every assignment folder follows the same structure: a concept explanation against the course's own
specification, the technical stack used, the real code that implements it (copied in full, not only linked),
and a captured, passing test run as evidence.

| Lab | Topic | Folder | What it demonstrates |
|---|---|---|---|
| 1 | Agent vs Chatbot | [`Assignments/LAB_01_Agent_vs_Chatbot`](Assignments/LAB_01_Agent_vs_Chatbot) | A real clarify → plan → revise loop as LangGraph nodes, not a one-shot answer |
| 2 | Tool-Using Agent | [`Assignments/LAB_02_Tool_Using_Agent`](Assignments/LAB_02_Tool_Using_Agent) | Every number (credit totals, staleness, skill coverage) is computed by a typed tool, never guessed by the LLM |
| 3 | Skill Creation | [`Assignments/LAB_03_Skill_Creation`](Assignments/LAB_03_Skill_Creation) | Reusable, schema-typed skills proven to work unchanged across two departments |
| 4 | Memory & Retrieval | [`Assignments/LAB_04_Memory_and_Retrieval`](Assignments/LAB_04_Memory_and_Retrieval) | Short-term state vs. a real LangChain retriever with tag and TF-IDF similarity search |
| 5 | MCP-Style Connector | [`Assignments/LAB_05_MCP_Connector`](Assignments/LAB_05_MCP_Connector) | A real MCP server (Anthropic SDK) is the only path to the data, discoverable live |
| 6 | OpenCLA/OpenClaw Runtime | [`Assignments/LAB_06_LangGraph_Runtime`](Assignments/LAB_06_LangGraph_Runtime) | LangGraph checkpoints, a step budget, and a callback-driven audit log |
| 7 | Agentic Node Graph | [`Assignments/LAB_07_Agentic_Node_Graph`](Assignments/LAB_07_Agentic_Node_Graph) | The whole pipeline as one explicit graph with a bounded retry back-edge |
| 8 | Parallel Swarm | [`Assignments/LAB_08_Parallel_Swarm`](Assignments/LAB_08_Parallel_Swarm) | Three independent agents LangGraph schedules concurrently, with a measured speed-up |
| 9 | Deep Research / Grounding | [`Assignments/LAB_09_Deep_Research_Grounding`](Assignments/LAB_09_Deep_Research_Grounding) | Every gap and recommendation carries dated, sourced evidence |
| 10 | Ops Resilience / Self-Healing | [`Assignments/LAB_10_Ops_Resilience_Self_Healing`](Assignments/LAB_10_Ops_Resilience_Self_Healing) | Fault injection proves only the failing item is regenerated, never the whole draft |
| 11 | Agentic SDLC Factory | [`Assignments/LAB_11_Agentic_SDLC_Factory`](Assignments/LAB_11_Agentic_SDLC_Factory) | An 8-check acceptance suite gates every draft before a human sees it |
| 12 | Safety & Governance | [`Assignments/LAB_12_Safety_and_Governance`](Assignments/LAB_12_Safety_and_Governance) | Roles, a confidentiality guard, versioned publish, rollback, and a real approve/adjust/reject gate |
| 13 | Discipline-Specific Agents | [`Assignments/LAB_13_Discipline_Specific_Agents`](Assignments/LAB_13_Discipline_Specific_Agents) | UG and PG specialist packs change recommendation targets and style |
| 14 | Capstone | [`Assignments/LAB_14_Capstone`](Assignments/LAB_14_Capstone) | The full system, demonstrated end to end as a Streamlit app and a CLI fallback |

---

## 4. The course project: Curriculum Intelligence System

### 4.1 Problem statement

Curriculum revision is currently done by manually comparing the syllabus against industry job postings and
accreditation guidelines — a process that takes weeks, happens infrequently, and produces recommendations
that are not traceably linked to evidence. Industry-skill demand changes faster than the review cycle, so
gaps surface only after students are already in interviews. The full problem statement, as shared at the
start of the course, is in
[`Course-Project/Problem_Statement`](Course-Project/Problem_Statement).

### 4.2 Objectives

- Replace an infrequent, manual curriculum review with a continuously re-runnable, evidence-linked pipeline.
- Ground every finding in real data: the official KLE Tech CSE-AI curriculum structure, real unit-wise
  syllabus topics, and live-searched industry postings — not assumptions.
- Benchmark against ACM CS2023 knowledge areas with named, citable categories.
- Keep a human — HoD, Dean (Academics), or Board of Studies — as the final authority, with a genuine
  approve / adjust / reject decision, not a rubber stamp.
- Make the system auditable end to end: every tool call, gap, recommendation and decision is logged and
  versioned.

### 4.3 Approach and architecture

A LangGraph state graph (`Course-Project/code/app/graph.py`) implements the whole pipeline:

```
Coordinator (clarify, plan, revise, lock plan, pick specialist pack)
        │
        ├── Curriculum Mapping Agent   ─┐
        ├── Industry Skills Agent       ├── run concurrently (Lab 8), merged by fan_in_specialists
        └── ACM/APNI Benchmarking Agent ┘
                        │
                 Gap Analysis Agent  (every gap grounded in A/B/C evidence)
                        │
                 Recommendation Agent (every recommendation tied to a gap + evidence)
                        │
      format → validate (8-check acceptance suite) → regenerate only the failing item
                        │
         HoD / Dean (Academics) / Board of Studies  — approve / adjust / reject
                        │
              versioned, rollback-capable publish
```

Every agent reaches data only through a real MCP server; LangChain provides the typed tools, the
callback-driven audit log, and the retrieval-augmented memory; LangGraph provides the checkpointed,
parallel, gated orchestration.

### 4.4 Implementation

| Component | Where | Labs |
|---|---|---|
| Real MCP server + client | `mcp_server/server.py`, `app/mcp_client.py` | 5 |
| LangChain tools, audit callback, retriever | `app/langchain_tools.py`, `app/audit_callback.py`, `app/memory.py` | 2, 4, 6 |
| LangGraph orchestration | `app/graph.py` | 1, 6, 7, 8, 10, 12 |
| Gap analysis, grounding, recommendations, acceptance suite | `app/analysis.py` | 9, 11, 13 |
| Governance: roles, scope, versioning, rollback | `app/governance.py` | 12 |
| Demo interface | `streamlit_app.py`, `demo/run_demo_cli.py` | 14 |

Setup and run instructions: [`Course-Project/code/README.md`](Course-Project/code/README.md).
What to do manually before a live demo, and a demo script: [`Course-Project/code/DEMO_GUIDE.md`](Course-Project/code/DEMO_GUIDE.md).

### 4.5 Results

- **33 automated tests pass** on a clean install — see
  [`Course-Project/docs/evidence/full_test_suite_run.txt`](Course-Project/docs/evidence/full_test_suite_run.txt).
- **Real finding:** industry skill coverage is **66.7%**, and every covered skill is verified against real unit-wise syllabus topics. The real Agentic AI syllabus already teaches
  LangChain, LangGraph, AutoGen and the Model Context Protocol (MCP); the real Generative AI syllabus already
  teaches Retrieval-Augmented Generation (RAG) with a vector-database lab.
- **Real finding, independently corroborated:** a Board of Studies member proposed Responsible AI and
  Ethics as a core courses; it was not adopted. The system's own gap analysis separately
  flags the same topic as elective-only — a human committee discussion and this system's own analysis
  converge on one real gap, from two independent sources.
- **Still genuinely missing** from the core curriculum: MLOps / model deployment and monitoring, and LLM
  evaluation and observability.
- The parallel swarm (Lab 8) measured a real wall-clock speed-up against a sequential estimate in every run.
- A full, captured pipeline run (real MCP calls, parallel agents, a validation self-repair, and a published,
  versioned release) is in
  [`Course-Project/docs/evidence/cli_demo_run.txt`](Course-Project/docs/evidence/cli_demo_run.txt).

### 4.6 Limitations

- The LLM is a deterministic mock, by design, so every demo run is reproducible; every other component
  (MCP, LangChain, LangGraph, the analysis) is real.
- Student attainment and a few committee notes are simulated and labelled as such, separate from the real
  Board of Studies resolutions used elsewhere.
- Course codes are inconsistent across the university's own documents for a few courses (for example,
  Cryptography & Network Security appears as 26ECAC402, 24ECAC403 and 26ECAC305 in different documents);
  every variant seen is recorded rather than one being silently chosen.

The full report — including the agent-roster compliance check, all 14 labs in detail, and the conclusion —
is the final report below.

---

## 5. Links

- **Assignments (Labs 1–14):** [`Assignments/`](Assignments)
- **Project code:** [`Course-Project/code/`](Course-Project/code)
- **Problem statement (shared at the start of the course):** [`Course-Project/Problem_Statement/`](Course-Project/Problem_Statement)
- **Final course project report:** [`Course-Project/Final_Report/Curriculum_Intelligence_System_Final_Report.docx`](Course-Project/Final_Report/Curriculum_Intelligence_System_Final_Report.docx)
- **Worklet learning canvas:** [`Course-Project/docs/Agentic_AI_Worklet_Canvas_Curriculum_Intelligence_System.pptx`](Course-Project/docs/Agentic_AI_Worklet_Canvas_Curriculum_Intelligence_System.pptx)
