"""
Configuration management for MCP integration.

This module provides comprehensive configuration loading, validation,
and management for MCP servers and settings.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field

from pydantic import BaseModel, ValidationError, validator

from .manager import MCPServerConfig


class MCPSettings(BaseModel):
    """Global MCP settings and preferences"""
    
    enabled: bool = True
    timeout: int = 30  # Connection timeout in seconds
    max_retries: int = 3
    context_limit: int = 10000  # Max characters in MCP context
    cache_ttl: int = 300  # Cache TTL in seconds
    log_level: str = "INFO"
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()


class MCPConfiguration(BaseModel):
    """Complete MCP configuration"""
    
    settings: MCPSettings = field(default_factory=MCPSettings)
    servers: List[MCPServerConfig] = field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


@dataclass
class ConfigurationPaths:
    """Standard configuration file paths"""
    
    # Global configuration (user home)
    global_config: Path = Path.home() / ".aider" / "mcp-config.json"
    
    # Project-specific configuration (git root)
    project_config: Optional[Path] = None
    
    # Local configuration (current directory)
    local_config: Path = Path.cwd() / ".aider.mcp.json"
    
    # Environment-specific configuration
    env_config: Optional[Path] = None
    
    def __post_init__(self):
        # Set environment config if specified
        env_path = os.environ.get('AIDER_MCP_CONFIG')
        if env_path:
            self.env_config = Path(env_path)


class MCPConfigurationManager:
    """Manages MCP configuration loading, validation, and merging"""
    
    def __init__(self, git_root: Optional[str] = None):
        self.git_root = git_root
        self.paths = ConfigurationPaths()
        
        if git_root:
            self.paths.project_config = Path(git_root) / ".aider.mcp.json"
        
        self._config_cache: Optional[MCPConfiguration] = None
        self._cache_timestamp: float = 0
    
    def load_configuration(self, force_reload: bool = False) -> MCPConfiguration:
        """Load and merge configuration from all sources"""
        
        # Check cache first
        if not force_reload and self._config_cache and self._is_cache_valid():
            return self._config_cache
        
        # Start with default configuration
        config = MCPConfiguration()
        
        # Load configurations in order of precedence (lowest to highest)
        config_files = [
            self.paths.global_config,
            self.paths.project_config,
            self.paths.local_config,
            self.paths.env_config
        ]
        
        for config_file in config_files:
            if config_file and config_file.exists():
                try:
                    file_config = self._load_config_file(config_file)
                    config = self._merge_configurations(config, file_config)
                except Exception as e:
                    print(f"Warning: Failed to load config from {config_file}: {e}")
        
        # Cache the result
        self._config_cache = config
        self._cache_timestamp = os.path.getmtime(self._get_newest_config_file())
        
        return config
    
    def _load_config_file(self, config_path: Path) -> MCPConfiguration:
        """Load configuration from a single file"""
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            
            # Validate and create configuration
            return MCPConfiguration(**data)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {config_path}: {e}")
        except ValidationError as e:
            raise ValueError(f"Invalid configuration in {config_path}: {e}")
    
    def _merge_configurations(self, base: MCPConfiguration, override: MCPConfiguration) -> MCPConfiguration:
        """Merge two configurations, with override taking precedence"""
        
        # Merge settings
        merged_settings = base.settings.model_dump()
        merged_settings.update(override.settings.model_dump(exclude_unset=True))
        
        # Merge servers (override completely replaces if present)
        merged_servers = override.servers if override.servers else base.servers
        
        return MCPConfiguration(
            settings=MCPSettings(**merged_settings),
            servers=merged_servers
        )
    
    def _is_cache_valid(self) -> bool:
        """Check if cached configuration is still valid"""
        try:
            newest_file_time = os.path.getmtime(self._get_newest_config_file())
            return newest_file_time <= self._cache_timestamp
        except (OSError, TypeError):
            return False
    
    def _get_newest_config_file(self) -> str:
        """Get the path of the most recently modified config file"""
        config_files = [
            self.paths.global_config,
            self.paths.project_config,
            self.paths.local_config,
            self.paths.env_config
        ]
        
        existing_files = [f for f in config_files if f and f.exists()]
        if not existing_files:
            return str(self.paths.global_config)  # Default
        
        return str(max(existing_files, key=lambda f: os.path.getmtime(f)))
    
    def save_configuration(self, config: MCPConfiguration, scope: str = "project") -> Path:
        """Save configuration to appropriate file"""
        
        if scope == "global":
            config_path = self.paths.global_config
        elif scope == "project" and self.paths.project_config:
            config_path = self.paths.project_config
        elif scope == "local":
            config_path = self.paths.local_config
        else:
            raise ValueError(f"Invalid scope: {scope}")
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save configuration
        with open(config_path, 'w') as f:
            json.dump(config.model_dump(), f, indent=2, default=str)
        
        # Invalidate cache
        self._config_cache = None
        
        return config_path
    
    def validate_configuration(self, config: MCPConfiguration) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Validate server configurations
        for i, server in enumerate(config.servers):
            server_issues = self._validate_server_config(server, i)
            issues.extend(server_issues)
        
        # Validate settings
        if config.settings.timeout <= 0:
            issues.append("Settings: timeout must be positive")
        
        if config.settings.max_retries < 0:
            issues.append("Settings: max_retries cannot be negative")
        
        if config.settings.context_limit <= 0:
            issues.append("Settings: context_limit must be positive")
        
        return issues
    
    def _validate_server_config(self, server: MCPServerConfig, index: int) -> List[str]:
        """Validate a single server configuration"""
        issues = []
        prefix = f"Server {index} ({server.name})"
        
        # Validate transport-specific requirements
        if server.transport == "stdio":
            if not server.command:
                issues.append(f"{prefix}: stdio transport requires command")
            elif not isinstance(server.command, list) or not server.command:
                issues.append(f"{prefix}: command must be a non-empty list")
        
        elif server.transport == "websocket":
            if not server.url:
                issues.append(f"{prefix}: websocket transport requires url")
            elif not server.url.startswith(('ws://', 'wss://')):
                issues.append(f"{prefix}: websocket url must start with ws:// or wss://")
        
        else:
            issues.append(f"{prefix}: unsupported transport '{server.transport}'")
        
        # Validate name
        if not server.name or not server.name.strip():
            issues.append(f"{prefix}: name cannot be empty")
        
        return issues
    
    def create_example_configuration(self) -> MCPConfiguration:
        """Create an example configuration with common servers"""
        return MCPConfiguration(
            settings=MCPSettings(
                enabled=True,
                timeout=30,
                max_retries=3,
                context_limit=10000,
                log_level="INFO"
            ),
            servers=[
                MCPServerConfig(
                    name="filesystem",
                    transport="stdio",
                    command=["mcp-server-filesystem", "/path/to/allowed/directory"],
                    enabled=True
                ),
                MCPServerConfig(
                    name="web-search",
                    transport="stdio",
                    command=["mcp-server-brave-search"],
                    env={"BRAVE_API_KEY": "your-api-key-here"},
                    enabled=False
                ),
                MCPServerConfig(
                    name="database",
                    transport="websocket",
                    url="ws://localhost:9000/mcp",
                    enabled=False
                ),
                MCPServerConfig(
                    name="aider-tools",
                    transport="websocket",
                    url="ws://localhost:8000/mcp",
                    enabled=True
                )
            ]
        )


def get_default_config_manager(git_root: Optional[str] = None) -> MCPConfigurationManager:
    """Get the default configuration manager instance"""
    return MCPConfigurationManager(git_root)


def load_mcp_configuration(git_root: Optional[str] = None) -> MCPConfiguration:
    """Convenience function to load MCP configuration"""
    manager = get_default_config_manager(git_root)
    return manager.load_configuration()


def validate_mcp_configuration(config: MCPConfiguration) -> List[str]:
    """Convenience function to validate MCP configuration"""
    manager = get_default_config_manager()
    return manager.validate_configuration(config)