"""
File I/O utilities for reading design documents and writing code files.

This module provides utilities for file operations, separate from AI logic
to maintain single responsibility principle.
"""
import os


def read_design_document(path: str) -> str:
    """
    Lee un documento de diseño desde un archivo.
    
    Args:
        path: Ruta al archivo de diseño (Markdown u otro formato de texto)
        
    Returns:
        El contenido del documento como string
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        IOError: Si hay un error al leer el archivo
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {path}")
    except Exception as e:
        raise IOError(f"Error al leer el archivo {path}: {str(e)}")


def write_python_file(code: str, path: str) -> None:
    """
    Escribe código Python en un archivo.
    
    Args:
        code: El código Python a escribir
        path: Ruta donde guardar el archivo .py
        
    Raises:
        IOError: Si hay un error al escribir el archivo
    """
    try:
        # Asegurar que el directorio existe
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(code)
    except Exception as e:
        raise IOError(f"Error al escribir el archivo {path}: {str(e)}")


def write_file(content: str, path: str, file_type: str = None) -> None:
    """
    Escribe contenido en un archivo con soporte para diferentes tipos.
    
    Esta función es extensible para manejar diferentes tipos de archivos
    con procesamiento específico en el futuro.
    
    Args:
        content: El contenido a escribir
        path: Ruta donde guardar el archivo
        file_type: Tipo de archivo (e.g., 'python', 'markdown', 'json').
                   Si no se especifica, se infiere de la extensión.
        
    Raises:
        IOError: Si hay un error al escribir el archivo
    """
    # Inferir tipo si no se especifica
    if file_type is None:
        _, ext = os.path.splitext(path)
        type_map = {
            '.py': 'python',
            '.md': 'markdown',
            '.json': 'json',
            '.txt': 'text'
        }
        file_type = type_map.get(ext.lower(), 'text')
    
    # Por ahora, tratamiento simple
    # En el futuro, aquí se pueden agregar procesadores específicos por tipo
    try:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        raise IOError(f"Error al escribir el archivo {path}: {str(e)}")


def read_file(path: str) -> str:
    """
    Lee contenido de cualquier archivo de texto.
    
    Args:
        path: Ruta al archivo a leer
        
    Returns:
        El contenido del archivo como string
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        IOError: Si hay un error al leer el archivo
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {path}")
    except Exception as e:
        raise IOError(f"Error al leer el archivo {path}: {str(e)}")
