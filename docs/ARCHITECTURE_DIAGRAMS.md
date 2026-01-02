# ATOLL Architecture Diagrams

This document contains visual representations of ATOLL's architecture using Mermaid diagrams.

## Overall System Architecture

```mermaid
graph TB
    subgraph "User Interface"
        UI[Terminal UI<br/>Prompt/Command Mode]
    end
    
    subgraph "Application Layer"
        App[Application<br/>main.py]
        ConfigMgr[Config Manager]
    end
    
    subgraph "Agent Layer"
        RootAgent[Root Agent<br/>User Interaction]
        AgentMgr[Agent Manager<br/>Lifecycle Control]
        Reasoning[Reasoning Engine<br/>Rule-based Analysis]
    end
    
    subgraph "LLM Integration"
        Ollama[Ollama LLM<br/>Local Model]
    end
    
    subgraph "MCP Integration"
        MCPMgr[MCP Server Manager]
        ToolRegistry[Tool Registry]
        
        subgraph "MCP Clients"
            StdioClient[Stdio Client]
            HTTPClient[HTTP Client]
            SSEClient[SSE Client]
        end
    end
    
    subgraph "Deployment Server"
        DeployAPI[REST API<br/>FastAPI]
        DeployServer[Process Manager]
        Storage[(Persistent<br/>Storage)]
        Auth[Authentication]
    end
    
    UI --> App
    App --> RootAgent
    App --> ConfigMgr
    RootAgent --> Reasoning
    RootAgent --> Ollama
    RootAgent --> MCPMgr
    AgentMgr --> DeployServer
    
    MCPMgr --> ToolRegistry
    MCPMgr --> StdioClient
    MCPMgr --> HTTPClient
    MCPMgr --> SSEClient
    
    DeployAPI --> Auth
    DeployAPI --> DeployServer
    DeployServer --> Storage
    
    style UI fill:#e1f5ff
    style Ollama fill:#fff4e1
    style DeployAPI fill:#e8f5e9
    style Storage fill:#f3e5f5
```

## Deployment Server Architecture

```mermaid
graph LR
    subgraph "External Clients"
        CLI[CLI Client]
        Web[Web Client]
        CI[CI/CD Pipeline]
    end
    
    subgraph "Deployment Server :8080"
        API[FastAPI Server]
        Auth[Authentication<br/>Middleware]
        
        subgraph "Core Services"
            PM[Process Manager]
            PortMgr[Port Manager]
            VenvMgr[Venv Manager]
        end
        
        Storage[(Agent Storage<br/>JSON DB)]
        Checksums[(Checksums<br/>MD5 Hashes)]
    end
    
    subgraph "Agent Instances"
        Agent1[Agent 1:8100<br/>FastAPI]
        Agent2[Agent 2:8101<br/>FastAPI]
        Agent3[Agent N:810x<br/>FastAPI]
    end
    
    CLI --> API
    Web --> API
    CI --> API
    
    API --> Auth
    Auth --> PM
    PM --> PortMgr
    PM --> VenvMgr
    PM --> Storage
    PM --> Checksums
    
    PM -.manages.-> Agent1
    PM -.manages.-> Agent2
    PM -.manages.-> Agent3
    
    style API fill:#e8f5e9
    style Auth fill:#ffebee
    style Storage fill:#f3e5f5
    style Agent1 fill:#e3f2fd
    style Agent2 fill:#e3f2fd
    style Agent3 fill:#e3f2fd
```

## Agent Deployment Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Storage
    participant Venv
    participant Agent
    
    Client->>API: POST /agents/deploy<br/>(agent.zip)
    API->>Storage: Check checksum exists
    
    alt Checksum exists
        Storage-->>API: Package already deployed
        API-->>Client: 409 Conflict
    else New package
        API->>API: Extract ZIP
        API->>API: Validate structure<br/>(agent.toml, main.py, requirements.txt)
        API->>Storage: Save agent record
        API->>Venv: Create virtual environment
        Venv->>Venv: Install dependencies
        API->>Storage: Update checksum
        API->>Agent: Deploy agent files
        API-->>Client: 201 Created
    end
    
    Client->>API: POST /agents/{name}/start
    API->>Storage: Get agent record
    API->>Venv: Get Python path
    API->>Agent: Start process
    Agent-->>API: PID
    API->>Storage: Update status=running
    API-->>Client: 200 OK
