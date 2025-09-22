# DeepAgents & MCP Integration for Advanced RAG Systems — Project Cookbook (for `github.com/donbr/deepagents` fork)

> Date: **September 21, 2025** (America/Los\_Angeles)
> Audience: AI engineers integrating **LangChain DeepAgents** with **Claude Code (MCP)** for multi-strategy RAG, with eval/observability.
> Outcome: A runnable, testable path + CI/CD to land the integration in your fork.

---

## 0) TL;DR

* **Architecture**: DeepAgents (planner, sub-agents, VFS) + MCP (Tools = commands, Resources = queries) using **CQRS** split; retrieval via a **RetrieverFactory** (bm25, vector, parent-doc, multi-query, rerank, ensemble). ;
* **Claude Code**: configure `.mcp.json` with env-expansion and per-workspace overrides; support **stdio** for local dev and **HTTP (streamable)** for team CI runs. ([Claude Docs][1]) ([Claude Docs][2])
* **POC goals**: raw retrieval **<2s**, full answer **<8s**; RAGAS metrics + Phoenix/LangSmith traces in CI.;
* **Grounding**: Patterns and steps below are derived from your attached docs and current upstream docs.   ([LangChain Docs][3])

---

## 1) Repository Additions (proposed tree)

Add a new **`integrations/mcp-rag/`** package to your fork. Keep DeepAgents core untouched; treat MCP/RAG as an integration layer.

```
deepagents/                     # existing
integrations/mcp-rag/
  README.md
  .env.example
  compose.yaml
  pyproject.toml
  src/
    retrievers/
      __init__.py
      factory.py
      bm25.py
      vector.py
      parent_doc.py
      multi_query.py
      rerank.py
      ensemble.py
    mcp/
      server.py            # FastMCP server (Tools + Resources)
      resources.py
      tools.py
    agent/
      deep_agent_boot.py   # create_deep_agent(...) + tool registration
      prompts.py
    eval/
      golden_set.jsonl
      harness.py
      traces.py
  claude/
    .mcp.json              # Claude Code per-workspace config
    CLAUDE.md              # operator runbook
.github/
  workflows/
    mcp-rag-ci.yml         # unit + eval + docker build + artifact publish
    ragas-report.yml       # nightly eval & report upload
```

**Why this shape?** Keeps **retrieval** and **agent wiring** independent from the MCP surface, enabling fast swaps of vector DBs and evaluators without changing agent code. (CQRS & modularity) ;

---

## 2) Claude Code configuration

### 2.1 `.mcp.json` (per-workspace, supports env expansion)

```json
{
  "$schema": "https://modelcontextprotocol.io/schemas/mcp.json",
  "clients": {
    "default": {
      "servers": {
        "deepagents-rag": {
          "command": "uvx",
          "args": ["fastmcp", "run", "integrations/mcp-rag/src/mcp/server.py", "--transport", "stdio"],
          "env": {
            "QDRANT_URL": "${QDRANT_URL}",
            "QDRANT_API_KEY": "${QDRANT_API_KEY:-}",
            "EMBED_MODEL": "${EMBED_MODEL:-sentence-transformers/all-MiniLM-L6-v2}",
            "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}",
            "LANGCHAIN_TRACING_V2": "true",
            "LANGSMITH_API_KEY": "${LANGSMITH_API_KEY:-}",
            "PHOENIX_COLLECTOR_ENDPOINT": "${PHOENIX_COLLECTOR_ENDPOINT:-http://localhost:4317}"
          },
          "timeout": 120000
        }
      }
    }
  }
}
```

* **Env expansion** and defaults (`${VAR:-default}`) are supported by Claude Code; use them to keep secrets out of the repo. ([Claude Docs][1])
* Prefer **stdio** locally; adopt **HTTP (streamable)** behind a container for team/shared runs. ([Claude Docs][2])

### 2.2 Operator runbook `claude/CLAUDE.md`

* `claude doctor` to confirm version & MCP connectivity.
* `claude mcp list` to verify server visibility.
* Workspace-specific overrides live in `claude/.mcp.json` if needed (keeps root clean).

---

## 3) DeepAgents wiring (Python)

