"""
Configuration types and utilities for autocode core modules.
"""

import yaml
import warnings
from pathlib import Path
from typing import Optional

from .types import (
    DocsConfig, 
    TestConfig, 
    GitConfig, 
    OpenCodeConfig, 
    CodeToDesignConfig, 
    TokenConfig,
    CheckConfig,
    DaemonConfig,
    ApiConfig,
    DocIndexConfig,
    AutocodeConfig
)


def find_config_file(start_path: Path) -> Optional[Path]:
    """Find autocode_config.yml by searching up the directory tree.
    
    Args:
        start_path: Starting directory to search from
        
    Returns:
        Path to autocode_config.yml if found, None otherwise
    """
    current = start_path.resolve()
    while current != current.parent:  # Until we reach filesystem root
        config_file = current / "autocode_config.yml"
        if config_file.exists():
            return config_file
        current = current.parent
    return None


def load_config(working_dir: Optional[Path] = None) -> AutocodeConfig:
    """Load configuration from autocode_config.yml.
    
    Searches up the directory tree starting from working_dir (or cwd) 
    until it finds autocode_config.yml.
    
    Args:
        working_dir: Directory to start search from (defaults to cwd)
        
    Returns:
        Loaded configuration with defaults
    """
    if working_dir is None:
        working_dir = Path.cwd()
    
    config_file = find_config_file(working_dir)
    
    if config_file is None:
        # Return default configuration if file doesn't exist
        return AutocodeConfig()
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        if not config_data:
            return AutocodeConfig()
        
        # Check for deprecated 'language' field in code_to_design
        if config_data and 'code_to_design' in config_data and 'language' in config_data['code_to_design']:
            warnings.warn(
                "⚠️  Campo 'language' está deprecado en code_to_design. Usa 'languages' como lista en su lugar.", 
                DeprecationWarning, 
                stacklevel=2
            )
        
        # Parse configuration with Pydantic
        return AutocodeConfig(**config_data)
        
    except Exception as e:
        print(f"⚠️  Warning: Error loading config from {config_file}: {e}")
        print("   Using default configuration")
        return AutocodeConfig()


def save_config(config: AutocodeConfig, config_path: Optional[Path] = None) -> None:
    """Save configuration to autocode_config.yml.
    
    Args:
        config: Configuration instance to save
        config_path: Path to save config file (defaults to autocode_config.yml in cwd)
    """
    if config_path is None:
        config_path = Path.cwd() / "autocode_config.yml"
    
    try:
        # Convert to dictionary for YAML serialization
        config_dict = config.model_dump()
        
        # Write to YAML file
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                config_dict, 
                f, 
                default_flow_style=False, 
                allow_unicode=True,
                sort_keys=True
            )
            
    except Exception as e:
        raise RuntimeError(f"Error saving config to {config_path}: {e}")


__all__ = [
    # Core config types
    "DocsConfig", 
    "TestConfig", 
    "GitConfig", 
    "OpenCodeConfig", 
    "CodeToDesignConfig", 
    "TokenConfig",
    "CheckConfig",
    "DaemonConfig",
    "ApiConfig",
    "DocIndexConfig",
    "AutocodeConfig",
    
    # Configuration utilities
    "load_config",
    "save_config",
    "find_config_file"
]
