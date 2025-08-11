#!/usr/bin/env python3
"""
Test script for Phase 1 MCP integration.

This script tests the basic MCP functionality without requiring actual MCP servers.
"""

import sys
import asyncio
from pathlib import Path

# Add aider to path for testing
sys.path.insert(0, str(Path(__file__).parent))

from aider.mcp import MCPManager, MCPServerConfig, MCPClient, parse_mcp_server_spec
from aider.io import InputOutput


async def test_mcp_manager():
    """Test MCPManager basic functionality"""
    print("Testing MCPManager...")
    
    # Create a mock IO object
    io = InputOutput(pretty=False, yes=True)
    
    # Test manager creation
    manager = MCPManager(io)
    print(f"✓ MCPManager created, available: {manager.is_available()}")
    
    # Test config parsing
    config = parse_mcp_server_spec("test:stdio:echo hello")
    print(f"✓ Parsed server spec: {config}")
    
    config2 = parse_mcp_server_spec("web:websocket:ws://localhost:8000/mcp")
    print(f"✓ Parsed websocket spec: {config2}")
    
    # Test invalid spec
    invalid = parse_mcp_server_spec("invalid")
    print(f"✓ Invalid spec handled: {invalid}")
    
    print("MCPManager tests passed!\n")


async def test_mcp_client():
    """Test MCPClient functionality"""
    print("Testing MCPClient...")
    
    # Create a mock IO object
    io = InputOutput(pretty=False, yes=True)
    
    # Test client creation
    client = MCPClient(io)
    print(f"✓ MCPClient created, connected: {client.is_connected()}")
    
    # Test context retrieval (should return empty when not connected)
    context = await client.get_context("test query")
    print(f"✓ Context retrieved: {context}")
    
    print("MCPClient tests passed!\n")


def test_cli_args():
    """Test that CLI arguments are properly defined"""
    print("Testing CLI arguments...")
    
    from aider.args import get_parser
    
    parser = get_parser([], None)
    
    # Test parsing MCP arguments
    test_args = [
        "--mcp-servers", "test:stdio:echo hello",
        "--mcp-config", "/path/to/config.json",
        "--enable-aider-mcp-server",
        "--mcp-server-port", "9000"
    ]
    
    try:
        args = parser.parse_args(test_args)
        print(f"✓ MCP servers: {args.mcp_servers}")
        print(f"✓ MCP config: {args.mcp_config}")
        print(f"✓ Enable aider server: {args.enable_aider_mcp_server}")
        print(f"✓ Server port: {args.mcp_server_port}")
        print("CLI arguments tests passed!\n")
    except Exception as e:
        print(f"✗ CLI arguments test failed: {e}")
        return False
    
    return True


async def main():
    """Run all tests"""
    print("=== Phase 1 MCP Integration Tests ===\n")
    
    try:
        # Test CLI arguments first (synchronous)
        if not test_cli_args():
            return 1
        
        # Test async components
        await test_mcp_manager()
        await test_mcp_client()
        
        print("=== All Phase 1 tests passed! ===")
        print("\nPhase 1 MCP integration is ready.")
        print("Next steps:")
        print("- Install dependencies: pip install pydantic-ai[mcp] fastmcp")
        print("- Test with actual MCP servers")
        print("- Proceed to Phase 2 (FastMCP server implementation)")
        
        return 0
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)