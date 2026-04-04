"""
grimoire init — declare project structure for search.

Two modes:

  Non-interactive (agent-friendly):
    grimoire init -s ./backend -s ./frontend -n . -r ./specs

  Interactive (human-friendly):
    grimoire init
    → walks you through choosing sources, notes, resources dirs

Writes to ~/.grimoire/projects/{project_name}-{hash}.toml
keyed by the resolved project root path.

Also generates a .grimignore with sane defaults if one doesn't exist.
"""

import hashlib
import os
import sys
from pathlib import Path
from typing import List, Optional

try:
    import tomli_w
    HAS_TOMLI_W = True
except ImportError:
    HAS_TOMLI_W = False

GRIMOIRE_HOME = Path.home() / '.grimoire'
PROJECTS_DIR = GRIMOIRE_HOME / 'projects'

# Sane defaults for .grimignore
DEFAULT_IGNORES = """\
# Version control
.git/
.hg/
.svn/

# Dependencies
node_modules/
vendor/
bower_components/
.venv/
venv/
__pycache__/

# Build output
dist/
build/
target/
.next/
.nuxt/
out/
*.egg-info/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Caches
.mypy_cache/
.pytest_cache/
.tox/
.cache/
.ruff_cache/

# OS
.DS_Store
Thumbs.db
"""

# Directories to never show in interactive selection
HIDDEN_DIRS = {
    '.git', '.hg', '.svn', 'node_modules', '__pycache__',
    '.venv', 'venv', 'dist', 'build', 'target', '.next',
    '.nuxt', '.idea', '.vscode', '.mypy_cache', '.pytest_cache',
    '.tox', '.cache', 'vendor', 'bower_components', '.ruff_cache',
    'out', '.egg-info', '.DS_Store',
}


def project_key(root: Path) -> str:
    """Stable key for a project based on its resolved path."""
    resolved = str(root.resolve())
    return hashlib.sha256(resolved.encode()).hexdigest()[:12]


def project_config_path(root: Path) -> Path:
    """Path to this project's config in ~/.grimoire/projects/."""
    name = root.resolve().name
    key = project_key(root)
    return PROJECTS_DIR / f"{name}-{key}.toml"


def _format_toml(config: dict) -> str:
    """Format config dict as TOML string."""
    if HAS_TOMLI_W:
        import io
        # Remove internal keys before serializing
        clean = {k: v for k, v in config.items() if not k.startswith('_')}
        buf = io.BytesIO()
        tomli_w.dump(clean, buf)
        return buf.getvalue().decode()

    # Manual formatting
    lines = []
    root = config.get('project', {}).get('root', '.')
    lines.append(f'# Grimoire config for {Path(root).name}')
    lines.append(f'# {root}')
    lines.append('')

    if 'project' in config:
        lines.append('[project]')
        for k, v in config['project'].items():
            lines.append(f'{k} = "{v}"')
        lines.append('')

    if 'paths' in config:
        lines.append('[paths]')
        for k, v in config['paths'].items():
            if isinstance(v, list):
                lines.append(f'{k} = [')
                for item in v:
                    lines.append(f'    "{item}",')
                lines.append(']')
            else:
                lines.append(f'{k} = "{v}"')
        lines.append('')

    if 'filetypes' in config:
        lines.append('[filetypes]')
        exts = config['filetypes']['extensions']
        lines.append('extensions = [')
        for ext in exts:
            lines.append(f'    "{ext}",')
        lines.append(']')
        lines.append('')

    return '\n'.join(lines) + '\n'


def _detect_extensions(root: Path, dirs: List[Path], max_files: int = 5000) -> List[str]:
    """Scan declared directories and return sorted list of extensions found."""
    from .config import DEFAULT_EXTENSIONS, DEFAULT_IGNORE_DIRS

    found = set()
    count = 0
    known = {
        '.py', '.js', '.ts', '.tsx', '.jsx',
        '.md', '.txt', '.json', '.yaml', '.yml',
        '.toml', '.sh', '.css', '.html', '.sql',
        '.h', '.cpp', '.c', '.go', '.rs',
        '.rb', '.java', '.kt', '.cs', '.swift',
        '.ex', '.exs', '.php', '.lua', '.zig', '.r', '.pl',
        '.graphql', '.scss', '.less', '.rst', '.adoc', '.org',
        '.env', '.ini', '.cfg', '.xml',
    }

    for d in dirs:
        resolved = (root / d).resolve() if not d.is_absolute() else d.resolve()
        if not resolved.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(resolved):
            dirnames[:] = [dn for dn in dirnames if dn not in DEFAULT_IGNORE_DIRS]
            for f in filenames:
                ext = Path(f).suffix.lower()
                if ext and ext in known:
                    found.add(ext)
                count += 1
                if count >= max_files:
                    return sorted(found) if found else DEFAULT_EXTENSIONS

    return sorted(found) if found else DEFAULT_EXTENSIONS


def _list_dirs(root: Path) -> List[str]:
    """List visible directories in root, sorted."""
    dirs = []
    try:
        for entry in sorted(root.iterdir()):
            if entry.is_dir() and entry.name not in HIDDEN_DIRS and not entry.name.startswith('.'):
                dirs.append(entry.name)
    except PermissionError:
        pass
    return dirs


