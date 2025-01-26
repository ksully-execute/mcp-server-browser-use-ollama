# System Architecture

## Overview

The browser-use-mcp system is built with a modular architecture centered around the Model Context Protocol (MCP) and Ollama integration. The system separates concerns into distinct components while maintaining clear communication channels through MCP, with a specific focus on local model execution using Ollama.

## MCP Architecture

The Model Context Protocol serves as the foundation for system communication:
- **Protocol Layer**: Implements MCP specifications for structured messaging
- **Context Management**: Handles sharing of browser state and context
- **Model Integration**: Direct integration with Ollama's local models
- **Security**: Ensures secure communication within the local environment

## Ollama Integration

The system's Ollama integration is structured around:
- **Model Management**: Handles Ollama model loading and configuration
- **API Integration**: Direct communication with Ollama's API
- **Context Optimization**: Efficient context sharing with local models
- **Performance Tuning**: Optimized for browser automation tasks

## Core Components

### MCP Server Module
- **Purpose**: MCP protocol implementation and Ollama integration
- **Key Features**:
  - MCP message handling
  - Ollama model management
  - Context synchronization
  - Protocol validation
- **Location**: `browser_use/mcp/`

### Browser Module
- **Purpose**: Direct browser control and automation
- **Key Features**:
  - Browser instance management
  - Screenshot capabilities
  - Click and interaction handling
  - Context management
- **Location**: `browser_use/browser/`

### DOM Module
- **Purpose**: DOM tree management and processing
- **Key Features**:
  - DOM tree construction
  - History tracking
  - Element selection and traversal
- **Location**: `browser_use/dom/`

### Agent Module
- **Purpose**: AI agent coordination
- **Key Features**:
  - Message management
  - Service orchestration
  - View handling
- **Location**: `browser_use/agent/`

### Controller Module
- **Purpose**: System coordination and registry
- **Key Features**:
  - Component registry
  - Service management
  - View coordination
- **Location**: `browser_use/controller/`

### Telemetry Module
- **Purpose**: System monitoring
- **Key Features**:
  - Performance tracking
  - Usage analytics
  - Error monitoring
- **Location**: `browser_use/telemetry/`

## Communication Flow

1. Agent requests flow through the Controller
2. Controller coordinates with Browser and DOM modules
3. Browser/DOM modules execute operations
4. Telemetry tracks system performance
5. Results flow back through Controller to Agent

## Testing Strategy

The system employs comprehensive testing:
- Unit tests for individual components
- Integration tests for module interaction
- Screenshot tests for visual verification
- Click tests for interaction validation

## MCP Client Integration

The system is designed to work with any MCP-compatible client:

### Client Communication
- **Protocol Endpoints**:
  - `browser_action`: Execute browser operations
  - `read_dom`: Retrieve DOM information
  - `get_screenshot`: Capture visual state

### Configuration Interface
- **Server Settings**:
  - Command: Python module execution
  - Arguments: MCP server module path
  - Environment configuration
  - Security settings

### Client Examples
- **Claude Desktop**:
  - Direct integration through config
  - Tool-based interaction
  - Context sharing
- **Other MCP Clients**:
  - Standard protocol support
  - Environment variable configuration
  - Extensible tool interface

## Extension Points

The system is designed for extensibility:
- Custom browser actions
- Additional agent capabilities
- New DOM processing features
- Enhanced telemetry metrics
- Client-specific integrations
