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
from autocode.core.models import GenericOutput

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
def read_file_content(path: str) -> GenericOutput:
    """Read the content of a file.

    Reads a file relative to the project root. Files larger than 500KB
    are truncated with a warning. Returns content, path, and size.

    Args:
        path: Relative path to the file to read
    """
    try:
        resolved = _resolve_path(path)

        if not resolved.exists():
            return GenericOutput(
                success=False,
                result=None,
                message=f"File not found: {path}",
            )

        size = resolved.stat().st_size
        content = resolved.read_text(encoding="utf-8")

        # Truncar si excede el límite
        truncated = False
        if size > MAX_READ_SIZE:
            content = content[:MAX_READ_SIZE]
            truncated = True

        message = f"Read {size} bytes from {path}"
        if truncated:
            message = f"File truncated: read {MAX_READ_SIZE} of {size} bytes (size limit exceeded)"

        return GenericOutput(
            success=True,
            result={
                "content": content,
                "path": str(path),
                "size": size,
            },
            message=message,
        )
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        return GenericOutput(success=False, result=None, message=str(e))


@register_function(interfaces=["mcp"])
def write_file_content(path: str, content: str) -> GenericOutput:
    """Write content to a file, creating directories if needed.

    Creates or overwrites a file with the given content. Parent directories
    are created automatically if they don't exist.

    Args:
        path: Relative path to the file to write
        content: Content to write to the file
    """
    try:
        resolved = _resolve_path(path)

        # Crear directorios intermedios
        resolved.parent.mkdir(parents=True, exist_ok=True)

        # Escribir contenido
        resolved.write_text(content, encoding="utf-8")
        bytes_written = len(content.encode("utf-8"))

        return GenericOutput(
            success=True,
            result={
                "path": str(path),
                "bytes_written": bytes_written,
            },
            message=f"Wrote {bytes_written} bytes to {path}",
        )
    except Exception as e:
        logger.error(f"Error writing file {path}: {e}")
        return GenericOutput(success=False, result=None, message=str(e))


@register_function(interfaces=["mcp"])
def replace_in_file(path: str, old_string: str, new_string: str) -> GenericOutput:
    """Replace the first occurrence of a string in a file.

    Searches for old_string in the file and replaces only the first
    occurrence with new_string. Reports the total number of occurrences found.

    Args:
        path: Relative path to the file to modify
        old_string: Exact string to search for (can be multiline)
        new_string: Replacement string
    """
    try:
        resolved = _resolve_path(path)

        if not resolved.exists():
            return GenericOutput(
                success=False,
                result=None,
                message=f"File not found: {path}",
            )

        content = resolved.read_text(encoding="utf-8")

        # Contar ocurrencias
        occurrences = content.count(old_string)

        if occurrences == 0:
            return GenericOutput(
                success=False,
                result={"occurrences": 0},
                message=f"old_string not found in {path}",
            )

        # Reemplazar solo la primera ocurrencia
        new_content = content.replace(old_string, new_string, 1)
        resolved.write_text(new_content, encoding="utf-8")

        message = f"Replaced 1 occurrence in {path}"
        if occurrences > 1:
            message += f" (warning: {occurrences} total occurrences found, only first replaced)"

        return GenericOutput(
            success=True,
            result={
                "replaced": True,
                "occurrences": occurrences,
                "path": str(path),
            },
            message=message,
        )
    except Exception as e:
        logger.error(f"Error replacing in file {path}: {e}")
        return GenericOutput(success=False, result=None, message=str(e))


@register_function(interfaces=["mcp"])
def delete_file(path: str) -> GenericOutput:
    """Delete a file.

    Removes a file from the filesystem. Returns error if the file
    does not exist.

    Args:
        path: Relative path to the file to delete
    """
    try:
        resolved = _resolve_path(path)

        if not resolved.exists():
            return GenericOutput(
                success=False,
                result=None,
                message=f"File not found: {path}",
            )

        resolved.unlink()

        return GenericOutput(
            success=True,
            result={"deleted": str(path)},
            message=f"Deleted {path}",
        )
    except Exception as e:
        logger.error(f"Error deleting file {path}: {e}")
        return GenericOutput(success=False, result=None, message=str(e))
