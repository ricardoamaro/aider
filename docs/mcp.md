# MCP Integration

Aider supports the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), allowing it to connect to external tools, services, and data sources to enhance AI capabilities. MCP provides a standardized way for AI applications to access external resources like file systems, databases, web APIs, and custom tools.

## Quick Start

### Enable Built-in MCP Server

The fastest way to get started is with aider's built-in MCP server:

```bash
aider --enable-aider-mcp-server
```

This provides immediate access to:
- **File analysis** with complexity scoring and issue detection
- **Command execution** with timeout and error handling  
- **Codebase search** using regex patterns
- **Repository structure** analysis
- **File and directory** resource providers

### Connect to External MCP Servers

```bash
# Connect to filesystem server
aider --mcp-servers "filesystem:stdio:mcp-server-filesystem /path/to/project"

# Connect to multiple servers
aider --mcp-servers "filesystem:stdio:mcp-server-filesystem /path" \
      --mcp-servers "web:websocket:ws://localhost:9000/mcp"
```

### Use Configuration Files

Create `.aider.mcp.json` in your project:

```json
{
  "settings": {
    "enabled": true,
    "timeout": 30,
    "context_limit": 10000
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

Then simply run:
```bash
aider  # Automatically loads configuration
```

## Installation

MCP functionality requires additional dependencies:

```bash
pip install pydantic-ai[mcp] fastmcp websockets uvicorn
```

Or install aider with MCP support:

```bash
pip install aider-chat[mcp]
```

## Configuration

### Configuration Hierarchy

Aider uses a hierarchical configuration system that loads settings in this order (later sources override earlier ones):

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
      "command": ["cmd", "arg1", "arg2"],  // for stdio transport
      "url": "ws://host:port/path",        // for websocket transport
      "env": {"KEY": "value"},             // environment variables
      "enabled": true
    }
  ]
}
```

### Generate Example Configuration

```bash
python scripts/generate_mcp_config.py
```

## Built-in Tools

When using `--enable-aider-mcp-server`, aider provides these MCP tools:

### Tools

#### `analyze_file`
Analyze source code files for complexity, issues, and metadata.

```python
# Example usage in chat:
# "Analyze the complexity of my Python files"
# "What issues are in src/main.py?"
```

**Returns:**
- Lines of code
- Programming language
- Complexity score (0-10)
- Issues found (TODOs, FIXMEs, etc.)
- File size and modification time

#### `run_command`
Execute shell commands with timeout and error handling.

```python
# Example usage in chat:
# "Run the tests and show me the results"
# "Execute 'npm run build' and check for errors"
```

**Features:**
- Configurable timeout (default 300s)
- Captures stdout and stderr
- Returns exit code and execution time
- Working directory support

#### `search_codebase`
Search code using regex patterns with file type filtering.

```python
# Example usage in chat:
# "Find all TODO comments in Python files"
# "Search for functions named 'process_*' in JavaScript"
```

**Features:**
- Regex pattern matching
- File type filtering
- Case-sensitive/insensitive search
- Configurable result limits
- Line number references

#### `get_repo_structure`
Get repository tree structure with depth control.

```python
# Example usage in chat:
# "Show me the project structure"
# "What directories are in the src folder?"
```

**Features:**
- Configurable depth limits
- Hidden file filtering
- File size and modification times
- Excludes common build/cache directories

### Resources

#### `file://path`
Access file contents with security checks.

```python
# Example usage:
# MCP client can request: file:///path/to/file.py
# Returns the complete file content
```

**Security:**
- Restricted to current directory and subdirectories
- UTF-8 encoding with error handling
- File existence validation

#### `directory://path`
List directory contents with metadata.

```python
# Example usage:
# MCP client can request: directory:///path/to/dir
# Returns formatted directory listing
```

**Features:**
- File and directory icons
- Size and modification time
- Sorted alphabetically
- Security restrictions

## CLI Options

### Basic Options

```bash
# Enable built-in server
aider --enable-aider-mcp-server

# Specify server port
aider --enable-aider-mcp-server --mcp-server-port 9000

# Connect to external servers
aider --mcp-servers "name:transport:command_or_url"

# Use configuration file
aider --mcp-config /path/to/config.json
```

### Server Specification Format