```

## MCP Tool Discovery and Execution

```mermaid
sequenceDiagram
    participant User
    participant RootAgent
    participant Reasoning
    participant MCPMgr as MCP Manager
    participant ToolReg as Tool Registry
    participant Server as MCP Server
    
    User->>RootAgent: Submit prompt
    RootAgent->>Reasoning: Analyze request
    Reasoning->>Reasoning: Pattern matching<br/>Context analysis
    Reasoning-->>RootAgent: Suggested tools
    
    RootAgent->>MCPMgr: Request tool execution
    MCPMgr->>ToolReg: Find tool
    ToolReg-->>MCPMgr: Tool definition
    
    MCPMgr->>Server: Execute tool<br/>(JSON-RPC)
    Server-->>MCPMgr: Result
    
    MCPMgr-->>RootAgent: Formatted result
    RootAgent-->>User: Display response
```

## Hierarchical Agent Pattern (Future v2.0)

```mermaid
graph TB
    subgraph "Root Level"
        Root[Root Agent<br/>Coordinator]
    end
    
    subgraph "Specialized Agents"
        Code[Code Agent<br/>Analysis & Review]
        Data[Data Agent<br/>Processing & ETL]
        Security[Security Agent<br/>Vulnerability Scan]
    end
    
    subgraph "Tool-Specific Agents"
        Ghidra[Ghidra Agent<br/>Binary Analysis]
        DB[Database Agent<br/>Query & Migration]
        API[API Agent<br/>External Services]
    end
    
    Root --> Code
    Root --> Data
    Root --> Security
    
    Code --> Ghidra
    Data --> DB
    Security --> API
    
    style Root fill:#ffebee
    style Code fill:#e8f5e9
    style Data fill:#e8f5e9
    style Security fill:#e8f5e9
    style Ghidra fill:#e3f2fd
    style DB fill:#e3f2fd
    style API fill:#e3f2fd
```

## Port Allocation Strategy

```mermaid
graph LR
    subgraph "Port Manager"
        PM[Port Manager<br/>Dynamic Allocation]
        Registry[(Port Registry<br/>Persistent)]
    end
    
    subgraph "Port Ranges"
        Management["Management API<br/>8080 (auto)"]
        Agents["Agent Servers<br/>8100-8199"]
        Reserved["Reserved<br/>8200+"]
    end
    
    subgraph "Allocation Process"
        Request[Request Port]
        Check{Port Available?}
        Bind[Bind to Port 0]
        OSAssign[OS Assigns Free Port]
        Store[Store in Registry]
    end
    
    PM --> Registry
    PM --> Management
    PM --> Agents
    PM --> Reserved
    
    Request --> Check
    Check -->|No| Bind
    Check -->|Yes| Store
    Bind --> OSAssign
    OSAssign --> Store
    
    style PM fill:#e8f5e9
    style Registry fill:#f3e5f5
    style Management fill:#ffebee
```

## Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth
    participant Handler
    
    alt API Key Authentication
        Client->>API: Request with X-API-Key header
        API->>Auth: Verify API key
        Auth->>Auth: Compare with env var
        Auth-->>API: Authenticated
        API->>Handler: Process request
        Handler-->>Client: Response
    else Bearer Token Authentication
        Client->>API: Request with Authorization: Bearer
        API->>Auth: Verify bearer token
        Auth->>Auth: Compare with env var
        Auth-->>API: Authenticated
        API->>Handler: Process request
        Handler-->>Client: Response
    else No Authentication
        Client->>API: Request without credentials
        API->>Auth: Check if auth enabled
        Auth-->>API: Auth disabled
        API->>Handler: Process request
        Handler-->>Client: Response
    else Invalid Credentials
        Client->>API: Request with invalid credentials
        API->>Auth: Verify credentials
        Auth-->>API: Invalid
        API-->>Client: 401 Unauthorized
    end
```

