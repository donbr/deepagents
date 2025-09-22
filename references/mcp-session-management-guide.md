# MCP Session Management: Anti-Patterns and Best Practices

## Overview

This guide documents critical lessons learned from implementing MCP (Model Context Protocol) integration with DeepAgents, specifically focusing on session management patterns that prevent connection storms and ensure optimal performance.

## The Connection Storm Problem

### What Happened
During the initial MCP integration, we encountered a **connection storm** where each tool call created a new MCP session, resulting in:
- 20+ simultaneous connections per research query
- Server overload and log spam
- Unacceptable user experience
- Need for emergency architectural fixes

### Root Cause
The issue stemmed from using `client.get_tools()` which, according to `langchain-mcp-adapters` documentation:
> "NOTE: a new session will be created for each tool call"

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Tool-Per-Session
**Problem:** Creating new session for each tool invocation.

```python
# DON'T DO THIS - Creates connection storm
from langchain_mcp_adapters.client import MultiServerMCPClient

async def wrong_approach():
    client = MultiServerMCPClient({
        "tavily-remote": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "mcp-remote", "https://mcp.tavily.com/mcp/?tavilyApiKey=..."]
        }
    })

    # ⚠️ PROBLEM: This creates a new session for each tool call!
    tools = await client.get_tools()

    # Each time these tools are used, new connection is created
    for tool in tools:
        result = await tool.ainvoke({"query": "test"})  # New session!
```

**Impact:**
- Exponential connection growth
- Resource exhaustion
- Server-side rate limiting
- Poor performance

### ❌ Anti-Pattern 2: Session Per Request
**Problem:** Creating new session for each user request.

```python
# DON'T DO THIS - Inefficient session management
async def handle_request(query: str):
    # New session for every request
    client = MultiServerMCPClient({...})
    session_ctx = client.session("tavily-remote")
    session = await session_ctx.__aenter__()

    try:
        result = await session.call_tool("tavily_search", {"query": query})
        return result
    finally:
        await session_ctx.__aexit__(None, None, None)
```

**Impact:**
- Connection overhead for each request
- Slow response times
- Resource waste

### ❌ Anti-Pattern 3: No Session Cleanup
**Problem:** Creating sessions without proper cleanup.

```python
# DON'T DO THIS - Resource leaks
async def leaky_session():
    client = MultiServerMCPClient({...})
    session_ctx = client.session("tavily-remote")
    session = await session_ctx.__aenter__()

    # Use session...
    result = await session.call_tool("search", {"query": "test"})

    # ⚠️ PROBLEM: No cleanup! Session remains open
    return result
```

**Impact:**
- Resource leaks
- Connection exhaustion over time
- Unpredictable behavior

### ❌ Anti-Pattern 4: Global Session Without Management
**Problem:** Global session without proper lifecycle management.

```python
# DON'T DO THIS - Unmanaged global state
mcp_session = None  # Global session

async def initialize():
    global mcp_session
    client = MultiServerMCPClient({...})
    session_ctx = client.session("tavily-remote")
    mcp_session = await session_ctx.__aenter__()
    # ⚠️ PROBLEM: No way to clean up context manager

async def use_session():
    global mcp_session
    return await mcp_session.call_tool("search", {"query": "test"})

# No cleanup mechanism defined
```

**Impact:**
- Difficult session lifecycle management
- No graceful shutdown
- Testing complications

## Best Practices

### ✅ Pattern 1: Application-Level Session Management
**Approach:** Create persistent session at application startup, reuse throughout lifecycle.

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from contextlib import asynccontextmanager

