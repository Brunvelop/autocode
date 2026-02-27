"""
Git Status - Función para obtener el estado actual del repositorio.

Este módulo proporciona funciones para consultar archivos modificados,
staged, untracked y sus diferencias.
"""
import subprocess
import logging
from typing import List, Optional, Literal

from pydantic import BaseModel, Field

from autocode.interfaces.registry import register_function
from autocode.interfaces.models import GenericOutput

logger = logging.getLogger(__name__)


# ==============================================================================
# MODELS
# ==============================================================================

FileStatus = Literal["added", "modified", "deleted", "renamed", "untracked", "staged"]


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


class GitStatusOutput(GenericOutput):
    """Output de get_git_status()."""
    
    result: Optional[GitStatusResult] = None


# ==============================================================================
# FUNCTIONS
# ==============================================================================

@register_function(http_methods=["GET"], interfaces=["api"])
def get_git_status() -> GitStatusOutput:
    """
    Obtiene el estado actual del repositorio git.
    
    Incluye archivos modificados, añadidos, eliminados, staged y untracked.
    También incluye estadísticas de líneas añadidas/eliminadas.
    
    Returns:
        GitStatusOutput con el estado completo del repositorio
    """
    try:
        # Obtener branch actual
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        branch = branch_result.stdout.strip()
        
        # Obtener status porcelain v2 (más parseable)
        status_result = subprocess.run(
            ["git", "status", "--porcelain=v2", "--untracked-files=all"],
            capture_output=True, text=True, check=True
        )
        
        files: List[GitFileStatus] = []
        counters = {
            "added": 0,
            "modified": 0, 
            "deleted": 0,
            "untracked": 0,
            "staged": 0
        }
        
        for line in status_result.stdout.strip().split('\n'):
            if not line:
                continue
            
            file_status = _parse_status_line(line)
            if file_status:
                files.append(file_status)
                
                # Actualizar contadores
                if file_status.status == "added":
                    counters["added"] += 1
                elif file_status.status == "modified":
                    counters["modified"] += 1
                elif file_status.status == "deleted":
                    counters["deleted"] += 1
                elif file_status.status == "untracked":
                    counters["untracked"] += 1
                
                if file_status.staged:
                    counters["staged"] += 1
        
        # Obtener estadísticas de líneas (--stat)
        files = _add_line_stats(files)
        
        is_clean = len(files) == 0
        
        result = GitStatusResult(
            branch=branch,
            is_clean=is_clean,
            files=files,
            total_added=counters["added"],
            total_modified=counters["modified"],
            total_deleted=counters["deleted"],
            total_untracked=counters["untracked"],
            total_staged=counters["staged"]
        )
        
        return GitStatusOutput(
            success=True,
            result=result,
            message=f"Status: {len(files)} archivos con cambios" if files else "Working directory limpio"
        )
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Git error: {e.stderr.strip() if e.stderr else str(e)}"
        logger.error(error_msg)
        return GitStatusOutput(success=False, message=error_msg)
        
    except Exception as e:
        error_msg = f"Error obteniendo git status: {str(e)}"
        logger.error(error_msg)
        return GitStatusOutput(success=False, message=error_msg)


@register_function(http_methods=["GET"], interfaces=["api", "mcp"])
def get_git_status_summary() -> GenericOutput:
    """
    Obtiene un resumen compacto del estado del repositorio git.
    
    Versión ligera de get_git_status(), optimizada para LLMs.
    Devuelve texto plano con el estado de cada archivo en formato corto
    y un resumen de contadores al final.
    
    Returns:
        GenericOutput con result=texto compacto del status
    """
    try:
        # Obtener branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        branch = branch_result.stdout.strip()
        
        # Obtener status porcelain v1 (más compacto)
        status_result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            capture_output=True, text=True, check=True
        )
        
        lines = [l for l in status_result.stdout.strip().split('\n') if l]
        
        if not lines:
            summary = f"Branch: {branch} | Clean (no changes)"
            return GenericOutput(
                success=True,
                result=summary,
                message="Working directory limpio"
            )
        
        # Construir resumen compacto
        output_lines = [f"Branch: {branch}"]
        
        counters = {"M": 0, "A": 0, "D": 0, "R": 0, "?": 0, "staged": 0}
        
        for line in lines:
            # Porcelain v1: "XY path" donde X=index, Y=worktree
            if len(line) < 4:
                continue
            
            xy = line[:2]
            path = line[3:]
            
            # Determinar símbolo compacto
            x, y = xy[0], xy[1]
            
            if xy == '??':
                counters["?"] += 1
                output_lines.append(f"  ? {path}")
            else:
                # Staged indicator
                staged = "+" if x != '.' and x != ' ' and x != '?' else " "
                if staged == "+":
                    counters["staged"] += 1
                
                # Status letter (usar el más significativo)
                status_char = x if x not in ('.', ' ', '?') else y
                if status_char in ('M', 'm'):
                    counters["M"] += 1
                    output_lines.append(f" {staged}M {path}")
                elif status_char == 'A':
                    counters["A"] += 1
                    output_lines.append(f" {staged}A {path}")
                elif status_char == 'D':
                    counters["D"] += 1
                    output_lines.append(f" {staged}D {path}")
                elif status_char == 'R':
                    counters["R"] += 1
                    output_lines.append(f" {staged}R {path}")
                else:
                    counters["M"] += 1
                    output_lines.append(f" {staged}{status_char} {path}")
        
        # Línea resumen
        parts = []
        if counters["M"]:
            parts.append(f"{counters['M']} modified")
        if counters["A"]:
            parts.append(f"{counters['A']} added")
        if counters["D"]:
            parts.append(f"{counters['D']} deleted")
        if counters["R"]:
            parts.append(f"{counters['R']} renamed")
        if counters["?"]:
            parts.append(f"{counters['?']} untracked")
        if counters["staged"]:
            parts.append(f"{counters['staged']} staged")
        
        output_lines.append(f"---\nTotal: {', '.join(parts)}")
        
        summary = "\n".join(output_lines)
        return GenericOutput(
            success=True,
            result=summary,
            message=f"Status: {len(lines)} archivos con cambios"
        )
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Git error: {e.stderr.strip() if e.stderr else str(e)}"
        logger.error(error_msg)
        return GenericOutput(success=False, result=None, message=error_msg)
        
    except Exception as e:
        error_msg = f"Error obteniendo git status summary: {str(e)}"
        logger.error(error_msg)
        return GenericOutput(success=False, result=None, message=error_msg)


