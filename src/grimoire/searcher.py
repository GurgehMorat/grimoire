"""
Core searching functionality for Grimoire.
"""

import os
import re
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
from .config import GrimoireConfig


@dataclass
class SearchMatch:
    """Represents a single search match with context."""
    file_path: Path
    line_number: int
    line_content: str
    context_before: List[str]
    context_after: List[str]


class GrimoireSearcher:
    """Core search functionality for technical documentation."""

    def __init__(self, config: GrimoireConfig):
        """Initialize searcher with configuration."""
        self.config = config
        self._result_cache: Dict[str, List[SearchMatch]] = {}
        self.limit_path = None

    def _get_file_contents(self, file_path: Path) -> List[str]:
        """Read and return file contents safely."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.readlines()
        except (UnicodeDecodeError, PermissionError, OSError):
            return []

    def _get_context(self, lines: List[str], match_index: int, context_after: int = 0, context_before: int = 0) -> SearchMatch:
        """Extract context lines around a match."""
        start = max(0, match_index - context_before)
        end = min(len(lines), match_index + context_after + 1)

        return SearchMatch(
            file_path=Path(),
            line_number=match_index + 1,
            line_content=lines[match_index].rstrip(),
            context_before=[line.rstrip() for line in lines[start:match_index]],
            context_after=[line.rstrip() for line in lines[match_index + 1:end]]
        )

    def _walk_files(self, base_dir: Path) -> List[Path]:
        """Walk directory tree respecting .grimignore and file type filters.

        Uses os.walk with in-place pruning for ignored directories.
        """
        ignore_dirs = self.config.ignore_dirs
        valid_extensions = set(self.config.file_types)
        files = []

        for dirpath, dirnames, filenames in os.walk(base_dir):
            # Prune ignored directories in-place
            dirnames[:] = [
                d for d in dirnames
                if d not in ignore_dirs and not d.startswith('.')
            ]

            for f in filenames:
                fp = Path(dirpath) / f
                if fp.suffix.lower() in valid_extensions:
                    files.append(fp)

        return files

    def _resolve_limit(self, base_dir: Path) -> List[Path]:
        """Resolve limit_path filter against a base directory."""
        limit = self.limit_path
        if not limit:
            return self._walk_files(base_dir)

        limit_path = Path(limit)

        # Absolute path
        if limit_path.is_absolute():
            if limit_path.exists():
                if limit_path.is_file():
                    return [limit_path]
                return self._walk_files(limit_path)
            return []

        # Relative to base_dir
        resolved = (base_dir / limit_path).resolve()
        if resolved.exists():
            if resolved.is_file():
                return [resolved]
            return self._walk_files(resolved)

        # Fuzzy match: find paths containing the limit string
        results = []
        for fp in self._walk_files(base_dir):
            if limit in str(fp):
                results.append(fp)
        return results

    def search(self, pattern: str, paths: List[str], context_after: int = 0, context_before: int = 0) -> List[SearchMatch]:
        """Execute search across specified paths with context."""
        context_after = min(max(0, context_after), self.config.max_context_lines)
        context_before = min(max(0, context_before), self.config.max_context_lines)

        cache_key = f"{pattern}:{','.join(paths)}:{context_after}:{context_before}:{self.limit_path}"
        if self.config.cache_results and cache_key in self._result_cache:
            return self._result_cache[cache_key]

        results: List[SearchMatch] = []

        for path_key in paths:
            if path_key not in self.config.search_paths:
                continue

            # search_paths values are lists of Paths
            for base_dir in self.config.search_paths[path_key]:
                if not base_dir.exists():
                    continue

                target_files = self._resolve_limit(base_dir)

                for file_path in target_files:
                    if not file_path.is_file():
                        continue

                    lines = self._get_file_contents(file_path)
                    for i, line in enumerate(lines):
                        if re.search(re.escape(pattern), line, re.IGNORECASE):
                            match = self._get_context(lines, i, context_after, context_before)
                            match.file_path = file_path
                            results.append(match)

        if self.config.cache_results:
            self._result_cache[cache_key] = results
            if len(self._result_cache) > self.config.cache_size:
                del self._result_cache[next(iter(self._result_cache))]

        return results
