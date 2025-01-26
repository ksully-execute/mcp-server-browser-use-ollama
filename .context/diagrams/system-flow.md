# System Flow Diagrams

## Main System Flow

```mermaid
graph TD
    A[AI Agent] --> M[MCP Server]
    M --> O[Ollama Model]
    M --> B[Controller]
    B --> C[Browser Module]
    B --> D[DOM Module]
    
    C --> E[Browser Instance]
    D --> F[DOM Tree]
    
    G[Telemetry] --> C
    G --> D
    
    E --> H[Screenshots]
    E --> I[Interactions]
    F --> J[Element Selection]
    F --> K[History Tracking]
    
    H --> B
    I --> B
    J --> B
    K --> B
    
    B --> A
```

## Component Communication

```mermaid
sequenceDiagram
    participant Agent
    participant MCP
    participant Ollama
    participant Controller
    participant Browser
    participant DOM
    participant Telemetry

    Agent->>MCP: Request Action
    MCP->>Ollama: Process Request
    Ollama->>MCP: Return Instructions
    MCP->>Controller: Execute Instructions
    Controller->>Browser: Execute Browser Action
    Browser->>DOM: Update DOM State
    DOM->>Controller: Return DOM Info
    Controller->>Telemetry: Log Operation
    Telemetry->>Controller: Confirm Logging
    Controller->>Agent: Return Result
```

## Module Architecture

```mermaid
graph LR
    subgraph MCP Layer
        M[MCP Server]
        O[Ollama Integration]
    end
    
    subgraph Agent Layer
        A[Agent Service]
        B[Message Manager]
    end
    
    subgraph Control Layer
        C[Controller Service]
        D[Registry Service]
    end
    
    subgraph Browser Layer
        E[Browser Service]
        F[Context Manager]
    end
    
    subgraph DOM Layer
        G[DOM Service]
        H[History Processor]
    end
    
    M --> O
    A --> M
    B --> M
    M --> C
    C --> D
    D --> E
    D --> G
    E --> F
    G --> H
