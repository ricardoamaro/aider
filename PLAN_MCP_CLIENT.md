# MCP Client Integration Plan for Aider

## Overview

This document outlines the detailed plan for integrating Model Context Protocol (MCP) client capabilities into aider using Pydantic AI and FastMCP. This integration will enable aider to connect to external MCP servers and provide enhanced context and tools to LLMs.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Aider Core    │    │  MCP Integration │    │   MCP Servers   │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │   Models    │◄┼────┼►│ MCP Manager  │◄┼────┼►│ External    │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ │ Servers     │ │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ └─────────────┘ │
│ │   Coders    │◄┼────┼►│ Pydantic AI  │ │    │ ┌─────────────┐ │
│ └─────────────┘ │    │ │ Agents       │ │    │ │ Built-in    │ │
│ ┌─────────────┐ │    │ └──────────────┘ │    │ │ FastMCP     │ │
│ │  Commands   │◄┼────┼►┌──────────────┐ │    │ │ Server      │ │
│ └─────────────┘ │    │ │ MCP Tools    │ │    │ └─────────────┘ │
└─────────────────┘    │ └──────────────┘ │    └─────────────────┘
                       └──────────────────┘
```

## Phase 1: Core MCP Integration (Week 1)

### 1.1 Dependencies and Setup

**New Dependencies:**
```toml
# Add to requirements/requirements.in
pydantic-ai[mcp]>=0.0.14
fastmcp>=2.0.0
websockets>=12.0  # For WebSocket transport
```

**File Structure:**
```
aider/
├── mcp/
│   ├── __init__.py
│   ├── manager.py          # MCP connection manager
│   ├── client.py           # MCP client wrapper
│   ├── tools.py            # Built-in MCP tools
│   └── servers/
│       ├── __init__.py
│       └── aider_tools.py  # FastMCP server for aider tools
├── models.py               # Modified for MCP integration
├── main.py                 # CLI args for MCP
└── args.py                 # MCP argument definitions
```

### 1.2 MCP Manager Implementation

**File: `aider/mcp/manager.py`**
```python
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from pydantic_ai.mcp import MCPClientSession
from pydantic_ai import Agent
from pydantic import BaseModel

class MCPServerConfig(BaseModel):
    name: str
    transport: str  # "stdio", "websocket", etc.
    command: Optional[List[str]] = None  # For stdio transport
    url: Optional[str] = None  # For websocket transport
    env: Optional[Dict[str, str]] = None
    enabled: bool = True

class MCPManager:
    """Manages MCP client connections and provides unified interface"""
    
    def __init__(self, io=None):
        self.io = io
        self.sessions: Dict[str, MCPClientSession] = {}
        self.agents: Dict[str, Agent] = {}
        self.available_tools: List[Any] = []
        self.available_resources: List[Any] = []
        self._connected = False
    
    async def connect_servers(self, configs: List[MCPServerConfig]):
        """Connect to configured MCP servers"""
        for config in configs:
            if not config.enabled:
                continue
                
            try:
                if self.io:
                    self.io.tool_output(f"Connecting to MCP server: {config.name}")
                
                session = MCPClientSession(
                    transport=config.transport,
                    command=config.command,
                    url=config.url,
                    env=config.env or {}
                )
                
                await session.connect()
                self.sessions[config.name] = session
                
                # Get available tools and resources
                tools = await session.list_tools()
                resources = await session.list_resources()
                
                self.available_tools.extend(tools)
                self.available_resources.extend(resources)
                
                if self.io:
                    self.io.tool_output(
                        f"Connected to {config.name}: "
                        f"{len(tools)} tools, {len(resources)} resources"
                    )
                    
            except Exception as e:
                if self.io:
                    self.io.tool_error(f"Failed to connect to {config.name}: {e}")
                continue
        
        self._connected = len(self.sessions) > 0
        return self._connected
    
    async def get_context_for_model(self, query: str = "") -> Dict[str, Any]:
        """Get relevant context from MCP servers for model input"""
        if not self._connected:
            return {}
        
        context = {
            "mcp_resources": [],
            "mcp_tools": [],
            "mcp_context": ""
        }
        
        # Collect relevant resources
        for session in self.sessions.values():
            try:
                # Get resources that might be relevant to the query
                resources = await session.list_resources()
                for resource in resources:
                    if self._is_resource_relevant(resource, query):
                        content = await session.read_resource(resource.uri)
                        context["mcp_resources"].append({
                            "uri": resource.uri,
                            "name": resource.name,
                            "content": content
                        })
            except Exception as e:
                if self.io:
                    self.io.tool_warning(f"Error getting MCP resources: {e}")
        
        # Add available tools info
        context["mcp_tools"] = [
            {"name": tool.name, "description": tool.description}
            for tool in self.available_tools
        ]
        
        return context
    
    def _is_resource_relevant(self, resource, query: str) -> bool:
        """Simple relevance check - can be enhanced with embeddings"""
        if not query:
            return True
        
        query_lower = query.lower()
        return (
            query_lower in resource.name.lower() or
            query_lower in (resource.description or "").lower()
        )
    
    async def create_enhanced_agent(self, model_name: str) -> Optional[Agent]:
        """Create Pydantic AI agent with MCP capabilities"""
        if not self._connected:
            return None
        
        try:
            agent = Agent(
                model=model_name,
                mcp_sessions=list(self.sessions.values())
            )
            return agent
        except Exception as e:
            if self.io:
                self.io.tool_error(f"Failed to create MCP agent: {e}")
            return None
    
    async def disconnect_all(self):
        """Disconnect from all MCP servers"""
        for session in self.sessions.values():
            try:
                await session.disconnect()
            except Exception:
                pass
        
        self.sessions.clear()
        self.agents.clear()
        self.available_tools.clear()
        self.available_resources.clear()
        self._connected = False

