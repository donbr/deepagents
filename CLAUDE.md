# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ CRITICAL: Pre-Development Checklist

**BEFORE STARTING ANY WORK, YOU MUST:**
- [ ] Read requirements documentation (`references/INSTRUCTIONS.md` or specifications) - See [Requirements Traceability Framework](./references/requirements-traceability-framework.md)
- [ ] Determine if feature is Additive, Enhancement, or Replacement - See [Feature Branch Strategy](./references/feature-branch-strategy.md)
- [ ] Review relevant anti-patterns for your task type - See [Retrospective Analysis](./references/retrospective-analysis.md)
- [ ] For MCP integrations, review session management - See [MCP Session Management Guide](./references/mcp-session-management-guide.md)
- [ ] For architecture decisions, use ADR template - See [ADR Template](./references/adr-template.md)
- [ ] Follow process checklists throughout development - See [Process Improvements](./references/process-improvements-checklists.md)

## 📚 Lessons Learned References

**🎯 QUICK START: See [QUICK-REFERENCE.md](./references/QUICK-REFERENCE.md) for scenario-based guidance on when to use each document**

**IMPORTANT: These documents contain critical lessons from past development. Reference them to avoid repeating mistakes:**

- **[QUICK REFERENCE](./references/QUICK-REFERENCE.md)** - Scenario-based guide for finding the right document quickly
- **[Retrospective Analysis](./references/retrospective-analysis.md)** - Comprehensive analysis of requirements gaps, feature development failures, and change management issues
- **[Requirements Traceability Framework](./references/requirements-traceability-framework.md)** - Systematic approach to prevent scope misalignment
- **[Feature Branch Strategy](./references/feature-branch-strategy.md)** - Guidelines for additive vs replacement development
- **[MCP Session Management Guide](./references/mcp-session-management-guide.md)** - Anti-patterns and best practices for MCP integration
- **[ADR Template](./references/adr-template.md)** - Architectural decision documentation template
- **[Process Improvements & Checklists](./references/process-improvements-checklists.md)** - Actionable checklists for all phases of development

## Development Commands

### Testing and Development
# NOTE: Before starting, review references/retrospective-analysis.md for common pitfalls
- **Install dependencies**: `uv sync` (installs all dependencies including MCP integration)
- **Alternative installation**: `pip install -e .` (editable install for development)
- **Run example research agent**: `uv run python examples/research/research_agent.py` (requires `TAVILY_API_KEY` environment variable)
- **Test package import**: `python3 -c "import deepagents; print('Success')"`
- **Test MCP integration**: `PYTHONPATH=src uv run python test_deepagents_mcp.py` (validates MCP tools work with DeepAgents)

### Package Management
- This project uses Python packaging with `setuptools`
- Dependencies are managed via `pyproject.toml`
- Core dependencies: `langgraph>=0.2.6`, `langchain-anthropic>=0.1.23`, `langchain>=0.2.14`, `tavily-python>=0.7.12`
- Additional model providers: `langchain-openai>=0.3.33`, `langchain-ollama>=0.3.8`
- MCP integration: `fastmcp>=2.12.3`, `langchain-mcp-adapters>=0.1.0`

### Testing
- **No formal test suite**: This project currently lacks unit tests
- **Manual testing**: Test functionality by running the research agent example
- **Integration testing**: Verify agent creation and tool execution via examples
- **MCP integration testing**: Use `test_deepagents_mcp.py` to validate MCP tool integration works end-to-end

## Code Architecture

### Core Components

**Main API Entry Points** (`src/deepagents/graph.py`):
- `create_deep_agent()` - Synchronous agent creation
- `async_create_deep_agent()` - Asynchronous agent creation
- `_agent_builder()` - Internal builder function that handles all agent construction logic

**Agent State Management** (`src/deepagents/state.py`):
- `DeepAgentState` - Core state schema extending LangGraph's state management
- Todo tracking and file system state management

**Built-in Tools** (`src/deepagents/tools.py`):
- `write_todos` - Planning and task management tool
- File system tools: `ls`, `read_file`, `write_file`, `edit_file` (operate on virtual filesystem in agent state)
- All tools use LangGraph's dependency injection for state and tool call IDs
- Tools support both sync and async execution patterns

**Sub-agent System** (`src/deepagents/sub_agent.py`):
- `_create_task_tool()` / `_create_sync_task_tool()` - Creates the `task` tool for spawning sub-agents
- Supports both `SubAgent` (defined by prompt/tools) and `CustomSubAgent` (pre-built LangGraph graphs)
- Built-in "general-purpose" sub-agent always available

**Prompting System** (`src/deepagents/prompts.py`):
- `BASE_AGENT_PROMPT` - Core system prompt heavily inspired by Claude Code's architecture
- Tool-specific descriptions with detailed usage instructions
- Comprehensive examples and patterns for todo management and sub-agent usage

### Key Architectural Patterns

**Virtual File System**:
- All file operations occur in LangGraph state (`files` key), not actual filesystem
- Enables safe multi-agent execution without file conflicts
- Files are accessed via standard CRUD operations through built-in tools

**Planning-First Approach**:
- `write_todos` tool encourages structured task breakdown
- Todo states: `pending`, `in_progress`, `completed`
- Designed to mirror Claude Code's TodoWrite functionality

