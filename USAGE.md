# Grimoire Advanced Usage Guide

This guide covers advanced usage patterns and detailed configuration options. For basic usage and setup, see [README.md](README.md).

## Configuration Details

### Config File Location
1. Primary: ~/.config/grimoire/config.toml
2. Fallback: ~/.grimoire.toml

### Complete Configuration Options
```toml
# ~/.config/grimoire/config.toml

[paths]
notes = "/path/to/notes"          # Technical documentation
resources = "/path/to/resources"  # Project resources
sources = "/path/to/sources"      # Source code directory

[filetypes]
# Files to search - add or remove as needed
extensions = [
    ".txt",    # Text files
    ".md",     # Markdown
    ".h",      # C/C++ headers
    ".cpp",    # C++ source
    ".inl",    # Inline files
    ".as"      # ActionScript files
]

[behavior]
max_context_lines = 10  # Maximum context lines
cache_enabled = true    # Enable result caching
cache_size = 100       # Number of results to cache
```

## Command Line Reference

### Search Location Flags
Flag | Description
-----|-------------
`-n` | Search in notes directory (documentation)
`-r` | Search in resources directory (project resources)
`-s` | Search in source code directory
Multiple can be combined: `-n -r -s` searches all locations

### Context Control
Flag | Description
-----|-------------
`-c N` | Show N lines after match
`-C N` | Show N lines before match
Can be combined: `-c 2 -C 1` shows 1 line before, 2 after

### Navigation and Filtering
Flag | Description
-----|-------------
`-l PATH` | Limit search to specific file/directory
`-L NUM` | Show specific line number
`-s` | Show summary with line numbers
`--no-cache` | Disable results caching

## Advanced Techniques

### Smart Path Navigation
Grimoire supports various ways to specify search paths:

1. **Direct Path**
   ```bash
   grimoire -n -l "exact/path/to/file.md" "pattern"
   ```

2. **Partial Path Matching**
   ```bash
   grimoire -n -l "file.md" "pattern"     # Finds any file.md
   grimoire -n -l "docs/api" "pattern"    # Matches paths containing docs/api
   ```

3. **Directory Traversal**
   ```bash
   grimoire -n -l "docs/" "pattern"       # All files under docs/
   grimoire -n -l "src/core" "pattern"    # All files under src/core
   ```

### Efficient Search Workflow

1. **Start Broad, Narrow Down**
   ```bash
   # First get overview
   grimoire -n -s "pattern"
   
   # Then examine specific file
   grimoire -n -l "interesting_file.md" -s "pattern"
   
   # Finally focus on specific section
   grimoire -n -l "interesting_file.md" -L 42 -c 3 "pattern"
   ```

2. **Using Context Effectively**
   ```bash
   # Quick peek
   grimoire -n -c 1 "pattern"
   
   # More context after match
   grimoire -n -c 3 "pattern"
   
   # Context before and after
   grimoire -n -C 2 -c 3 "pattern"
   ```

3. **Combining Search Locations**
   ```bash
   # Documentation and source
   grimoire -n -s "pattern"
   
   # All locations with summary
   grimoire -n -r -s -s "pattern"
   ```

### Performance Tips

1. **Cache Management**
   - Results are cached by default
   - Use `--no-cache` for fresh results
   - Cache size configurable in config.toml

2. **Search Scope**
   - Use `-l` to limit search area
   - Combine with specific extensions in config
   - Target specific directories for faster results

3. **Memory Usage**
   - Limit context lines for large files
   - Use summary mode for initial searches
   - Clear cache if memory usage grows

### Common Patterns

1. **Finding Definitions**
   ```bash
   # Search in source files
   grimoire -s "class MyClass"
   
   # With wider context
   grimoire -s -C 5 -c 10 "class MyClass"
   ```

2. **Tracking Usage**
   ```bash
   # Find all uses
   grimoire -n -r -s -s "function_name"
   
   # Examine each use
   grimoire -n -l "file.cpp" -L 42 -c 2 "function_name"
   ```

3. **Documentation Search**
   ```bash
   # Find topic
   grimoire -n -s "Topic"
   
   # Get full context
   grimoire -n -l "guide.md" -C 5 -c 5 "Topic"
   ```

## Troubleshooting

### Common Issues

1. **Path Not Found**
   - Check config.toml paths
   - Verify directory permissions
   - Use absolute paths if needed

2. **No Results**
   - Check file extensions in config
   - Try broader search terms
   - Verify search location flags

3. **Performance Issues**
   - Limit search scope with `-l`
   - Reduce context lines
   - Use `--no-cache` if memory is full

### Getting Help

1. Run with `--help` for command reference
2. Check config file for path issues
3. See README.md for basic usage
4. Report issues on GitHub
```

### Common Use Cases
```bash
# Quick file overview
grimoire -n -s "." 

# Find all UI-related content
grimoire -n -s "UI"

# Find VR-specific implementations
grimoire -n -s "VR"

# Deep dive into specific line
grimoire -n -c 3 -L 42 -l "filename.md" "pattern"
```

## Parameters Explained

Flag | Description
-----|-------------
`-n` | Search in notes directory
`-r` | Search in resources directory
`-s` | Show summary with line numbers
`-l` | Limit search to specific file
`-L` | Show specific line number
`-c NUMBER` | Show NUMBER lines of context
`--no-cache` | Disable results caching

## Search Tips

1. Start with `-s` to get a summary and line numbers
2. Use `-l` to focus on a specific file
3. Use `-L` to examine specific lines of interest
4. Adjust context with `-c` as needed
5. Combine flags for precise searches

## Workflow Examples

### Finding and Examining Implementation Details
1. Get overview of all VR-related files:
   ```bash
   grimoire -n -s "VR"
   ```

2. Focus on specific file:
   ```bash
   grimoire -n -s -l "scaleform_vr_integration.md" "VR"
   ```

3. Examine specific implementation:
   ```bash
   grimoire -n -c 2 -L 42 -l "scaleform_vr_integration.md" "VR"
   ```

### Quick Content Overview
1. List all content:
   ```bash
   grimoire -n -s "."
   ```

2. Find specific topics:
   ```bash
   grimoire -n -s "implementation"
   ```

3. Deep dive into matches:
   ```bash
   grimoire -n -c 3 -L 25 "implementation"
   ```

## Best Practices

1. **Efficient Searching**
   - Start broad with summaries
   - Narrow down to specific files
   - Use line numbers for precise examination

2. **Context Management**
   - Use `-c 1` for minimal context
   - Use `-c 2` or `-c 3` for better understanding
   - Adjust based on content density

3. **File Navigation**
   - Use `.` to list all content
   - Use specific terms to find relevant files
   - Combine with `-l` for file-specific searches

---
