"""
base.py
Clase base abstracta para parsers de código.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from autocode.core.code.models import CodeNode


class BaseParser(ABC):
    """
    Parser base para extraer estructura de código.
    Cada lenguaje implementa su propio parser.
    
    El método principal es parse_flat() que devuelve una lista plana
    de nodos con parent_id para evitar recursión en OpenAPI schema.
    """
    
    # Lenguaje que parsea este parser
    language: str = ""
    
    @abstractmethod
    def parse_flat(self, file_path: str) -> List[CodeNode]:
        """
        Parsea un archivo y devuelve una lista plana de nodos.
        
        El primer nodo es siempre el archivo, seguido de sus contenidos
        (imports, clases, funciones, métodos).
        
        Args:
            file_path: Path al archivo a parsear
            
        Returns:
            Lista plana de CodeNodes con parent_id establecido
        """
        pass
    
    def _read_file(self, file_path: str) -> str:
        """
        Lee el contenido de un archivo.
        
        Args:
            file_path: Path al archivo
            
        Returns:
            Contenido del archivo como string
        """
        path = Path(file_path)
        try:
            return path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Intentar con latin-1 si UTF-8 falla
            return path.read_text(encoding='latin-1')
    
    def _count_lines(self, content: str) -> int:
        """
        Cuenta líneas de código (no vacías).
        
        Args:
            content: Contenido del código
            
        Returns:
            Número de líneas no vacías
        """
        lines = content.split('\n')
        return sum(1 for line in lines if line.strip())
    
    def _create_file_node(self, file_path: str) -> CodeNode:
        """
        Crea un CodeNode de tipo file.
        
        Args:
            file_path: Path al archivo
            
        Returns:
            CodeNode representando el archivo
        """
        path = Path(file_path)
        content = self._read_file(file_path)
        loc = self._count_lines(content)
        
        return CodeNode(
            id=file_path,
            parent_id=None,  # Se establece en structure.py
            name=path.name,
            type="file",
            language=self.language,
            path=file_path,
            loc=loc
        )
