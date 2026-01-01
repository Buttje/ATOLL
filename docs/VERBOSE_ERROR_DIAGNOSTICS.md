# ATOLL v2.0 - Enhanced Error Diagnostics

## Overview

ATOLL v2.0 introduces comprehensive error diagnostics for failed agent startups, providing verbose error output to help users quickly identify and fix configuration issues.

## Features

### 1. Comprehensive Error Capture

When an agent fails to start, the system now captures:

- **Full STDERR Output**: Complete error messages and tracebacks
- **Full STDOUT Output**: All console output from the agent process
- **Exit Code**: Process exit code for debugging
- **Automatic Diagnostics**: AI-powered analysis of common failure scenarios

### 2. Intelligent Pattern Recognition

The diagnostics system automatically detects and explains common issues:

#### Python Version Compatibility
```
⚠️  WARNING: Python 3.14+ detected
   LangChain's Pydantic V1 compatibility may cause issues
   RECOMMENDED: Use Python 3.11 or 3.13
```

#### Missing Dependencies
```
💡 LIKELY CAUSE: Missing Python dependencies
   FIX: Install dependencies in the agent's virtual environment:
   .venv\Scripts\pip.exe install -r requirements.txt
```

#### Port Conflicts
```
💡 LIKELY CAUSE: Port 8100 already in use
   FIX: Stop other services using that port, or
   change 'base_port' in deployment server config
```

#### Permission Errors
```
💡 LIKELY CAUSE: Permission/access error
   FIX: Check file permissions and try running with appropriate privileges
```

#### Connection Issues
```
💡 LIKELY CAUSE: Cannot connect to required service
   FIX: Ensure Ollama, Ghidra, or other required services are running
```

### 3. Configuration Analysis

The system examines your agent configuration and reports:

- Python version requirements from agent.toml
- Required dependencies and packages
- File structure verification (main.py, requirements.txt, .venv)
- Configuration parsing errors

### 4. Actionable Troubleshooting Steps

Every error includes step-by-step guidance:

```
📋 TROUBLESHOOTING STEPS:
   1. Check the STDERR and STDOUT logs above for specific errors
   2. Verify all dependencies are installed in the virtual environment
   3. Test the agent configuration with: atoll --agent <config_path> --test
   4. Check system logs for more details
   5. Review agent documentation: <agent_path>/README.md
```

## Example: GhidraAgent Python 3.14 Issue

### Before v2.0
```
Agent Status: GhidraAgentStatus: failed
Health: unknown
PID: 14956
Port: 8100
Error: C:\...\deprecation.py:26: UserWarning: Core Pydantic V1...
```
*(truncated, unhelpful)*

### After v2.0
```
Agent Status: GhidraAgent
Status: failed
Health: unknown
PID: 14956
Port: 8100
URL: http://localhost:8100
Started: 2026-01-01T20:25:31.268856
Restarts: 0

===== ERROR DETAILS =====

STDERR:
C:\Users\user\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\
langchain_core\_api\deprecation.py:26: UserWarning: Core Pydantic V1
functionality isn't compatible with Python 3.14 or greater.
  from pydantic.v1.fields import FieldInfo as FieldInfoV1
Traceback (most recent call last):
  File "main.py", line 15, in <module>
    from langchain_ollama import ChatOllama
ImportError: cannot import name 'ChatOllama' from 'langchain_ollama'

STDOUT:
Starting GhidraAgent v2.0.0...
Initializing LLM connection...
ERROR: Failed to initialize LLM

EXIT CODE: 1

DIAGNOSTICS:
Python version: 3.14.2
⚠️  WARNING: Python 3.14+ detected
   LangChain's Pydantic V1 compatibility may cause issues
   RECOMMENDED: Use Python 3.11 or 3.13
Config file: D:\agents\ghidra_agent\agent.toml (exists)
Required Python: >=3.11,<3.14
Dependencies: 5 packages required
  Packages: langchain-ollama, langchain-core, aiohttp, pydantic>=2.0, ghidra-bridge
Working directory: D:\agents\ghidra_agent
  main.py: ✓ found
  requirements.txt: ✓ found
  .venv: ✓ found

💡 LIKELY CAUSE: Pydantic V1 compatibility with Python 3.14+
   FIX: Use Python 3.11 or 3.13 instead of 3.14
   OR: Wait for LangChain to fully support Python 3.14

📋 TROUBLESHOOTING STEPS:
   1. Check the STDERR and STDOUT logs above for specific errors
   2. Verify all dependencies are installed in the virtual environment
   3. Test the agent configuration with: atoll --agent <config_path> --test
   4. Check system logs for more details
   5. Review agent documentation: D:\agents\ghidra_agent\README.md
```

## Implementation Details

### Code Location
The error diagnostics system is implemented in `src/atoll/deployment/server.py`:

- **AgentInstance dataclass**: Enhanced with `stdout_log`, `stderr_log`, `exit_code` fields
- **start_agent() method**: Captures full process output and generates diagnostics
- **_generate_diagnostics() method**: Analyzes failures and returns actionable advice

### Test Coverage
Comprehensive test suite in `tests/unit/test_deployment_error_diagnostics.py`:

- Python version compatibility detection
- Missing dependency identification
- Port conflict detection
- Permission error recognition
- Configuration file structure validation
- Troubleshooting step generation

All 61 deployment tests pass, including 4 new diagnostic tests.

## Usage

The enhanced error output appears automatically when:

1. Using `list deployment` command to see agent status
2. Checking specific agent status with `status deployment <name>`
3. Via REST API `/agents/{name}/status` endpoint

No configuration needed - the diagnostics run automatically when an agent fails to start.

## Benefits

1. **Faster Debugging**: Identify root cause in seconds instead of minutes
2. **Self-Service Support**: Users can fix common issues without help
3. **Better UX**: Clear, actionable error messages instead of cryptic tracebacks
4. **Production Ready**: Comprehensive logging for post-mortem analysis

## Technical Notes

- Diagnostics use pattern matching on stderr/stdout to detect issues
- Python version detection uses `sys.version_info`
- Configuration parsing uses existing `TOMLAgentConfig` validation
- File structure checks use `Path.exists()` for main.py, requirements.txt, .venv
- Platform-aware pip path construction (Windows: Scripts\pip.exe, Unix: bin/pip)

## Future Enhancements

Potential improvements for v2.1:

- Log persistence to files for historical analysis
- Integration with external monitoring systems (Sentry, DataDog)
- Email/Slack notifications for critical failures
- Automatic fix suggestions with shell command generation
- Machine learning-based failure prediction
