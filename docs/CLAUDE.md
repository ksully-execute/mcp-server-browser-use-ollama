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
# Interactive client
python src/client.py src/server.py

# With custom task
python src/client.py src/server.py "Navigate to Google and search for MCP"

# From task file
python src/client.py src/server.py task.txt --file

# With specific Ollama model
python src/client.py src/server.py "Your task" --model llama3.2:latest
```

### Testing
```bash
# Run pure MCP tests (recommended)
pytest tests/test_server_mcp.py -v

# Run all tests
pytest

# Run with test runner script
python tests/run_tests.py
```

## Project Structure

```
mcp-server-browser-use-ollama/
├── src/                    # Core source code
│   ├── server.py          # MCP server implementation
│   └── client.py          # Interactive client with Ollama integration
├── docs/                   # Documentation
├── tests/                  # Test suite
├── pyproject.toml         # Project configuration
└── mcp-server.json        # MCP Central registry config
```

## Architecture

The codebase implements a client-server architecture with MCP protocol:

1. **src/server.py**: MCP server that provides browser automation tools via Playwright
   - Implements 10 core tools: launch_browser, click_element, type_text, scroll_page, etc.
   - Uses pure MCP SDK for protocol implementation
   - Browser control through Playwright library

2. **Client Application**:
   - **client.py**: Interactive MCP client with Ollama integration, conversation history, and file input support

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
- Test suite includes pure MCP tests (test_server_mcp.py) and integration tests
- Browser automation tools are implemented as MCP tools in server.py
- Pure MCP SDK implementation (not FastMCP) for full protocol compliance
- Browser launches maximized (1920x1080) to minimize scrolling needs