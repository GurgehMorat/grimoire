"""
Command-line interface for Grimoire search tool.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List
from .config import GrimoireConfig
from .searcher import GrimoireSearcher, SearchMatch

def format_results(results: List[SearchMatch], show_context: bool = True, summary: bool = False, line_number: int = None) -> str:
    """Format search results for display."""
    if not results:
        return "No matches found."
        
    if line_number:
        # Find the match with the specified line number
        for match in results:
            if match.line_number == line_number:
                output = []
                output.append("\n" + "=" * 80)
                output.append(f"File: {match.file_path}")
                output.append(f"Line: {match.line_number}\n")
                
                if show_context and match.context_before:
                    for line in match.context_before:
                        output.append(f"  | {line}")
                        
                output.append(f"  > {match.line_content}")
                
                if show_context and match.context_after:
                    for line in match.context_after:
                        output.append(f"  | {line}")
                        
                return "\n".join(output)
        return f"Line {line_number} not found in search results."
        
    if summary:
        # Group by file path and track line numbers
        file_info = {}
        for match in results:
            file_path = str(match.file_path)
            if file_path not in file_info:
                file_info[file_path] = {'count': 0, 'lines': []}
            file_info[file_path]['count'] += 1
            file_info[file_path]['lines'].append(match.line_number)
            
        # Format summary
        output = []
        output.append("\nSearch Result Summary:")
        output.append("-" * 80)
        for file_path, info in sorted(file_info.items()):
            output.append(f"{info['count']:3d} matches in {file_path}")
            output.append(f"    Lines: {', '.join(str(line) for line in sorted(info['lines']))}")
        output.append("-" * 80)
        output.append(f"Total: {len(file_info)} files with {len(results)} matches")
        return "\n".join(output)
    
    # Detailed results format
    output = []
    for match in results:
        output.append("\n" + "=" * 80)
        output.append(f"File: {match.file_path}")
        output.append(f"Line: {match.line_number}\n")
        
        if show_context and match.context_before:
            for line in match.context_before:
                output.append(f"  | {line}")
                
        output.append(f"  > {match.line_content}")
        
        if show_context and match.context_after:
            for line in match.context_after:
                output.append(f"  | {line}")
                
    return "\n".join(output)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Search through technical documentation.',
        epilog='At least one search location must be specified.'
    )
    
    parser.add_argument('pattern',
                       help='Search pattern (case-insensitive)',
                       nargs='?' if '-L' in sys.argv or '--line' in sys.argv else None)
    parser.add_argument('-n', '--notes',
                       action='store_true',
                       help='Search in technical notes')
    parser.add_argument('-r', '--resources',
                       action='store_true',
                       help='Search in resources directory')
    parser.add_argument('-s', '--sources',
                       action='store_true',
                       help='Search in source code directory')
    parser.add_argument('-c', '--context',
                       type=int,
                       default=0,
                       help='Number of context lines to show after the match')
    parser.add_argument('-C', '--context-before',
                       type=int,
                       default=0,
                       help='Number of context lines to show before the match')
    parser.add_argument('-l', '--limit',
                       type=str,
                       help='Limit search to specific file or directory')
    parser.add_argument('--no-cache',
                       action='store_true',
                       help='Disable result caching')
    parser.add_argument('-m', '--summary',
                       action='store_true',
                       help='Show only file summary with match counts')
    parser.add_argument('-L', '--line',
                       type=int,
                       help='Show only the specified line number from results')
    
    args = parser.parse_args()
    
    # Validate search locations
    if not (args.notes or args.resources or args.sources):
        parser.error("At least one search location must be specified (-n for notes, -r for resources, -s for sources)")
    
    # Initialize configuration
    config = GrimoireConfig()
    config.cache_results = not args.no_cache
    
    # Determine search paths
    paths = []
    if args.notes:
        paths.append('notes')
    if args.resources:
        paths.append('resources')
    if args.sources:
        paths.append('sources')
    
    # Validate configuration for requested paths
    errors = config.validate(paths)
    if errors:
        print("Configuration errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        print("\nPlease create a config file at ~/.config/grimoire/config.toml", file=sys.stderr)
        print("See README.md for configuration examples.", file=sys.stderr)
        sys.exit(1)
    
    # Initialize searcher
    searcher = GrimoireSearcher(config)
    if args.limit:
        searcher.limit_path = args.limit
    
    # Execute search
    try:
        if args.pattern is None and args.line:
            # When using -L without pattern, use "." to match any line
            results = searcher.search(".", paths, args.context, args.context_before)
        else:
            results = searcher.search(args.pattern, paths, args.context, args.context_before)
        print(format_results(results, args.context > 0, args.summary, args.line))
    except Exception as e:
        print(f"Error during search: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()