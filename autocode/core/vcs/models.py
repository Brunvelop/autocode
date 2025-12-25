"""
Git Models - Modelos Pydantic para estructuras de datos Git.

Este módulo define los modelos de datos usados para representar
estructuras del repositorio Git.
"""
from typing import List, Literal, Optional

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
