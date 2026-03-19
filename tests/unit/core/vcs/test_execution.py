"""
Unit tests for autocode.core.vcs.execution module.

Tests for async git primitives:
  - async_rev_parse_head
  - async_diff_name_only
  - async_reset_mixed
  - async_reset_hard

All tests mock asyncio.create_subprocess_exec to avoid needing a real git repo.
asyncio_mode = "auto" (set in pyproject.toml) — no @pytest.mark.asyncio needed.
"""

from unittest.mock import patch, MagicMock, AsyncMock, call

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_proc(stdout: bytes = b"", returncode: int = 0) -> MagicMock:
    """Build a mock asyncio Process whose communicate() returns (stdout, b'')."""
    proc = MagicMock()
    proc.returncode = returncode
    proc.communicate = AsyncMock(return_value=(stdout, b""))
    return proc


# ==============================================================================
# TestAsyncRevParseHead
# ==============================================================================


class TestAsyncRevParseHead:
    """Tests for async_rev_parse_head()."""

    async def test_returns_head_hash_on_success(self):
        """Returns stripped HEAD hash when git exits 0."""
        proc = _make_proc(stdout=b"abc123def456\n", returncode=0)

        with patch(
            "autocode.core.vcs.execution.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            from autocode.core.vcs.execution import async_rev_parse_head

            result = await async_rev_parse_head("/repo")

        assert result == "abc123def456"

    async def test_returns_empty_string_on_failure(self):
        """Returns '' when git exits non-zero (not a repo)."""
        proc = _make_proc(stdout=b"", returncode=128)

        with patch(
            "autocode.core.vcs.execution.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            from autocode.core.vcs.execution import async_rev_parse_head

            result = await async_rev_parse_head("/not-a-repo")

        assert result == ""

    async def test_returns_empty_string_on_exception(self):
        """Returns '' when create_subprocess_exec raises (git not found)."""
        with patch(
            "autocode.core.vcs.execution.asyncio.create_subprocess_exec",
            new=AsyncMock(side_effect=FileNotFoundError("git not found")),
        ):
            from autocode.core.vcs.execution import async_rev_parse_head

            result = await async_rev_parse_head("/repo")

        assert result == ""

    async def test_passes_cwd_to_subprocess(self):
        """Passes cwd argument to create_subprocess_exec."""
        proc = _make_proc(stdout=b"deadbeef\n", returncode=0)
        mock_exec = AsyncMock(return_value=proc)

        with patch(
            "autocode.core.vcs.execution.asyncio.create_subprocess_exec",
            new=mock_exec,
        ):
            from autocode.core.vcs.execution import async_rev_parse_head

            await async_rev_parse_head("/my/project")

        mock_exec.assert_awaited_once()
        _, kwargs = mock_exec.call_args
        assert kwargs.get("cwd") == "/my/project"


# ==============================================================================
# TestAsyncDiffNameOnly
# ==============================================================================


class TestAsyncDiffNameOnly:
    """Tests for async_diff_name_only()."""

    async def test_returns_list_of_changed_files(self):
        """Returns list of file paths from git diff --name-only output."""
        output = b"src/foo.py\nsrc/bar.py\nREADME.md\n"
        proc = _make_proc(stdout=output, returncode=0)

        with patch(
            "autocode.core.vcs.execution.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            from autocode.core.vcs.execution import async_diff_name_only

            result = await async_diff_name_only("/repo", "abc123")

        assert result == ["src/foo.py", "src/bar.py", "README.md"]

    async def test_returns_empty_list_when_no_changes(self):
        """Returns [] when git diff outputs nothing (no changes)."""
        proc = _make_proc(stdout=b"", returncode=0)

        with patch(
            "autocode.core.vcs.execution.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            from autocode.core.vcs.execution import async_diff_name_only

            result = await async_diff_name_only("/repo", "abc123")

        assert result == []

    async def test_returns_empty_list_on_failure(self):
        """Returns [] when git exits with non-zero code."""
        proc = _make_proc(stdout=b"some output", returncode=1)

        with patch(
            "autocode.core.vcs.execution.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            from autocode.core.vcs.execution import async_diff_name_only

            result = await async_diff_name_only("/repo", "abc123")

        assert result == []

    async def test_filters_empty_strings_from_output(self):
        """Filters out empty lines from git output (trailing newline, blank lines)."""
        output = b"src/a.py\n\nsrc/b.py\n"
        proc = _make_proc(stdout=output, returncode=0)

        with patch(
            "autocode.core.vcs.execution.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            from autocode.core.vcs.execution import async_diff_name_only

            result = await async_diff_name_only("/repo", "abc123")

        assert result == ["src/a.py", "src/b.py"]
        assert "" not in result

    async def test_passes_cwd_and_ref_to_subprocess(self):
        """Passes cwd and ref as positional arg to create_subprocess_exec."""
        proc = _make_proc(stdout=b"file.py\n", returncode=0)
        mock_exec = AsyncMock(return_value=proc)

        with patch(
            "autocode.core.vcs.execution.asyncio.create_subprocess_exec",
            new=mock_exec,
        ):
            from autocode.core.vcs.execution import async_diff_name_only

            await async_diff_name_only("/my/project", "deadbeef")

        mock_exec.assert_awaited_once()
        args, kwargs = mock_exec.call_args
        assert kwargs.get("cwd") == "/my/project"
        assert "deadbeef" in args


# ==============================================================================
# TestAsyncResetMixed
# ==============================================================================


class TestAsyncResetMixed:
    """Tests for async_reset_mixed()."""

    async def test_calls_git_reset_mixed_with_correct_ref(self):
        """Calls git reset --mixed <ref> with the supplied ref."""
        proc = _make_proc(returncode=0)
        mock_exec = AsyncMock(return_value=proc)

        with patch(
            "autocode.core.vcs.execution.asyncio.create_subprocess_exec",
            new=mock_exec,
        ):
            from autocode.core.vcs.execution import async_reset_mixed

            await async_reset_mixed("/repo", "abc123")

        mock_exec.assert_awaited_once()
        args, _ = mock_exec.call_args
        assert args == ("git", "reset", "--mixed", "abc123")

    async def test_silently_ignores_errors(self):
        """Does not raise when git exits non-zero (best effort)."""
        proc = _make_proc(returncode=1)

        with patch(
            "autocode.core.vcs.execution.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            from autocode.core.vcs.execution import async_reset_mixed

            # Should not raise
            await async_reset_mixed("/repo", "abc123")

    async def test_passes_cwd_to_subprocess(self):
        """Passes cwd to create_subprocess_exec."""
        proc = _make_proc(returncode=0)
        mock_exec = AsyncMock(return_value=proc)

        with patch(
            "autocode.core.vcs.execution.asyncio.create_subprocess_exec",
            new=mock_exec,
        ):
            from autocode.core.vcs.execution import async_reset_mixed

            await async_reset_mixed("/my/project", "abc123")

        _, kwargs = mock_exec.call_args
        assert kwargs.get("cwd") == "/my/project"


# ==============================================================================
# TestAsyncResetHard
# ==============================================================================


class TestAsyncResetHard:
    """Tests for async_reset_hard()."""

    async def test_calls_git_reset_hard_with_correct_ref(self):
        """Calls git reset --hard <ref> with the supplied ref."""
        proc = _make_proc(returncode=0)
        mock_exec = AsyncMock(return_value=proc)

        with patch(
            "autocode.core.vcs.execution.asyncio.create_subprocess_exec",
            new=mock_exec,
        ):
            from autocode.core.vcs.execution import async_reset_hard

            await async_reset_hard("/repo", "deadbeef")

        mock_exec.assert_awaited_once()
        args, _ = mock_exec.call_args
        assert args == ("git", "reset", "--hard", "deadbeef")

    async def test_silently_ignores_errors(self):
        """Does not raise when git exits non-zero (best effort)."""
        proc = _make_proc(returncode=128)

        with patch(
            "autocode.core.vcs.execution.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=proc),
        ):
            from autocode.core.vcs.execution import async_reset_hard

            # Should not raise
            await async_reset_hard("/repo", "deadbeef")

    async def test_passes_cwd_to_subprocess(self):
        """Passes cwd to create_subprocess_exec."""
        proc = _make_proc(returncode=0)
        mock_exec = AsyncMock(return_value=proc)

        with patch(
            "autocode.core.vcs.execution.asyncio.create_subprocess_exec",
            new=mock_exec,
        ):
            from autocode.core.vcs.execution import async_reset_hard

            await async_reset_hard("/my/project", "deadbeef")

        _, kwargs = mock_exec.call_args
        assert kwargs.get("cwd") == "/my/project"
