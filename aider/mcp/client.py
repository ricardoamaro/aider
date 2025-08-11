"""
MCP client wrapper for aider integration.

This module provides a simplified interface for working with MCP clients
within aider's architecture.
"""

import asyncio
from typing import Optional, Dict, Any, List

from .manager import MCPManager, MCPServerConfig, parse_mcp_server_spec, load_mcp_config


class MCPClient:
    """Simplified MCP client interface for aider integration"""
    
    def __init__(self, io=None):
        self.manager = MCPManager(io)
        self.io = io
    
    async def setup_from_args(self, args) -> bool:
        """Setup MCP integration from command line arguments"""
        if not self.manager.is_available():
            if self.io:
                self.io.tool_warning(
                    "MCP functionality not available. Install with: pip install pydantic-ai[mcp] fastmcp"
                )
            return False
        
        server_configs = []
        
        # Load from config file
        if hasattr(args, 'mcp_config') and args.mcp_config:
            from pathlib import Path
            config_path = Path(args.mcp_config)
            server_configs.extend(load_mcp_config(config_path))
        
        # Add servers from CLI args
        if hasattr(args, 'mcp_servers') and args.mcp_servers:
            for server_spec in args.mcp_servers:
                config = parse_mcp_server_spec(server_spec)
                if config:
                    server_configs.append(config)
                elif self.io:
                    self.io.tool_error(f"Invalid MCP server specification: {server_spec}")
        
        # TODO: Handle built-in aider MCP server in Phase 2
        if hasattr(args, 'enable_aider_mcp_server') and args.enable_aider_mcp_server:
            if self.io:
                self.io.tool_warning("Built-in aider MCP server not yet implemented (Phase 2)")
        
        # Connect to configured servers
        if server_configs:
            connected = await self.manager.connect_servers(server_configs)
            if connected and self.io:
                self.io.tool_output(f"MCP integration enabled with {len(self.manager.sessions)} servers")
            return connected
        
        return False
    
    async def get_context(self, query: str = "") -> Dict[str, Any]:
        """Get MCP context for model input"""
        return await self.manager.get_context_for_model(query)
    
    async def create_agent(self, model_name: str):
        """Create Pydantic AI agent with MCP capabilities"""
        return await self.manager.create_enhanced_agent(model_name)
    
    def is_connected(self) -> bool:
        """Check if MCP is connected and available"""
        return self.manager.is_connected()
    
    async def disconnect(self):
        """Disconnect from all MCP servers"""
        await self.manager.disconnect_all()


def create_example_config() -> Dict[str, Any]:
    """Create an example MCP configuration file content"""
    return {
        "servers": [
            {
                "name": "filesystem",
                "transport": "stdio",
                "command": ["mcp-server-filesystem", "/path/to/allowed/directory"],
                "enabled": True
            },
            {
                "name": "web-search",
                "transport": "stdio",
                "command": ["mcp-server-brave-search"],
                "env": {
                    "BRAVE_API_KEY": "your-api-key-here"
                },
                "enabled": False
            },
            {
                "name": "database",
                "transport": "websocket",
                "url": "ws://localhost:9000/mcp",
                "enabled": False
            }
        ]
    }