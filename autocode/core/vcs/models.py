"""
Git Models - Modelos Pydantic para estructuras de datos Git.

Este módulo define los modelos de datos usados para representar
estructuras del repositorio Git.
"""
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from autocode.interfaces.models import GenericOutput


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


class GitTreeOutput(GenericOutput):
    """Output específico para la estructura del árbol git."""

    result: Optional[GitTreeGraph] = Field(default=None, description="Representación en grafo del árbol git")


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


class GitLogOutput(GenericOutput):
    """Output de get_git_log()."""

    result: Optional[GitLogGraph] = Field(default=None, description="Grafo del log git")


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


class GitCommitDetailOutput(GenericOutput):
    """Output de get_commit_detail()."""

    result: Optional[GitCommitDetail] = Field(default=None, description="Detalle del commit")
