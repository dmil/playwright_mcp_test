#!/usr/bin/env python3
"""
MCP Client for Playwright Integration

This module provides a client for connecting to the Playwright MCP server
and using it with Claude via the Anthropic API.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from anthropic import Anthropic


class PlaywrightMCPClient:
    """
    Client for interacting with Playwright MCP server and Claude.

    This class:
    1. Connects to the Playwright MCP server via stdio
    2. Retrieves available tools from the server
    3. Converts MCP tools to Anthropic tool format
    4. Handles the agentic loop for tool calling with Claude
    """

    def __init__(self, api_key: str):
        """
        Initialize the MCP client.

        Args:
            api_key: Anthropic API key
        """
        self.api_key = api_key
        self.anthropic = Anthropic(api_key=api_key)
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect(self):
        """Connect to the Playwright MCP server."""
        # Configure the MCP server parameters based on .mcp.json
        server_params = StdioServerParameters(
            command="npx",
            args=["@playwright/mcp@latest", "--executable-path", "/usr/bin/chromium"],
            env=None
        )

        # Connect to the server
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        # Initialize the session
        await self.session.initialize()

        print("✓ Connected to Playwright MCP server")

    async def disconnect(self):
        """Disconnect from the MCP server."""
        await self.exit_stack.aclose()
        print("✓ Disconnected from Playwright MCP server")

    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get the list of available tools from the MCP server.

        Returns:
            List of tools in Anthropic tool format
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        # List tools from the MCP server
        response = await self.session.list_tools()

        # Convert MCP tools to Anthropic tool format
        anthropic_tools = []
        for tool in response.tools:
            anthropic_tool = {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema
            }
            anthropic_tools.append(anthropic_tool)

        print(f"✓ Retrieved {len(anthropic_tools)} tools from MCP server")
        return anthropic_tools

    async def call_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            tool_input: Input parameters for the tool

        Returns:
            Tool execution result
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        # Call the tool via MCP
        result = await self.session.call_tool(tool_name, arguments=tool_input)

        return result

    async def run_agent_loop(
        self,
        user_message: str,
        max_iterations: int = 10,
        final_answer_tool: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Run the agentic loop with Claude and MCP tools.

        This implements the tool calling loop:
        1. Send message to Claude with available tools
        2. If Claude wants to use a tool, execute it via MCP
        3. Send tool results back to Claude
        4. Repeat until Claude provides a final answer

        Args:
            user_message: The user's request/prompt
            max_iterations: Maximum number of iterations to prevent infinite loops
            final_answer_tool: Optional tool definition for structured output.
                             If provided, Claude will use this tool to return structured data.

        Returns:
            If final_answer_tool is provided: the structured data from that tool
            Otherwise: Claude's final text response
        """
        # Get available tools from MCP
        tools = await self.get_available_tools()

        # Add the final answer tool if provided (for structured outputs)
        if final_answer_tool:
            tools.append(final_answer_tool)

        # Initialize conversation messages
        messages = [{"role": "user", "content": user_message}]

        print(f"\n{'='*70}")
        print("Starting agentic loop with Claude + Playwright MCP")
        print(f"{'='*70}\n")

        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"--- Iteration {iteration} ---")

            # Call Claude with tools
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                tools=tools,
                messages=messages
            )

            print(f"Stop reason: {response.stop_reason}")

            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Add Claude's response to messages
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Process each tool use
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_use_id = block.id

                        print(f"  → Claude wants to use tool: {tool_name}")
                        print(f"    Input: {json.dumps(tool_input, indent=2)[:200]}...")

                        # Check if this is the final answer tool
                        if final_answer_tool and tool_name == final_answer_tool["name"]:
                            print(f"  ✓ Claude provided structured final answer")
                            return tool_input

                        # Execute the tool via MCP
                        try:
                            result = await self.call_tool(tool_name, tool_input)

                            # MCP returns a list of content items
                            # Convert to string for Anthropic
                            if hasattr(result, 'content'):
                                result_content = []
                                for item in result.content:
                                    if hasattr(item, 'text'):
                                        result_content.append(item.text)
                                result_str = "\n".join(result_content)
                            else:
                                result_str = str(result)

                            print(f"  ✓ Tool executed successfully")

                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": result_str
                            })
                        except Exception as e:
                            print(f"  ✗ Tool execution failed: {e}")
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": f"Error: {str(e)}",
                                "is_error": True
                            })

                # Add tool results to messages
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

            elif response.stop_reason == "end_turn":
                # Claude has finished - extract the final text response
                final_response = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        final_response += block.text

                print(f"\n✓ Claude finished after {iteration} iterations")
                return final_response
            else:
                # Unexpected stop reason
                print(f"Unexpected stop reason: {response.stop_reason}")
                break

        print(f"\n✗ Reached max iterations ({max_iterations})")
        return "Error: Maximum iterations reached without completion"


async def main():
    """Example usage of the PlaywrightMCPClient."""
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key or api_key == "your_api_key_here":
        print("Error: Please set ANTHROPIC_API_KEY in .env file")
        return

    # Create and connect the client
    client = PlaywrightMCPClient(api_key)

    try:
        await client.connect()

        # Example: Navigate to a website and extract information
        user_message = """
        Please use Playwright MCP to:
        1. Navigate to https://omar.house.gov/
        2. Close any popups that appear
        3. Find the social media links container (class 'evo-social-icons-here')
        4. Extract all the social media link URLs
        5. Return them as a JSON array
        """

        response = await client.run_agent_loop(user_message)

        print(f"\n{'='*70}")
        print("Final Response:")
        print(f"{'='*70}")
        print(response)

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
