#!/usr/bin/env python3
"""
Test DeepAgents integration with MCP RAG server.
This validates that DeepAgents agents can call our MCP tools.
"""

import asyncio
import subprocess
import time
from deepagents import async_create_deep_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_mcp_integration():
    """Test if DeepAgents can call MCP tools via proper MCP client."""

    print("🤖 Creating MCP client and connecting to server...")

    try:
        # Create MCP client with stdio transport
        client = MultiServerMCPClient({
            "deepagents-rag": {
                "transport": "stdio",
                "command": "uv",
                "args": ["run", "python", "integrations/mcp-rag/minimal_test.py"]
            }
        })

        print("🔗 Getting MCP tools...")

        # Get tools from MCP server
        tools = await client.get_tools()
        print(f"📦 Available MCP tools: {[tool.name for tool in tools]}")

        print("🚀 Creating DeepAgents agent with MCP tools...")

        # Create DeepAgents agent with MCP tools
        agent = async_create_deep_agent(
            tools=tools,
            instructions="""You are a test agent for validating MCP integration.
            You have access to MCP tools: test_connection and simple_benchmark.
            Use these tools to test the MCP connection and report the results."""
        )

        print("📞 Testing MCP tool calls through DeepAgents...")

        # Test the agent with MCP tools
        result = await agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": "Test the MCP connection by calling the test_connection tool and then run a simple_benchmark. Report the results."
            }]
        })

        print("✅ DeepAgents Response:")
        # Extract the final message content
        final_message = result["messages"][-1]
        if hasattr(final_message, 'content'):
            print(final_message.content)
        else:
            print(f"Final message: {final_message}")

        # Check if tools were actually called
        tool_calls_found = any(
            hasattr(msg, 'tool_calls') and msg.tool_calls
            for msg in result["messages"]
            if hasattr(msg, 'tool_calls')
        )

        if tool_calls_found:
            print("🎉 SUCCESS: MCP tools were called successfully!")
            return True
        else:
            print("⚠️  WARNING: No tool calls detected in conversation")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # MultiServerMCPClient cleanup is handled automatically
        pass

async def test_simple_mcp_call():
    """Test simple MCP client connection without DeepAgents."""

    print("🔧 Testing direct MCP client connection...")

    try:
        # Test direct MCP client connection
        client = MultiServerMCPClient({
            "deepagents-rag": {
                "transport": "stdio",
                "command": "uv",
                "args": ["run", "python", "integrations/mcp-rag/minimal_test.py"]
            }
        })

        # Get available tools
        tools = await client.get_tools()
        print(f"📦 Direct MCP tools: {[tool.name for tool in tools]}")

        # Test calling a tool directly
        if tools:
            tool_name = tools[0].name
            print(f"🔧 Testing direct tool call: {tool_name}")

            # Get the tool and call it
            result = await tools[0].ainvoke({})
            print(f"📄 Tool result: {result}")

        # MultiServerMCPClient cleanup is handled automatically
        return len(tools) > 0

    except Exception as e:
        print(f"❌ Direct MCP Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run MCP integration tests."""
    print("🧪 Testing DeepAgents MCP Integration\n")

    # Test 1: Direct MCP client
    print("=" * 50)
    print("Test 1: Direct MCP Client Connection")
    print("=" * 50)

    mcp_success = await test_simple_mcp_call()
    print(f"Direct MCP client: {'✅ PASS' if mcp_success else '❌ FAIL'}\n")

    # Test 2: DeepAgents integration
    print("=" * 50)
    print("Test 2: DeepAgents MCP Integration")
    print("=" * 50)

    deepagents_success = await test_mcp_integration()
    print(f"DeepAgents integration: {'✅ PASS' if deepagents_success else '❌ FAIL'}\n")

    # Summary
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Direct MCP Client: {'✅ PASS' if mcp_success else '❌ FAIL'}")
    print(f"DeepAgents Integration: {'✅ PASS' if deepagents_success else '❌ FAIL'}")

    if mcp_success and deepagents_success:
        print("\n🎉 ALL TESTS PASSED - MCP Integration Working!")
        return True
    else:
        print("\n⚠️  Some tests failed - Need debugging")
        return False

if __name__ == "__main__":
    asyncio.run(main())