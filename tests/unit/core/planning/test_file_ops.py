"""
Tests for file operation tools registered as MCP.

RED phase: These tests define the expected behavior for:
- read_file_content: read files with size limits
- write_file_content: create/overwrite files with directory creation
- replace_in_file: search-and-replace with occurrence tracking
- delete_file: remove files safely
- _resolve_path: path resolution with traversal protection
- MCP registration: functions exposed only as MCP tools
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from autocode.core.planning.file_ops import (
    read_file_content,
    write_file_content,
    replace_in_file,
    delete_file,
    _resolve_path,
)


class TestReadFileContent:
    """Tests for read_file_content MCP tool."""

    def test_read_existing_file(self, tmp_path):
        """Lee un archivo existente y retorna su contenido."""
        f = tmp_path / "hello.py"
        f.write_text("print('hello')", encoding="utf-8")
        with patch("autocode.core.planning.file_ops._resolve_path", return_value=f):
            result = read_file_content(path="hello.py")
        assert result.success is True
        assert result.result["content"] == "print('hello')"

    def test_read_nonexistent_file(self):
        """Retorna error si el archivo no existe."""
        with patch(
            "autocode.core.planning.file_ops._resolve_path",
            return_value=Path("/nonexistent/file.py"),
        ):
            result = read_file_content(path="nonexistent.py")
        assert result.success is False
        assert (
            "no encontrado" in result.message.lower()
            or "not found" in result.message.lower()
        )

    def test_read_file_size_limit(self, tmp_path):
        """Retorna warning/truncamiento si el archivo excede el límite (~500KB)."""
        f = tmp_path / "big.txt"
        f.write_text("x" * 600_000, encoding="utf-8")
        with patch("autocode.core.planning.file_ops._resolve_path", return_value=f):
            result = read_file_content(path="big.txt")
        # Debe indicar que es muy grande (puede ser truncamiento con warning)
        assert result.success is True
        assert "truncat" in result.message.lower() or "size" in result.message.lower()

    def test_read_file_returns_path_and_size(self, tmp_path):
        """El resultado incluye path y size además del contenido."""
        f = tmp_path / "test.py"
        f.write_text("content", encoding="utf-8")
        with patch("autocode.core.planning.file_ops._resolve_path", return_value=f):
            result = read_file_content(path="test.py")
        assert "size" in result.result
        assert "path" in result.result


class TestWriteFileContent:
    """Tests for write_file_content MCP tool."""

    def test_write_new_file(self, tmp_path):
        """Crea un archivo nuevo con el contenido dado."""
        target = tmp_path / "new_file.py"
        with patch("autocode.core.planning.file_ops._resolve_path", return_value=target):
            result = write_file_content(path="new_file.py", content="print('new')")
        assert result.success is True
        assert target.read_text() == "print('new')"

    def test_write_creates_directories(self, tmp_path):
        """Crea directorios intermedios si no existen."""
        target = tmp_path / "deep" / "nested" / "dir" / "file.py"
        with patch("autocode.core.planning.file_ops._resolve_path", return_value=target):
            result = write_file_content(path="deep/nested/dir/file.py", content="# new")
        assert result.success is True
        assert target.exists()

    def test_write_overwrites_existing(self, tmp_path):
        """Sobreescribe archivo existente."""
        target = tmp_path / "existing.py"
        target.write_text("old content")
        with patch("autocode.core.planning.file_ops._resolve_path", return_value=target):
            result = write_file_content(path="existing.py", content="new content")
        assert result.success is True
        assert target.read_text() == "new content"

    def test_write_returns_bytes_written(self, tmp_path):
        """El resultado incluye la cantidad de bytes escritos."""
        target = tmp_path / "test.py"
        with patch("autocode.core.planning.file_ops._resolve_path", return_value=target):
            result = write_file_content(path="test.py", content="hello")
        assert result.result["bytes_written"] == 5


class TestReplaceInFile:
    """Tests for replace_in_file MCP tool (search-and-replace)."""

    def test_replace_single_occurrence(self, tmp_path):
        """Reemplaza una única ocurrencia de old_string por new_string."""
        f = tmp_path / "code.py"
        f.write_text("def hello():\n    return 'hello'\n")
        with patch("autocode.core.planning.file_ops._resolve_path", return_value=f):
            result = replace_in_file(
                path="code.py", old_string="'hello'", new_string="'world'"
            )
        assert result.success is True
        assert f.read_text() == "def hello():\n    return 'world'\n"

    def test_replace_old_string_not_found(self, tmp_path):
        """Retorna error si old_string no existe en el archivo."""
        f = tmp_path / "code.py"
        f.write_text("def hello(): pass\n")
        with patch("autocode.core.planning.file_ops._resolve_path", return_value=f):
            result = replace_in_file(
                path="code.py", old_string="nonexistent", new_string="new"
            )
        assert result.success is False
        assert (
            "not found" in result.message.lower()
            or "no encontr" in result.message.lower()
        )

    def test_replace_multiple_occurrences_replaces_first(self, tmp_path):
        """Si hay múltiples ocurrencias, reemplaza solo la primera y avisa."""
        f = tmp_path / "code.py"
        f.write_text("a = 1\nb = 1\nc = 1\n")
        with patch("autocode.core.planning.file_ops._resolve_path", return_value=f):
            result = replace_in_file(path="code.py", old_string="1", new_string="2")
        assert result.success is True
        content = f.read_text()
        assert content == "a = 2\nb = 1\nc = 1\n"  # Solo primera
        assert result.result["occurrences"] == 3  # Informa cuántas había

    def test_replace_multiline_block(self, tmp_path):
        """Puede reemplazar bloques multilínea."""
        f = tmp_path / "code.py"
        f.write_text("class Foo:\n    x = 1\n    y = 2\n")
        old = "    x = 1\n    y = 2"
        new = "    x = 10\n    y = 20\n    z = 30"
        with patch("autocode.core.planning.file_ops._resolve_path", return_value=f):
            result = replace_in_file(path="code.py", old_string=old, new_string=new)
        assert result.success is True
        assert "z = 30" in f.read_text()

    def test_replace_nonexistent_file(self):
        """Retorna error si el archivo no existe."""
        with patch(
            "autocode.core.planning.file_ops._resolve_path",
            return_value=Path("/nonexistent/file.py"),
        ):
            result = replace_in_file(path="file.py", old_string="a", new_string="b")
        assert result.success is False


class TestDeleteFile:
    """Tests for delete_file MCP tool."""

    def test_delete_existing_file(self, tmp_path):
        """Elimina un archivo existente."""
        f = tmp_path / "to_delete.py"
        f.write_text("delete me")
        with patch("autocode.core.planning.file_ops._resolve_path", return_value=f):
            result = delete_file(path="to_delete.py")
        assert result.success is True
        assert not f.exists()

    def test_delete_nonexistent_file(self):
        """Retorna error si el archivo no existe."""
        with patch(
            "autocode.core.planning.file_ops._resolve_path",
            return_value=Path("/nonexistent/file.py"),
        ):
            result = delete_file(path="nonexistent.py")
        assert result.success is False


class TestResolvePath:
    """Tests for _resolve_path helper."""

    def test_resolve_relative_path(self):
        """Resuelve path relativo al CWD del proyecto."""
        resolved = _resolve_path("src/main.py")
        assert resolved.is_absolute()

    def test_resolve_rejects_path_traversal(self):
        """Rechaza paths que intentan salir del proyecto (../../etc/passwd)."""
        with pytest.raises(ValueError, match="Path traversal"):
            _resolve_path("../../etc/passwd")


class TestFileOpsRegistration:
    """Tests for file_ops MCP registration.

    Note: The autouse cleanup_registry fixture clears the registry between tests,
    but importlib won't re-execute decorators for already-imported modules.
    We use importlib.reload() to force re-registration of file_ops decorators.
    """

    def test_functions_registered_as_mcp(self):
        """Las 4 funciones se registran con interfaces=['mcp']."""
        import importlib
        from autocode.core import registry as reg_module
        import autocode.core.planning.file_ops as file_ops_module

        importlib.reload(file_ops_module)
        mcp_funcs = [f for f in reg_module._registry if "mcp" in f.interfaces]
        names = [f.name for f in mcp_funcs]
        assert "read_file_content" in names
        assert "write_file_content" in names
        assert "replace_in_file" in names
        assert "delete_file" in names

    def test_functions_not_registered_as_api(self):
        """Las file_ops NO se exponen como API endpoints."""
        import importlib
        from autocode.core import registry as reg_module
        import autocode.core.planning.file_ops as file_ops_module

        importlib.reload(file_ops_module)
        api_funcs = [f for f in reg_module._registry if "api" in f.interfaces]
        names = [f.name for f in api_funcs]
        assert "read_file_content" not in names
        assert "write_file_content" not in names
        assert "replace_in_file" not in names
        assert "delete_file" not in names
