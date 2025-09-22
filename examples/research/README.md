# DeepAgents Research Examples

This directory contains examples demonstrating how to build research agents using DeepAgents framework.

## Available Examples

### 1. research_agent.py (Original)
The original research agent using direct Tavily Python client integration.

**Features:**
- Direct Tavily API integration
- Sub-agent composition (research + critique)
- File system for report generation
- Comprehensive research workflows

**Usage:**
```bash
export TAVILY_API_KEY=your_api_key_here
PYTHONPATH=../../src uv run python research_agent.py
```

### 2. research_agent_mcp.py (MCP Integration) ⭐
**NEW**: Research agent using Tavily MCP server integration.

**Features:**
- MCP-based tool integration (replacing direct API calls)
- Same research quality with improved architecture
- Demonstrates DeepAgents + MCP integration pattern
- Uses `langchain-mcp-adapters` for seamless tool integration

**Usage:**
```bash
export TAVILY_API_KEY=your_api_key_here
PYTHONPATH=../../src uv run python research_agent_mcp.py
```

**MCP Configuration:**
The agent automatically uses the Tavily MCP server configured in `/.mcp.json`:
```json
{
  "mcpServers": {
    "tavily-remote": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.tavily.com/mcp/?tavilyApiKey=${TAVILY_API_KEY}"],
      "env": {"TAVILY_API_KEY": "${TAVILY_API_KEY}"},
      "timeout": 30000
    }
  }
}
```

### 3. test_mcp_simple.py (Debug/Testing)
Simple test script to verify MCP integration works correctly.

**Usage:**
```bash
export TAVILY_API_KEY=your_api_key_here
PYTHONPATH=../../src uv run python test_mcp_simple.py
```

## MCP Integration Benefits

### Architecture Improvements
- **Separation of Concerns**: Research logic separated from API client management
- **Standardized Interface**: Uses MCP protocol for tool integration
- **Better Error Handling**: MCP provides structured error responses
- **Tool Discovery**: Dynamic tool discovery from MCP servers

### Operational Benefits
- **Multiple Search Engines**: Easy to add Brave Search, other MCP search tools
- **Tool Composition**: Combine multiple MCP servers (search + docs + reasoning)
- **Claude Code Integration**: Works seamlessly with Claude Code MCP ecosystem
- **Remote vs Local**: Can switch between remote and local MCP servers

## Connection Management Best Practices

### ⚠️ Critical: Avoid Connection Storms

**Problem**: Using `client.get_tools()` directly creates a new MCP session for each tool call, causing connection spam.

**❌ Wrong Approach (Connection Storm)**:
```python
# DON'T DO THIS - Creates new session per tool call
client = MultiServerMCPClient({...})
tools = await client.get_tools()  # ⚠️ Connection storm!
```

**✅ Correct Approach (Session Management)**:
```python
# DO THIS - Use explicit session management
from langchain_mcp_adapters.tools import load_mcp_tools

client = MultiServerMCPClient({...})
session_context = client.session("server-name")
session = await session_context.__aenter__()

# Load tools from persistent session
tools = await load_mcp_tools(session)

# Always cleanup
await session_context.__aexit__(None, None, None)
```

### Session Lifecycle Management

1. **Create persistent session** using `client.session()`
2. **Load tools once** from session using `load_mcp_tools()`
3. **Reuse tools** throughout agent execution
4. **Clean up session** on completion or error

### Performance Impact

- **Before Fix**: 20+ connections per research query
- **After Fix**: Single persistent connection
- **Benefit**: Reduced server load, faster execution, cleaner logs

## Next Steps

### Phase 2: Multi-MCP Enhancement
Add support for multiple MCP servers:
- **Brave Search**: Alternative search engine
- **AI Docs**: Technical documentation research
- **Context7**: Library/framework documentation
- **Sequential Thinking**: Enhanced reasoning capabilities

### Phase 3: Advanced Features
- **Search Strategy Selection**: Auto-choose best tool based on query type
- **Cross-Validation**: Compare results from multiple sources
- **Research Workflow Optimization**: Parallel research using sub-agents

## Requirements

- Python 3.11+
- TAVILY_API_KEY environment variable
- Dependencies: `langchain-mcp-adapters`, `deepagents`, `asyncio`

## Troubleshooting

### Common Issues
1. **Missing API Key**: Ensure `TAVILY_API_KEY` is set
2. **MCP Connection**: Check internet connectivity and API key validity
3. **Tool Not Found**: Verify MCP server is responding (use `test_mcp_simple.py`)

### Debug Steps
```bash
# Test MCP connectivity
PYTHONPATH=../../src uv run python test_mcp_simple.py

# Check available MCP servers in Claude Code
claude mcp list

# Verify environment
echo $TAVILY_API_KEY
```

This demonstrates a practical, working example of DeepAgents + MCP integration that provides immediate value while establishing patterns for broader MCP adoption.