def load_mcp_config(config_path: Path) -> List[MCPServerConfig]:
    """Load MCP server configurations from file"""
    if not config_path.exists():
        return []
    
    try:
        with open(config_path) as f:
            data = json.load(f)
        
        return [MCPServerConfig(**server) for server in data.get("servers", [])]
    except Exception as e:
        print(f"Error loading MCP config: {e}")
        return []
```

### 1.3 CLI Integration

**File: `aider/args.py` (additions)**
```python
# Add MCP-related arguments
mcp_group = parser.add_argument_group("MCP (Model Context Protocol)")

mcp_group.add_argument(
    "--mcp-servers",
    action="append",
    metavar="NAME:TRANSPORT:COMMAND",
    help="MCP server configuration (e.g., 'filesystem:stdio:mcp-server-filesystem')"
)

mcp_group.add_argument(
    "--mcp-config",
    metavar="PATH",
    help="Path to MCP configuration file (JSON)"
)

mcp_group.add_argument(
    "--enable-aider-mcp-server",
    action="store_true",
    help="Enable built-in aider MCP server with aider-specific tools"
)

mcp_group.add_argument(
    "--mcp-server-port",
    type=int,
    default=8000,
    help="Port for built-in aider MCP server (default: 8000)"
)
```

## Phase 2: Built-in FastMCP Server (Week 2)

### 2.1 Aider Tools MCP Server

**File: `aider/mcp/servers/aider_tools.py`**
```python
import asyncio
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastmcp import FastMCP
from pydantic import BaseModel

# Initialize FastMCP server
mcp = FastMCP("aider-tools")

class FileAnalysis(BaseModel):
    path: str
    lines: int
    language: str
    complexity_score: float
    issues: List[str]

class TestResult(BaseModel):
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float

@mcp.tool()
async def analyze_file(path: str) -> FileAnalysis:
    """Analyze a source code file for complexity, issues, and metadata"""
    try:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        content = file_path.read_text(encoding='utf-8')
        lines = len(content.splitlines())
        
        # Simple language detection
        suffix = file_path.suffix.lower()
        language_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.java': 'java', '.cpp': 'cpp', '.c': 'c', '.go': 'go',
            '.rs': 'rust', '.rb': 'ruby', '.php': 'php'
        }
        language = language_map.get(suffix, 'unknown')
        
        # Basic complexity analysis (can be enhanced)
        complexity_score = min(lines / 100.0, 10.0)  # Simple metric
        
        issues = []
        if lines > 1000:
            issues.append("File is very large (>1000 lines)")
        if 'TODO' in content:
            issues.append("Contains TODO comments")
        if 'FIXME' in content:
            issues.append("Contains FIXME comments")
        
        return FileAnalysis(
            path=path,
            lines=lines,
            language=language,
            complexity_score=complexity_score,
            issues=issues
        )
    except Exception as e:
        raise RuntimeError(f"Failed to analyze file: {e}")

@mcp.tool()
async def run_command(command: str, cwd: Optional[str] = None) -> TestResult:
    """Execute a shell command and return results"""
    import subprocess
    import time
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        duration = time.time() - start_time
        
        return TestResult(
            command=command,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            duration=duration
        )
    except subprocess.TimeoutExpired:
        return TestResult(
            command=command,
            exit_code=-1,
            stdout="",
            stderr="Command timed out after 5 minutes",
            duration=300.0
        )
    except Exception as e:
        return TestResult(
            command=command,
            exit_code=-1,
            stdout="",
            stderr=f"Error executing command: {e}",
            duration=time.time() - start_time
        )

