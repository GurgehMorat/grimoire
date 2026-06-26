"""
Configuration management for Grimoire search tool.

Config resolution order (first found wins):
  1. CWD/.grimoire.toml  (project-local, legacy/manual)
  2. Walk parent dirs up to $HOME looking for .grimoire.toml
  3. ~/.grimoire/projects/{name}-{hash}.toml  (created by grimoire init)
  4. ~/.config/grimoire/config.toml  (user global)
  5. ~/.grimoire.toml  (user global fallback)
  6. Environment variables
  7. $HOME fallback (search everything)

Relative paths in configs are resolved relative to the project root
(from [project].root or the directory containing the config file).

The .grimignore file at project root controls directory exclusion.
"""

import os
import sys
import tomli
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

# Global config locations (user home)
GLOBAL_CONFIG_PATHS = [
    Path.home() / '.config' / 'grimoire' / 'config.toml',
    Path.home() / '.grimoire.toml'
]

# Project-local config filename
LOCAL_CONFIG_NAME = '.grimoire.toml'

# Default file extensions for modern dev workflows
DEFAULT_EXTENSIONS = [
    '.py', '.js', '.ts', '.tsx', '.jsx',
    '.md', '.txt', '.json', '.yaml', '.yml',
    '.toml', '.sh', '.css', '.html', '.sql',
    '.h', '.cpp', '.c', '.go', '.rs',
]

# Default directories to ignore (always, even without .grimignore)
DEFAULT_IGNORE_DIRS = {
    '.git', '.hg', '.svn', 'node_modules', '__pycache__',
    '.venv', 'venv', 'dist', 'build', 'target', '.next',
    '.nuxt', '.idea', '.vscode', '.mypy_cache', '.pytest_cache',
    '.tox', '.cache', 'vendor', 'bower_components', '.ruff_cache',
    'out', 'worktrees', 'htmlcov',
}


def _find_project_config_in_registry() -> Optional[Path]:
    """Look up CWD in ~/.grimoire/projects/ registry.

    Matches when CWD is inside the project root OR the project root
    is inside CWD (e.g. CWD=$HOME, project at $HOME/dev/platform).
    When multiple projects match, the deepest (most specific) wins.
    """
    projects_dir = Path.home() / '.grimoire' / 'projects'
    if not projects_dir.is_dir():
        return None

    cwd = Path.cwd().resolve()
    best_match = None
    best_depth = -1

    for config_file in projects_dir.glob('*.toml'):
        try:
            with open(config_file, 'rb') as f:
                data = tomli.load(f)
            project_root = data.get('project', {}).get('root', '')
            if not project_root:
                continue
            project_path = Path(project_root).resolve()
            # CWD is inside this project
            if cwd == project_path or project_path in cwd.parents:
                depth = len(project_path.parts)
                if depth > best_depth:
                    best_match = config_file
                    best_depth = depth
            # Project is inside CWD (e.g. CWD=$HOME)
            elif cwd in project_path.parents:
                depth = len(project_path.parts)
                if depth > best_depth:
                    best_match = config_file
                    best_depth = depth
        except Exception:
            continue

    return best_match


def find_config_path() -> tuple[Optional[Path], Optional[Path]]:
    """Find the config file. Returns (config_path, project_root).

    Walks from CWD upward looking for .grimoire.toml, stopping at $HOME.
    Then checks ~/.grimoire/projects/ registry.
    Falls back to global config locations.
    """
    home = Path.home()
    cwd = Path.cwd().resolve()

    # Walk CWD -> parent -> ... -> home looking for .grimoire.toml
    current = cwd
    while True:
        candidate = current / LOCAL_CONFIG_NAME
        if candidate.exists():
            return candidate, current

        if current == home or current == current.parent:
            break
        current = current.parent

    # Check project registry
    registry_config = _find_project_config_in_registry()
    if registry_config:
        # project_root is stored inside the config, will be read during load
        return registry_config, None

    # When CWD is $HOME, scan immediate subdirectories (depth 2) for
    # project-local configs — covers repos cloned under ~/dev/*/
    if cwd == home:
        best = None
        for child in home.iterdir():
            if not child.is_dir() or child.name.startswith('.'):
                continue
            candidate = child / LOCAL_CONFIG_NAME
            if candidate.exists():
                best = (candidate, child)
                continue
            # One level deeper (e.g. ~/dev/platform/.grimoire.toml)
            for grandchild in child.iterdir():
                if not grandchild.is_dir() or grandchild.name.startswith('.'):
                    continue
                candidate = grandchild / LOCAL_CONFIG_NAME
                if candidate.exists():
                    # Prefer deeper (more specific) matches
                    if best is None or len(grandchild.parts) > len(best[1].parts):
                        best = (candidate, grandchild)
        if best:
            return best

    # Fall back to global config paths
    for path in GLOBAL_CONFIG_PATHS:
        if path.exists():
            return path, None

    return None, None