def _interactive_select(prompt: str, dirs: List[str], allow_dot: bool = True) -> List[str]:
    """Interactive directory selection. Returns list of chosen dirs."""
    print(f"\n{prompt}")
    print("-" * 40)

    options = []
    if allow_dot:
        options.append('.')
        print(f"  0) .  (project root)")

    for i, d in enumerate(dirs):
        options.append(d)
        print(f"  {i + (1 if allow_dot else 0)}) {d}/")

    print(f"\n  Enter numbers separated by spaces, or paths directly.")
    print(f"  Leave empty to skip.")

    try:
        raw = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return []

    if not raw:
        return []

    selected = []
    for token in raw.split():
        # Numeric selection
        if token.isdigit():
            idx = int(token)
            if 0 <= idx < len(options):
                val = options[idx]
                selected.append(f"./{val}" if val != '.' else '.')
            else:
                print(f"  (skipping invalid index: {token})")
        else:
            # Direct path
            selected.append(token if token.startswith('./') or token.startswith('/') else f"./{token}")

    return selected


def _interactive_init(root: Path) -> dict:
    """Walk the user through configuring grimoire for a project."""
    print(f"\n  Grimoire init — {root.name}")
    print(f"  {root}\n")

    dirs = _list_dirs(root)

    if not dirs:
        print("  No subdirectories found. Using project root for everything.")
        return {
            'sources': ['.'],
            'notes': ['.'],
            'resources': ['.'],
        }

    paths = {}

    # Sources
    result = _interactive_select("Source code directories:", dirs)
    if result:
        paths['sources'] = result

    # Notes
    result = _interactive_select("Notes & documentation directories:", dirs)
    if result:
        paths['notes'] = result

    # Resources
    result = _interactive_select("Resources & specs directories:", dirs)
    if result:
        paths['resources'] = result

    if not paths:
        print("\n  Nothing selected. Using project root for everything.")
        paths = {'sources': ['.'], 'notes': ['.'], 'resources': ['.']}

    return paths


def init_project(
    root: Path = None,
    sources: List[str] = None,
    notes: List[str] = None,
    resources: List[str] = None,
    extensions: List[str] = None,
    force: bool = False,
    dry_run: bool = False,
    interactive: bool = False,
) -> str:
    """Initialize grimoire config for a project.

    Args:
        root: Project root directory. Defaults to CWD.
        sources: Source code directories (multiple allowed).
        notes: Notes/docs directories (multiple allowed).
        resources: Resource/spec directories (multiple allowed).
        extensions: Override file extensions. Auto-detected if not given.
        force: Overwrite existing config.
        dry_run: Print config without writing.
        interactive: Run interactive mode.

    Returns:
        The generated TOML content.
    """
    if root is None:
        root = Path.cwd()
    root = root.resolve()

    config_path = project_config_path(root)

    if config_path.exists() and not force:
        if not dry_run:
            print(f"Already initialized: {config_path}", file=sys.stderr)
            print("Use --force to overwrite.", file=sys.stderr)
            return config_path.read_text()

    # Determine paths
    if interactive or (not sources and not notes and not resources):
        if sys.stdin.isatty():
            paths_config = _interactive_init(root)
        else:
            print("Error: no paths declared and not a terminal.", file=sys.stderr)
            print("  grimoire init -s ./src -n ./docs -r ./specs", file=sys.stderr)
            sys.exit(1)
    else:
        paths_config = {}
        if sources:
            paths_config['sources'] = sources if len(sources) > 1 else sources[0]
        if notes:
            paths_config['notes'] = notes if len(notes) > 1 else notes[0]
        if resources:
            paths_config['resources'] = resources if len(resources) > 1 else resources[0]

    # Collect all declared dirs for extension scanning
    all_dirs = []
    for v in paths_config.values():
        if isinstance(v, list):
            all_dirs.extend(Path(p) for p in v)
        else:
            all_dirs.append(Path(v))

    # Auto-detect extensions from declared paths
    if extensions:
        ext_list = extensions
    else:
        ext_list = _detect_extensions(root, all_dirs)

    # Normalize paths_config: flatten single-item lists for cleaner TOML
    for k, v in paths_config.items():
        if isinstance(v, list) and len(v) == 1:
            paths_config[k] = v[0]

    config = {
        'project': {
            'root': str(root),
        },
        'paths': paths_config,
        'filetypes': {'extensions': ext_list},
    }

    toml_content = _format_toml(config)

    if dry_run:
        return toml_content

    # Ensure ~/.grimoire/projects/ exists
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    # Write config
    config_path.write_text(toml_content)

    # Write .grimignore if it doesn't exist
    grimignore = root / '.grimignore'
    if not grimignore.exists():
        grimignore.write_text(DEFAULT_IGNORES)
        print(f"Wrote {grimignore}")

    # Summary
    print(f"Wrote {config_path}")
    print(f"  project: {root.name} ({root})")
    for k, v in paths_config.items():
        if isinstance(v, list):
            for item in v:
                print(f"  {k:10s} → {item}")
        else:
            print(f"  {k:10s} → {v}")
    print(f"  {len(ext_list)} file extensions detected")

    return toml_content
