"""
parsers
Registry de parsers de código por extensión.
"""

from .base import BaseParser
from .python_parser import PythonParser
from .js_parser import JSParser


# Registry de parsers por extensión de archivo
PARSERS: dict[str, type[BaseParser]] = {
    '.py': PythonParser,
    '.js': JSParser,
    '.mjs': JSParser,
    '.jsx': JSParser,
}


def get_parser(extension: str) -> BaseParser | None:
    """
    Obtiene una instancia del parser apropiado para la extensión.
    
    Args:
        extension: Extensión del archivo (ej: '.py', '.js')
        
    Returns:
        Instancia del parser o None si no hay parser para esa extensión
    """
    parser_class = PARSERS.get(extension.lower())
    if parser_class:
        return parser_class()
    return None


__all__ = [
    'BaseParser',
    'PythonParser', 
    'JSParser',
    'PARSERS',
    'get_parser',
]