def load_ignore_dirs(project_root: Optional[Path] = None) -> Set[str]:
    """Load directory names to ignore.

    Combines built-in defaults with .grimignore at project root.
    """
    ignore = set(DEFAULT_IGNORE_DIRS)

    if project_root:
        grimignore = project_root / '.grimignore'
        if grimignore.exists():
            try:
                for line in grimignore.read_text().splitlines():
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    ignore.add(line.rstrip('/'))
            except Exception:
                pass

    return ignore


@dataclass
class GrimoireConfig:
    """Configuration settings for Grimoire."""

    search_paths: Dict[str, list] = field(default_factory=dict)  # key -> [Path, ...]
    file_types: List[str] = field(default_factory=list)
    max_context_lines: int = 10
    cache_results: bool = True
    cache_size: int = 100
    project_root: Optional[Path] = None
    ignore_dirs: Set[str] = field(default_factory=set)

    def __post_init__(self):
        """Load configuration from file or environment variables."""
        config_path, discovered_root = find_config_path()

        if config_path and config_path.exists():
            try:
                with open(config_path, 'rb') as f:
                    config_data = tomli.load(f)

                # Determine project root:
                # 1. From [project].root in config (grimoire init)
                # 2. From directory containing .grimoire.toml (local config)
                # 3. CWD
                stored_root = config_data.get('project', {}).get('root')
                if stored_root:
                    self.project_root = Path(stored_root).resolve()
                elif discovered_root:
                    self.project_root = discovered_root.resolve()
                else:
                    self.project_root = Path.cwd().resolve()

                # Load paths — resolve relative paths against project root
                if 'paths' in config_data:
                    for k, v in config_data['paths'].items():
                        if not v:
                            continue
                        # Value can be a string or a list of strings
                        if isinstance(v, list):
                            resolved = []
                            for item in v:
                                p = Path(item)
                                if not p.is_absolute():
                                    p = (self.project_root / p).resolve()
                                resolved.append(p)
                            self.search_paths[k] = resolved
                        else:
                            p = Path(v)
                            if not p.is_absolute():
                                p = (self.project_root / p).resolve()
                            self.search_paths[k] = [p]

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
                print(f"Warning: Error reading config file {config_path}: {e}", file=sys.stderr)

        # If paths not set in config, try environment variables
        if not self.search_paths:
            env_notes = os.environ.get('GRIMOIRE_NOTES_PATH', '')
            env_resources = os.environ.get('GRIMOIRE_RESOURCES_PATH', '')
            env_sources = os.environ.get('GRIMOIRE_SOURCES_PATH', '')

            if env_notes:
                self.search_paths['notes'] = [Path(env_notes)]
            if env_resources:
                self.search_paths['resources'] = [Path(env_resources)]
            if env_sources:
                self.search_paths['sources'] = [Path(env_sources)]

        # Last resort: all paths point at $HOME
        if not self.search_paths:
            home = Path.home()
            self.search_paths = {
                'notes': [home],
                'resources': [home],
                'sources': [home],
            }

        # Set project root if not yet set
        if not self.project_root:
            self.project_root = Path.cwd().resolve()

        # Load ignore patterns
        self.ignore_dirs = load_ignore_dirs(self.project_root)

        # Set default file types if none configured
        if not self.file_types:
            self.file_types = DEFAULT_EXTENSIONS

    def validate(self, used_paths: List[str] = None) -> List[str]:
        """Validate configuration and return list of any errors."""
        errors = []

        paths_to_check = used_paths if used_paths else list(self.search_paths.keys())
        for name in paths_to_check:
            if name not in self.search_paths:
                errors.append(
                    f"Search path '{name}' is not configured. "
                    f"Run 'grimoire init' or add a .grimoire.toml"
                )
                continue

            for path in self.search_paths[name]:
                if not path.exists():
                    errors.append(
                        f"Search path '{name}' does not exist: {path}"
                    )

        for ext in self.file_types:
            if not ext.startswith('.'):
                errors.append(f"File type must start with '.': {ext}")

        if self.max_context_lines < 0:
            errors.append("max_context_lines must be non-negative")
        if self.cache_size < 0:
            errors.append("cache_size must be non-negative")

        return errors