```python
# integrations/mcp-rag/src/agent/deep_agent_boot.py
from deepagents import create_deep_agent
from .prompts import INSTRUCTIONS
from ..mcp.tools import retrieve_tool, research_tool  # wraps RetrieverFactory + synthesis

BUILTINS = ["write_todos", "ls", "read_file", "write_file", "edit_file"]  # VFS
CUSTOM_TOOLS = [retrieve_tool, research_tool]

def make_agent():
    return create_deep_agent(
        tools=CUSTOM_TOOLS,
        instructions=INSTRUCTIONS,
        builtin_tools=BUILTINS
    )
```

DeepAgents provides planner, sub-agents, and a sandbox VFS you can keep or trim via `builtin_tools`. ([GitHub][4]) ([LangChain Docs][5]);

---

## 4) MCP surface (CQRS)

* **Tools** (commands): full RAG pipeline with synthesis — `agent.research(question, strategy="auto")`
* **Resources** (queries): raw retrieval — `retriever://{strategy}/{query}` (JSON docs/snippets)
  This dual surface avoids duplication and gives **3–5×** faster responses for quick lookups while preserving a full-answer path.;

```python
# integrations/mcp-rag/src/mcp/server.py
from fastmcp import FastMCP
from .tools import research_tool
from .resources import retrieval_resource

mcp = FastMCP("DeepAgents-RAG")

mcp.tool()(research_tool)  # command path
mcp.resource("retriever://{strategy}/{query}")(retrieval_resource)  # query path

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

FastMCP quickstart + uv install patterns are current and recommended. ([FastMCP][6])
MCP concepts & tool/resource definitions follow spec. ([Model Context Protocol][7])

---

## 5) Retrieval strategies

Implement **six** pluggable strategies behind a shared interface:

```python
# integrations/mcp-rag/src/retrievers/factory.py
from .bm25 import BM25Retriever
from .vector import VectorRetriever
from .parent_doc import ParentDocRetriever
from .multi_query import MultiQueryRetriever
from .rerank import RerankRetriever
from .ensemble import EnsembleRetriever

REGISTRY = {
  "bm25": BM25Retriever,
  "vector": VectorRetriever,
  "parent_doc": ParentDocRetriever,
  "multi_query": MultiQueryRetriever,
  "rerank": RerankRetriever,
  "ensemble": EnsembleRetriever,
  "auto": EnsembleRetriever  # sane default
}

def make(strategy: str, **kw):
    return REGISTRY[strategy](**kw)
```

* Strategy selection guidelines & performance trade-offs reflect your plan and literature. ;
* Ensemble/RRF and parent-doc patterns are first-class. ([Reddit][8]);

---

## 6) Evaluation & Observability

### 6.1 RAGAS harness

```python
# integrations/mcp-rag/src/eval/harness.py
from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

def run_ragas(dataset):
    return evaluate(dataset, metrics=[answer_relevancy, context_precision, context_recall, faithfulness])
```

* Use **golden\_set.jsonl** (10–20 Q/A). Metrics + CSV/JSON artifacts are emitted in CI.;
* LangSmith + Phoenix spans (strategy, k, latency, tokens, scores) for every step (plan→search→synthesize).;

### 6.2 Telemetry

* **Phoenix**: local dev OpenTelemetry collector (`4317`)
* **LangSmith**: prod-like tracing and dataset runs
* Adopt GenAI semantic attributes for spans. (See Observability notes.);

---

## 7) Docker & local run

### 7.1 `compose.yaml`

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
  phoenix:
    image: arizephoenix/phoenix:latest
    ports: ["4317:4317", "6006:6006"]
  mcp:
    build:
      context: .
      dockerfile: integrations/mcp-rag/Dockerfile
    environment:
      QDRANT_URL: http://qdrant:6333
      PHOENIX_COLLECTOR_ENDPOINT: http://phoenix:4317
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    command: ["uvx","fastmcp","run","integrations/mcp-rag/src/mcp/server.py","--transport","http","--port","6277","--path","/mcp"]
    ports: ["6277:6277"]
```

* Prefer **stdio** for Claude local; expose **HTTP** for CI/preview. ([Claude Docs][2])

---

## 8) CI/CD (GitHub Actions)

### 8.1 `mcp-rag-ci.yml` (PRs & main)

* **jobs**: `lint`, `unit`, `build-docker`, `rag-eval`
* Cache uv/pip; run **seed ingest**; execute **RAGAS**; upload **report artifacts**.

