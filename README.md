# Grimoire

Ever wish you could have, ls, grep, cat, and who knows what else, just in one go to search codebases? The larger the more you want to have someting like that? 

Yes, we all have global search this days on the IDE, but sometimes, you just want to run some CLI commands and comb information.

Grimoire: A command-line search tool designed for developers to efficiently navigate technical documentation, source code, and project resources.

"The bigger the project, the greater the responsibility"

## Quick Start

```bash
# Install
pip install grimoire

# Create your config file
mkdir -p ~/.config/grimoire/
nano ~/.config/grimoire/config.toml
```

Add this to your config.toml:
```toml
[paths]
notes = "/path/to/your/notes"      # Documentation directory
resources = "/path/to/resources"   # Project resources
sources = "/path/to/source/code"   # Source code

[filetypes]
extensions = [".md", ".txt", ".h", ".cpp", ".inl", ".as"]
```

## Key Features

- **Smart Context Display**
  ```bash
  grimoire -n -c 2 "pattern"     # Show 2 lines after match
  grimoire -n -C 2 "pattern"     # Show 2 lines before match
  grimoire -n -c 2 -C 1 pattern  # 1 line before, 2 after
  ```

- **Multiple Search Locations**
  ```bash
  grimoire -n "pattern"      # Search notes
  grimoire -r "pattern"      # Search resources
  grimoire -s "pattern"      # Search source code
  grimoire -n -r -s "query"  # Search all locations
  ```

- **Efficient Navigation**
  ```bash
  grimoire -n -s "pattern"   # Get file summary with line numbers
  grimoire -n -L 42 "query"  # Jump to specific line
  ```

## Common Use Cases

1. **Find Implementations**
   ```bash
   # Get overview
   grimoire -s -s "function_name"  # -s (sources), -s (summary)
   
   # Examine specific match
   grimoire -s -c 3 -L 42 "function_name"
   ```

2. **Search Documentation**
   ```bash
   # List all documentation files
   grimoire -n -s "."
   
   # Find specific topic
   grimoire -n -c 2 "topic"
   ```

3. **Project-wide Search**
   ```bash
   # Search all locations with context
   grimoire -n -r -s -c 2 "pattern"
   ```

## Configuration

Grimoire can be configured using either:
1. A TOML configuration file (recommended)
2. Environment variables

### Quick Configuration
```bash
# Using config file
mkdir -p ~/.config/grimoire
cp default_config.toml ~/.config/grimoire/config.toml
nano ~/.config/grimoire/config.toml

# Or using environment variables
export GRIMOIRE_NOTES_PATH="/path/to/notes"
export GRIMOIRE_RESOURCES_PATH="/path/to/resources"
export GRIMOIRE_SOURCES_PATH="/path/to/source"
```

See [CONFIGURATION.md](CONFIGURATION.md) for detailed setup options and examples.

## Installation

From PyPI:
```bash
pip install grimoire
```

From source:
```bash
git clone <repository-url> grimoire
cd grimoire
pip install -e .
```

## License

MIT License - See LICENSE file for details.