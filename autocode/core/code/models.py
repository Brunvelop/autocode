"""
models.py
Modelos de datos para estructura de código normalizada.

Usa estructura plana (adjacency list) para evitar recursión en OpenAPI schema.
Similar a GitNodeEntry/GitTreeGraph en autocode/core/vcs/models.py.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from autocode.interfaces.models import GenericOutput


# Tipos de nodos soportados
NodeType = Literal["directory", "file", "class", "function", "method", "import", "variable"]

# Lenguajes soportados
Language = Literal["python", "javascript"]


class CodeNode(BaseModel):
    """
    Nodo normalizado de estructura de código (no-recursivo / adjacency list).
    
    Representa directorios, archivos, clases, funciones, etc.
    La relación padre-hijo se establece via parent_id, no con children anidados.
    """
    id: str = Field(..., description="ID único del nodo (path::name para código interno)")
    parent_id: Optional[str] = Field(None, description="ID del nodo padre; None solo para root")
    name: str = Field(..., description="Nombre display del nodo")
    type: NodeType = Field(..., description="Tipo de nodo")
    language: Optional[Language] = Field(None, description="Lenguaje del código (null para directorios)")
    path: str = Field(..., description="Path relativo al root")
    line_start: Optional[int] = Field(None, description="Línea de inicio (solo para código)")
    line_end: Optional[int] = Field(None, description="Línea de fin (solo para código)")
    loc: int = Field(0, description="Lines of code")
    
    # Metadata adicional según tipo
    decorators: Optional[List[str]] = Field(None, description="Decoradores (funciones/clases Python)")
    params: Optional[List[str]] = Field(None, description="Parámetros (funciones)")
    bases: Optional[List[str]] = Field(None, description="Clases base (herencia)")
    exports: Optional[bool] = Field(None, description="Es exportado (JS)")
    is_async: Optional[bool] = Field(None, description="Es async (funciones)")


class CodeGraph(BaseModel):
    """
    Representación no-recursiva del árbol de código como grafo.
    
    El frontend puede reconstruir el árbol usando parent_id de cada nodo.
    """
    root_id: str = Field(..., description="ID del nodo raíz")
    nodes: List[CodeNode] = Field(default_factory=list, description="Todos los nodos del árbol")


class CodeStructureResult(BaseModel):
    """
    Resultado de análisis de estructura de código.
    """
    graph: CodeGraph = Field(..., description="Grafo de nodos (no recursivo)")
    languages: List[str] = Field(default_factory=list, description="Lenguajes detectados")
    total_files: int = Field(0, description="Total de archivos")
    total_loc: int = Field(0, description="Total de líneas de código")
    total_functions: int = Field(0, description="Total de funciones")
    total_classes: int = Field(0, description="Total de clases")


class CodeStructureOutput(GenericOutput):
    """
    Output de get_code_structure().
    Extiende GenericOutput con tipado específico para result.
    """
    result: Optional[CodeStructureResult] = None