class MCPSessionManager:
    def __init__(self, config: dict):
        self.config = config
        self.client = None
        self.session_contexts = {}
        self.sessions = {}
        self.tools = {}

    async def initialize(self):
        """Initialize MCP client and create persistent sessions"""
        self.client = MultiServerMCPClient(self.config)

        for server_name in self.config.keys():
            # Create session context
            session_ctx = self.client.session(server_name)
            self.session_contexts[server_name] = session_ctx

            # Initialize session
            session = await session_ctx.__aenter__()
            self.sessions[server_name] = session

            # Load tools from session
            tools = await load_mcp_tools(session)
            self.tools[server_name] = tools

        print(f"✅ Initialized {len(self.sessions)} MCP sessions")

    async def cleanup(self):
        """Clean up all sessions"""
        for server_name, session_ctx in self.session_contexts.items():
            try:
                await session_ctx.__aexit__(None, None, None)
                print(f"🔗 Closed MCP session: {server_name}")
            except Exception as e:
                print(f"⚠️ Error closing session {server_name}: {e}")

        self.sessions.clear()
        self.session_contexts.clear()
        self.tools.clear()

    def get_tools(self, server_name: str = None):
        """Get tools from specific server or all servers"""
        if server_name:
            return self.tools.get(server_name, [])

        # Return all tools from all servers
        all_tools = []
        for tools in self.tools.values():
            all_tools.extend(tools)
        return all_tools

    async def call_tool(self, server_name: str, tool_name: str, args: dict):
        """Direct tool call using persistent session"""
        session = self.sessions.get(server_name)
        if not session:
            raise ValueError(f"No session for server: {server_name}")

        return await session.call_tool(tool_name, args)

# Usage example
session_manager = MCPSessionManager({
    "tavily-remote": {
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "mcp-remote", "https://mcp.tavily.com/mcp/?tavilyApiKey=..."]
    }
})

async def application_startup():
    await session_manager.initialize()

async def application_shutdown():
    await session_manager.cleanup()

async def search(query: str):
    # Reuse persistent session - no new connections!
    return await session_manager.call_tool("tavily-remote", "tavily_search", {"query": query})
```

### ✅ Pattern 2: Context Manager Pattern
**Approach:** Use proper async context managers for session lifecycle.

```python
@asynccontextmanager
async def mcp_session(config: dict, server_name: str):
    """Async context manager for MCP session lifecycle"""
    client = MultiServerMCPClient(config)
    session_ctx = client.session(server_name)

    try:
        session = await session_ctx.__aenter__()
        tools = await load_mcp_tools(session)
        yield session, tools
    finally:
        await session_ctx.__aexit__(None, None, None)

# Usage
async def research_with_proper_cleanup(query: str):
    config = {"tavily-remote": {...}}

    async with mcp_session(config, "tavily-remote") as (session, tools):
        # Use session and tools
        search_tool = next(t for t in tools if t.name == "tavily_search")
        result = await search_tool.ainvoke({"query": query})
        return result
    # Session automatically cleaned up