## CI/CD Pipeline

```mermaid
graph LR
    subgraph "Trigger"
        Push[Push to main/develop]
        PR[Pull Request]
        Tag[Version Tag v*.*.*]
    end
    
    subgraph "CI Jobs"
        Lint[Lint & Type Check<br/>ruff, mypy]
        Test[Test Matrix<br/>Ubuntu/Windows<br/>Python 3.9/3.11/3.12]
        Coverage[Coverage Check<br/>≥90% required]
    end
    
    subgraph "Build Jobs"
        BuildLinux[Build Package<br/>Ubuntu]
        BuildWin[Build Package<br/>Windows]
        Artifacts[Upload Artifacts]
    end
    
    subgraph "Release Jobs"
        GHRelease[Create GitHub Release]
        PyPI[Publish to PyPI]
    end
    
    Push --> Lint
    PR --> Lint
    Lint --> Test
    Test --> Coverage
    Coverage --> BuildLinux
    Coverage --> BuildWin
    BuildLinux --> Artifacts
    BuildWin --> Artifacts
    
    Tag --> GHRelease
    GHRelease --> PyPI
    
    style Lint fill:#e8f5e9
    style Test fill:#e3f2fd
    style Coverage fill:#ffebee
    style GHRelease fill:#f3e5f5
```

## Data Flow: Agent Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Discovered: Package uploaded
    Discovered --> Deploying: Deploy command
    Deploying --> Deployed: Venv created,<br/>dependencies installed
    Deployed --> Starting: Start command
    Starting --> Running: Process started
    Running --> Stopping: Stop command
    Running --> Failed: Process crashed
    Stopping --> Stopped: Process terminated
    Stopped --> Starting: Restart command
    Failed --> Starting: Restart command
    Deployed --> [*]: Delete command
    
    note right of Discovered
        Metadata saved,
        checksum stored
    end note
    
    note right of Running
        PID & port tracked,
        health checked
    end note
    
    note right of Failed
        Diagnostics generated,
        logs captured
    end note
```

## Configuration Management

```mermaid
graph TB
    subgraph "Config Sources"
        Env[Environment Variables<br/>ATOLL_API_KEY, etc.]
        Files[Config Files<br/>~/.ollama_server/*.json]
        Defaults[Default Values<br/>Hardcoded]
    end
    
    subgraph "Config Manager"
        Loader[Config Loader]
        Validator[Pydantic Validator]
        Cache[Runtime Cache]
    end
    
    subgraph "Config Models"
        Ollama[OllamaConfig<br/>base_url, port, model]
        MCP[MCPConfig<br/>servers, transports]
        Deploy[DeploymentConfig<br/>agents_dir, ports]
        Auth[AuthConfig<br/>enabled, api_key]
    end
    
    Env --> Loader
    Files --> Loader
    Defaults --> Loader
    
    Loader --> Validator
    Validator --> Cache
    
    Cache --> Ollama
    Cache --> MCP
    Cache --> Deploy
    Cache --> Auth
    
    style Loader fill:#e8f5e9
    style Validator fill:#ffebee
    style Cache fill:#f3e5f5
```

---

## Diagram Rendering

These diagrams use [Mermaid](https://mermaid.js.org/) syntax and can be viewed:

1. **GitHub**: Renders automatically in markdown files
2. **VS Code**: Install "Markdown Preview Mermaid Support" extension
3. **Mermaid Live Editor**: https://mermaid.live/
4. **Command Line**: Use `mmdc` CLI tool

### Export as Images

```bash
# Install mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Export diagrams
mmdc -i docs/ARCHITECTURE_DIAGRAMS.md -o docs/architecture.png
```

---

**Last Updated:** January 2025  
**Version:** 2.0.0
