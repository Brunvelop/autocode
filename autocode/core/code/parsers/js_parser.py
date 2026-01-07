"""
js_parser.py
Parser de código JavaScript usando regex simple.
No pretende ser completo, solo extraer estructura básica.
"""

import re
from pathlib import Path
from typing import List

from autocode.core.code.models import CodeNode
from .base import BaseParser


class JSParser(BaseParser):
    """
    Parser simple para archivos JavaScript usando regex.
    Extrae clases, funciones e imports de forma básica.
    
    Soporta:
    - class X {} y class X extends Y {}
    - function f() {} y async function f() {}
    - const/let/var f = () => {} y const/let/var f = function() {}
    - import X from 'Y' y import { X } from 'Y'
    - export class/function/const
    """
    
    language = "javascript"
    
    # Regex patterns
    CLASS_PATTERN = re.compile(
        r'^(?P<export>export\s+)?(?:default\s+)?class\s+(?P<name>\w+)'
        r'(?:\s+extends\s+(?P<base>\w+))?',
        re.MULTILINE
    )
    
    FUNCTION_PATTERN = re.compile(
        r'^(?P<export>export\s+)?(?:default\s+)?(?P<async>async\s+)?function\s+(?P<name>\w+)\s*\(',
        re.MULTILINE
    )
    
    ARROW_FUNCTION_PATTERN = re.compile(
        r'^(?P<export>export\s+)?(?:const|let|var)\s+(?P<name>\w+)\s*=\s*(?P<async>async\s+)?'
        r'(?:\([^)]*\)|[^=])\s*=>',
        re.MULTILINE
    )
    
    FUNCTION_EXPRESSION_PATTERN = re.compile(
        r'^(?P<export>export\s+)?(?:const|let|var)\s+(?P<name>\w+)\s*=\s*(?P<async>async\s+)?function\s*\(',
        re.MULTILINE
    )
    
    IMPORT_PATTERN = re.compile(
        r'^import\s+(?:(?P<default>\w+)|(?:\{[^}]+\})|(?:\*\s+as\s+\w+))?'
        r'(?:\s*,\s*(?:\{[^}]+\}|\*\s+as\s+\w+))?\s+from\s+[\'"](?P<module>[^"\']+)[\'"]',
        re.MULTILINE
    )
    
    METHOD_PATTERN = re.compile(
        r'^\s+(?P<async>async\s+)?(?P<name>\w+)\s*\([^)]*\)\s*\{',
        re.MULTILINE
    )
    
    def parse_flat(self, file_path: str) -> List[CodeNode]:
        """
        Parsea un archivo JavaScript y devuelve una lista plana de nodos.
        
        Args:
            file_path: Path al archivo .js
            
        Returns:
            Lista plana de CodeNodes con parent_id establecido
        """
        nodes = []
        
        try:
            content = self._read_file(file_path)
            file_node = self._create_file_node(file_path)
            nodes.append(file_node)
            
            self._extract_nodes_flat(content, file_path, nodes, parent_id=file_path)
            
            return nodes
            
        except Exception:
            # Cualquier error, devolver solo el nodo de archivo
            return [self._create_file_node(file_path)]
    
    def _extract_nodes_flat(
        self, 
        content: str, 
        file_path: str, 
        nodes: List[CodeNode],
        parent_id: str
    ) -> None:
        """
        Extrae nodos del contenido JavaScript y los agrega a la lista.
        
        Args:
            content: Contenido del archivo
            file_path: Path del archivo
            nodes: Lista de nodos (se modifica in-place)
            parent_id: ID del nodo padre
        """
        lines = content.split('\n')
        existing_ids = set()
        
        # Extraer imports
        for match in self.IMPORT_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            module = match.group('module')
            import_node = self._create_import_node(file_path, module, line_num, parent_id)
            nodes.append(import_node)
        
        # Extraer clases
        for match in self.CLASS_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            name = match.group('name')
            base = match.group('base')
            is_export = match.group('export') is not None
            
            class_id = f"{file_path}::{name}"
            
            # Encontrar fin de la clase
            class_content, end_line = self._find_block_end(content, match.start(), line_num)
            
            # Crear nodo de clase
            class_node = CodeNode(
                id=class_id,
                parent_id=parent_id,
                name=name,
                type="class",
                language=self.language,
                path=file_path,
                line_start=line_num,
                line_end=end_line,
                loc=self._count_block_lines(class_content),
                bases=[base] if base else None,
                exports=is_export if is_export else None
            )
            nodes.append(class_node)
            existing_ids.add(class_id)
            
            # Extraer métodos de la clase
            self._extract_methods_flat(class_content, file_path, name, line_num, nodes, class_id)
        
        # Extraer funciones declaradas
        for match in self.FUNCTION_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            name = match.group('name')
            is_async = match.group('async') is not None
            is_export = match.group('export') is not None
            
            node_id = f"{file_path}::{name}"
            if node_id in existing_ids:
                continue
            
            _, end_line = self._find_block_end(content, match.start(), line_num)
            loc = end_line - line_num + 1
            
            func_node = CodeNode(
                id=node_id,
                parent_id=parent_id,
                name=name,
                type="function",
                language=self.language,
                path=file_path,
                line_start=line_num,
                line_end=end_line,
                loc=loc,
                is_async=is_async if is_async else None,
                exports=is_export if is_export else None
            )
            nodes.append(func_node)
            existing_ids.add(node_id)
        
        # Extraer arrow functions
        for match in self.ARROW_FUNCTION_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            name = match.group('name')
            is_async = match.group('async') is not None
            is_export = match.group('export') is not None
            
            node_id = f"{file_path}::{name}"
            if node_id in existing_ids:
                continue
            
            end_line = self._estimate_arrow_end(lines, line_num - 1)
            loc = end_line - line_num + 1
            
            func_node = CodeNode(
                id=node_id,
                parent_id=parent_id,
                name=name,
                type="function",
                language=self.language,
                path=file_path,
                line_start=line_num,
                line_end=end_line,
                loc=loc,
                is_async=is_async if is_async else None,
                exports=is_export if is_export else None
            )
            nodes.append(func_node)
            existing_ids.add(node_id)
        
        # Extraer function expressions
        for match in self.FUNCTION_EXPRESSION_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            name = match.group('name')
            is_async = match.group('async') is not None
            is_export = match.group('export') is not None
            
            node_id = f"{file_path}::{name}"
            if node_id in existing_ids:
                continue
            
            _, end_line = self._find_block_end(content, match.start(), line_num)
            loc = end_line - line_num + 1
            
            func_node = CodeNode(
                id=node_id,
                parent_id=parent_id,
                name=name,
                type="function",
                language=self.language,
                path=file_path,
                line_start=line_num,
                line_end=end_line,
                loc=loc,
                is_async=is_async if is_async else None,
                exports=is_export if is_export else None
            )
            nodes.append(func_node)
            existing_ids.add(node_id)
    
    def _extract_methods_flat(
        self, 
        class_content: str, 
        file_path: str, 
        class_name: str, 
        class_start: int,
        nodes: List[CodeNode],
        parent_id: str
    ) -> None:
        """
        Extrae métodos de una clase y los agrega a la lista.
        
        Args:
            class_content: Contenido de la clase
            file_path: Path del archivo
            class_name: Nombre de la clase
            class_start: Línea de inicio de la clase
            nodes: Lista de nodos (se modifica in-place)
            parent_id: ID del nodo padre (la clase)
        """
        for match in self.METHOD_PATTERN.finditer(class_content):
            name = match.group('name')
            is_async = match.group('async') is not None
            relative_line = class_content[:match.start()].count('\n')
            line_num = class_start + relative_line
            
            method_node = CodeNode(
                id=f"{file_path}::{class_name}::{name}",
                parent_id=parent_id,
                name=name,
                type="method",
                language=self.language,
                path=file_path,
                line_start=line_num,
                loc=1,  # Simplificado
                is_async=is_async if is_async else None
            )
            nodes.append(method_node)
    
    def _create_import_node(
        self, 
        file_path: str, 
        module: str, 
        line_num: int,
        parent_id: str
    ) -> CodeNode:
        """Crea un CodeNode para un import."""
        return CodeNode(
            id=f"{file_path}::import::{module}",
            parent_id=parent_id,
            name=module,
            type="import",
            language=self.language,
            path=file_path,
            line_start=line_num,
            line_end=line_num,
            loc=1
        )
    
    def _find_block_end(self, content: str, start_pos: int, start_line: int) -> tuple[str, int]:
        """
        Encuentra el final de un bloque {} balanceado.
        
        Args:
            content: Contenido completo
            start_pos: Posición de inicio
            start_line: Línea de inicio
            
        Returns:
            Tuple de (contenido del bloque, línea de fin)
        """
        # Buscar primera llave
        brace_pos = content.find('{', start_pos)
        if brace_pos == -1:
            return "", start_line
        
        depth = 1
        pos = brace_pos + 1
        
        while pos < len(content) and depth > 0:
            char = content[pos]
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
            pos += 1
        
        block_content = content[brace_pos:pos]
        end_line = start_line + block_content.count('\n')
        
        return block_content, end_line
    
    def _estimate_arrow_end(self, lines: list[str], start_idx: int) -> int:
        """
        Estima el fin de una arrow function.
        Simple heurística basada en indentación.
        
        Args:
            lines: Líneas del archivo
            start_idx: Índice de línea de inicio
            
        Returns:
            Línea de fin (1-indexed)
        """
        if start_idx >= len(lines):
            return start_idx + 1
        
        start_line = lines[start_idx]
        start_indent = len(start_line) - len(start_line.lstrip())
        
        # Si tiene => { buscar el } correspondiente
        if '=>' in start_line and '{' in start_line:
            depth = start_line.count('{') - start_line.count('}')
            for i in range(start_idx + 1, len(lines)):
                depth += lines[i].count('{') - lines[i].count('}')
                if depth <= 0:
                    return i + 1
        
        # Si no, buscar hasta que la indentación vuelva al nivel original
        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            if line.strip():  # Ignorar líneas vacías
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= start_indent and not line.strip().startswith('.'):
                    return i  # Retorna línea anterior
        
        return len(lines)
    
    def _count_block_lines(self, block: str) -> int:
        """Cuenta líneas no vacías en un bloque."""
        return sum(1 for line in block.split('\n') if line.strip())