```

### ✅ Pattern 3: Tool Factory with Session Reuse
**Approach:** Create tools once, reuse throughout application lifecycle.

```python
class MCPToolFactory:
    def __init__(self):
        self.session_manager = None
        self.tools_cache = {}

    async def initialize(self, config: dict):
        """Initialize session manager and cache tools"""
        self.session_manager = MCPSessionManager(config)
        await self.session_manager.initialize()

        # Cache tools by name for easy access
        for server_name, tools in self.session_manager.tools.items():
            for tool in tools:
                self.tools_cache[tool.name] = tool

    async def get_tool(self, tool_name: str):
        """Get cached tool - no session creation"""
        tool = self.tools_cache.get(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        return tool

    async def cleanup(self):
        """Clean up session manager"""
        if self.session_manager:
            await self.session_manager.cleanup()

# Global factory instance
tool_factory = MCPToolFactory()

async def initialize_tools():
    config = {"tavily-remote": {...}}
    await tool_factory.initialize(config)

async def search(query: str):
    # Get cached tool - no new sessions!
    search_tool = await tool_factory.get_tool("tavily_search")
    return await search_tool.ainvoke({"query": query})
```

### ✅ Pattern 4: Session Pool for High Concurrency
**Approach:** Pool of sessions for high-throughput applications.

```python
import asyncio
from asyncio import Queue

class MCPSessionPool:
    def __init__(self, config: dict, server_name: str, pool_size: int = 5):
        self.config = config
        self.server_name = server_name
        self.pool_size = pool_size
        self.session_pool = Queue(maxsize=pool_size)
        self.client = None

    async def initialize(self):
        """Initialize session pool"""
        self.client = MultiServerMCPClient(self.config)

        # Create pool of sessions
        for _ in range(self.pool_size):
            session_ctx = self.client.session(self.server_name)
            session = await session_ctx.__aenter__()
            await self.session_pool.put((session_ctx, session))

        print(f"✅ Initialized session pool with {self.pool_size} sessions")

    @asynccontextmanager
    async def get_session(self):
        """Get session from pool, return after use"""
        session_ctx, session = await self.session_pool.get()
        try:
            yield session
        finally:
            await self.session_pool.put((session_ctx, session))

    async def cleanup(self):
        """Clean up all sessions in pool"""
        while not self.session_pool.empty():
            session_ctx, session = await self.session_pool.get()
            try:
                await session_ctx.__aexit__(None, None, None)
            except Exception as e:
                print(f"⚠️ Error closing pooled session: {e}")

# Usage for high-concurrency scenarios
pool = MCPSessionPool(config, "tavily-remote", pool_size=10)

async def concurrent_search(query: str):
    async with pool.get_session() as session:
        return await session.call_tool("tavily_search", {"query": query})

# Can handle many concurrent requests efficiently
tasks = [concurrent_search(f"query {i}") for i in range(100)]
results = await asyncio.gather(*tasks)
```

## Framework Integration Patterns

### DeepAgents Integration
**Corrected implementation from our case study:**

```python
from deepagents import async_create_deep_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

# Global session management
mcp_client = None
mcp_session_context = None
search_tool = None

async def initialize_mcp():
    """Initialize MCP with proper session management"""
    global mcp_client, mcp_session_context, search_tool

    if mcp_client is None:
        print("🔗 Initializing MCP client with persistent session...")
        mcp_client = MultiServerMCPClient({
            "tavily-remote": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "mcp-remote", f"https://mcp.tavily.com/mcp/?tavilyApiKey=..."]
            }
        })

        # Create persistent session to avoid connection storms
        print("📡 Creating persistent MCP session...")
        mcp_session_context = mcp_client.session("tavily-remote")
        session = await mcp_session_context.__aenter__()

        # Load tools from persistent session
        tools = await load_mcp_tools(session)
        print(f"📦 Available MCP tools: {[tool.name for tool in tools]}")

        # Find and rename tool for agent use
        for tool in tools:
            if tool.name == "tavily_search":
                search_tool = tool
                search_tool.name = "internet_search"  # Rename for agent
                break

        if not search_tool:
            raise RuntimeError("Tavily search tool not found in MCP server")

        print("✅ MCP integration ready with persistent session!")

    return search_tool

async def cleanup_mcp():
    """Clean up MCP session"""
    global mcp_session_context
    if mcp_session_context:
        try:
            await mcp_session_context.__aexit__(None, None, None)
            print("🔗 MCP session closed")
        except Exception as e:
            print(f"⚠️ Error closing MCP session: {e}")

async def create_research_agent():
    """Create DeepAgents research agent with MCP tools"""
    # Initialize MCP with proper session management
    search_tool = await initialize_mcp()

    # Create agent with persistent MCP tool
    agent = async_create_deep_agent(
        tools=[search_tool],
        instructions="You are an expert researcher...",
        subagents=[research_sub_agent, critique_sub_agent],
    )

    return agent

async def main():
    try:
        agent = await create_research_agent()
        result = await agent.ainvoke({"messages": [...]})
        return result
    finally:
        # Always clean up
        await cleanup_mcp()
```

## Performance Monitoring

### Connection Metrics
```python
import time
from collections import defaultdict

class MCPMetrics:
    def __init__(self):
        self.connection_count = 0
        self.session_durations = []
        self.tool_call_times = defaultdict(list)

    def track_session_start(self):
        self.connection_count += 1
        return time.time()

    def track_session_end(self, start_time: float):
        duration = time.time() - start_time
        self.session_durations.append(duration)

    def track_tool_call(self, tool_name: str, duration: float):
        self.tool_call_times[tool_name].append(duration)

    def get_stats(self):
        return {
            "total_connections": self.connection_count,
            "avg_session_duration": sum(self.session_durations) / len(self.session_durations) if self.session_durations else 0,
            "tool_call_stats": {
                name: {
                    "count": len(times),
                    "avg_duration": sum(times) / len(times),
                    "max_duration": max(times) if times else 0
                }
                for name, times in self.tool_call_times.items()
            }
        }

