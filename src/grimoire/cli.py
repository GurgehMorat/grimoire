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
        file_info = {}
        for match in results:
            file_path = str(match.file_path)
            if file_path not in file_info:
                file_info[file_path] = {'count': 0, 'lines': []}
            file_info[file_path]['count'] += 1
            file_info[file_path]['lines'].append(match.line_number)

        output = []
        output.append("\nSearch Result Summary:")
        output.append("-" * 80)
        for file_path, info in sorted(file_info.items()):
            output.append(f"{info['count']:3d} matches in {file_path}")
            output.append(f"    Lines: {', '.join(str(line) for line in sorted(info['lines']))}")
        output.append("-" * 80)
        output.append(f"Total: {len(file_info)} files with {len(results)} matches")
        return "\n".join(output)

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


def cmd_init(argv):
    """Handle 'grimoire init' subcommand."""
    parser = argparse.ArgumentParser(
        prog='grimoire init',
        description='Initialize grimoire for a project. '
                    'Without flags, runs interactively. '
                    'With flags, writes config directly.'
    )
    parser.add_argument('-s', '--sources', action='append', default=[],
                       metavar='DIR', help='Source code directory (repeatable)')
    parser.add_argument('-n', '--notes', action='append', default=[],
                       metavar='DIR', help='Notes/docs directory (repeatable)')
    parser.add_argument('-r', '--resources', action='append', default=[],
                       metavar='DIR', help='Resources/specs directory (repeatable)')
    parser.add_argument('-e', '--ext', action='append', default=[],
                       metavar='.EXT', help='File extension to include (repeatable)')
    parser.add_argument('-p', '--path', default=None,
                       metavar='DIR', help='Project root (default: CWD)')
    parser.add_argument('--force', action='store_true',
                       help='Overwrite existing config')
    parser.add_argument('--dry-run', action='store_true',
                       help='Print config without writing')

    args = parser.parse_args(argv)

    from .init import init_project

    root = Path(args.path) if args.path else None
    has_flags = bool(args.sources or args.notes or args.resources)

    content = init_project(
        root=root,
        sources=args.sources or None,
        notes=args.notes or None,
        resources=args.resources or None,
        extensions=args.ext or None,
        force=args.force,
        dry_run=args.dry_run,
        interactive=not has_flags,
    )

    if args.dry_run:
        print(content)


def cmd_search(argv):
    """Handle search (default) subcommand."""
    parser = argparse.ArgumentParser(
        description='Search through codebases, documentation, and resources.',
        epilog='Run "grimoire init" to set up a project.'
    )

    parser.add_argument('pattern',
                       help='Search pattern (case-insensitive)',
                       nargs='?' if '-L' in sys.argv or '--line' in sys.argv else None)
    parser.add_argument('-n', '--notes',
                       action='store_true',
                       help='Search in notes (plans, docs, markdown)')
    parser.add_argument('-r', '--resources',
                       action='store_true',
                       help='Search in resources (specs, reference)')
    parser.add_argument('-s', '--sources',
                       action='store_true',
                       help='Search in source code')
    parser.add_argument('-c', '--context',
                       type=int, default=0,
                       help='Number of context lines after match')
    parser.add_argument('-C', '--context-before',
                       type=int, default=0,
                       help='Number of context lines before match')
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

    args = parser.parse_args(argv)

    if not (args.notes or args.resources or args.sources):
        print("Error: at least one search location required (-n, -r, -s)", file=sys.stderr)
        sys.exit(1)

    config = GrimoireConfig()
    config.cache_results = not args.no_cache

    paths = []
    if args.notes:
        paths.append('notes')
    if args.resources:
        paths.append('resources')
    if args.sources:
        paths.append('sources')

    errors = config.validate(paths)
    if errors:
        print("Configuration errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        print("\nRun 'grimoire init' to set up this project.", file=sys.stderr)
        sys.exit(1)

    searcher = GrimoireSearcher(config)
    if args.limit:
        searcher.limit_path = args.limit

    try:
        if args.pattern is None and args.line:
            results = searcher.search(".", paths, args.context, args.context_before)
        else:
            results = searcher.search(args.pattern, paths, args.context, args.context_before)
        print(format_results(results, args.context > 0, args.summary, args.line))
    except Exception as e:
        print(f"Error during search: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        cmd_init(sys.argv[2:])
    else:
        cmd_search(sys.argv[1:])


if __name__ == "__main__":
    main()
