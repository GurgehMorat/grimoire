"""
Configuration management for Grimoire search tool.
"""

import os
import sys
import tomli
import tomli_w
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field

CONFIG_PATHS = [
    Path.home() / '.config' / 'grimoire' / 'config.toml',
    Path.home() / '.grimoire.toml'
]

def get_config_path() -> Optional[Path]:
    """Get the path to the config file."""
    for path in CONFIG_PATHS:
        if path.exists():
            return path
    return None

@dataclass
class GrimoireConfig:
    """Configuration settings for Grimoire."""
    
    search_paths: Dict[str, Path] = field(default_factory=dict)
    file_types: List[str] = field(default_factory=list)
    max_context_lines: int = 10
    cache_results: bool = True
    cache_size: int = 100
    
    def __post_init__(self):
        """Load configuration from file or environment variables."""
        # Try to load from config file first
        config_path = get_config_path()
        if config_path and config_path.exists():
            try:
                with open(config_path, 'rb') as f:
                    config_data = tomli.load(f)
                    
                # Load paths
                if 'paths' in config_data:
                    self.search_paths = {
                        k: Path(v) for k, v in config_data['paths'].items() if v
                    }
                    
                # Load file types
                if 'filetypes' in config_data and 'extensions' in config_data['filetypes']:
                    self.file_types = config_data['filetypes']['extensions']
                    
                # Load behavior settings
                if 'behavior' in config_data:
                    behavior = config_data['behavior']
                    if 'max_context_lines' in behavior:
                        self.max_context_lines = behavior['max_context_lines']
                    if 'cache_enabled' in behavior:
                        self.cache_results = behavior['cache_enabled']
                    if 'cache_size' in behavior:
                        self.cache_size = behavior['cache_size']
                        
            except Exception as e:
                print(f"Warning: Error reading config file: {e}", file=sys.stderr)
                
        # If paths not set in config, try environment variables
        if not self.search_paths:
            self.search_paths = {
                'notes': Path(os.environ.get('GRIMOIRE_NOTES_PATH', '')),
                'resources': Path(os.environ.get('GRIMOIRE_RESOURCES_PATH', '')),
                'sources': Path(os.environ.get('GRIMOIRE_SOURCES_PATH', ''))
            }
            
        # Set default file types if none configured
        if not self.file_types:
            self.file_types = ['.txt', '.md', '.h', '.cpp', '.inl', '.as']
    
    def validate(self, used_paths: List[str] = None) -> List[str]:
        """Validate configuration and return list of any errors."""
        errors = []
        
        # Check if requested search paths exist
        paths_to_check = used_paths if used_paths else self.search_paths.keys()
        for name in paths_to_check:
            if name not in self.search_paths:
                errors.append(f"Search path '{name}' is not configured. Add it to your config file (~/.config/grimoire/config.toml)")
                continue
            
            path = self.search_paths[name]
            if str(path) == '':
                errors.append(f"Path for '{name}' is not set. Edit your config file and set a valid path in the [paths] section:\n"
                            f"[paths]\n{name} = \"/path/to/your/{name}\"")
                continue
                
            if not path.exists():
                errors.append(f"Search path '{name}' does not exist: {path}\n"
                            f"Update the path in your config file: ~/.config/grimoire/config.toml")
        
        # Validate file types
        for ext in self.file_types:
            if not ext.startswith('.'):
                errors.append(f"File type must start with '.': {ext}")
        
        # Validate numeric settings
        if self.max_context_lines < 0:
            errors.append("max_context_lines must be non-negative")
        if self.cache_size < 0:
            errors.append("cache_size must be non-negative")
            
        return errors


