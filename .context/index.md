# Browser Use MCP Project Context

This document serves as the main entry point for AI tools to understand the browser-use-mcp project.

## Project Overview

This project is a browser automation and control system built on the Model Context Protocol (MCP), specifically designed to work with Ollama local models. It enables AI agents to interact with web browsers through a structured communication protocol while maintaining security and efficiency by using locally-hosted AI models. The system provides a comprehensive set of tools and APIs for browser manipulation, DOM interaction, and telemetry collection.

## MCP Integration

The project leverages the Model Context Protocol (MCP) for:
- Structured communication between AI models and browser automation
- Standardized message formats for browser control
- Efficient context sharing between components
- Secure local model execution through Ollama

## Ollama Integration

The system is specifically optimized for Ollama local models:
- Direct integration with Ollama's API
- Support for various Ollama models (CodeLlama, Llama2, etc.)
- Local execution for enhanced security and privacy
- Optimized performance for browser automation tasks

## Key Components

1. MCP Server
   - Located in `browser_use/mcp/`
   - Manages Model Context Protocol communication
   - Handles Ollama model integration
   - Coordinates context sharing

2. Browser Control
   - Located in `browser_use/browser/`
   - Handles direct browser manipulation and automation
   - Includes screenshot and click testing capabilities
   - Integrates with MCP for structured control

2. DOM Management
   - Located in `browser_use/dom/`
   - Manages DOM tree building and processing
   - Includes history tree processing functionality

3. Agent System
   - Located in `browser_use/agent/`
   - Handles AI agent interactions and message management
   - Includes service layer and view components

4. Controller Layer
   - Located in `browser_use/controller/`
   - Manages system registry and service coordination
   - Provides high-level control interfaces

5. Telemetry
   - Located in `browser_use/telemetry/`
   - Handles system monitoring and data collection

## Documentation Structure

- `/docs` - Contains detailed documentation about system components
- `/diagrams` - Contains architectural and flow diagrams
- This index file serves as the main entry point

## Project Goals

1. Provide robust browser automation capabilities
2. Enable AI agents to interact with web interfaces
3. Support multiple browser instances and parallel operations
4. Maintain comprehensive testing and telemetry