```yaml
name: mcp-rag-ci
on: [push, pull_request]
jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: astral-sh/setup-uv@v4
    - run: uv sync
    - run: uv run pytest -q
  rag-eval:
    needs: unit
    runs-on: ubuntu-latest
    services:
      qdrant:
        image: qdrant/qdrant:latest
        ports: ['6333:6333']
      phoenix:
        image: arizephoenix/phoenix:latest
        ports: ['4317:4317']
    steps:
    - uses: actions/checkout@v4
    - uses: astral-sh/setup-uv@v4
    - run: uv sync
    - name: Ingest sample corpus
      run: uv run integrations/mcp-rag/scripts/ingest.py
    - name: Run RAGAS
      run: uv run integrations/mcp-rag/src/eval/cli.py --out ragas_report.json
    - uses: actions/upload-artifact@v4
      with: { name: ragas_report, path: ragas_report.json }
  docker:
    needs: unit
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: docker/setup-buildx-action@v3
    - uses: docker/login-action@v3
      with: { username: ${{ secrets.DOCKERHUB_USERNAME }}, password: ${{ secrets.DOCKERHUB_TOKEN }} }
    - uses: docker/build-push-action@v6
      with:
        context: .
        file: integrations/mcp-rag/Dockerfile
        push: true
        tags: donbr/deepagents-mcp:sha-${{ github.sha }}
```

### 8.2 `ragas-report.yml` (nightly)

* Nightly **evaluation drift** check with rolling trend, publishes to **GitHub Pages** (or uploads artifact).

---

## 9) Step-by-step instructions

1. **Pull fork & create feature branch**

```bash
git checkout -b feat/mcp-rag
```

2. **Install deps**

```bash
uv sync && uv add fastmcp qdrant-client ragas langsmith arize-phoenix-client
```

(uv + fastmcp are recommended by maintainers.) ([FastMCP][9])

3. **Copy `.env.example` → `.env`** and set `ANTHROPIC_API_KEY`, `QDRANT_URL`, etc.

4. **Local run**

```bash
docker compose -f integrations/mcp-rag/compose.yaml up -d qdrant phoenix
uvx fastmcp run integrations/mcp-rag/src/mcp/server.py --transport stdio
```

5. **Claude Code**
   Place `claude/.mcp.json` above into your workspace and open **Claude Code**; run **“list tools”** to confirm. ([Claude Docs][1])

6. **Smoke test**

```bash
# Tool (command): full answer with citations
claude call tool deepagents-rag.research_tool '{"question":"What is DeepAgents and how do I add a custom tool?"}'

# Resource (query): raw retrieval only
curl 'http://localhost:6277/mcp/retriever://bm25/DeepAgents%20planner'
```

7. **Run evaluation**

```bash
uv run integrations/mcp-rag/src/eval/cli.py --dataset integrations/mcp-rag/src/eval/golden_set.jsonl
```

