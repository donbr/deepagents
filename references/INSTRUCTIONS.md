# Research Prompt: DeepAgents for MCP-Based Retrieval & Evaluation

## Objective
Understand LangChain’s **DeepAgents** (Python + JS) and determine how to integrate it with an **MCP dual interface** (Tools/Resources) to power multi-strategy retrieval and evaluation (RAGAS, Phoenix/LangSmith). Deliver a concise architecture & POC plan we can ship.

## Primary Sources (read in this order)
1) DeepAgents (Python): https://github.com/langchain-ai/deepagents
2) Deep Agents — Labs docs: https://docs.langchain.com/labs/deep-agents/overview
3) Deep-agents-from-scratch: https://github.com/langchain-ai/deep-agents-from-scratch
4) Deep-agents-ui: https://github.com/langchain-ai/deep-agents-ui
5) Deep Agents blog overview: https://blog.langchain.com/deep-agents/

## Key Questions
A. Architecture & APIs  
- What are the core building blocks (planner, sub-agents, tool registry, FS/project context, long-horizon loop)?  
- Python package entry points and minimal example (instantiate, register tools, run).  
- JS/TS parity (capabilities, maturity, gaps).  
- How does state persist (project workspace, scratch files, memory), and where do we hook retrieval?

B. MCP Integration (CQRS)  
- Map DeepAgents calls → **MCP Tools** (command/full answer) and **MCP Resources** (query/raw retrieval).  
- What’s the clean seam to expose: `plan`, `act`, `reflect`, `summarize`, `file_ops`, `retrieval.search(strategy=...)`?  
- Auth & sandboxing for FS/tools; stdio vs HTTP/SSE transport trade-offs; version pinning.

C. Retrieval Strategy Plug-ins  
- Best way to slot **BM25, vector, parent-doc, multi-query expansion, rerank, and RRF/ensemble** under one interface.  
- Where does DeepAgents expect “tools” vs “orchestrated chains”?  
- Latency/recall trade-offs and caching (doc/embedding/result).

D. Evaluation & Observability  
- Minimal harness to score: **answer relevancy, context precision/recall, faithfulness** (RAGAS).  
- Telemetry hooks (Phoenix/OpenTelemetry, LangSmith) for per-step spans (plan → search → synthesize).  
- What JSON artifact should each run emit for dashboards?

## Concrete Tasks
1) **Read/Skim & Extract**  
   - Collect DeepAgents minimal runnable example(s) for Python & (optionally) JS.  
   - Note any required env vars, file layout, and “planner/sub-agent” contracts.

2) **MCP Design (CQRS)**  
   - Propose MCP schema:  
     - Tools (commands): `agent.research(question, strategy="auto")`, `agent.plan(goal)`, `agent.execute(step)`  
     - Resources (queries): `retriever://{strategy}/{query}`, `workspace://files/{path}`  
   - Show stdio vs HTTP config snippets and secrets handling.

3) **Retrieval Plug-in Plan**  
   - Define a **RetrieverFactory** with strategies: `naive`, `bm25`, `multi_query`, `rerank`, `parent_doc`, `ensemble`.  
   - Specify how each is invoked from DeepAgents as a tool (inputs/outputs) and where ranking/fusion occurs.

4) **Eval Harness**  
   - Draft a small golden set (10–20 Q/A) and RAGAS run; specify metrics captured + CSV/JSON schema.  
   - Outline Phoenix/LangSmith span names and attributes (strategy, k, latency, token_use, scores).

5) **POC Checklist & Risks**  
   - Acceptance: raw retrieval <2s, full answer <8s on local stack; RAGAS scores reported; traces visible.  
   - Risks: FS sandboxing, tool mis-use, model JSON-mode reliability; pin versions + fallbacks.

## Output Format (one markdown report)
- **Section 1 — Findings:** bullet summary + short code snippet (DeepAgents init + tool registration).  
- **Section 2 — MCP Interface:** tool/resource table + example `claude.mcp` (or client) config.  
- **Section 3 — Retrieval:** strategy matrix (latency/recall/precision), `RetrieverFactory` stub.  
- **Section 4 — Evaluation:** RAGAS config + sample results JSON + links to traces.  
- **Section 5 — POC Plan:** step-by-step tasks, env vars, compose/services.  
Append **artifacts/** folder: `mcp_server.py`, `retriever_factory.py`, `eval_harness.py`, `golden_set.jsonl`.

## Constraints
- Prefer Python first; JS optional.  
- Local-first runnable via Docker/WSL2; Qdrant/Redis/Phoenix optional services.  
- Keep secrets out of code; use env and .env.example.  
- Pin library versions; add health checks.

## Seed Prompts / Queries (for the agent)
- “Summarize deepagents’ planner + sub-agent model and show a minimal runnable Python example.”  
- “Show how to register a custom ‘retrieve’ tool that calls our RetrieverFactory(strategy=...).”  
- “Propose MCP Tools/Resources to expose DeepAgents; include stdio + HTTP examples.”  
- “Design a RAGAS run capturing answer_relevancy, context_precision/recall, faithfulness, and emit JSON.”  
- “List risks and mitigations for FS access, long-horizon loops, and evaluation drift.”