**Sub-agent Spawning**:
- `task` tool creates ephemeral sub-agents for isolated, complex tasks
- Context quarantine prevents main agent context pollution
- Supports parallel execution of independent sub-tasks

**Human-in-the-Loop** (`src/deepagents/interrupt.py`):
- `ToolInterruptConfig` defines approval workflows
- Supports approve, edit, and respond interactions
- Requires checkpointer for state persistence

### Configuration Options

**Agent Creation Parameters**:
- `tools` - Custom tools to add beyond built-ins
- `instructions` - Custom instructions appended to base prompt
- `model` - Defaults to `"claude-sonnet-4-20250514"`, accepts any LangChain model
- `subagents` - List of custom sub-agent definitions
- `builtin_tools` - Control which built-in tools are available (default: all)
- `main_agent_tools` - Filter which passed-in tools the main agent can use
- `interrupt_config` - Configure human approval for specific tools

**State Schema Customization**:
- `state_schema` parameter allows extending `DeepAgentState`
- Custom schemas must inherit from `DeepAgentState` base class

## Examples and Usage Patterns

**Basic Research Agent** (`examples/research/research_agent.py`):
- Demonstrates sub-agent composition with research and critique agents
- Shows tool filtering (research agent gets only `internet_search`)
- Illustrates virtual file system usage for report generation
- Uses recursion limit of 1000 for complex multi-step research

**Configurable Agents** (`src/deepagents/builder.py`):
- `create_configurable_agent()` for LangGraph Platform deployment
- Enables runtime configuration via `langgraph.json`

**Model Configuration** (`src/deepagents/model.py`):
- `get_default_model()` - Returns default Claude Sonnet 4 model
- Supports custom model configuration per agent and sub-agent

**MCP Integration** (`test_deepagents_mcp.py`):
- Demonstrates proper MCP tool integration using `langchain-mcp-adapters`
- Shows `MultiServerMCPClient` usage with stdio transport
- Validates end-to-end tool execution through DeepAgents
- Pattern: `client.get_tools()` → `async_create_deep_agent(tools=tools)`

## Development Guidelines

# IMPORTANT: Review references/feature-branch-strategy.md before modifying any existing functionality
# WARNING: Never modify working code directly - use additive development patterns

### Working with Sub-agents
- Use `SubAgent` for prompt-defined agents with tool subsets
- Use `CustomSubAgent` for complex pre-built LangGraph graphs
- Always provide clear descriptions for main agent decision-making
- Consider tool filtering to prevent sub-agents from having unnecessary capabilities

### File System Operations
- Always use `ls` before `read_file` or `edit_file`
- Files persist in agent state between tool calls
- Pass files into agent via `files` key in invoke parameter
- Retrieve files from result via `result["files"]`

### Async Considerations
- Use `async_create_deep_agent()` for async tools (e.g., MCP tools)
- MCP integration supported via `langchain-mcp-adapters`
- All built-in tools support both sync and async patterns

### Development Workflow
# CRITICAL: Follow references/process-improvements-checklists.md for all development phases

- **Requirements First**: ALWAYS read requirements documentation before coding - See [Requirements Analysis Checklist](./references/process-improvements-checklists.md#requirements-analysis)
- **Feature Classification**: Determine if Additive, Enhancement, or Replacement - See [Feature Branch Strategy](./references/feature-branch-strategy.md)
- **Preserve Working Code**: Never modify working functionality without explicit approval and migration plan
- **Manual code review**: Changes are reviewed through pull requests using [Pre-Merge Checklist](./references/process-improvements-checklists.md#pre-merge-checklist)
- **Example-driven development**: New features tested via working examples in `examples/`
- **Document Architectural Decisions**: Use [ADR Template](./references/adr-template.md) for significant decisions
- **ADR Location**: ALL Architecture Decision Records MUST be placed in `/adr/` directory (NOT references/)

### Model Configuration
- Per-sub-agent model override via `model_settings` in SubAgent definition
- Supports both model strings and full LangChain model instances
- Temperature, max_tokens, and other parameters configurable per sub-agent

### MCP Integration Guidelines

# ⚠️ CRITICAL WARNING: Avoid Connection Storms
# READ references/mcp-session-management-guide.md BEFORE implementing MCP integration

- **Use `MultiServerMCPClient`**: Connect to MCP servers via stdio transport for best reliability
- **❌ ANTI-PATTERN (DO NOT USE)**: `tools = await client.get_tools()` - This creates connection storms!
- **✅ CORRECT PATTERN**: Use explicit session management:
  ```python
  from langchain_mcp_adapters.tools import load_mcp_tools

  # Create persistent session
  session_ctx = client.session("server-name")
  session = await session_ctx.__aenter__()
  tools = await load_mcp_tools(session)  # Load tools from persistent session
  # Always cleanup: await session_ctx.__aexit__(None, None, None)
  ```
- **Transport Types**: Prefer stdio over HTTP for local MCP servers
- **Testing**: Validate integration with `test_deepagents_mcp.py` after changes
- **Session Management**: Always use explicit session lifecycle management to avoid connection storms
- **Performance Impact**: Proper session management reduces connections from 20+ to 1 per server