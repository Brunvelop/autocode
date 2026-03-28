"""
file_ops.py
Herramientas de archivo para el executor de planes.

Proporciona 4 operaciones atómicas (read, write, replace, delete) registradas
como MCP tools. El ReAct agent las usa para implementar las tareas de un plan.

Seguridad:
- Todos los paths se resuelven relativos al CWD del proyecto.
- Se rechaza cualquier path que intente escapar del directorio del proyecto.
- Límite de lectura de 500KB para evitar desbordar el contexto del LLM.
"""

import logging
from pathlib import Path

from refract import register_function
from autocode.core.planning.models import (
    FileReadResult,
    FileWriteResult,
    FileReplaceResult,
    FileDeleteResult,
)

logger = logging.getLogger(__name__)

# Límite de lectura: 500KB
MAX_READ_SIZE = 500_000


# ==============================================================================
# PATH RESOLUTION
# ==============================================================================


def _resolve_path(path: str) -> Path:
    """Resuelve un path relativo al CWD del proyecto, con protección contra traversal.

    Args:
        path: Path relativo (e.g. "src/main.py", "tests/test_foo.py")

    Returns:
        Path absoluto resuelto, garantizado dentro del CWD.
    """
    cwd = Path.cwd()
    resolved = (cwd / path).resolve()

    # Protección contra path traversal: fail-closed
    if not str(resolved).startswith(str(cwd)):
        raise ValueError(
            f"Path traversal detected: '{path}' resolves outside project directory"
        )

    return resolved


# ==============================================================================
# MCP TOOLS
# ==============================================================================


@register_function(interfaces=["mcp"])
def read_file_content(path: str) -> FileReadResult:
    """Read the content of a file.

    Reads a file relative to the project root. Files larger than 500KB
    are truncated with a warning. Returns content, path, and size.

    Args:
        path: Relative path to the file to read
    """
    resolved = _resolve_path(path)

    if not resolved.exists():
        raise ValueError(f"File not found: {path}")

    size = resolved.stat().st_size
    content = resolved.read_text(encoding="utf-8")

    # Truncar si excede el límite
    truncated = False
    if size > MAX_READ_SIZE:
        content = content[:MAX_READ_SIZE]
        truncated = True

    return FileReadResult(
        content=content,
        path=str(path),
        size=size,
        truncated=truncated,
    )


@register_function(interfaces=["mcp"])
def write_file_content(path: str, content: str) -> FileWriteResult:
    """Write content to a file, creating directories if needed.

    Creates or overwrites a file with the given content. Parent directories
    are created automatically if they don't exist.

    Args:
        path: Relative path to the file to write
        content: Content to write to the file
    """
    resolved = _resolve_path(path)

    # Crear directorios intermedios
    resolved.parent.mkdir(parents=True, exist_ok=True)

    # Escribir contenido
    resolved.write_text(content, encoding="utf-8")
    bytes_written = len(content.encode("utf-8"))

    return FileWriteResult(
        path=str(path),
        bytes_written=bytes_written,
    )


@register_function(interfaces=["mcp"])
def replace_in_file(path: str, old_string: str, new_string: str) -> FileReplaceResult:
    """Replace the first occurrence of a string in a file.

    Searches for old_string in the file and replaces only the first
    occurrence with new_string. Reports the total number of occurrences found.

    Args:
        path: Relative path to the file to modify
        old_string: Exact string to search for (can be multiline)
        new_string: Replacement string
    """
    resolved = _resolve_path(path)

    if not resolved.exists():
        raise ValueError(f"File not found: {path}")

    content = resolved.read_text(encoding="utf-8")

    # Contar ocurrencias
    occurrences = content.count(old_string)

    if occurrences == 0:
        raise ValueError(f"old_string not found in {path}")

    # Reemplazar solo la primera ocurrencia
    new_content = content.replace(old_string, new_string, 1)
    resolved.write_text(new_content, encoding="utf-8")

    return FileReplaceResult(
        replaced=True,
        occurrences=occurrences,
        path=str(path),
    )


@register_function(interfaces=["mcp"])
def delete_file(path: str) -> FileDeleteResult:
    """Delete a file.

    Removes a file from the filesystem. Returns error if the file
    does not exist.

    Args:
        path: Relative path to the file to delete
    """
    resolved = _resolve_path(path)

    if not resolved.exists():
        raise ValueError(f"File not found: {path}")

    resolved.unlink()

    return FileDeleteResult(deleted=str(path))
