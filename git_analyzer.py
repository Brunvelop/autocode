"""
Git changes analyzer for automatic commit message generation.
"""

import fnmatch
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple, Set


class FileChange(NamedTuple):
    """Represents a change in a file."""
    file: str
    status: str
    staged: bool
    additions: int
    deletions: int
    diff: str


class GitStatus(NamedTuple):
    """Represents repository status summary."""
    total_files: int
    modified: int
    added: int
    deleted: int
    untracked: int
    renamed: int


class GitAnalyzer:
    """Analyzes git changes and generates structured data for commit messages."""
    
    def __init__(self, project_root: Path):
        """Initialize git analyzer.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = project_root
        
    def _run_git_command(self, args: List[str]) -> str:
        """Run a git command and return output.
        
        Args:
            args: Git command arguments
            
        Returns:
            Command output as string
            
        Raises:
            subprocess.CalledProcessError: If git command fails
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git command failed: {e.stderr}") from e
    
    def _get_file_status(self) -> Dict[str, tuple]:
        """Get status of all changed files.
        
        Returns:
            Dict mapping file paths to (index_status, worktree_status) tuples
        """
        status_output = self._run_git_command(["status", "--porcelain"])
        file_status = {}
        
        for line in status_output.split('\n'):
            if not line.strip():
                continue
            
            # Parse porcelain format: XY filename
            index_status = line[0] if line[0] != ' ' else None
            worktree_status = line[1] if line[1] != ' ' else None
            filename = line[3:].strip()
            
            # Handle renamed files (format: "R  old -> new")
            if ' -> ' in filename:
                filename = filename.split(' -> ')[1]
            
            # If it's an untracked directory, expand to individual files
            if worktree_status == '?' and filename.endswith('/'):
                directory_path = Path(self.project_root / filename)
                if directory_path.exists() and directory_path.is_dir():
                    # Recursively find all files in the untracked directory
                    for file_path in directory_path.rglob('*'):
                        if file_path.is_file():
                            relative_path = file_path.relative_to(self.project_root)
                            file_status[str(relative_path)] = (index_status, worktree_status)
                else:
                    file_status[filename] = (index_status, worktree_status)
            else:
                file_status[filename] = (index_status, worktree_status)
        
        return file_status
    
    def _get_file_diff(self, filepath: str, staged: bool = False) -> tuple:
        """Get diff for a specific file.
        
        Args:
            filepath: Path to the file
            staged: Whether to get staged diff
            
        Returns:
            Tuple of (additions, deletions, diff_content)
        """
        # Check if file exists and is untracked
        file_path = Path(self.project_root / filepath)
        if not staged and file_path.exists():
            # For untracked files, we need special handling
            try:
                # Try to get diff against /dev/null for untracked files
                diff_args = ["diff", "--no-index", "/dev/null", filepath]
                diff_content = self._run_git_command(diff_args)
                
                # Get numstat for additions/deletions
                numstat_args = ["diff", "--numstat", "--no-index", "/dev/null", filepath]
                numstat_output = self._run_git_command(numstat_args)
                
                additions, deletions = 0, 0
                if numstat_output.strip():
                    parts = numstat_output.split('\t')
                    if len(parts) >= 2:
                        try:
                            additions = int(parts[0]) if parts[0] != '-' else 0
                            deletions = int(parts[1]) if parts[1] != '-' else 0
                        except ValueError:
                            pass
                
                return additions, deletions, diff_content
                
            except RuntimeError:
                # Fallback: count lines manually for untracked files
                try:
                    content = file_path.read_text(encoding='utf-8')
                    lines = len(content.splitlines()) if content else 0
                    return lines, 0, f"+++ New file:\n{content}"
                except Exception:
                    return 0, 0, "Binary file or read error"
        
        # For tracked files (staged/unstaged changes)
        try:
            # Get diff content
            diff_args = ["diff"]
            if staged:
                diff_args.append("--cached")
            diff_args.extend(["--", filepath])
            
            diff_content = self._run_git_command(diff_args)
            
            # Get numstat for additions/deletions
            numstat_args = ["diff", "--numstat"]
            if staged:
                numstat_args.append("--cached")
            numstat_args.extend(["--", filepath])
            
            numstat_output = self._run_git_command(numstat_args)
            
            additions, deletions = 0, 0
            if numstat_output.strip():
                parts = numstat_output.split('\t')
                if len(parts) >= 2:
                    try:
                        additions = int(parts[0]) if parts[0] != '-' else 0
                        deletions = int(parts[1]) if parts[1] != '-' else 0
                    except ValueError:
                        pass
            
            return additions, deletions, diff_content
            
        except RuntimeError:
            return 0, 0, ""
    
    def _categorize_status(self, index_status: Optional[str], worktree_status: Optional[str]) -> str:
        """Categorize file status based on git porcelain format.
        
        Args:
            index_status: Index status character
            worktree_status: Worktree status character
            
        Returns:
            Human-readable status string
        """
        # Priority: staged changes first, then worktree changes
        if index_status:
            if index_status == 'A':
                return 'added'
            elif index_status == 'M':
                return 'modified'
            elif index_status == 'D':
                return 'deleted'
            elif index_status == 'R':
                return 'renamed'
            elif index_status == 'C':
                return 'copied'
        
        if worktree_status:
            if worktree_status == 'M':
                return 'modified'
            elif worktree_status == 'D':
                return 'deleted'
            elif worktree_status == '?':
                return 'untracked'
        
        return 'unknown'
    
    def _load_gitignore_patterns(self) -> Set[str]:
        """Load patterns from .gitignore file.
        
        Returns:
            Set of gitignore patterns
        """
        gitignore_path = self.project_root / '.gitignore'
        patterns = set()
        
        if not gitignore_path.exists():
            return patterns
            
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        patterns.add(line)
        except Exception:
            # If we can't read .gitignore, just return empty set
            pass
            
        return patterns
    
    def _should_ignore_file(self, filepath: str) -> bool:
        """Check if a file should be ignored based on .gitignore patterns.
        
        Args:
            filepath: Path to the file
            
        Returns:
            True if file should be ignored, False otherwise
        """
        # Load gitignore patterns
        ignore_patterns = self._load_gitignore_patterns()
        
        # Convert Windows paths to Unix-style for consistent matching
        normalized_path = filepath.replace('\\', '/')
        
        # Check against each pattern
        for pattern in ignore_patterns:
            # Handle directory patterns (ending with /)
            if pattern.endswith('/'):
                # Check if the file is in a directory that matches the pattern
                dir_pattern = pattern.rstrip('/')
                if fnmatch.fnmatch(normalized_path, f"{dir_pattern}/*") or \
                   fnmatch.fnmatch(normalized_path, f"**/{dir_pattern}/*"):
                    return True
                # Also check if any part of the path matches the directory pattern
                path_parts = normalized_path.split('/')
                for part in path_parts[:-1]:  # Exclude filename
                    if fnmatch.fnmatch(part, dir_pattern):
                        return True
            else:
                # Handle file patterns
                # Check direct match
                if fnmatch.fnmatch(normalized_path, pattern):
                    return True
                # Check if filename matches pattern
                filename = Path(normalized_path).name
                if fnmatch.fnmatch(filename, pattern):
                    return True
                # Check with ** wildcard for nested paths
                if fnmatch.fnmatch(normalized_path, f"**/{pattern}"):
                    return True
        
        return False
    
    def get_all_changes(self) -> List[FileChange]:
        """Get all file changes (staged and unstaged).
        
        Returns:
            List of FileChange objects
        """
        file_status = self._get_file_status()
        changes = []
        
        for filepath, (index_status, worktree_status) in file_status.items():
            # Skip cache files and other typically ignored files
            if self._should_ignore_file(filepath):
                continue
            
            # Handle untracked files (both index and worktree status are '?')
            if index_status == '?' and worktree_status == '?':
                additions, deletions, diff = self._get_file_diff(filepath, staged=False)
                changes.append(FileChange(
                    file=filepath,
                    status='untracked',
                    staged=False,
                    additions=additions,
                    deletions=deletions,
                    diff=diff
                ))
            else:
                # Handle staged changes
                if index_status and index_status != ' ' and index_status != '?':
                    additions, deletions, diff = self._get_file_diff(filepath, staged=True)
                    status = self._categorize_status(index_status, None)
                    changes.append(FileChange(
                        file=filepath,
                        status=status,
                        staged=True,
                        additions=additions,
                        deletions=deletions,
                        diff=diff
                    ))
                
                # Handle unstaged changes
                if worktree_status and worktree_status != ' ' and worktree_status != '?':
                    additions, deletions, diff = self._get_file_diff(filepath, staged=False)
                    status = self._categorize_status(None, worktree_status)
                    changes.append(FileChange(
                        file=filepath,
                        status=status,
                        staged=False,
                        additions=additions,
                        deletions=deletions,
                        diff=diff
                    ))
        
        return changes
    
    def get_repository_status(self, changes: List[FileChange]) -> GitStatus:
        """Get repository status summary.
        
        Args:
            changes: List of file changes
            
        Returns:
            GitStatus summary
        """
        total_files = len(set(change.file for change in changes))
        modified = len([c for c in changes if c.status == 'modified'])
        added = len([c for c in changes if c.status in ['added', 'untracked']])
        deleted = len([c for c in changes if c.status == 'deleted'])
        untracked = len([c for c in changes if c.status == 'untracked'])
        renamed = len([c for c in changes if c.status in ['renamed', 'copied']])
        
        return GitStatus(
            total_files=total_files,
            modified=modified,
            added=added,
            deleted=deleted,
            untracked=untracked,
            renamed=renamed
        )
    
    def analyze_changes(self) -> Dict:
        """Analyze all git changes and return structured data.
        
        Returns:
            Dictionary with structured change data
        """
        changes = self.get_all_changes()
        status = self.get_repository_status(changes)
        
        # Get list of modified files (unique)
        modified_files = list(set(change.file for change in changes))
        modified_files.sort()
        
        # Convert changes to dict format
        changes_data = []
        for change in changes:
            changes_data.append({
                "file": change.file,
                "status": change.status,
                "staged": change.staged,
                "additions": change.additions,
                "deletions": change.deletions,
                "diff": change.diff
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "repository_status": {
                "total_files": status.total_files,
                "modified": status.modified,
                "added": status.added,
                "deleted": status.deleted,
                "untracked": status.untracked,
                "renamed": status.renamed
            },
            "modified_files": modified_files,
            "changes": changes_data
        }
    
    def save_changes_to_file(self, output_path: Path) -> Dict:
        """Analyze changes and save to JSON file.
        
        Args:
            output_path: Path where to save the JSON file
            
        Returns:
            The analyzed changes data
        """
        changes_data = self.analyze_changes()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(changes_data, f, indent=2, ensure_ascii=False)
        
        return changes_data
