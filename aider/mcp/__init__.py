"""
MCP (Model Context Protocol) integration for aider.

This module provides MCP client capabilities, allowing aider to connect to
external MCP servers and leverage their tools and resources.
"""

from .manager import MCPManager, MCPServerConfig, load_mcp_config, parse_mcp_server_spec
from .client import MCPClient, create_example_config

__all__ = [
    "MCPManager",
    "MCPServerConfig", 
    "MCPClient",
    "load_mcp_config",
    "parse_mcp_server_spec",
    "create_example_config",
]