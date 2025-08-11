# MCP Integration for Aider

This directory contains the complete Model Context Protocol (MCP) integration for aider, enabling it to connect to external MCP servers and leverage their tools and resources for enhanced AI-powered coding assistance.

## 🚀 Complete Implementation Status

All phases of MCP integration are now complete:

- ✅ **Phase 1**: Core MCP client connectivity and CLI integration
- ✅ **Phase 2**: Built-in FastMCP server with aider-specific tools
- ✅ **Phase 3**: Model integration with context injection and Pydantic AI
- ✅ **Phase 4**: Configuration system, validation, and documentation

## 📦 Installation

To use MCP functionality, install the required dependencies:

```bash
pip install pydantic-ai[mcp] fastmcp websockets uvicorn
```

## 🎯 Quick Start

### 1. Enable Built-in Aider MCP Server

```bash
aider --enable-aider-mcp-server
```

This starts aider with its built-in MCP server providing:
- File analysis with complexity scoring
- Command execution with timeout support
- Regex-based codebase search
- Repository structure analysis
- File and directory resource providers

### 2. Connect to External MCP Servers

```bash
# Connect to filesystem server
aider --mcp-servers "filesystem:stdio:mcp-server-filesystem /path/to/project"

# Connect to multiple servers
aider --mcp-servers "filesystem:stdio:mcp-server-filesystem /path" \
      --mcp-servers "web:websocket:ws://localhost:9000/mcp"
```

### 3. Use Configuration File

Create `.aider.mcp.json` in your project:

```json
{
  "settings": {
    "enabled": true,
    "timeout": 30,
    "context_limit": 10000,
    "log_level": "INFO"
  },
  "servers": [
    {
      "name": "filesystem",
      "transport": "stdio",
      "command": ["mcp-server-filesystem", "/allowed/path"],
      "enabled": true
    },
    {
      "name": "aider-tools",
      "transport": "websocket", 
      "url": "ws://localhost:8000/mcp",
      "enabled": true
    }
  ]
}
```

Then run:
```bash
aider  # Automatically loads configuration
```

## 🏗️ Architecture

```
aider/mcp/
├── __init__.py          # Public API exports
├── manager.py           # MCPManager - core connection handling
├── client.py            # MCPClient - simplified interface
├── config.py            # Configuration system with validation
└── servers/             # Built-in MCP servers
    ├── __init__.py
    └── aider_tools.py   # FastMCP server with aider tools
```

## 🔧 Configuration System

The MCP integration supports a hierarchical configuration system:

1. **Global**: `~/.aider/mcp-config.json`
2. **Project**: `<git-root>/.aider.mcp.json`
3. **Local**: `./.aider.mcp.json`
4. **Environment**: `$AIDER_MCP_CONFIG`
5. **CLI Arguments**: Override all file-based configs

### Configuration Schema

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
      "name": "server-name",
      "transport": "stdio|websocket",
      "command": ["cmd", "arg1", "arg2"],  // for stdio
      "url": "ws://host:port/path",        // for websocket
      "env": {"KEY": "value"},
      "enabled": true
    }
  ]
}
```

## 🛠️ Built-in Tools

When using `--enable-aider-mcp-server`, aider provides these MCP tools:

### Tools
- **analyze_file**: Analyze source files for complexity, issues, and metadata
- **run_command**: Execute shell commands with timeout and error handling
- **search_codebase**: Search code using regex patterns with file type filtering
- **get_repo_structure**: Get repository tree structure with depth control

### Resources
- **file://path**: Access file contents with security checks
- **directory://path**: List directory contents with metadata

## 🔌 Integration Points

### Model Integration
- Automatic MCP context injection into LLM messages
- Pydantic AI agent integration for enhanced completions
- Graceful fallback to standard completions when MCP unavailable

### Coder Integration
- MCP detection in base coder with `mcp_enabled` attribute
- Async completion support with `asyncio.run()` for MCP calls
- Seamless integration preserving existing aider workflow

## 🧪 Testing

Run the comprehensive test suites:

```bash
# Test each phase individually
python test_mcp_phase1.py  # Core connectivity
python test_mcp_phase2.py  # FastMCP server
python test_mcp_phase3.py  # Model integration

# Test end-to-end integration
python test_mcp_integration.py
```

## 📚 Examples

### Example 1: File Analysis
```bash
aider --enable-aider-mcp-server
# In chat: "Analyze the complexity of my Python files"
# MCP will provide detailed file analysis with complexity scores
```

### Example 2: External Tools
```bash
aider --mcp-servers "filesystem:stdio:mcp-server-filesystem ."
# In chat: "What files are in my project?"
# MCP filesystem server provides directory listings
```

### Example 3: Command Execution
```bash
aider --enable-aider-mcp-server
# In chat: "Run the tests and show me the results"
# MCP will execute test commands and provide formatted output
```

## 🔒 Security

- **Sandboxing**: File access restricted to allowed directories
- **Validation**: All server configurations validated before connection
- **Timeouts**: Commands and connections have configurable timeouts
- **Error Handling**: Graceful degradation when servers unavailable

## 🚀 Performance

- **Caching**: Configuration and context caching with TTL
- **Async**: Non-blocking MCP operations with asyncio
- **Connection Pooling**: Efficient connection management
- **Context Limits**: Configurable limits to prevent overwhelming LLMs

## 🔄 Compatibility

- **Backward Compatible**: All MCP features are opt-in via CLI flags
- **Graceful Fallback**: Works without MCP dependencies installed
- **Version Support**: Compatible with existing aider workflows
- **Error Recovery**: Clear error messages and recovery suggestions

## 🎛️ Advanced Usage

### Custom MCP Servers

Create your own MCP server and connect it:

```python
# my_mcp_server.py
from fastmcp import FastMCP

mcp = FastMCP("my-tools")

@mcp.tool()
async def my_custom_tool(input: str) -> str:
    return f"Processed: {input}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.app, host="localhost", port=9000)
```

Connect to aider:
```bash
aider --mcp-servers "custom:websocket:ws://localhost:9000/mcp"
```

### Environment Variables

```bash
export AIDER_MCP_CONFIG="/path/to/config.json"
export AIDER_MCP_SERVERS="filesystem:stdio:mcp-server-filesystem /path"
export AIDER_ENABLE_AIDER_MCP_SERVER="true"
export AIDER_MCP_SERVER_PORT="8000"
```

## 🐛 Troubleshooting

### Common Issues

1. **Dependencies not installed**
   ```bash
   pip install pydantic-ai[mcp] fastmcp websockets uvicorn
   ```

2. **Server connection failed**
   - Check server is running and accessible
   - Verify transport type (stdio vs websocket)
   - Check firewall and network settings

3. **Configuration errors**
   - Validate JSON syntax
   - Check required fields for transport type
   - Verify file paths and permissions

4. **Performance issues**
   - Reduce `context_limit` in settings
   - Increase `cache_ttl` for better caching
   - Limit number of concurrent servers

### Debug Mode

Enable verbose logging:
```bash
aider --verbose --mcp-config config.json
```

## 🤝 Contributing

The MCP integration is designed to be extensible:

1. **Add new tools** to `aider/mcp/servers/aider_tools.py`
2. **Create new servers** in `aider/mcp/servers/`
3. **Extend configuration** in `aider/mcp/config.py`
4. **Add tests** following existing patterns

## 📄 License

MCP integration follows the same license as aider.