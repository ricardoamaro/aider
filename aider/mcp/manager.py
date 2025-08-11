import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

try:
    from pydantic_ai.mcp import MCPClientSession
    from pydantic_ai import Agent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    MCPClientSession = None
    Agent = None

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
        self.sessions: Dict[str, Any] = {}
        self.agents: Dict[str, Any] = {}
        self.available_tools: List[Any] = []
        self.available_resources: List[Any] = []
        self._connected = False
        
        if not MCP_AVAILABLE:
            if self.io:
                self.io.tool_warning(
                    "MCP dependencies not available. Install with: pip install pydantic-ai[mcp] fastmcp"
                )
    
    async def connect_servers(self, configs: List[MCPServerConfig]):
        """Connect to configured MCP servers"""
        if not MCP_AVAILABLE:
            if self.io:
                self.io.tool_error("MCP dependencies not installed")
            return False
            
        for config in configs:
            if not config.enabled:
                continue
                
            try:
                if self.io:
                    self.io.tool_output(f"Connecting to MCP server: {config.name}")
                
                # Create session based on transport type
                if config.transport == "stdio" and config.command:
                    session = MCPClientSession(
                        transport="stdio",
                        command=config.command,
                        env=config.env or {}
                    )
                elif config.transport == "websocket" and config.url:
                    session = MCPClientSession(
                        transport="websocket",
                        url=config.url,
                        env=config.env or {}
                    )
                else:
                    if self.io:
                        self.io.tool_error(
                            f"Invalid transport configuration for {config.name}: "
                            f"transport={config.transport}, command={config.command}, url={config.url}"
                        )
                    continue
                
                await session.connect()
                self.sessions[config.name] = session
                
                # Get available tools and resources
                try:
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
                        self.io.tool_warning(f"Could not list capabilities for {config.name}: {e}")
                    # Still consider the connection successful
                    
            except Exception as e:
                if self.io:
                    self.io.tool_error(f"Failed to connect to {config.name}: {e}")
                continue
        
        self._connected = len(self.sessions) > 0
        return self._connected
    
    async def get_context_for_model(self, query: str = "") -> Dict[str, Any]:
        """Get relevant context from MCP servers for model input"""
        if not self._connected or not MCP_AVAILABLE:
            return {}
        
        context = {
            "mcp_resources": [],
            "mcp_tools": [],
            "mcp_context": ""
        }
        
        # Collect relevant resources
        for session_name, session in self.sessions.items():
            try:
                # Get resources that might be relevant to the query
                resources = await session.list_resources()
                for resource in resources:
                    if self._is_resource_relevant(resource, query):
                        try:
                            content = await session.read_resource(resource.uri)
                            context["mcp_resources"].append({
                                "uri": resource.uri,
                                "name": resource.name,
                                "content": content,
                                "server": session_name
                            })
                        except Exception as e:
                            if self.io:
                                self.io.tool_warning(f"Error reading resource {resource.uri}: {e}")
            except Exception as e:
                if self.io:
                    self.io.tool_warning(f"Error getting MCP resources from {session_name}: {e}")
        
        # Add available tools info
        context["mcp_tools"] = [
            {
                "name": getattr(tool, 'name', str(tool)),
                "description": getattr(tool, 'description', ''),
                "server": getattr(tool, 'server', 'unknown')
            }
            for tool in self.available_tools
        ]
        
        return context
    
    def _is_resource_relevant(self, resource, query: str) -> bool:
        """Simple relevance check - can be enhanced with embeddings"""
        if not query:
            return True
        
        query_lower = query.lower()
        resource_name = getattr(resource, 'name', '')
        resource_desc = getattr(resource, 'description', '')
        
        return (
            query_lower in resource_name.lower() or
            query_lower in resource_desc.lower()
        )
    
    async def create_enhanced_agent(self, model_name: str) -> Optional[Any]:
        """Create Pydantic AI agent with MCP capabilities"""
        if not self._connected or not MCP_AVAILABLE:
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
        if not MCP_AVAILABLE:
            return
            
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
    
    def is_available(self) -> bool:
        """Check if MCP functionality is available"""
        return MCP_AVAILABLE
    
    def is_connected(self) -> bool:
        """Check if any MCP servers are connected"""
        return self._connected


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


def parse_mcp_server_spec(server_spec: str) -> Optional[MCPServerConfig]:
    """Parse MCP server specification from CLI argument
    
    Format: name:transport:command_or_url
    Examples:
        filesystem:stdio:mcp-server-filesystem /path
        web:websocket:ws://localhost:8000/mcp
    """
    parts = server_spec.split(':', 2)
    if len(parts) < 2:
        return None
    
    name, transport = parts[0], parts[1]
    
    if transport == "stdio":
        if len(parts) < 3:
            return None
        command = parts[2].split()
        return MCPServerConfig(
            name=name,
            transport=transport,
            command=command
        )
    elif transport == "websocket":
        if len(parts) < 3:
            return None
        url = parts[2]
        return MCPServerConfig(
            name=name,
            transport=transport,
            url=url
        )
    else:
        return None