# Browser Use MCP

A powerful browser automation and control system that enables AI agents to interact with web browsers through the Model Context Protocol (MCP). This implementation is specifically designed to work with Ollama local models, providing a secure and efficient way to automate browser interactions using locally-hosted AI models.

## Features

- **MCP Integration**: Full support for Model Context Protocol, enabling structured communication between AI models and browser automation
- **Ollama Model Support**: Optimized for local AI models running through Ollama
- **Browser Control**: Direct browser manipulation and automation with screenshot capabilities
- **DOM Management**: Advanced DOM tree building and processing
- **AI Agent System**: Sophisticated message management and service orchestration
- **Telemetry**: Built-in system monitoring and performance tracking
- **Extensible Architecture**: Modular design supporting custom actions and features

## Prerequisites

- Ollama installed and running locally
- Python 3.8 or higher
- pip package manager

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/browser-use-mcp.git
cd browser-use-mcp

# Install dependencies
pip install -r requirements.txt

# Configure Ollama (ensure Ollama is running)
ollama pull codellama # or your preferred model
```

## Quick Start

```python
from browser_use.agent import Agent
from browser_use.browser import Browser
from browser_use.mcp import MCPServer

# Initialize MCP server and Ollama model
mcp_server = MCPServer(model="codellama")

# Initialize browser and agent
browser = Browser()
agent = Agent(browser, mcp_server)

# Execute browser actions through MCP
agent.execute("Navigate to https://example.com and click the first button")
```

## Project Structure

```
browser_use/
├── agent/              # AI agent coordination
├── browser/           # Browser control and automation
├── dom/               # DOM tree management
├── controller/        # System coordination
└── telemetry/        # System monitoring
```

## Documentation

Comprehensive documentation is available in the `.context` directory:

- Project overview and goals in `.context/index.md`
- System architecture in `.context/docs/architecture.md`
- System flow diagrams in `.context/diagrams/system-flow.md`

## Using with MCP Clients

### Claude Desktop Integration

To use browser-use-mcp with Claude Desktop:

1. Add the MCP server configuration to Claude Desktop's settings (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "browser-use": {
      "command": "python",
      "args": ["-m", "browser_use.mcp_server"],
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

2. Restart Claude Desktop to load the new MCP server

3. The browser control tools will now be available to Claude through the MCP protocol:
   - `browser_action`: Control browser interactions
   - `read_dom`: Access page DOM information
   - `get_screenshot`: Capture browser state

### Other MCP Clients

For other MCP-compatible clients, configure the server using these parameters:

- Command: `python`
- Arguments: `["-m", "browser_use.mcp_server"]`
- Environment Variables:
  - `OLLAMA_HOST`: Ollama API host (default: http://localhost:11434)
  - `BROWSER_HEADLESS`: Run browser in headless mode (default: false)
  - `SCREENSHOT_DIR`: Directory for saving screenshots (default: ./screenshots)

## Examples

Check out the `examples/` directory for various use cases:

- Simple browser automation
- Custom function integration
- Multi-tab handling
- Parallel agent operations
- MCP client integration examples
- And more!

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_browser.py
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
