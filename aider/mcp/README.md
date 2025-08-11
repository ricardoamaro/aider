# MCP Integration for Aider

This directory contains the Model Context Protocol (MCP) integration for aider, allowing it to connect to external MCP servers and leverage their tools and resources.

## Phase 1 Implementation Status ✅

Phase 1 (Core MCP Integration) is now complete and includes:

- **MCPManager**: Core connection management for MCP servers
- **MCPClient**: Simplified interface for aider integration  
- **CLI Arguments**: Command-line options for MCP configuration
- **Configuration**: JSON-based server configuration support
- **Error Handling**: Graceful fallbacks when MCP dependencies unavailable

## Installation

To use MCP functionality, install the required dependencies:

```bash
pip install pydantic-ai[mcp] fastmcp websockets
```

## Usage

### Command Line Options

```bash
# Connect to MCP servers via CLI
aider --mcp-servers "filesystem:stdio:mcp-server-filesystem /path/to/dir"

# Use configuration file
aider --mcp-config examples/mcp-config.json

# Enable built-in aider MCP server (Phase 2)
aider --enable-aider-mcp-server --mcp-server-port 8000
```

### Configuration File

Create a JSON configuration file (see `examples/mcp-config.json`):

```json
{
  "servers": [
    {
      "name": "filesystem",
      "transport": "stdio", 
      "command": ["mcp-server-filesystem", "/allowed/path"],
      "enabled": true
    }
  ]
}
```

## Architecture

```
aider/mcp/
├── __init__.py          # Public API exports
├── manager.py           # MCPManager - core connection handling
├── client.py            # MCPClient - simplified interface
└── servers/             # Built-in MCP servers (Phase 2)
    ├── __init__.py
    └── aider_tools.py   # FastMCP server (Phase 2)
```

## Testing

Run the Phase 1 test suite:

```bash
python test_mcp_phase1.py
```

## Next Steps (Phase 2)

- Implement built-in FastMCP server with aider tools
- Add file analysis, command execution, and search capabilities
- Integrate with aider's existing functionality

## Compatibility

- **Backward Compatible**: All MCP features are opt-in
- **Graceful Fallback**: Works without MCP dependencies installed
- **Error Handling**: Clear messages when servers unavailable