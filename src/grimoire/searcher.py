"""
Core searching functionality for Grimoire.
"""

import re
from pathlib import Path
from typing import List, Set, Dict, Optional
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
        
    def _get_file_contents(self, file_path: Path) -> List[str]:
        """Read and return file contents safely."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.readlines()
        except UnicodeDecodeError:
            return []
            
    def _find_matching_paths(self, base_dir: Path, pattern: str) -> List[Path]:
        """Smart path matching with support for partial paths."""
        if not pattern:
            return []
            
        pattern_path = Path(pattern)
        matches = []
        
        # Direct match for absolute paths
        if pattern_path.is_absolute() and pattern_path.exists():
            return [pattern_path]
            
        # Search for matches
        for path in base_dir.rglob('*'):
            # Skip hidden files
            if any(part.startswith('.') for part in path.parts):
                continue
                
            # Full name match
            if pattern_path.name == path.name:
                matches.append(path)
                continue
                
            # Partial path match
            if pattern in str(path):
                matches.append(path)
                
        return matches
        
    def _get_context(self, lines: List[str], match_index: int, context_after: int = 0, context_before: int = 0) -> SearchMatch:
        """Extract context lines around a match."""
        start = max(0, match_index - context_before)
        end = min(len(lines), match_index + context_after + 1)
        
        return SearchMatch(
            file_path=Path(),  # Set by caller
            line_number=match_index + 1,
            line_content=lines[match_index].rstrip(),
            context_before=[line.rstrip() for line in lines[start:match_index]],
            context_after=[line.rstrip() for line in lines[match_index + 1:end]]
        )
        
    def search(self, pattern: str, paths: List[str], context_after: int = 0, context_before: int = 0) -> List[SearchMatch]:
        """Execute search across specified paths with context."""
        # Validate and adjust context lines
        context_after = min(max(0, context_after), self.config.max_context_lines)
        context_before = min(max(0, context_before), self.config.max_context_lines)
        
        # Check cache if enabled
        cache_key = f"{pattern}:{','.join(paths)}:{context_after}:{context_before}"
        if self.config.cache_results and cache_key in self._result_cache:
            return self._result_cache[cache_key]
            
        results: List[SearchMatch] = []
        
        # Search each specified path
        for path_key in paths:
            if path_key not in self.config.search_paths:
                continue
                
            base_dir = self.config.search_paths[path_key]
            if not base_dir.exists():
                continue
                
            # Search through files
            target_paths = []
            if hasattr(self, 'limit_path') and self.limit_path:
                limit_path = self.limit_path
                # Convert to Path object if it's not already
                if not isinstance(limit_path, Path):
                    limit_path = Path(limit_path)
                
                # If absolute path, use directly if it exists
                if limit_path.is_absolute():
                    if limit_path.exists():
                        target_paths = [limit_path]
                else:
                    # For relative paths, try different matching strategies
                    pattern_parts = limit_path.parts
                    
                    for path in base_dir.rglob('*'):
                        # Skip hidden files
                        if any(part.startswith('.') for part in path.parts):
                            continue
                            
                        # Check if path contains all pattern parts in order
                        path_str = str(path)
                        if all(part in path_str for part in pattern_parts):
                            target_paths.append(path)
            else:
                target_paths = [p for p in base_dir.rglob('*') if p.is_file()]

            for file_path in target_paths:
                if not file_path.is_file() or file_path.suffix not in self.config.file_types:
                    continue
                    
                lines = self._get_file_contents(file_path)
                for i, line in enumerate(lines):
                    if re.search(pattern, line, re.IGNORECASE):
                        match = self._get_context(lines, i, context_after, context_before)
                        match.file_path = file_path
                        results.append(match)
                        
        # Cache results if enabled
        if self.config.cache_results:
            self._result_cache[cache_key] = results
            if len(self._result_cache) > self.config.cache_size:
                # Remove oldest entry
                del self._result_cache[next(iter(self._result_cache))]
                
        return results