For `--mcp-servers`, use the format: `name:transport:command_or_url`

**stdio transport:**
```bash
aider --mcp-servers "filesystem:stdio:mcp-server-filesystem /path"
```

**websocket transport:**
```bash
aider --mcp-servers "api:websocket:ws://localhost:9000/mcp"
```

### Environment Variables

```bash
export AIDER_MCP_CONFIG="/path/to/config.json"
export AIDER_MCP_SERVERS="filesystem:stdio:mcp-server-filesystem /path"
export AIDER_ENABLE_AIDER_MCP_SERVER="true"
export AIDER_MCP_SERVER_PORT="8000"
```

## Examples

### Example 1: File Analysis Workflow

```bash
aider --enable-aider-mcp-server
```

In the chat:
```
User: Analyze all Python files in my project and identify the most complex ones.

Aider: I'll analyze your Python files using the MCP file analysis tool...
[Uses analyze_file tool on each .py file]

Based on the analysis:
- src/complex_algorithm.py: Complexity 8.5/10 (247 lines, multiple nested loops)
- src/data_processor.py: Complexity 6.2/10 (156 lines, 3 TODO items)
- src/utils.py: Complexity 2.1/10 (45 lines, well-structured)

The most complex file is src/complex_algorithm.py. Would you like me to suggest refactoring improvements?
```

### Example 2: External Tool Integration

```bash
aider --mcp-servers "filesystem:stdio:mcp-server-filesystem ." \
      --mcp-servers "web:websocket:ws://localhost:9000/mcp"
```

In the chat:
```
User: What files are in my project and can you search the web for best practices?

Aider: I'll check your project structure and search for best practices...
[Uses filesystem MCP server to list files]
[Uses web MCP server to search for relevant information]

Your project contains:
- 15 Python files in src/
- 8 test files in tests/
- Configuration files: setup.py, requirements.txt

Based on web search, here are the best practices for your Python project structure...
```

### Example 3: Development Workflow

```bash
aider --enable-aider-mcp-server
```

In the chat:
```
User: Run the tests, analyze any failures, and suggest fixes.

Aider: I'll run your tests and analyze the results...
[Uses run_command tool to execute tests]
[Uses analyze_file tool on failing test files]
[Uses search_codebase tool to find related code]

Test Results:
- 12 tests passed
- 3 tests failed in test_authentication.py

Analysis of failures:
1. test_login_invalid_password: AssertionError on line 45
2. test_token_expiry: Timeout in authentication flow
3. test_user_permissions: Missing mock data

I found the issues in src/auth.py lines 123-145. Here are the suggested fixes...
```

## Advanced Usage

### Custom MCP Servers

Create your own MCP server:

```python
# my_custom_server.py
from fastmcp import FastMCP

mcp = FastMCP("my-tools")

@mcp.tool()
async def analyze_database(query: str) -> dict:
    """Analyze database with custom query"""
    # Your custom logic here
    return {"results": "analysis data"}

@mcp.resource("db://{table}")
async def get_table_data(table: str) -> str:
    """Get data from database table"""
    # Your database logic here
    return "table data"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.app, host="localhost", port=9000)
```

Connect to aider:
```bash
aider --mcp-servers "custom:websocket:ws://localhost:9000/mcp"
```

### Configuration Management

**Create project-specific config:**
```bash
# Generate example config
python scripts/generate_mcp_config.py

# Edit for your needs
vim .aider.mcp.json

# Use with aider
aider  # Automatically loads config
```

**Validate configuration:**
```python
from aider.mcp import validate_mcp_configuration, load_mcp_configuration

config = load_mcp_configuration()
issues = validate_mcp_configuration(config)
if issues:
    print("Configuration issues:", issues)
```

### Performance Tuning

**Optimize for large codebases:**
```json
{
  "settings": {
    "context_limit": 5000,
    "cache_ttl": 600,
    "timeout": 60
  }
}
```

**Optimize for fast responses:**
```json
{
  "settings": {
    "context_limit": 15000,
    "cache_ttl": 60,
    "timeout": 10
  }
}
```

## Troubleshooting

### Common Issues

**1. Dependencies not installed**
```bash
pip install pydantic-ai[mcp] fastmcp websockets uvicorn
```

