#!/usr/bin/env python
import asyncio
import sys
import logging
import json
import os
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_ollama import ChatOllama

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        # Get Ollama model from environment variable or use default
        ollama_model = os.environ.get("OLLAMA_MODEL", "qwen3")
        logger.info(f"Using Ollama model: {ollama_model}")
        
        self.llm = ChatOllama(
            model=ollama_model,
            num_ctx=32000,
            base_url="http://localhost:11434",  # Explicitly set Ollama URL
            temperature=0,  # Reduce randomness for more consistent outputs
        )

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        logger.debug(f"Connecting to server at {server_script_path}")
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
            
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
        
        logger.debug("Creating stdio transport")
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        
        logger.debug("Creating client session")
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        logger.debug("Initializing session")
        await self.session.initialize()
        
        # List available tools
        logger.debug("Listing tools")
        try:
            response = await self.session.list_tools()
            tools = response.tools
            print("\nConnected to server with tools:", [tool.name for tool in tools])
        except Exception as e:
            logger.error(f"Error listing tools: {str(e)}", exc_info=True)
            raise

    async def test_ollama_models(self):
        """Test browser automation with Ollama model library"""
        try:
            # Get available tools for LLM
            response = await self.session.list_tools()
            available_tools = [{
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            } for tool in response.tools]

            # Initial prompt for LLM
            prompt = """
            You are a browser automation expert with advanced capabilities for web analysis and data extraction. Your task is to navigate to Ollama's model library, analyze the page content, and extract structured information about the available models.
            
            Available tools:
            {tools}
            
            Browser window size: 900x600 pixels
            
            Required steps:
            1. Launch browser to https://ollama.com/library
            2. Wait for page to load
            3. Get the DOM structure to understand the page layout
            4. Extract data about the models (look for model names, descriptions, sizes)
            5. Take a screenshot to capture the visual state
            6. Scroll down to see more models
            7. Get page content for text analysis
            8. Extract additional data that might be visible after scrolling
            9. Close the browser
            
            For each step, output a JSON object with the tool name and parameters needed.
            Format your entire response as a JSON array of these objects.
            
            Use semantic selectors when possible instead of raw coordinates. For example, use click_selector with CSS selectors rather than click_element with x,y coordinates when elements can be identified by selectors.
            
            Example format:
            [
                {{"name": "launch_browser", "parameters": {{"url": "https://ollama.com/library"}}}},
                {{"name": "get_dom_structure", "parameters": {{"session_id": "0", "max_depth": 3}}}},
                {{"name": "extract_data", "parameters": {{"session_id": "0", "pattern": "article headlines"}}}},
                {{"name": "click_selector", "parameters": {{"session_id": "0", "selector": ".model-card"}}}}
            ]
            """.format(tools=json.dumps(available_tools, indent=2))

            # Get LLM's response
            print("\nSending prompt to Ollama...")
            response = await self.llm.ainvoke(prompt)
            print("\nLLM Response:", response)

            # Validate and parse tool calls
            tool_calls = self._parse_tool_calls(response)
            if not tool_calls:
                print("\nWarning: Using default tool calls sequence")
                tool_calls = self._get_default_tool_calls()

            # Execute tool calls
            session_id = None
            for tool_call in tool_calls:
                print(f"\nExecuting: {tool_call['name']}")
                print(f"Parameters: {json.dumps(tool_call['parameters'], indent=2)}")
                
                result = await self.session.call_tool(
                    tool_call['name'],
                    tool_call['parameters']
                )
                print("Result:", result.content[0].text)
                
                # Store session ID from launch_browser result
                if tool_call['name'] == "launch_browser":
                    session_id = result.content[0].text
                    # Update session ID in remaining tool calls
                    for remaining_call in tool_calls:
                        if "session_id" in remaining_call["parameters"]:
                            remaining_call["parameters"]["session_id"] = session_id
                
                # Add delay between actions
                await asyncio.sleep(3)  # Longer delay to ensure page loads

            # Ensure browser is closed
            if session_id:
                await self.session.call_tool("close_browser", {"session_id": session_id})

            print("\nTest completed successfully!")

        except Exception as e:
            logger.error(f"Error during testing: {str(e)}", exc_info=True)
            print(f"\nError during testing: {str(e)}")

    def _parse_tool_calls(self, llm_response: str) -> List[Dict[str, Any]]:
        """Parse tool calls from LLM response"""
        try:
            # Try to find JSON array in response
            start_idx = llm_response.find('[')
            end_idx = llm_response.rfind(']')
            
            if start_idx == -1 or end_idx == -1:
                logger.warning("No JSON array found in LLM response")
                return []
                
            json_str = llm_response[start_idx:end_idx + 1]
            tool_calls = json.loads(json_str)
            
            # Validate tool calls
            if not isinstance(tool_calls, list):
                logger.warning("Tool calls is not a list")
                return []
                
            for call in tool_calls:
                if not isinstance(call, dict):
                    logger.warning("Tool call is not a dictionary")
                    return []
                if "name" not in call or "parameters" not in call:
                    logger.warning("Tool call missing required fields")
                    return []
                    
            return tool_calls
            
        except Exception as e:
            logger.warning(f"Failed to parse tool calls from response: {e}")
            return []

    def _get_default_tool_calls(self) -> List[Dict[str, Any]]:
        """Get default sequence of tool calls"""
        return [
            {
                "name": "launch_browser",
                "parameters": {"url": "https://ollama.com/library"}
            },
            {
                "name": "get_dom_structure",
                "parameters": {"session_id": "0", "max_depth": 3}
            },
            {
                "name": "extract_data",
                "parameters": {"session_id": "0", "pattern": "article headlines"}
            },
            {
                "name": "take_screenshot",
                "parameters": {"session_id": "0"}
            },
            {
                "name": "scroll_page",
                "parameters": {"session_id": "0", "direction": "down"}
            },
            {
                "name": "get_page_content",
                "parameters": {"session_id": "0"}
            },
            {
                "name": "extract_data",
                "parameters": {"session_id": "0", "pattern": "model names"}
            },
            {
                "name": "scroll_page",
                "parameters": {"session_id": "0", "direction": "up"}
            }
        ]

    async def cleanup(self):
        """Clean up resources"""
        logger.debug("Cleaning up resources")
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)
            
    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.test_ollama_models()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
