# MCP Quick Reference

## Installation
```bash
pip install pydantic-ai[mcp] fastmcp websockets uvicorn
```

## Quick Start Commands

### Built-in Server
```bash
# Enable built-in MCP server
aider --enable-aider-mcp-server

# Custom port
aider --enable-aider-mcp-server --mcp-server-port 9000
```

### External Servers
```bash
# Filesystem access
aider --mcp-servers "filesystem:stdio:mcp-server-filesystem /path"

# WebSocket server
aider --mcp-servers "api:websocket:ws://localhost:9000/mcp"

# Multiple servers
aider --mcp-servers "fs:stdio:mcp-server-filesystem /path" \
      --mcp-servers "web:websocket:ws://localhost:9000/mcp"
```

### Configuration File
```bash
# Use config file
aider --mcp-config .aider.mcp.json

# Generate example config
python scripts/generate_mcp_config.py
```

## Configuration Template

### Basic Configuration
```json
{
  "settings": {
    "enabled": true,
    "timeout": 30
  },
  "servers": [
    {
      "name": "aider-tools",
      "transport": "websocket", 
      "url": "ws://localhost:8000/mcp",
      "enabled": true
    }
  ]
}
```

### Full Configuration
```json
{
  "settings": {
    "enabled": true,
    "timeout": 30,
    "max_retries": 3,
    "context_limit": 10000,
    "cache_ttl": 300,
    "log_level": "INFO"
  },
  "servers": [
    {
      "name": "filesystem",
      "transport": "stdio",
      "command": ["mcp-server-filesystem", "/allowed/path"],
      "env": {"DEBUG": "1"},
      "enabled": true
    },
    {
      "name": "database",
      "transport": "websocket",
      "url": "ws://localhost:9000/mcp",
      "enabled": true
    }
  ]
}
```

## Built-in Tools

| Tool | Description | Example Usage |
|------|-------------|---------------|
| `analyze_file` | Analyze code complexity | "Analyze complexity of main.py" |
| `run_command` | Execute shell commands | "Run the tests" |
| `search_codebase` | Search with regex | "Find all TODO comments" |
| `get_repo_structure` | Show project structure | "What's in the src directory?" |

## Built-in Resources

| Resource | Description | Example |
|----------|-------------|---------|
| `file://path` | File contents | `file:///src/main.py` |
| `directory://path` | Directory listing | `directory:///src` |

## Environment Variables

```bash
export AIDER_MCP_CONFIG="/path/to/config.json"
export AIDER_MCP_SERVERS="fs:stdio:mcp-server-filesystem /path"
export AIDER_ENABLE_AIDER_MCP_SERVER="true"
export AIDER_MCP_SERVER_PORT="8000"
```

## Configuration Hierarchy

1. Global: `~/.aider/mcp-config.json`
2. Project: `<git-root>/.aider.mcp.json`
3. Local: `./.aider.mcp.json`
4. Environment: `$AIDER_MCP_CONFIG`
5. CLI Arguments: `--mcp-*`

## Common Patterns

### Development Workflow
```bash
# Start with built-in tools
aider --enable-aider-mcp-server

# Chat examples:
# "Analyze my Python files for complexity"
# "Run the tests and show results"
# "Search for TODO comments"
# "What's the project structure?"
```

### External Integration
```bash
# Add filesystem access
aider --enable-aider-mcp-server \
      --mcp-servers "fs:stdio:mcp-server-filesystem ."

# Chat examples:
# "List files in the docs directory"
# "Show me the content of README.md"
```

### Custom Server
```python
# my_server.py
from fastmcp import FastMCP
mcp = FastMCP("my-tools")

@mcp.tool()
async def my_tool(input: str) -> str:
    return f"Processed: {input}"

# Run: uvicorn my_server:mcp.app --port 9000
```

```bash
# Connect to custom server
aider --mcp-servers "custom:websocket:ws://localhost:9000/mcp"
```

## Troubleshooting

### Check Dependencies
```bash
python -c "import pydantic_ai, fastmcp; print('MCP dependencies OK')"
```

### Validate Configuration
```bash
python -m json.tool .aider.mcp.json
python -c "from aider.mcp import load_mcp_configuration; print('Config OK')"
```

### Test Server Connection
```bash
# Built-in server
curl http://localhost:8000/health

# WebSocket server
wscat -c ws://localhost:8000/mcp
```

### Debug Mode
```bash
aider --verbose --enable-aider-mcp-server
```

## Error Solutions

| Error | Solution |
|-------|----------|
| "MCP dependencies not available" | `pip install pydantic-ai[mcp] fastmcp` |
| "Failed to connect to MCP server" | Check server is running, verify URL/command |
| "Configuration validation failed" | Check JSON syntax, required fields |
| "Permission denied" | Check file paths, directory permissions |
| "Timeout connecting to server" | Increase timeout in settings, check network |

## Performance Tips

### For Large Codebases
```json
{
  "settings": {
    "context_limit": 5000,
    "cache_ttl": 600,
    "timeout": 60
  }
}
```

### For Fast Responses
```json
{
  "settings": {
    "context_limit": 15000,
    "cache_ttl": 60,
    "timeout": 10
  }
}
```

## Security Checklist

- ✅ Restrict file access to necessary directories
- ✅ Use authentication for external servers
- ✅ Monitor resource usage and set limits
- ✅ Validate inputs in custom servers
- ✅ Use HTTPS/WSS for remote connections
- ✅ Keep MCP dependencies updated