# Grimoire Configuration Guide

Grimoire supports two ways to configure search paths and behavior: configuration files and environment variables.

## Configuration File

### Location
The configuration file can be placed in either:
1. `~/.config/grimoire/config.toml` (preferred)
2. `~/.grimoire.toml` (fallback)

### Example Configuration
```toml
# Search Paths Configuration
[paths]
notes = "/path/to/your/notes"      # Technical documentation and notes
resources = "/path/to/resources"    # Project resources and assets
sources = "/path/to/source/code"    # Source code files

# File Types to Search
[filetypes]
extensions = [
    ".txt",    # Text files
    ".md",     # Markdown files
    ".h",      # C/C++ headers
    ".cpp",    # C++ source files
    ".inl",    # Inline files
    ".as"      # ActionScript files
]

# Search Behavior Settings
[behavior]
max_context_lines = 10  # Maximum number of context lines to show
cache_enabled = true    # Enable result caching
cache_size = 100       # Number of results to cache
```

## Environment Variables

If no configuration file is found, Grimoire will look for these environment variables:

```bash
# Set search paths
export GRIMOIRE_NOTES_PATH="/path/to/your/notes"
export GRIMOIRE_RESOURCES_PATH="/path/to/resources"
export GRIMOIRE_SOURCES_PATH="/path/to/source/code"
```

You can add these to your shell's startup file (e.g., `~/.bashrc` or `~/.zshrc`).

## Priority Order

1. Configuration file (`~/.config/grimoire/config.toml`)
2. Fallback configuration file (`~/.grimoire.toml`)
3. Environment variables
4. Default values

## Default Values

If neither configuration file nor environment variables are found:
- File extensions: [".txt", ".md", ".h", ".cpp", ".inl", ".as"]
- Max context lines: 10
- Cache enabled: true
- Cache size: 100 entries

## Validation

Grimoire validates your configuration and will show helpful error messages if:
- Configured paths don't exist
- File extensions don't start with '.'
- Numeric settings are invalid

## Examples

### Basic Setup
```bash
# Create default config
mkdir -p ~/.config/grimoire
cp default_config.toml ~/.config/grimoire/config.toml

# Edit with your paths
nano ~/.config/grimoire/config.toml
```

### Environment Variable Setup
```bash
# Add to ~/.bashrc or ~/.zshrc
export GRIMOIRE_NOTES_PATH="$HOME/dev/notes"
export GRIMOIRE_RESOURCES_PATH="$HOME/dev/resources"
export GRIMOIRE_SOURCES_PATH="$HOME/dev/src"
```

### Multiple Project Setup
```bash
# Project A
export GRIMOIRE_NOTES_PATH="$HOME/projectA/docs"
grimoire -n "search term"

# Project B
export GRIMOIRE_NOTES_PATH="$HOME/projectB/docs"
grimoire -n "search term"
```