def _parse_status_line(line: str) -> Optional[GitFileStatus]:
    """
    Parsea una línea del output de `git status --porcelain=v2`.
    
    Formato v2:
    - "1 <XY> ..." para archivos tracked modificados
    - "2 <XY> ..." para archivos renamed/copied
    - "? <path>" para untracked
    - "! <path>" para ignored
    
    Args:
        line: Línea del output de git status
        
    Returns:
        GitFileStatus o None si no es parseable
    """
    if not line:
        return None
    
    parts = line.split()
    
    # Untracked files: "? <path>"
    if line.startswith('?'):
        path = line[2:].strip()
        return GitFileStatus(path=path, status="untracked", staged=False)
    
    # Ignored: "! <path>" - ignoramos estos
    if line.startswith('!'):
        return None
    
    # Changed entries: "1 <XY> <sub> <mH> <mI> <mW> <hH> <hI> <path>"
    if line.startswith('1 '):
        try:
            xy = parts[1]
            path = parts[-1]
            
            staged = xy[0] != '.'
            status = _xy_to_status(xy)
            
            return GitFileStatus(path=path, status=status, staged=staged)
        except (IndexError, ValueError):
            return None
    
    # Renamed/copied: "2 <XY> <sub> <mH> <mI> <mW> <hH> <hI> <X><score> <path><sep><origPath>"
    if line.startswith('2 '):
        try:
            xy = parts[1]
            # El path puede contener tab separando new_path y old_path
            path_part = ' '.join(parts[9:])
            if '\t' in path_part:
                new_path, old_path = path_part.split('\t')
            else:
                new_path = path_part
                old_path = None
            
            return GitFileStatus(
                path=new_path, 
                status="renamed", 
                staged=xy[0] != '.',
                old_path=old_path
            )
        except (IndexError, ValueError):
            return None
    
    return None


def _xy_to_status(xy: str) -> FileStatus:
    """
    Convierte los códigos XY de git status a nuestro FileStatus.
    
    X = estado en index (staged)
    Y = estado en worktree
    
    Args:
        xy: String de 2 caracteres (ej: "M.", ".M", "A.", "D.")
        
    Returns:
        FileStatus correspondiente
    """
    x, y = xy[0], xy[1]
    
    # Priorizar el estado más significativo
    if x == 'A' or y == 'A':
        return "added"
    if x == 'D' or y == 'D':
        return "deleted"
    if x == 'R' or y == 'R':
        return "renamed"
    if x == 'M' or y == 'M':
        return "modified"
    
    return "modified"  # Default


def _add_line_stats(files: List[GitFileStatus]) -> List[GitFileStatus]:
    """
    Añade estadísticas de líneas (additions/deletions) a cada archivo.
    
    Args:
        files: Lista de GitFileStatus
        
    Returns:
        Lista actualizada con estadísticas
    """
    if not files:
        return files
    
    try:
        # Obtener diff stat para archivos tracked
        tracked_paths = [f.path for f in files if f.status != "untracked"]
        
        if tracked_paths:
            result = subprocess.run(
                ["git", "diff", "--numstat", "HEAD", "--"] + tracked_paths,
                capture_output=True, text=True, check=False
            )
            
            # También staged
            staged_result = subprocess.run(
                ["git", "diff", "--numstat", "--cached", "--"] + tracked_paths,
                capture_output=True, text=True, check=False
            )
            
            # Parsear stats
            stats = {}
            for line in (result.stdout + staged_result.stdout).strip().split('\n'):
                if line and '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        add = int(parts[0]) if parts[0] != '-' else 0
                        delete = int(parts[1]) if parts[1] != '-' else 0
                        path = parts[2]
                        
                        # Acumular si ya existe
                        if path in stats:
                            stats[path] = (stats[path][0] + add, stats[path][1] + delete)
                        else:
                            stats[path] = (add, delete)
            
            # Actualizar files
            for f in files:
                if f.path in stats:
                    f.additions, f.deletions = stats[f.path]
    
    except Exception as e:
        logger.debug(f"Error obteniendo line stats: {e}")
    
    return files
