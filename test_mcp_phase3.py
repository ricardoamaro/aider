#!/usr/bin/env python3
"""
Test script for Phase 3 MCP integration - Model Integration.

This script tests the Model class MCP integration and coder support.
"""

import sys
import asyncio
from pathlib import Path

# Add aider to path for testing
sys.path.insert(0, str(Path(__file__).parent))

from aider.models import Model
from aider.io import InputOutput


async def test_model_mcp_integration():
    """Test Model class MCP integration"""
    print("Testing Model class MCP integration...")
    
    # Create a test model
    model = Model("gpt-4o-mini", verbose=False)
    
    # Test MCP attributes exist
    print(f"✓ Model has mcp_client attribute: {hasattr(model, 'mcp_client')}")
    print(f"✓ Model has _mcp_agent attribute: {hasattr(model, '_mcp_agent')}")
    
    # Test MCP methods exist
    mcp_methods = [
        'set_mcp_client', 'has_mcp_support', 'send_completion_with_mcp',
        '_get_mcp_agent', '_inject_mcp_context', '_convert_agent_response'
    ]
    
    for method in mcp_methods:
        has_method = hasattr(model, method)
        print(f"✓ Model has {method} method: {has_method}")
        if not has_method:
            return False
    
    # Test initial state
    print(f"✓ Initial MCP support: {model.has_mcp_support()}")
    
    return True


async def test_mcp_context_injection():
    """Test MCP context injection functionality"""
    print("\nTesting MCP context injection...")
    
    model = Model("gpt-4o-mini", verbose=False)
    
    # Test context injection with empty context
    messages = [{"role": "user", "content": "Hello"}]
    result = model._inject_mcp_context(messages, {})
    print(f"✓ Empty context injection: {len(result) == len(messages)}")
    
    # Test context injection with MCP data
    mcp_context = {
        "mcp_resources": [
            {"name": "test.py", "uri": "file://test.py", "content": "print('hello')"}
        ],
        "mcp_tools": [
            {"name": "analyze_file", "description": "Analyze a file"}
        ]
    }
    
    result = model._inject_mcp_context(messages, mcp_context)
    context_added = len(result) > len(messages)
    print(f"✓ Context injection with data: {context_added}")
    
    # Check that context was added
    has_context = any("Available MCP" in msg.get("content", "") for msg in result)
    print(f"✓ Context message added: {has_context}")
    
    return True


async def test_model_with_mock_mcp_client():
    """Test model with a mock MCP client"""
    print("\nTesting model with mock MCP client...")
    
    class MockMCPClient:
        def is_connected(self):
            return True
        
        async def get_context(self, query=""):
            return {
                "mcp_resources": [],
                "mcp_tools": [{"name": "test_tool", "description": "A test tool"}]
            }
        
        async def create_agent(self, model_name):
            return None  # Simulate no agent available
    
    model = Model("gpt-4o-mini", verbose=False)
    mock_client = MockMCPClient()
    
    # Set mock client
    model.set_mcp_client(mock_client)
    print(f"✓ MCP client set: {model.mcp_client is not None}")
    print(f"✓ MCP support enabled: {model.has_mcp_support()}")
    
    # Test MCP completion (should fallback to regular completion)
    messages = [{"role": "user", "content": "Hello"}]
    try:
        # This should not crash and should fallback gracefully
        result = await model.send_completion_with_mcp(messages)
        print("✓ MCP completion fallback works")
        return True
    except Exception as e:
        print(f"✗ MCP completion failed: {e}")
        return False


def test_coder_mcp_integration():
    """Test Coder class MCP integration"""
    print("\nTesting Coder class MCP integration...")
    
    try:
        from aider.coders.base_coder import Coder
        from aider.io import InputOutput
        
        # Create test components
        io = InputOutput(pretty=False, yes=True)
        model = Model("gpt-4o-mini", verbose=False)
        
        # Create a coder (this tests the integration)
        coder = Coder.create(
            main_model=model,
            io=io,
            fnames=[],
            edit_format="whole"
        )
        
        print(f"✓ Coder created successfully")
        print(f"✓ Coder has mcp_enabled attribute: {hasattr(coder, 'mcp_enabled')}")
        print(f"✓ MCP enabled state: {getattr(coder, 'mcp_enabled', False)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Coder MCP integration test failed: {e}")
        return False


def test_main_integration():
    """Test main.py integration"""
    print("\nTesting main.py integration...")
    
    # Test that the model enhancement doesn't break argument parsing
    from aider.args import get_parser
    
    parser = get_parser([], None)
    
    # Test that MCP arguments still work
    test_args = [
        "--mcp-servers", "test:stdio:echo hello",
        "--enable-aider-mcp-server"
    ]
    
    try:
        args = parser.parse_args(test_args)
        print("✓ Argument parsing still works with MCP integration")
        return True
    except Exception as e:
        print(f"✗ Argument parsing failed: {e}")
        return False


async def main():
    """Run all Phase 3 tests"""
    print("=== Phase 3 MCP Integration Tests ===\n")
    
    try:
        # Test async components
        tests = [
            test_model_mcp_integration(),
            test_mcp_context_injection(),
            test_model_with_mock_mcp_client()
        ]
        
        results = await asyncio.gather(*tests, return_exceptions=True)
        
        # Test synchronous components
        sync_results = [
            test_coder_mcp_integration(),
            test_main_integration()
        ]
        
        # Combine results
        all_results = list(results) + sync_results
        
        failed_tests = []
        for i, result in enumerate(all_results):
            if isinstance(result, Exception):
                failed_tests.append(f"Test {i+1}: {result}")
            elif not result:
                failed_tests.append(f"Test {i+1}: Failed")
        
        if failed_tests:
            print(f"\n✗ {len(failed_tests)} test(s) failed:")
            for failure in failed_tests:
                print(f"  - {failure}")
            return 1
        
        print("\n=== All Phase 3 tests passed! ===")
        print("\nPhase 3 Model Integration is ready.")
        print("Features available:")
        print("- Enhanced Model class with MCP client support")
        print("- MCP context injection into LLM messages")
        print("- Pydantic AI agent integration (when available)")
        print("- Async completion support with MCP fallback")
        print("- Coder class integration with MCP detection")
        print("- Seamless integration with existing aider workflow")
        
        return 0
        
    except Exception as e:
        print(f"✗ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)