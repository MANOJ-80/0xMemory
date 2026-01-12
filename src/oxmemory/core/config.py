"""Configuration loading and management for 0xMemory."""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from oxmemory.core.models import Config


# Default brain directory name
BRAIN_DIR = ".0xmemory"
CONFIG_FILE = "config.yaml"


def get_brain_path(project_dir: Optional[Path] = None) -> Path:
    """Get the brain directory path for a project.
    
    Args:
        project_dir: Project directory. Defaults to current directory.
        
    Returns:
        Path to the .0xmemory directory.
    """
    if project_dir is None:
        project_dir = Path.cwd()
    return project_dir / BRAIN_DIR


def get_config_path(project_dir: Optional[Path] = None) -> Path:
    """Get the config file path for a project.
    
    Args:
        project_dir: Project directory. Defaults to current directory.
        
    Returns:
        Path to config.yaml.
    """
    return get_brain_path(project_dir) / CONFIG_FILE


def get_default_config(project_name: Optional[str] = None) -> Config:
    """Get default configuration.
    
    Args:
        project_name: Optional project name. Defaults to directory name.
        
    Returns:
        Default Config object.
    """
    if project_name is None:
        project_name = Path.cwd().name
    
    config = Config()
    config.project.name = project_name
    return config


def _interpolate_env_vars(data: dict) -> dict:
    """Recursively interpolate environment variables in config.
    
    Supports ${VAR_NAME} syntax in string values.
    
    Args:
        data: Configuration dictionary.
        
    Returns:
        Dictionary with env vars interpolated.
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = _interpolate_env_vars(value)
        elif isinstance(value, list):
            result[key] = [
                _interpolate_env_vars(item) if isinstance(item, dict) else item
                for item in value
            ]
        elif isinstance(value, str) and "${" in value:
            # Interpolate ${VAR_NAME} patterns
            import re
            pattern = r'\$\{(\w+)\}'
            def replace(match: re.Match) -> str:
                var_name = match.group(1)
                return os.environ.get(var_name, match.group(0))
            result[key] = re.sub(pattern, replace, value)
        else:
            result[key] = value
    return result


def load_config(project_dir: Optional[Path] = None) -> Config:
    """Load configuration from config.yaml.
    
    Args:
        project_dir: Project directory. Defaults to current directory.
        
    Returns:
        Config object.
        
    Raises:
        FileNotFoundError: If config.yaml doesn't exist.
        ValidationError: If config is invalid.
    """
    config_path = get_config_path(project_dir)
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            f"Run '0xmemory init' to create a new brain."
        )
    
    with open(config_path) as f:
        raw_config = yaml.safe_load(f)
    
    if raw_config is None:
        raw_config = {}
    
    # Interpolate environment variables
    config_data = _interpolate_env_vars(raw_config)
    
    return Config.model_validate(config_data)


def save_config(config: Config, project_dir: Optional[Path] = None) -> Path:
    """Save configuration to config.yaml.
    
    Args:
        config: Config object to save.
        project_dir: Project directory. Defaults to current directory.
        
    Returns:
        Path to saved config file.
    """
    config_path = get_config_path(project_dir)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict, excluding defaults that match
    config_dict = config.model_dump(exclude_defaults=False)
    
    with open(config_path, 'w') as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    
    return config_path


def brain_exists(project_dir: Optional[Path] = None) -> bool:
    """Check if a brain exists in the project directory.
    
    Args:
        project_dir: Project directory. Defaults to current directory.
        
    Returns:
        True if .0xmemory directory exists.
    """
    return get_brain_path(project_dir).exists()
