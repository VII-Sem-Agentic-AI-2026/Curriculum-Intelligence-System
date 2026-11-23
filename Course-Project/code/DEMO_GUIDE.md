# Demo guide: what to do manually, and what to show the teacher

## Do these yourself before the review (about 20 minutes)

1. Install and test: `pip install -r requirements.txt`, then `python -m pytest tests/ -q`. Expect 29 passed.
2. Run `streamlit run streamlit_app.py` once end to end so the first-run caches are warm.
3. Take screenshots for your report: Dashboard tab, Gaps tab, Audit tab, MCP tab (after pressing Discover), Governance tab after a publish.
   Optionally run the MCP Inspector command from the README and screenshot it.
4. Fill your team name and member names wherever your submission needs them (the app has none hard-coded).
5. If you obtain the real attainment export, replace `mcp_server/data/student_performance.json` (same structure). No code changes.
6. Real unit-wise topics are already loaded for Agentic AI, Generative AI, Cryptography & Network Security and the key electives. If you get an updated syllabus, edit that course's `topics` list in `curriculum.json`; coverage recomputes automatically.
7. Delete the `governance_store/`, `checkpoints/` and `audit_logs/` folders for a clean demo (they are recreated automatically).

## 10-minute demo script

1. Problem (1 min): manual comparison takes weeks, recommendations are not traceable to evidence.
2. Data (1 min), tab "Curriculum and industry data": real KLE curriculum, real postings with URLs. State clearly what is simulated.
3. Run (2 min), tab "Run pipeline": defaults, press Run. While it runs, explain the graph.
4. Result: the parallel-swarm line (wall time vs sequential), the 8 acceptance checks.
5. Dashboard: coverage, ACM table, gap report. Point out the department already added Agentic AI in 2026 and that the system recognises this.
6. Gaps and recommendations: open REC-01, show evidence, prerequisites (real course codes), host course.
7. Approval gate: choose role Faculty and approve to show rejection. Then choose HoD, enter a name, approve. Version v1 is published.
8. Governance: show the version, roll back is possible, metrics row.
9. Second run with the fault slider at 2: show "validation failed 2 time(s); only the failing recommendation was regenerated". Audit tab shows the targeted repair.
10. Run department "ECE": blocked by the confidentiality guard. MCP tab: press Discover to show live MCP capabilities.

## Likely questions and short answers

* **Where is MCP used?** Real MCP server in `mcp_server/server.py`; the agents can only reach data through it. Live proof in the MCP tab and Inspector.
* **LangChain or LangGraph?** Both. LangGraph is the orchestrator, checkpointing and human gate. LangChain gives tools, callback audit log and the retriever.
* **Is the LLM real?** No, a deterministic mock, by design, so every number is reproducible. The numbers come from tools, not from a model.
* **Did you train a model?** No. The system retrieves and computes from data; see limitation 4.
* **Where did the industry data come from?** Live search on 2026-10-20: LinkedIn-hosted postings, Naukri Campus, company career pages. Every skill lists its URLs.
* **How do you know Agentic AI really covers LangChain/LangGraph/MCP?** Its real unit-wise topics were supplied (lesson-plan document) and are loaded into `curriculum.json`; the coverage result is syllabus-verified, not a title guess.
* **What changes in the curriculum are you proposing?** Seven drafts: RAG and vector DB elective, MLOps/cloud-native elective, MCP lab inside Agentic AI, AI security module, HCI module, and two syllabus confirmations. All need Board of Studies approval.