**2. Server connection failed**
- Check server is running: `curl http://localhost:8000/health`
- Verify transport type matches (stdio vs websocket)
- Check firewall and network settings
- Review server logs for errors

**3. Configuration errors**
```bash
# Validate JSON syntax
python -m json.tool .aider.mcp.json

# Check configuration
python -c "from aider.mcp import load_mcp_configuration; print(load_mcp_configuration())"
```

**4. Performance issues**
- Reduce `context_limit` in settings
- Increase `cache_ttl` for better caching
- Limit number of concurrent servers
- Use file type filtering in searches

### Debug Mode

Enable verbose logging:
```bash
aider --verbose --enable-aider-mcp-server
```

Check MCP server status:
```bash
# Test built-in server
curl http://localhost:8000/health

# Test WebSocket connection
wscat -c ws://localhost:8000/mcp
```

### Error Messages

**"MCP dependencies not available"**
- Install required packages: `pip install pydantic-ai[mcp] fastmcp`

**"Failed to connect to MCP server"**
- Check server is running and accessible
- Verify URL/command in configuration
- Check network connectivity

**"Configuration validation failed"**
- Review configuration syntax
- Check required fields for transport type
- Verify file paths and permissions

## Security Considerations

### Built-in Server Security

- **File Access**: Restricted to current directory and subdirectories
- **Command Execution**: No shell injection protection (use with caution)
- **Network**: Binds to localhost only by default
- **Timeouts**: All operations have configurable timeouts

### External Server Security

- **Validation**: All server configurations validated before connection
- **Sandboxing**: Servers run in separate processes
- **Authentication**: Support for API keys and authentication headers
- **Encryption**: WebSocket connections support WSS (secure WebSocket)

### Best Practices

1. **Restrict file access** to necessary directories only
2. **Use authentication** for external MCP servers
3. **Monitor resource usage** and set appropriate limits
4. **Validate inputs** in custom MCP servers
5. **Use HTTPS/WSS** for remote connections
6. **Regular updates** of MCP dependencies

## Integration with Aider Features

### Model Integration

MCP context is automatically injected into LLM conversations:

```
System: ## Available MCP Resources:
- config.json (file://config.json)
- database schema (db://schema)

## Available MCP Tools:
- analyze_file: Analyze source code complexity
- run_command: Execute shell commands
- search_codebase: Search code with regex

User: Help me optimize this function...
```

### Git Integration

MCP tools work seamlessly with aider's git features:

```bash
# Analyze changes before commit
aider --enable-aider-mcp-server --auto-commits

# In chat: "Analyze the files I've changed and suggest improvements"
# MCP tools analyze modified files
# Aider suggests improvements and commits changes
```

### Testing Integration

```bash
# Run tests via MCP and analyze results
aider --enable-aider-mcp-server --auto-test

# In chat: "Run tests and fix any failures"
# MCP executes test command
# Analyzes failures and suggests fixes
# Aider implements fixes and re-runs tests
```

## Community and Ecosystem

### Popular MCP Servers

- **[mcp-server-filesystem](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)**: File system access
- **[mcp-server-brave-search](https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search)**: Web search
- **[mcp-server-github](https://github.com/modelcontextprotocol/servers/tree/main/src/github)**: GitHub integration
- **[mcp-server-postgres](https://github.com/modelcontextprotocol/servers/tree/main/src/postgres)**: PostgreSQL database
- **[mcp-server-sqlite](https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite)**: SQLite database

### Creating MCP Servers

See the [MCP documentation](https://modelcontextprotocol.io/) and [FastMCP](https://github.com/jlowin/fastmcp) for creating custom servers.

### Contributing

The MCP integration is designed to be extensible. Contributions welcome:

1. **Add new built-in tools** to `aider/mcp/servers/aider_tools.py`
2. **Create new server templates** in `aider/mcp/servers/`
3. **Extend configuration options** in `aider/mcp/config.py`
4. **Add tests** following existing patterns in `test_mcp_*.py`

## Changelog

### Version 0.86.1+
- ✅ Complete MCP client integration
- ✅ Built-in FastMCP server with aider tools
- ✅ Model integration with context injection
- ✅ Hierarchical configuration system
- ✅ Comprehensive documentation and examples

## License

MCP integration follows the same license as aider.