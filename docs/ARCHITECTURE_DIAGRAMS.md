# ATOLL Architecture Diagrams

This document contains visual representations of the ATOLL system architecture, components, and workflows.

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Hierarchical Agent Structure](#hierarchical-agent-structure)
3. [Deployment Server Architecture](#deployment-server-architecture)
4. [REST API Flow](#rest-api-flow)
5. [Agent Lifecycle](#agent-lifecycle)
6. [Remote Deployment Process](#remote-deployment-process)

---

## System Architecture

High-level overview of ATOLL components and their interactions:

```mermaid
graph TB
    subgraph "User Interface"
        UI[Terminal UI]
        CLI[CLI Tools]
    end
    
    subgraph "ATOLL Core"
        APP[Application Layer]
        ROOT[Root Agent]
        BASE[ATOLLAgent Base Class]
        
        APP --> ROOT
        ROOT -.inherits.-> BASE
    end
    
    subgraph "AI Integration"
        LLM[Ollama LLM]
        REASON[Reasoning Engine]
        MEMORY[Conversation Memory]
        
        ROOT --> LLM
        ROOT --> REASON
        ROOT --> MEMORY
    end
    
    subgraph "MCP Integration"
        MCP_MGR[MCP Server Manager]
        REGISTRY[Tool Registry]
        
        subgraph "MCP Clients"
            STDIO[stdio Client]
            HTTP[HTTP Client]
            SSE[SSE Client]
        end
        
        MCP_MGR --> STDIO
        MCP_MGR --> HTTP
        MCP_MGR --> SSE
        MCP_MGR --> REGISTRY
    end
    
    subgraph "Deployment System"
        DEPLOY_SRV[Deployment Server]
        DEPLOY_API[REST API]
        PORT_MGR[Port Manager]
        
        DEPLOY_SRV --> DEPLOY_API
        DEPLOY_SRV --> PORT_MGR
    end
    
    UI --> APP
    CLI --> DEPLOY_API
    ROOT --> MCP_MGR
    APP --> DEPLOY_SRV
    
    style ROOT fill:#4CAF50
    style BASE fill:#8BC34A
    style DEPLOY_API fill:#2196F3
```

---

## Hierarchical Agent Structure

ATOLL v2.0's hierarchical agent system showing parent-child relationships:

```mermaid
graph TD
    subgraph "Agent Hierarchy"
        ROOT[Root Agent<br/>ATOLLAgent]
        
        subgraph "Specialized Agents"
            CODE[Code Analysis Agent<br/>ATOLLAgent]
            DATA[Data Processing Agent<br/>ATOLLAgent]
            SEC[Security Agent<br/>ATOLLAgent]
        end
        
        subgraph "Sub-Agents"
            GHIDRA[Ghidra Agent]
            SCAN[Vulnerability Scanner]
        end
        
        ROOT --> CODE
        ROOT --> DATA
        ROOT --> SEC
        
        CODE --> GHIDRA
        SEC --> SCAN
    end
    
    subgraph "Agent Components"
        LLM_CONFIG[LLM Config]
        MCP_SERVERS[MCP Servers]
        CONV_MEM[Conversation Memory]
        TOOLS[Tools Registry]
        
        CODE -.owns.-> LLM_CONFIG
        CODE -.owns.-> MCP_SERVERS
        CODE -.owns.-> CONV_MEM
        CODE -.owns.-> TOOLS
    end
    
    USER[User] --> ROOT
    
    style ROOT fill:#FF9800
    style CODE fill:#4CAF50
    style DATA fill:#2196F3
    style SEC fill:#F44336
```

**Key Features:**
- Each agent inherits from `ATOLLAgent` base class
- Agents can have independent LLM configurations
- Agents maintain separate conversation memory
- Tools are scoped to agent context

---

## Deployment Server Architecture

Internal architecture of the deployment server:

```mermaid
graph LR
    subgraph "Deployment Server"
        MGR[Deployment Manager]
        
        subgraph "Agent Management"
            DISCOVER[Agent Discovery]
            LIFECYCLE[Lifecycle Manager]
            MONITOR[Health Monitor]
        end
        
        subgraph "Resource Management"
            PORT[Port Manager]
            VENV[Virtual Env Manager]
            PROCESS[Process Manager]
        end
        
        subgraph "Storage"
            CHECKSUM[Checksum DB<br/>checksums.json]
            METADATA[Agent Metadata]
        end
        
        MGR --> DISCOVER
        MGR --> LIFECYCLE
        MGR --> MONITOR
        
        LIFECYCLE --> PORT
        LIFECYCLE --> VENV
        LIFECYCLE --> PROCESS
        
        MGR --> CHECKSUM
        MGR --> METADATA
    end
    
    subgraph "REST API"
        FASTAPI[FastAPI Server]
        AUTH[Authentication<br/>API Key]
        ENDPOINTS[Endpoints]
        
        FASTAPI --> AUTH
        FASTAPI --> ENDPOINTS
    end
    
    subgraph "Agent Instances"
        A1[Agent 1<br/>Port 8100]
        A2[Agent 2<br/>Port 8101]
        A3[Agent 3<br/>Port 8102]
    end
    
    CLIENT[API Client] --> FASTAPI
    ENDPOINTS --> MGR
    
    PROCESS --> A1
    PROCESS --> A2
    PROCESS --> A3
    
    style MGR fill:#FF9800
    style FASTAPI fill:#2196F3
    style AUTH fill:#F44336
```

---

## REST API Flow

Request flow through the REST API with authentication:

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Auth
    participant DeploymentServer
    participant Agent
    
    Client->>FastAPI: POST /deploy (ZIP file)
    FastAPI->>Auth: Verify API Key
    
    alt Valid API Key
        Auth-->>FastAPI: Authorized
        FastAPI->>DeploymentServer: Process deployment
        
        DeploymentServer->>DeploymentServer: Calculate MD5 checksum
        DeploymentServer->>DeploymentServer: Check if exists
        
        alt New Agent
            DeploymentServer->>DeploymentServer: Extract ZIP
            DeploymentServer->>DeploymentServer: Create venv
            DeploymentServer->>DeploymentServer: Install dependencies
            DeploymentServer->>Agent: Initialize agent
            Agent-->>DeploymentServer: Ready
            DeploymentServer-->>FastAPI: Success
            FastAPI-->>Client: 200 OK + agent info
        else Agent Exists
            DeploymentServer-->>FastAPI: Already deployed
            FastAPI-->>Client: 200 OK (cached)
        end
        
    else Invalid API Key
        Auth-->>FastAPI: Unauthorized
        FastAPI-->>Client: 401 Unauthorized
    end
```

---

## Agent Lifecycle

State transitions and operations during agent lifecycle:

```mermaid
stateDiagram-v2
    [*] --> Discovered: Agent found in directory
    
    Discovered --> Deploying: Deploy command
    Deploying --> Stopped: Deployment complete
    Deploying --> Failed: Deployment error
    
    Stopped --> Starting: Start command
    Starting --> Running: Process started
    Starting --> Failed: Start error
    
    Running --> Stopping: Stop command
    Running --> Failed: Process crashed
    Running --> Restarting: Restart command
    
    Restarting --> Starting: Stop complete
    
    Stopping --> Stopped: Process terminated
    
    Failed --> Starting: Retry (if enabled)
    Failed --> Stopped: Manual intervention
    
    Stopped --> [*]: Delete command
    Failed --> [*]: Delete command
    
    note right of Running
        Health checks active
        Port allocated
        Logs captured
    end note
    
    note right of Failed
        Diagnostics generated
        Error logs captured
        Restart count tracked
    end note
```

**State Descriptions:**

- **Discovered**: Agent configuration found, not yet deployed
- **Deploying**: Creating venv, installing dependencies
- **Stopped**: Agent deployed but not running
- **Starting**: Process being launched
- **Running**: Agent active and serving requests
- **Stopping**: Graceful shutdown in progress
- **Restarting**: Stop + Start sequence
- **Failed**: Error state with diagnostics available

---

## Remote Deployment Process

End-to-end flow for deploying an agent to a remote server:

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Local as Local Machine
    participant API as Deployment API<br/>(Remote)
    participant Server as Deployment Server<br/>(Remote)
    participant Agent as Agent Instance
    
    Dev->>Local: Create agent.toml
    Dev->>Local: Write main.py
    Dev->>Local: Create requirements.txt
    Dev->>Local: Package as ZIP
    
    Local->>API: POST /deploy<br/>+ API Key<br/>+ ZIP file
    
    API->>API: Verify authentication
    API->>Server: Forward deployment request
    
    Server->>Server: Calculate MD5 checksum
    
    alt New Package
        Server->>Server: Extract ZIP to temp directory
        Server->>Server: Validate agent.toml
        Server->>Server: Create virtual environment
        Server->>Server: Install requirements.txt
        Server->>Server: Allocate port (OS binding)
        Server->>Server: Save checksum
        Server->>Agent: Initialize agent process
        
        Agent-->>Server: Process started (PID)
        Server-->>API: Deployment success
        API-->>Local: 200 OK + agent info
        Local-->>Dev: Agent deployed at port XXXX
        
    else Package Exists (same checksum)
        Server-->>API: Already deployed
        API-->>Local: 200 OK (cached)
        Local-->>Dev: Agent already exists (skip)
    end
    
    Dev->>Local: Start agent
    Local->>API: POST /agents/{name}/start
    API->>Server: Start request
    Server->>Agent: Execute main.py
    Agent-->>Server: Running on port XXXX
    Server-->>API: Started
    API-->>Local: 200 OK + port info
    Local-->>Dev: Agent running at http://remote:XXXX
```

---

## Component Interaction Matrix

| Component | Interacts With | Purpose |
|-----------|----------------|---------|
| **Terminal UI** | Application Layer | User input/output |
| **Application** | Root Agent, Deployment Server | Orchestration |
| **Root Agent** | LLM, MCP Manager, Memory | User interaction |
| **MCP Manager** | MCP Clients, Tool Registry | Tool execution |
| **Deployment Server** | REST API, Port Manager, Agents | Agent lifecycle |
| **REST API** | Authentication, Deployment Server | Remote access |
| **Port Manager** | OS Sockets, Registry | Port allocation |
| **Agent Instance** | Virtual Env, Process Manager | Isolated execution |

---

## Data Flow Diagrams

### Tool Execution Flow

```mermaid
flowchart LR
    USER[User Input] --> ROOT[Root Agent]
    ROOT --> REASON[Reasoning Engine]
    REASON --> TOOL_SEL[Tool Selection]
    TOOL_SEL --> MCP[MCP Manager]
    MCP --> CLIENT[MCP Client]
    CLIENT --> EXTERNAL[External Tool]
    EXTERNAL --> RESULT[Result]
    RESULT --> ROOT
    ROOT --> FORMAT[Format Response]
    FORMAT --> DISPLAY[Display to User]
    
    style USER fill:#90CAF9
    style ROOT fill:#4CAF50
    style REASON fill:#FFF59D
    style EXTERNAL fill:#FF9800
```

### Deployment Data Flow

```mermaid
flowchart TD
    ZIP[Agent ZIP Package] --> API[REST API]
    API --> AUTH{Authentication}
    
    AUTH -->|Valid| CHECKSUM[Calculate MD5]
    AUTH -->|Invalid| REJECT[401 Unauthorized]
    
    CHECKSUM --> CHECK{Exists?}
    CHECK -->|No| EXTRACT[Extract Files]
    CHECK -->|Yes| CACHED[Return Cached Info]
    
    EXTRACT --> VALIDATE[Validate agent.toml]
    VALIDATE --> VENV[Create Virtual Env]
    VENV --> DEPS[Install Dependencies]
    DEPS --> PORT[Allocate Port]
    PORT --> SAVE[Save Metadata]
    SAVE --> SUCCESS[200 OK]
    
    style ZIP fill:#90CAF9
    style AUTH fill:#F44336
    style SUCCESS fill:#4CAF50
```

---

## Technology Stack

```mermaid
graph TB
    subgraph "Frontend"
        CLI[Click CLI]
        TUI[Rich Terminal UI]
    end
    
    subgraph "Application Layer"
        LANG[LangChain]
        FAST[FastAPI]
        PYD[Pydantic]
    end
    
    subgraph "LLM Layer"
        OLLAMA[Ollama]
        MODELS[Local Models]
    end
    
    subgraph "Tools Layer"
        MCP[MCP Protocol]
        TOOLS[External Tools]
    end
    
    subgraph "Infrastructure"
        VENV[Python venv]
        PROC[subprocess]
        SOCK[socket]
    end
    
    CLI --> FAST
    TUI --> LANG
    
    LANG --> OLLAMA
    OLLAMA --> MODELS
    
    LANG --> MCP
    MCP --> TOOLS
    
    FAST --> PROC
    PROC --> VENV
    FAST --> SOCK
```

---

## Deployment Patterns

### Pattern 1: Local Development

```mermaid
graph LR
    DEV[Developer] --> ATOLL[ATOLL CLI]
    ATOLL --> LOCAL_LLM[Local Ollama]
    ATOLL --> LOCAL_MCP[Local MCP Servers]
    
    style DEV fill:#90CAF9
    style ATOLL fill:#4CAF50
```

### Pattern 2: Remote Deployment

```mermaid
graph LR
    DEV[Developer] --> CLI[atoll-deploy CLI]
    CLI --> API[Remote API]
    API --> SERVER[Deployment Server]
    SERVER --> AGENT1[Agent 1]
    SERVER --> AGENT2[Agent 2]
    SERVER --> AGENT3[Agent 3]
    
    style DEV fill:#90CAF9
    style API fill:#2196F3
    style SERVER fill:#FF9800
```

### Pattern 3: Multi-Server Setup

```mermaid
graph TB
    ROOT[Root Agent] --> BALANCER[Load Balancer]
    
    BALANCER --> SERVER1[Server 1]
    BALANCER --> SERVER2[Server 2]
    BALANCER --> SERVER3[Server 3]
    
    SERVER1 --> A1[Agents]
    SERVER2 --> A2[Agents]
    SERVER3 --> A3[Agents]
    
    style ROOT fill:#4CAF50
    style BALANCER fill:#FF9800
```

---

## Notes

- All diagrams are rendered using Mermaid syntax
- For interactive viewing, use a Mermaid-compatible viewer
- GitHub automatically renders these diagrams in Markdown
- VS Code supports Mermaid with appropriate extensions

---

**Tip:** To edit these diagrams, use the [Mermaid Live Editor](https://mermaid.live/) for instant preview.
