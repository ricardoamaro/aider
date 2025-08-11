"""
MCP client wrapper for aider integration.

This module provides a simplified interface for working with MCP clients
within aider's architecture.
"""

import asyncio
from typing import Optional, Dict, Any, List

from .manager import MCPManager, MCPServerConfig, parse_mcp_server_spec, load_mcp_config
from .config import MCPConfigurationManager, load_mcp_configuration


class MCPClient:
    """Simplified MCP client interface for aider integration"""
    
    def __init__(self, io=None):
        self.manager = MCPManager(io)
        self.io = io
    
    async def setup_from_args(self, args, git_root: str = None) -> bool:
        """Setup MCP integration from command line arguments"""
        if not self.manager.is_available():
            if self.io:
                self.io.tool_warning(
                    "MCP functionality not available. Install with: pip install pydantic-ai[mcp] fastmcp"
                )
            return False
        
        server_configs = []
        
        # Load from comprehensive configuration system
        try:
            config_manager = MCPConfigurationManager(git_root)
            
            # Load from specific config file if provided
            if hasattr(args, 'mcp_config') and args.mcp_config:
                from pathlib import Path
                config_path = Path(args.mcp_config)
                if config_path.exists():
                    # Load specific file
                    file_config = config_manager._load_config_file(config_path)
                    server_configs.extend(file_config.servers)
                else:
                    if self.io:
                        self.io.tool_error(f"MCP config file not found: {config_path}")
            else:
                # Load from standard configuration hierarchy
                full_config = config_manager.load_configuration()
                
                # Validate configuration
                issues = config_manager.validate_configuration(full_config)
                if issues:
                    if self.io:
                        self.io.tool_warning("MCP configuration issues found:")
                        for issue in issues:
                            self.io.tool_warning(f"  - {issue}")
                
                # Use servers from configuration
                server_configs.extend(full_config.servers)
                
                if self.io and full_config.servers:
                    self.io.tool_output(f"Loaded {len(full_config.servers)} MCP server(s) from configuration")
        
        except Exception as e:
            if self.io:
                self.io.tool_warning(f"Failed to load MCP configuration: {e}")
        
        # Add servers from CLI args (these override config file)
        if hasattr(args, 'mcp_servers') and args.mcp_servers:
            cli_configs = []
            for server_spec in args.mcp_servers:
                config = parse_mcp_server_spec(server_spec)
                if config:
                    cli_configs.append(config)
                elif self.io:
                    self.io.tool_error(f"Invalid MCP server specification: {server_spec}")
            
            # CLI servers override config file servers with same name
            for cli_config in cli_configs:
                # Remove any existing server with same name
                server_configs = [s for s in server_configs if s.name != cli_config.name]
                server_configs.append(cli_config)
        
        # Handle built-in aider MCP server
        if hasattr(args, 'enable_aider_mcp_server') and args.enable_aider_mcp_server:
            try:
                from .servers.aider_tools import is_server_available, start_aider_mcp_server
                
                if not is_server_available():
                    if self.io:
                        self.io.tool_warning(
                            "Built-in aider MCP server not available. "
                            "Install with: pip install fastmcp uvicorn"
                        )
                else:
                    # Start server in background thread
                    import threading
                    
                    def start_server():
                        try:
                            port = getattr(args, 'mcp_server_port', 8000)
                            asyncio.run(start_aider_mcp_server(port))
                        except Exception as e:
                            if self.io:
                                self.io.tool_error(f"Failed to start aider MCP server: {e}")
                    
                    server_thread = threading.Thread(target=start_server, daemon=True)
                    server_thread.start()
                    
                    # Give server time to start
                    await asyncio.sleep(1)
                    
                    # Add localhost server to configs
                    port = getattr(args, 'mcp_server_port', 8000)
                    localhost_config = MCPServerConfig(
                        name="aider-tools",
                        transport="websocket",
                        url=f"ws://localhost:{port}/mcp"
                    )
                    server_configs.append(localhost_config)
                    
                    if self.io:
                        self.io.tool_output(f"Started built-in aider MCP server on port {port}")
                        
            except ImportError as e:
                if self.io:
                    self.io.tool_warning(f"Could not start built-in MCP server: {e}")
        
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