8. **Open traces** in Phoenix ([http://localhost:6006](http://localhost:6006)) and LangSmith (if key provided).;

9. **PR checklist**

* Meets **<2s/<8s** targets on local stack; eval artifacts attached; CI green.;

---

## 10) Security, scaling, and ops notes

* **VFS is sandboxed** (DeepAgents files are not OS files). Keep tool surface minimal; rate-limit & audit.;
* **Transport**: stdio for local trust boundary; streamable HTTP in containers for shared use. ([Claude Docs][2])
* **Caching**: result + embedding + doc caches; measure hit rates and regressions in CI.;
* **Version pinning**: lock DeepAgents, FastMCP, LangChain to avoid schema drift.;
* **Risks**: tool hallucination, long-horizon loops; mitigate with strict tool registry and max-steps.;

---

## 11) References (Appendix)

### A) Attached project docs (primary)

* **DeepAgents & MCP Integration for Advanced RAG Systems** — analysis & roadmap. ;
* **LangChain Local-Deep-Researcher: MCP-Based RAG Enhancement Plan v3** — phased plan & patterns. ;
* **Enhancing Local Deep Researcher with MCP-Based Retrieval & Evaluation (PDF)** — CQRS + quick-wins + eval. ;
* **Research Prompt & INSTRUCTIONS** — acceptance targets, artifacts list.;

### B) Upstream & official docs (current as of 2025-09-21)

* **LangChain DeepAgents (GitHub + Docs)** — built-ins, prompt, APIs. ([GitHub][4])
* **Deep-agents-from-scratch** — sub-agent & delegation patterns. ([GitHub][10])
* **Claude Code MCP configuration** — `.mcp.json`, env expansion. ([Claude Docs][1])
* **Anthropic SDK MCP overview** — transports & embedding in apps. ([Claude Docs][2])
* **MCP spec & concepts** (official). ([Model Context Protocol][7])
* **FastMCP** — quickstart + installation + 2.0 docs. ([FastMCP][6])
* **LangChain ensemble retriever how-to** (RRF). ([Reddit][8])

---

## 12) Appendix — Example code snippets

### 12.1 MCP Tools/Resources (FastMCP)

```python
# tools.py
from ..retrievers.factory import make
from ..agent.deep_agent_boot import make_agent

async def research_tool(question: str, strategy: str = "auto", k: int = 5):
    agent = make_agent()
    retriever = make(strategy, k=k)
    docs = await retriever.retrieve(question)
    # (Synthesis via agent invoke; attach citations)
    return {"answer": "...", "sources": [d.metadata for d in docs], "strategy_used": strategy}
```

```python
# resources.py
from ..retrievers.factory import make

async def retrieval_resource(strategy: str, query: str, k: int = 5):
    retriever = make(strategy, k=k)
    docs = await retriever.retrieve(query)
    return {"documents": [d.page_content for d in docs],
            "metadata": [d.metadata for d in docs]}
```

### 12.2 RAGAS CLI (for CI)

```python
# src/eval/cli.py
import json, sys
from .harness import run_ragas
from .dataset import load_jsonl

if __name__ == "__main__":
    ds = load_jsonl(sys.argv[sys.argv.index("--dataset")+1])
    result = run_ragas(ds)
    with open("ragas_report.json","w") as f:
        json.dump(result.to_dict() if hasattr(result,"to_dict") else result, f, indent=2)
```

---

## 13) Definition of Done (DoD)

* [ ] `.mcp.json` works in Claude Code; tool + resource invocations succeed. ([Claude Docs][1])
* [ ] **RetrieverFactory** exposes 6 strategies; **ensemble** is default.;
* [ ] RAGAS metrics produced and uploaded in CI artifacts; traces visible (Phoenix/LangSmith).;
* [ ] **Performance**: P50 raw retrieval <2s; full answer <8s on dev laptop (compose).;
* [ ] Security checklist: tool registry locked, max-steps enforced, rate limits configured.;

---

### Notes

* DeepAgents’ built-ins (planner/VFS) are intentionally kept — they align with Claude Code’s effective patterns and speed up complex tasks. ([LangChain Docs][5])
* JS parity exists (deepagentsjs) but Python remains primary for this integration. ([GitHub][11])
* Keep transport **stdio** by default. Only expose HTTP inside Docker network for CI. ([Claude Docs][2])

---

If you want, I can also draft the **PR template** and a **Conventional Commits**-aware release workflow next.

[1]: https://docs.claude.com/en/docs/claude-code/mcp?utm_source=chatgpt.com "Connect Claude Code to tools via MCP"
[2]: https://docs.anthropic.com/en/docs/claude-code/sdk/sdk-mcp?utm_source=chatgpt.com "MCP in the SDK - Claude Docs"
[3]: https://docs.langchain.com/labs/deep-agents/overview?utm_source=chatgpt.com "Deep Agents - Docs by LangChain"
[4]: https://github.com/langchain-ai/deepagents?utm_source=chatgpt.com "langchain-ai/deepagents"
[5]: https://docs.langchain.com/labs/deep-agents/built-in-components?utm_source=chatgpt.com "Built-in components - Docs by LangChain"
[6]: https://gofastmcp.com/getting-started/quickstart?utm_source=chatgpt.com "Quickstart"
[7]: https://modelcontextprotocol.io/?utm_source=chatgpt.com "Model Context Protocol"
[8]: https://www.reddit.com/r/ClaudeAI/comments/1jf4hnt/setting_up_mcp_servers_in_claude_code_a_tech/?utm_source=chatgpt.com "Setting Up MCP Servers in Claude Code: A Tech Ritual for ..."
[9]: https://gofastmcp.com/getting-started/installation?utm_source=chatgpt.com "Installation"
[10]: https://github.com/langchain-ai/deep-agents-from-scratch?utm_source=chatgpt.com "langchain-ai/deep-agents-from-scratch"
[11]: https://github.com/langchain-ai/deepagentsjs?utm_source=chatgpt.com "langchain-ai/deepagentsjs: Deep Agents in JS"
