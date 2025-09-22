## 🔧 Claude Code Configuration & Change Management

### Claude Code Workspace Configuration

* **`.mcp.json`**:

  * Define MCP servers (FastMCP, ai-docs-server, context7).
  * Support `${VAR:-default}` expansion for environment portability.
  * Stdio for local dev, HTTP streaming for CI/CD.
* **`CLAUDE.md`**:

  * Operator guide including setup, troubleshooting, and CI/CD usage.
  * Rules for tool invocation (`sequential-thinking` for planning, `brave-search` fallback, etc.).

### GitHub Projects & Task Management

* **GitHub Projects Board**:

  * Columns: *Backlog → In Progress → Review → Done*.
  * Labels for MCP tools (`fastmcp`, `deepagents`, `ragas`, `observability`).
  * Milestones aligned to Phases (Foundation, Integration, CI/CD, Production).

* **Tasks & Issues**:

  * Each Phase deliverable tracked as a GitHub issue.
  * Linked to feature branches with auto-closing keywords (`closes #12`).
  * Example issue template: `feature: implement RetrieverFactory strategy #qdrant`.

### Branching & PR Workflow

* **Branching Strategy**:

  * `main`: protected, production-ready.
  * `develop`: integration of feature branches.
  * `feature/*`: one branch per deliverable (e.g., `feature/mcp-resources`).
  * `hotfix/*`: for urgent production fixes.

* **Pull Requests**:

  * Require 1 reviewer + passing CI checks before merge.
  * Include checklist (tests, docs, evaluation metrics).
  * PR template includes “Impact on DeepAgents & MCP Integration” section.

### CI/CD & Change Validation

* **Workflows in `.github/workflows/`**:

  * `mcp-rag-ci.yml`: unit + integration tests.
  * `ragas-report.yml`: nightly drift evals.
* **Branch Protection Rules**:

  * Block merge if tests fail or coverage drops below threshold.
  * Require signed commits for compliance.

### Documentation & Visibility

* **CHANGELOG.md**: auto-updated via GitHub Action on merge.
* **Project Wiki / docs/**: architectural decisions (ADR format).
* **Claude Code Config in Repo**: ensures contributors have consistent environment (`claude config import claude/.mcp.json`).

---

✅ By layering this **change management process** on top of the architecture, you’ve now got:

* Explicit Claude Code workspace config (`.mcp.json`, `CLAUDE.md`).
* GitHub Projects workflow for tracking DeepAgents + MCP deliverables.
* Branching & PR rules for controlled, observable change.
* CI/CD integration enforcing RAG evaluation + observability.
