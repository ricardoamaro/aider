#!/usr/bin/env python3
"""
MCP Configuration Generator

This script helps generate MCP configuration files for aider.
"""

import json
import sys
from pathlib import Path

# Add aider to path
sys.path.insert(0, str(Path(__file__).parent))

from aider.mcp.config import MCPConfigurationManager


def main():
    """Generate example MCP configuration"""
    if len(sys.argv) > 1:
        output_path = Path(sys.argv[1])
    else:
        output_path = Path(".aider.mcp.json")
    
    # Create configuration manager
    manager = MCPConfigurationManager()
    
    # Generate example configuration
    config = manager.create_example_configuration()
    
    # Save to file
    try:
        saved_path = manager.save_configuration(config, scope="local")
        print(f"✓ Example MCP configuration saved to: {saved_path}")
        
        # Show validation results
        issues = manager.validate_configuration(config)
        if issues:
            print(f"⚠️  Configuration has {len(issues)} issues:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✓ Configuration is valid")
        
        print(f"\nTo use this configuration:")
        print(f"  aider  # Automatically loads {saved_path}")
        print(f"  aider --mcp-config {saved_path}")
        
    except Exception as e:
        print(f"✗ Failed to save configuration: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())