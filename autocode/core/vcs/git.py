"""
git.py
Shared git helper functions for the autocode project.

Provides low-level subprocess wrappers for git operations used
across metrics, architecture, planning, and review modules.
Extracted from duplicated _git() helpers in metrics.py, planner.py,
executor.py, and reviewer.py.
"""

import subprocess
from pathlib import Path
from typing import List, Optional


def git(*args: str, cwd: str = ".") -> str:
    """Run a git command and return stripped stdout. Errors silenced.

    Args:
        *args: Git subcommand and arguments (e.g., "rev-parse", "HEAD")
        cwd: Working directory for the git command (default: ".")

    Returns:
        Stripped stdout string, empty on failure.
    """
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True, text=True, check=False, cwd=cwd,
    )
    return result.stdout.strip()


def git_checked(*args: str, cwd: str = ".") -> str:
    """Run a git command, raising RuntimeError on failure.

    For critical operations where failure should halt execution.

    Args:
        *args: Git subcommand and arguments
        cwd: Working directory for the git command (default: ".")

    Returns:
        Stripped stdout string on success.

    Raises:
        RuntimeError: If git exits with non-zero code.
    """
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True, text=True, check=False, cwd=cwd,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or (
            f"git {args[0]} failed with code {result.returncode}"
        )
        raise RuntimeError(f"git error: {stderr}")
    return result.stdout.strip()


def git_show(ref: str, cwd: str = ".") -> Optional[str]:
    """Get file content at a specific git ref.

    Args:
        ref: Git ref (e.g., "HEAD:path/to/file.py")
        cwd: Working directory for the git command (default: ".")

    Returns:
        File content string, or None on error.
    """
    result = subprocess.run(
        ["git", "show", ref],
        capture_output=True, text=True, check=False, cwd=cwd,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def git_add_and_commit(
    files: List[str], message: str, cwd: str = "."
) -> str:
    """Execute git add + git commit and return the commit hash.

    Args:
        files: List of file paths to stage.
        message: Commit message.
        cwd: Working directory for the git command (default: ".")

    Returns:
        Hash of the created commit.
    """
    for f in files:
        subprocess.run(
            ["git", "add", f], check=True, cwd=cwd,
            capture_output=True, text=True,
        )
    subprocess.run(
        ["git", "commit", "-m", message], check=True, cwd=cwd,
        capture_output=True, text=True,
    )
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True, cwd=cwd,
    )
    return result.stdout.strip()


def get_tracked_files_at_commit(
    commit: str, *extensions: str, cwd: str = "."
) -> List[str]:
    """Get all files tracked by git at a specific commit matching the given extensions.

    Uses `git ls-tree -r --name-only <commit>` to list files at a historical
    commit, then filters results to ensure exact extension match.

    Args:
        commit: Git commit hash or ref to inspect.
        *extensions: File extensions to include (e.g., ".py", ".js", ".mjs")
        cwd: Working directory for the git command (default: ".")

    Returns:
        List of relative file paths matching the requested extensions at that commit.
    """
    if not extensions:
        return []

    output = git("ls-tree", "-r", "--name-only", commit, cwd=cwd)

    if not output:
        return []

    ext_set = set(extensions)
    return [f for f in output.split("\n") if f and Path(f).suffix in ext_set]


def get_tracked_files(*extensions: str, cwd: str = ".") -> List[str]:
    """Get all files tracked by git matching the given extensions.

    Uses `git ls-files --cached` with glob patterns per extension,
    then filters results to ensure exact extension match.

    Args:
        *extensions: File extensions to include (e.g., ".py", ".js", ".mjs")
        cwd: Working directory for the git command (default: ".")

    Returns:
        List of relative file paths matching the requested extensions.
    """
    if not extensions:
        return []

    # Build git ls-files args with glob patterns
    patterns = [f"*{ext}" for ext in extensions]
    output = git("ls-files", "--cached", *patterns, cwd=cwd)

    if not output:
        return []

    # Filter to ensure exact extension match (git glob may be broader)
    ext_set = set(extensions)
    return [
        f for f in output.split("\n")
        if f and Path(f).suffix in ext_set
    ]
