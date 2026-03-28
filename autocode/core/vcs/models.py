"""
Git Models - Modelos Pydantic para estructuras de datos Git.

Este módulo define los modelos de datos usados para representar
estructuras del repositorio Git.
"""
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

FileStatus = Literal["added", "modified", "deleted", "renamed", "untracked", "staged"]


class GitNodeEntry(BaseModel):
    """Representación plana de un nodo en el árbol git (no-recursivo / adjacency list)."""

    id: str = Field(description="ID estable del nodo (usamos path completo; root es string vacío)")
    parent_id: Optional[str] = Field(default=None, description="ID del nodo padre; None solo para root")
    name: str = Field(description="Nombre del archivo o directorio")
    path: str = Field(description="Path completo desde la raíz del repositorio")
    type: Literal["file", "directory"] = Field(description="Tipo del nodo")
    size: int = Field(default=0, description="Tamaño en bytes (solo archivos)")


class GitTreeGraph(BaseModel):
    """Representación no-recursiva del árbol como grafo."""

    root_id: str = Field(description="ID del nodo raíz")
    nodes: List[GitNodeEntry] = Field(default_factory=list, description="Todos los nodos del árbol")


# ==============================================================================
# GIT STATUS MODELS
# ==============================================================================


class GitFileStatus(BaseModel):
    """Estado de un archivo individual en el repositorio."""

    path: str = Field(..., description="Path relativo del archivo")
    status: FileStatus = Field(..., description="Estado del archivo")
    staged: bool = Field(default=False, description="Si está en staging area")
    old_path: Optional[str] = Field(None, description="Path anterior (para renamed)")
    additions: int = Field(default=0, description="Líneas añadidas")
    deletions: int = Field(default=0, description="Líneas eliminadas")


class GitStatusResult(BaseModel):
    """Resultado del status del repositorio."""

    branch: str = Field(..., description="Nombre de la branch actual")
    is_clean: bool = Field(default=True, description="Si el repo está limpio")
    files: List[GitFileStatus] = Field(default_factory=list, description="Archivos con cambios")

    # Contadores por tipo
    total_added: int = Field(default=0, description="Total archivos añadidos")
    total_modified: int = Field(default=0, description="Total archivos modificados")
    total_deleted: int = Field(default=0, description="Total archivos eliminados")
    total_untracked: int = Field(default=0, description="Total archivos sin trackear")
    total_staged: int = Field(default=0, description="Total archivos en staging")


class GitStatusSummary(BaseModel):
    """Resumen compacto del git status en texto plano (para MCP/LLM)."""

    summary: str = Field(..., description="Texto compacto del status")


# ==============================================================================
# GIT LOG / GRAPH MODELS
# ==============================================================================


class GitCommit(BaseModel):
    """Representación de un commit en el grafo git."""

    hash: str = Field(description="SHA completo del commit")
    short_hash: str = Field(description="SHA abreviado (7 chars)")
    message: str = Field(description="Primera línea del mensaje de commit")
    author: str = Field(description="Nombre del autor")
    author_email: str = Field(default="", description="Email del autor")
    date: str = Field(description="Fecha ISO 8601")
    parents: List[str] = Field(default_factory=list, description="Hashes de commits padres")
    branches: List[str] = Field(default_factory=list, description="Ramas que apuntan a este commit")
    tags: List[str] = Field(default_factory=list, description="Tags que apuntan a este commit")
    is_merge: bool = Field(default=False, description="True si tiene 2+ padres")


class GitBranch(BaseModel):
    """Representación de una rama git."""

    name: str = Field(description="Nombre de la rama")
    head_commit: str = Field(description="Hash del commit HEAD de la rama")
    is_current: bool = Field(default=False, description="Si es la rama activa")
    is_remote: bool = Field(default=False, description="Si es una rama remota")


class GitLogGraph(BaseModel):
    """Grafo del historial de commits con info de ramas."""

    commits: List[GitCommit] = Field(default_factory=list, description="Commits ordenados por fecha desc")
    branches: List[GitBranch] = Field(default_factory=list, description="Todas las ramas")


class GitLogSummary(BaseModel):
    """Resumen compacto del historial de commits en texto plano (para MCP/LLM)."""

    summary: str = Field(..., description="Texto compacto del log")


class GitFileChange(BaseModel):
    """Cambio en un archivo dentro de un commit."""

    path: str = Field(description="Path relativo del archivo")
    status: str = Field(description="Estado: added, modified, deleted, renamed")
    additions: int = Field(default=0, description="Líneas añadidas")
    deletions: int = Field(default=0, description="Líneas eliminadas")
    old_path: Optional[str] = Field(default=None, description="Path anterior si renamed")


class GitCommitDetail(BaseModel):
    """Detalle completo de un commit incluyendo archivos cambiados."""

    hash: str = Field(description="SHA completo")
    short_hash: str = Field(description="SHA abreviado")
    message_full: str = Field(description="Mensaje completo del commit")
    author: str = Field(description="Nombre del autor")
    author_email: str = Field(default="", description="Email del autor")
    date: str = Field(description="Fecha ISO 8601")
    parents: List[str] = Field(default_factory=list, description="Hashes de padres")
    files: List[GitFileChange] = Field(default_factory=list, description="Archivos modificados")
    stats: Dict[str, int] = Field(
        default_factory=dict,
        description="Estadísticas: total_additions, total_deletions, files_changed"
    )