# Usage
metrics = MCPMetrics()

# Track session lifecycle
@asynccontextmanager
async def monitored_session(config, server_name):
    start_time = metrics.track_session_start()
    try:
        async with mcp_session(config, server_name) as (session, tools):
            yield session, tools
    finally:
        metrics.track_session_end(start_time)
```

## Testing Strategies

### Session Management Tests
```python
import pytest
import asyncio

class TestMCPSessionManagement:
    async def test_single_session_multiple_calls(self):
        """Verify single session can handle multiple tool calls"""
        session_manager = MCPSessionManager(test_config)
        await session_manager.initialize()

        try:
            # Multiple calls should reuse same session
            result1 = await session_manager.call_tool("tavily-remote", "tavily_search", {"query": "test1"})
            result2 = await session_manager.call_tool("tavily-remote", "tavily_search", {"query": "test2"})

            # Verify results without creating new connections
            assert result1 is not None
            assert result2 is not None
            assert len(session_manager.sessions) == 1  # Only one session created

        finally:
            await session_manager.cleanup()

    async def test_session_cleanup(self):
        """Verify proper session cleanup"""
        session_manager = MCPSessionManager(test_config)
        await session_manager.initialize()

        # Verify session exists
        assert len(session_manager.sessions) == 1

        # Clean up
        await session_manager.cleanup()

        # Verify cleanup
        assert len(session_manager.sessions) == 0
        assert len(session_manager.session_contexts) == 0

    async def test_concurrent_tool_calls(self):
        """Verify concurrent calls don't create connection storms"""
        session_manager = MCPSessionManager(test_config)
        await session_manager.initialize()

        try:
            # Concurrent calls using same session
            tasks = [
                session_manager.call_tool("tavily-remote", "tavily_search", {"query": f"test{i}"})
                for i in range(10)
            ]

            results = await asyncio.gather(*tasks)

            # All calls successful, still only one session
            assert len(results) == 10
            assert all(r is not None for r in results)
            assert len(session_manager.sessions) == 1

        finally:
            await session_manager.cleanup()

    async def test_session_error_recovery(self):
        """Verify graceful handling of session errors"""
        session_manager = MCPSessionManager(test_config)
        await session_manager.initialize()

        try:
            # Simulate session error
            session = session_manager.sessions["tavily-remote"]
            # Force close connection
            await session.close()

            # Attempt to use should fail gracefully
            with pytest.raises(Exception):
                await session_manager.call_tool("tavily-remote", "tavily_search", {"query": "test"})

        finally:
            await session_manager.cleanup()
```

## Troubleshooting Guide

### Common Issues and Solutions

**Issue 1: Connection Storms**
- **Symptom:** Many connections shown in logs
- **Cause:** Using `client.get_tools()` without session management
- **Solution:** Use persistent session with `load_mcp_tools(session)`

**Issue 2: Session Leaks**
- **Symptom:** Memory usage grows over time
- **Cause:** Sessions created but not cleaned up
- **Solution:** Always use try/finally or context managers

**Issue 3: Tool Not Found**
- **Symptom:** Tool not available in DeepAgents
- **Cause:** Session not initialized properly
- **Solution:** Verify session creation and tool loading

**Issue 4: Performance Degradation**
- **Symptom:** Slow response times
- **Cause:** Creating new sessions per request
- **Solution:** Reuse sessions at application level

### Debugging Commands
```bash
# Monitor active connections
netstat -an | grep :443 | wc -l

# Check MCP server logs
docker logs mcp-server-container

# Test MCP connectivity
PYTHONPATH=../../src uv run python test_mcp_simple.py

# Monitor session lifecycle
tail -f application.log | grep "MCP session"
```

This guide provides the foundation for robust MCP session management that avoids connection storms and ensures optimal performance in production deployments.