@mcp.tool()
async def search_codebase(pattern: str, file_types: Optional[List[str]] = None) -> Dict[str, List[str]]:
    """Search for patterns in the codebase"""
    import re
    
    if file_types is None:
        file_types = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']
    
    results = {}
    cwd = Path.cwd()
    
    for file_path in cwd.rglob('*'):
        if file_path.is_file() and file_path.suffix in file_types:
            try:
                content = file_path.read_text(encoding='utf-8')
                matches = []
                
                for line_num, line in enumerate(content.splitlines(), 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        matches.append(f"Line {line_num}: {line.strip()}")
                
                if matches:
                    results[str(file_path.relative_to(cwd))] = matches
                    
            except (UnicodeDecodeError, PermissionError):
                continue
    
    return results

@mcp.resource("file://{path}")
async def get_file_content(path: str) -> str:
    """Get the content of a file"""
    try:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        return file_path.read_text(encoding='utf-8')
    except Exception as e:
        raise RuntimeError(f"Failed to read file: {e}")

@mcp.resource("directory://{path}")
async def get_directory_listing(path: str) -> str:
    """Get a listing of files in a directory"""
    try:
        dir_path = Path(path)
        if not dir_path.exists() or not dir_path.is_dir():
            raise NotADirectoryError(f"Directory not found: {path}")
        
        files = []
        for item in sorted(dir_path.iterdir()):
            if item.is_file():
                files.append(f"📄 {item.name}")
            elif item.is_dir():
                files.append(f"📁 {item.name}/")
        
        return "\n".join(files)
    except Exception as e:
        raise RuntimeError(f"Failed to list directory: {e}")

# Server startup function
async def start_aider_mcp_server(port: int = 8000):
    """Start the aider MCP server"""
    import uvicorn
    
    config = uvicorn.Config(
        app=mcp.app,
        host="127.0.0.1",
        port=port,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(start_aider_mcp_server())
```

## Phase 3: Model Integration (Week 3)

### 3.1 Enhanced Model Class

**File: `aider/models.py` (modifications)**
```python
# Add imports at the top
from aider.mcp.manager import MCPManager
import asyncio

class Model(ModelSettings):
    def __init__(self, model, weak_model=None, editor_model=None, editor_edit_format=None, verbose=False):
        # ... existing initialization ...
        
        # MCP integration
        self.mcp_manager: Optional[MCPManager] = None
        self._mcp_agent = None
    
    def set_mcp_manager(self, mcp_manager: MCPManager):
        """Set the MCP manager for this model"""
        self.mcp_manager = mcp_manager
    
    async def _get_mcp_agent(self):
        """Get or create MCP-enhanced agent"""
        if self._mcp_agent is None and self.mcp_manager:
            self._mcp_agent = await self.mcp_manager.create_enhanced_agent(self.name)
        return self._mcp_agent
    
    def _inject_mcp_context(self, messages: List[dict], mcp_context: dict) -> List[dict]:
        """Inject MCP context into messages"""
        if not mcp_context:
            return messages
        
        # Create context message
        context_parts = []
        
        if mcp_context.get("mcp_resources"):
            context_parts.append("## Available MCP Resources:")
            for resource in mcp_context["mcp_resources"]:
                context_parts.append(f"- {resource['name']}: {resource['uri']}")
        
        if mcp_context.get("mcp_tools"):
            context_parts.append("\n## Available MCP Tools:")
            for tool in mcp_context["mcp_tools"]:
                context_parts.append(f"- {tool['name']}: {tool['description']}")
        
        if context_parts:
            context_message = {
                "role": "system",
                "content": "\n".join(context_parts)
            }
            
            # Insert context after system message if it exists, otherwise at the beginning
            if messages and messages[0].get("role") == "system":
                messages.insert(1, context_message)
            else:
                messages.insert(0, context_message)
        
        return messages
    
    async def send_completion_with_mcp(self, messages, functions=None, stream=False, temperature=None):
        """Enhanced completion with MCP support"""
        if not self.mcp_manager:
            # Fallback to regular completion
            return self.send_completion(messages, functions, stream, temperature)
        
        try:
            # Get MCP context
            query = ""
            if messages:
                # Use the last user message as context query
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        query = msg.get("content", "")
                        break
            
            mcp_context = await self.mcp_manager.get_context_for_model(query)
            
            # Get MCP agent
            agent = await self._get_mcp_agent()
            
            if agent:
                # Use Pydantic AI agent with MCP support
                enhanced_messages = self._inject_mcp_context(messages, mcp_context)
                
                # Convert to Pydantic AI format and run
                result = await agent.run(enhanced_messages[-1]["content"])
                
                # Convert back to expected format
                return self._convert_agent_response(result)
            else:
                # Fallback: inject context and use regular completion
                enhanced_messages = self._inject_mcp_context(messages, mcp_context)
                return self.send_completion(enhanced_messages, functions, stream, temperature)
                
        except Exception as e:
            if self.verbose:
                print(f"MCP completion error: {e}")
            # Fallback to regular completion
            return self.send_completion(messages, functions, stream, temperature)
    
    def _convert_agent_response(self, agent_result):
        """Convert Pydantic AI agent result to expected format"""
        # This is a simplified conversion - may need adjustment based on actual response format
        class MockResponse:
            def __init__(self, content):
                self.choices = [MockChoice(content)]
        
        class MockChoice:
            def __init__(self, content):
                self.message = MockMessage(content)
        
        class MockMessage:
            def __init__(self, content):
                self.content = str(agent_result)
        
        return None, MockResponse(agent_result)  # hash, response format
```

### 3.2 Coder Integration

**File: `aider/coders/base_coder.py` (modifications)**
```python
# Add MCP support to base coder
class Coder:
    def __init__(self, main_model, io, repo, **kwargs):
        # ... existing initialization ...
        
        # MCP integration
        self.mcp_manager = kwargs.get('mcp_manager')
        if self.mcp_manager and hasattr(main_model, 'set_mcp_manager'):
            main_model.set_mcp_manager(self.mcp_manager)
    
    async def send_with_mcp(self, messages, functions=None, stream=None):
        """Send messages with MCP support if available"""
        if hasattr(self.main_model, 'send_completion_with_mcp'):
            return await self.main_model.send_completion_with_mcp(
                messages, functions, stream
            )
        else:
            return self.main_model.send_completion(messages, functions, stream)
```

## Phase 4: Configuration and CLI (Week 4)

### 4.1 Main Entry Point Integration

**File: `aider/main.py` (modifications)**
```python
# Add imports
from aider.mcp.manager import MCPManager, MCPServerConfig, load_mcp_config
from aider.mcp.servers.aider_tools import start_aider_mcp_server
import asyncio
import threading

async def setup_mcp_integration(args, io):
    """Setup MCP integration based on CLI arguments"""
    if not (args.mcp_servers or args.mcp_config or args.enable_aider_mcp_server):
        return None
    
    mcp_manager = MCPManager(io)
    server_configs = []
    
    # Load from config file
    if args.mcp_config:
        config_path = Path(args.mcp_config)
        server_configs.extend(load_mcp_config(config_path))
    
    # Add servers from CLI args
    if args.mcp_servers:
        for server_spec in args.mcp_servers:
            parts = server_spec.split(':', 2)
            if len(parts) >= 2:
                name, transport = parts[0], parts[1]
                command = parts[2].split() if len(parts) > 2 else None
                
                config = MCPServerConfig(
                    name=name,
                    transport=transport,
                    command=command
                )
                server_configs.append(config)
    
    # Start built-in aider MCP server if requested
    if args.enable_aider_mcp_server:
        # Start server in background thread
        def start_server():
            asyncio.run(start_aider_mcp_server(args.mcp_server_port))
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Add localhost server to configs
        localhost_config = MCPServerConfig(
            name="aider-tools",
            transport="websocket",
            url=f"ws://localhost:{args.mcp_server_port}/mcp"
        )
        server_configs.append(localhost_config)
    
    # Connect to all configured servers
    if server_configs:
        connected = await mcp_manager.connect_servers(server_configs)
        if connected:
            io.tool_output(f"MCP integration enabled with {len(mcp_manager.sessions)} servers")
            return mcp_manager
        else:
            io.tool_warning("No MCP servers could be connected")
    
    return None

def main(argv=None, input=None, output=None, force_git_root=None, return_coder=False):
    # ... existing main function ...
    
    # Add MCP setup after model creation but before coder creation
    mcp_manager = None
    if not return_coder:  # Skip MCP in test/return mode
        try:
            mcp_manager = asyncio.run(setup_mcp_integration(args, io))
        except Exception as e:
            io.tool_warning(f"MCP setup failed: {e}")
    
    # Pass MCP manager to coder creation
    try:
        coder = Coder.create(
            main_model=main_model,
            # ... existing args ...
            mcp_manager=mcp_manager,  # Add this
        )
    except UnknownEditFormat as err:
        # ... existing error handling ...
    
    # Cleanup MCP connections on exit
    if mcp_manager:
        import atexit
        atexit.register(lambda: asyncio.run(mcp_manager.disconnect_all()))
```

### 4.2 Example Configuration File

**File: `examples/mcp-config.json`**
```json
{
  "servers": [
    {
      "name": "filesystem",
      "transport": "stdio",
      "command": ["mcp-server-filesystem", "/path/to/allowed/directory"],
      "enabled": true
    },
    {
      "name": "web-search",
      "transport": "stdio", 
      "command": ["mcp-server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your-api-key-here"
      },
      "enabled": true
    },
    {
      "name": "database",
      "transport": "websocket",
      "url": "ws://localhost:9000/mcp",
      "enabled": false
    }
  ]
}
```

## Testing Strategy

### Unit Tests
```python
# tests/test_mcp_integration.py
import pytest
import asyncio
from aider.mcp.manager import MCPManager, MCPServerConfig

@pytest.mark.asyncio
async def test_mcp_manager_connection():
    """Test MCP manager can connect to servers"""
    manager = MCPManager()
    
    # Test with mock server config
    config = MCPServerConfig(
        name="test",
        transport="stdio",
        command=["echo", "test"]
    )
    
    # This would need proper mocking
    # connected = await manager.connect_servers([config])
    # assert connected

@pytest.mark.asyncio 
async def test_mcp_context_injection():
    """Test MCP context is properly injected into messages"""
    # Test context injection logic
    pass
```

### Integration Tests
```python
# tests/test_mcp_end_to_end.py
def test_mcp_cli_args():
    """Test MCP CLI arguments are parsed correctly"""
    pass

def test_mcp_with_coder():
    """Test coder works with MCP integration"""
    pass
```

## Documentation

### User Documentation
- Add MCP section to main README
- Create `docs/mcp-integration.md` with setup instructions
- Add examples of MCP server configurations
- Document built-in aider MCP tools

### Developer Documentation  
- Document MCP architecture in codebase
- Add docstrings to all MCP-related classes
- Create contribution guide for adding new MCP tools

## Migration and Compatibility

### Backward Compatibility
- All MCP features are opt-in via CLI flags
- Existing functionality unchanged when MCP disabled
- Graceful fallback when MCP servers unavailable

### Configuration Migration
- Provide migration script for existing users
- Support both old and new configuration formats during transition
- Clear deprecation warnings for old patterns

## Performance Considerations

### Async Integration
- Use asyncio for all MCP operations to avoid blocking
- Implement connection pooling for multiple MCP servers
- Add timeouts and retry logic for MCP calls

### Caching
- Cache MCP server capabilities and resources
- Implement smart context selection to avoid overwhelming LLMs
- Add configuration for context size limits

## Security Considerations

### Sandboxing
- Validate all MCP server configurations
- Implement allowlist for MCP server commands
- Sanitize all data from MCP servers before passing to LLMs

### Authentication
- Support authentication for MCP servers
- Secure storage of API keys and credentials
- Audit logging for MCP operations

## Future Enhancements

### Phase 5: Advanced Features
- Smart context selection using embeddings
- MCP server discovery and marketplace integration
- Visual MCP server management interface
- Performance monitoring and analytics

### Phase 6: Ecosystem Integration
- Integration with popular MCP servers (GitHub, Slack, etc.)
- Custom MCP server templates for common use cases
- Community MCP server registry
- Plugin system for third-party MCP integrations

## Success Metrics

### Technical Metrics
- MCP server connection success rate > 95%
- Context injection latency < 100ms
- Zero regression in existing functionality
- Test coverage > 90% for MCP code

### User Experience Metrics
- Easy setup (< 5 minutes for basic configuration)
- Clear error messages and troubleshooting
- Comprehensive documentation and examples
- Positive community feedback

## Timeline Summary

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1 | Core MCP Integration | MCP Manager, CLI args, basic connectivity |
| 2 | Built-in FastMCP Server | Aider tools server, file analysis, command execution |
| 3 | Model Integration | Enhanced Model class, Pydantic AI integration |
| 4 | Configuration & Polish | Config files, documentation, testing |

## Conclusion

This plan provides a comprehensive roadmap for integrating MCP client capabilities into aider using modern, well-supported libraries (Pydantic AI and FastMCP). The phased approach ensures incremental progress while maintaining backward compatibility and code quality.

The integration will significantly enhance aider's capabilities by providing access to external tools, resources, and context through the standardized MCP protocol, making it a more powerful and versatile AI coding assistant.