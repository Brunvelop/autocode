"""
execution.py
Async git primitives for sandboxing plan execution.

Provides low-level async subprocess wrappers for git operations
used by ExecutionSandbox to snapshot, collect, and revert
workspace changes around agent execution.
"""

import asyncio
from typing import Optional


# ==============================================================================
# Async git primitives
# ==============================================================================


async def async_rev_parse_head(cwd: str) -> str:
    """Return the current HEAD commit hash, or empty string on failure.

    Args:
        cwd: Working directory of the git repository.

    Returns:
        Stripped SHA hash string, or "" if not a git repo / git not found.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "rev-parse", "HEAD",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode != 0:
            return ""
        return stdout.decode().strip()
    except Exception:
        return ""


async def async_diff_name_only(cwd: str, ref: str) -> list[str]:
    """Return list of files changed since *ref*.

    Runs ``git diff --name-only <ref>`` and returns non-empty lines.

    Args:
        cwd: Working directory of the git repository.
        ref: Git ref to diff against (e.g. a commit hash).

    Returns:
        List of changed file paths, or [] on failure / no changes.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "diff", "--name-only", ref,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode != 0:
            return []
        lines = stdout.decode().splitlines()
        return [line for line in lines if line]
    except Exception:
        return []


async def async_reset_mixed(cwd: str, ref: str) -> None:
    """Run ``git reset --mixed <ref>`` (best effort, errors silenced).

    Unstages commits made by the agent without touching working tree files,
    so the diff against *ref* captures everything as unstaged changes.

    Args:
        cwd: Working directory of the git repository.
        ref: Git ref to reset to.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "reset", "--mixed", ref,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        await proc.communicate()
    except Exception:
        pass


async def async_reset_hard(cwd: str, ref: str) -> None:
    """Run ``git reset --hard <ref>`` (best effort, errors silenced).

    Discards all uncommitted changes and resets HEAD to *ref*.

    Args:
        cwd: Working directory of the git repository.
        ref: Git ref to reset to.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "reset", "--hard", ref,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        await proc.communicate()
    except Exception:
        pass
