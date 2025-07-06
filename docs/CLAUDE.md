# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an MCP (Model Context Protocol) server implementation for browser automation with Ollama support. The project enables AI-driven browser control through either direct MCP integration or via local Ollama models.

## Common Commands

### Installation and Setup
```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate
uv pip install -e .
playwright install

# Install development dependencies
uv pip install -e ".[dev]"

# Alternative: Direct installation without manual venv
uv pip install -e .
playwright install
```

### Running the Application
```bash
# Run with default Ollama model (qwen2.5-coder:7b)
python src/client.py src/server.py

# Run with specific Ollama model
OLLAMA_MODEL=llama3.2:latest python src/client.py src/server.py

# Run enhanced client with conversation history
python src/enhanced_client.py src/server.py

# Run complex task automation
python src/run_complex_task.py src/server.py
```

### Testing
```bash
# Run all tests
cd tests && ./run_all_tests.sh

# Run enhanced tests only
cd tests && ./run_enhanced_test.sh
```

## Project Structure

```
mcp-server-browser-use-ollama/
├── src/                    # Core source code
│   ├── server.py          # MCP server implementation
│   ├── client.py          # Basic MCP client
│   ├── enhanced_client.py # Advanced client
│   └── run_complex_task.py # Complex task runner
├── docs/                   # Documentation
├── examples/               # Example prompts
├── tests/                  # Test scripts
├── pyproject.toml         # Project configuration
└── requirements.txt       # Dependencies
```

## Architecture

The codebase implements a client-server architecture with MCP protocol:

1. **src/server.py**: MCP server that provides browser automation tools via Playwright
   - Implements 10 core tools: launch_browser, click_element, type_text, scroll_page, etc.
   - Uses FastMCP framework for MCP protocol implementation
   - Browser control through Playwright library

2. **Client Applications** (in src/):
   - **client.py**: Basic MCP client with Ollama integration
   - **enhanced_client.py**: Advanced client with conversation history and caching
   - **run_complex_task.py**: Complex task automation runner

3. **Integration Flow**:
   ```
   User → Client (Ollama LLM) → MCP Protocol → Server → Playwright Browser
   ```

## Key Implementation Details

- **MCP Transport**: Uses stdio transport for client-server communication
- **Browser Control**: Playwright handles all browser automation (supports Chrome, Firefox, Safari)
- **AI Integration**: Langchain-Ollama for local LLM support
- **Error Handling**: Browser sessions are automatically cleaned up on errors
- **Screenshot Support**: Automatic screenshot capture for debugging

## Environment Variables

- `OLLAMA_MODEL`: Specify the Ollama model to use (default: qwen2.5-coder:7b)
- `OLLAMA_HOST`: Ollama API endpoint (default: http://localhost:11434)
- `BROWSER_HEADLESS`: Run browser in headless mode
- `SCREENSHOT_DIR`: Directory for saving screenshots

## Development Notes

- The project uses `pyproject.toml` for configuration (PEP 518 compliant)
- No traditional unit tests - testing is done through integration test scripts
- Browser automation tools are implemented as MCP tools in server.py
- Client applications demonstrate different usage patterns and capabilities