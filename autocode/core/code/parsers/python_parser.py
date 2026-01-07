"""
python_parser.py
Parser de código Python usando el módulo ast.
"""

import ast
from pathlib import Path
from typing import List

from autocode.core.code.models import CodeNode
from .base import BaseParser


class PythonParser(BaseParser):
    """
    Parser para archivos Python usando ast.
    Extrae clases, funciones, imports y su estructura.
    """
    
    language = "python"
    
    def parse_flat(self, file_path: str) -> List[CodeNode]:
        """
        Parsea un archivo Python y devuelve una lista plana de nodos.
        
        Args:
            file_path: Path al archivo .py
            
        Returns:
            Lista plana de CodeNodes con parent_id establecido
        """
        nodes = []
        
        try:
            content = self._read_file(file_path)
            file_node = self._create_file_node(file_path)
            nodes.append(file_node)
            
            tree = ast.parse(content, filename=file_path)
            self._extract_nodes_flat(tree, file_path, content, nodes, parent_id=file_path)
            
            return nodes
            
        except SyntaxError:
            # Si hay error de sintaxis, devolver solo el nodo de archivo
            return [self._create_file_node(file_path)]
        except Exception:
            # Cualquier otro error, devolver solo el nodo de archivo
            return [self._create_file_node(file_path)]
    
    def _extract_nodes_flat(
        self, 
        tree: ast.Module, 
        file_path: str, 
        content: str, 
        nodes: List[CodeNode],
        parent_id: str
    ) -> None:
        """
        Extrae nodos de nivel superior del AST y los agrega a la lista.
        
        Args:
            tree: AST parseado
            file_path: Path del archivo
            content: Contenido del archivo
            nodes: Lista de nodos (se modifica in-place)
            parent_id: ID del nodo padre
        """
        lines = content.split('\n')
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_node = self._create_import_node(
                        file_path, alias.name, node.lineno, node.lineno, parent_id
                    )
                    nodes.append(import_node)
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                names = [alias.name for alias in node.names]
                import_name = f"from {module} import {', '.join(names)}"
                import_node = self._create_import_node(
                    file_path, import_name, node.lineno, node.lineno, parent_id
                )
                nodes.append(import_node)
            
            elif isinstance(node, ast.ClassDef):
                self._parse_class_flat(node, file_path, lines, nodes, parent_id)
            
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_node = self._create_function_node(node, file_path, lines, "function", parent_id)
                nodes.append(func_node)
    
    def _parse_class_flat(
        self, 
        node: ast.ClassDef, 
        file_path: str, 
        lines: list[str], 
        nodes: List[CodeNode],
        parent_id: str
    ) -> None:
        """
        Parsea una clase y agrega sus nodos a la lista.
        
        Args:
            node: Nodo AST de la clase
            file_path: Path del archivo
            lines: Líneas del archivo
            nodes: Lista de nodos (se modifica in-place)
            parent_id: ID del nodo padre
        """
        class_id = f"{file_path}::{node.name}"
        
        # Extraer decoradores
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        
        # Extraer clases base
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{self._get_attribute_name(base)}")
        
        # Calcular LOC
        line_start = node.lineno
        line_end = node.end_lineno or node.lineno
        loc = self._count_node_lines(lines, line_start, line_end)
        
        # Crear nodo de clase
        class_node = CodeNode(
            id=class_id,
            parent_id=parent_id,
            name=node.name,
            type="class",
            language=self.language,
            path=file_path,
            line_start=line_start,
            line_end=line_end,
            loc=loc,
            decorators=decorators if decorators else None,
            bases=bases if bases else None
        )
        nodes.append(class_node)
        
        # Agregar métodos de la clase
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_node = self._create_method_node(item, file_path, lines, node.name, class_id)
                nodes.append(method_node)
    
    def _create_function_node(
        self, 
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: str, 
        lines: list[str], 
        node_type: str,
        parent_id: str
    ) -> CodeNode:
        """
        Crea un CodeNode para función.
        
        Args:
            node: Nodo AST
            file_path: Path del archivo
            lines: Líneas del archivo
            node_type: "function" o "method"
            parent_id: ID del nodo padre
            
        Returns:
            CodeNode
        """
        # Extraer decoradores
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        
        # Extraer parámetros
        params = [arg.arg for arg in node.args.args]
        
        # Calcular LOC
        line_start = node.lineno
        line_end = node.end_lineno or node.lineno
        loc = self._count_node_lines(lines, line_start, line_end)
        
        # Detectar si es async
        is_async = isinstance(node, ast.AsyncFunctionDef)
        
        return CodeNode(
            id=f"{file_path}::{node.name}",
            parent_id=parent_id,
            name=node.name,
            type=node_type,
            language=self.language,
            path=file_path,
            line_start=line_start,
            line_end=line_end,
            loc=loc,
            decorators=decorators if decorators else None,
            params=params if params else None,
            is_async=is_async if is_async else None
        )
    
    def _create_method_node(
        self, 
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: str, 
        lines: list[str],
        class_name: str,
        parent_id: str
    ) -> CodeNode:
        """
        Crea un CodeNode para método de clase.
        
        Args:
            node: Nodo AST del método
            file_path: Path del archivo
            lines: Líneas del archivo
            class_name: Nombre de la clase contenedora
            parent_id: ID del nodo padre (la clase)
            
        Returns:
            CodeNode
        """
        # Extraer decoradores
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        
        # Extraer parámetros (excluyendo self)
        params = [arg.arg for arg in node.args.args if arg.arg != 'self']
        
        # Calcular LOC
        line_start = node.lineno
        line_end = node.end_lineno or node.lineno
        loc = self._count_node_lines(lines, line_start, line_end)
        
        # Detectar si es async
        is_async = isinstance(node, ast.AsyncFunctionDef)
        
        return CodeNode(
            id=f"{file_path}::{class_name}::{node.name}",
            parent_id=parent_id,
            name=node.name,
            type="method",
            language=self.language,
            path=file_path,
            line_start=line_start,
            line_end=line_end,
            loc=loc,
            decorators=decorators if decorators else None,
            params=params if params else None,
            is_async=is_async if is_async else None
        )
    
    def _create_import_node(
        self, 
        file_path: str, 
        name: str, 
        line_start: int, 
        line_end: int,
        parent_id: str
    ) -> CodeNode:
        """
        Crea un CodeNode para un import.
        
        Args:
            file_path: Path del archivo
            name: Nombre/descripción del import
            line_start: Línea de inicio
            line_end: Línea de fin
            parent_id: ID del nodo padre
            
        Returns:
            CodeNode
        """
        return CodeNode(
            id=f"{file_path}::import::{name}",
            parent_id=parent_id,
            name=name,
            type="import",
            language=self.language,
            path=file_path,
            line_start=line_start,
            line_end=line_end,
            loc=1
        )
    
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Extrae el nombre de un decorador."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return self._get_attribute_name(decorator)
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return "unknown"
    
    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Extrae el nombre completo de un atributo (ej: module.Class)."""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return '.'.join(reversed(parts))
    
    def _count_node_lines(self, lines: list[str], start: int, end: int) -> int:
        """
        Cuenta líneas no vacías en un rango.
        
        Args:
            lines: Todas las líneas del archivo
            start: Línea de inicio (1-indexed)
            end: Línea de fin (1-indexed)
            
        Returns:
            Número de líneas no vacías
        """
        # Ajustar índices (ast usa 1-indexed)
        relevant_lines = lines[start - 1:end]
        return sum(1 for line in relevant_lines if line.strip())
