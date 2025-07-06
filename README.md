# MCP Browser Automation with Ollama

A powerful browser automation system that enables AI agents to control web browsers through the Model Context Protocol (MCP). This implementation is specifically designed to work with Ollama local models, providing a secure and efficient way to automate browser interactions using locally-hosted AI models.

## Features

- **MCP Integration**: Full support for Model Context Protocol for structured AI-browser communication
- **Ollama Model Support**: Optimized for local AI models running through Ollama 
- **Browser Control**: Complete browser automation with Playwright (Chrome, Firefox, Safari)
- **AI-Driven Automation**: Natural language browser control via local LLMs
- **Screenshot Capabilities**: Visual feedback and debugging support
- **Session Management**: Multiple browser sessions with automatic cleanup
- **Interactive Mode**: Continuous feedback loop between AI and browser state

## Quick Start

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai) installed and running
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/Cam10001110101/mcp-server-browser-use-ollama
cd mcp-server-browser-use-ollama

# Install with uv (recommended)
uv pip install -e .
playwright install

# Start Ollama and pull a model
ollama serve  # In one terminal
ollama pull qwen3  # In another terminal
```

### Usage

The system can be used in two modes:

#### Option 1: Direct MCP Integration (with Claude Desktop)
Configure in `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "browser-use-ollama": {
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/src/server.py"]
    }
  }
}
```

#### Option 2: Ollama-Driven Automation
```bash
# Interactive automation with conversation history
python src/client.py src/server.py

# Custom task via command line
python src/client.py src/server.py "Navigate to Google and search for 'Ollama models'"

# Complex task from file
python src/client.py src/server.py task_description.txt --file

# With custom model
python src/client.py src/server.py "Your task" --model llama3.2:latest
```

## Available Tools

The MCP server provides 10 browser automation tools:

- `launch_browser(url)` - Launch browser and navigate to URL
- `click_element(session_id, x, y)` - Click at coordinates
- `click_selector(session_id, selector)` - Click element by CSS selector
- `type_text(session_id, text)` - Type text at current position
- `scroll_page(session_id, direction)` - Scroll page up/down
- `get_page_content(session_id)` - Extract page text content
- `get_dom_structure(session_id, max_depth)` - Get DOM tree
- `extract_data(session_id, pattern)` - Extract structured data
- `take_screenshot(session_id)` - Capture screenshot
- `close_browser(session_id)` - Close browser session

## Examples

### Basic Web Search
```bash
python src/client.py src/server.py "Search for 'Ollama models' on Google and summarize the top 3 results"
```

### E-commerce Analysis
```bash
python src/client.py src/server.py "Compare wireless headphones on Amazon - create a table with prices, ratings, and features"
```

### Research Workflow
```bash
python src/client.py src/server.py "Research transformer architecture improvements in 2024, visit 5 sources, and compile a summary"
```

### File-based Complex Tasks
```bash
# Create a task file
echo "Navigate to GitHub, search for MCP repositories, and analyze the top 5 results" > my_task.txt

# Run the task
python src/client.py src/server.py my_task.txt --file
```

## Environment Variables

- `OLLAMA_MODEL`: Specify Ollama model (default: `qwen3`)
- `OLLAMA_HOST`: Ollama API endpoint (default: `http://localhost:11434`)

## Testing

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/test_server.py
pytest tests/test_integration.py

```

## Project Structure

```
mcp-server-browser-use-ollama/
├── src/                    # Core source code
│   ├── server.py          # MCP server implementation
│   └── client.py          # Interactive client with full automation capabilities
├── tests/                  # Test suite
├── docs/                   # Additional documentation
├── pyproject.toml         # Project configuration
└── README.md              # This file
```

## Architecture

The system uses a client-server architecture with MCP protocol:

```
User → Client → MCP Protocol → Server → Playwright Browser
```

- **Server**: FastMCP-based server providing browser automation tools
- **Client**: Langchain-Ollama integration for natural language processing
- **Transport**: stdio-based MCP communication
- **Browser**: Playwright automation for cross-browser support

## Key Features

### Interactive Feedback Loop
The client maintains a continuous dialogue with Ollama for dynamic automation:
- Ollama receives results after each action
- Can adjust strategy based on browser state
- Maintains full conversation history for context
- Supports both command-line and file-based task input

### Advanced Capabilities
- **Conversation History**: 32k token context window for complex multi-step tasks
- **Action Parsing**: JSON and heuristic parsing of LLM responses
- **File Input**: Support for complex task descriptions from files
- **Model Selection**: Easy switching between Ollama models
- **Debug Mode**: Comprehensive logging for troubleshooting

### Flexible Model Support
- Works with any Ollama-compatible model
- Optimized for coding models (qwen3, qwen2.5-coder:7b)
- Configurable context windows and parameters
- Temperature=0 for deterministic outputs

### Robust Error Handling
- Automatic browser session cleanup
- Graceful recovery from parsing errors
- Comprehensive logging for debugging