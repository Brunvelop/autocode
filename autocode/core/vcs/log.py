"""
Git Log - Funciones para obtener el historial de commits y detalles.

Este módulo proporciona endpoints registrados para consultar
el grafo de commits, ramas, tags y detalles de commits individuales.
"""
import subprocess
import logging
from typing import Optional

from autocode.interfaces.registry import register_function
from autocode.core.vcs.models import (
    GitCommit,
    GitBranch,
    GitLogGraph,
    GitLogOutput,
    GitFileChange,
    GitCommitDetail,
    GitCommitDetailOutput,
)

logger = logging.getLogger(__name__)

# Separador único para parsear git log
_SEP = "‖"
# Formato: hash, short_hash, author, email, date ISO, parents, subject
_LOG_FORMAT = f"%H{_SEP}%h{_SEP}%an{_SEP}%ae{_SEP}%aI{_SEP}%P{_SEP}%s"


@register_function(http_methods=["GET"], interfaces=["api", "mcp"])
def get_git_log(max_count: int = 50, branch: str = "") -> GitLogOutput:
    """
    Obtiene el historial de commits del repositorio como un grafo.

    Incluye commits con sus padres, ramas y tags para poder
    renderizar un grafo interactivo de la historia git.

    Args:
        max_count: Número máximo de commits a retornar (default 50)
        branch: Rama específica a consultar (vacío = todas las ramas)
    """
    try:
        # 1. Obtener commits
        commits = _get_commits(max_count, branch)

        # 2. Obtener ramas
        branches = _get_branches()

        # 3. Obtener tags
        tag_map = _get_tag_map()

        # 4. Obtener rama actual
        current_branch = _get_current_branch()

        # 5. Mapear ramas y tags a commits
        branch_map: dict[str, list[str]] = {}
        for b in branches:
            branch_map.setdefault(b.head_commit, []).append(b.name)

        for commit in commits:
            commit.branches = branch_map.get(commit.hash, [])
            commit.tags = tag_map.get(commit.hash, [])

        # 6. Marcar rama actual
        for b in branches:
            b.is_current = b.name == current_branch

        graph = GitLogGraph(commits=commits, branches=branches)

        return GitLogOutput(
            success=True,
            result=graph,
            message=f"{len(commits)} commits, {len(branches)} branches",
        )

    except subprocess.CalledProcessError as e:
        error_msg = f"Git error: {e.stderr.strip() if e.stderr else str(e)}"
        logger.error(error_msg)
        return GitLogOutput(success=False, message=error_msg)

    except Exception as e:
        error_msg = f"Error obteniendo git log: {str(e)}"
        logger.error(error_msg)
        return GitLogOutput(success=False, message=error_msg)


@register_function(http_methods=["GET"], interfaces=["api", "mcp"])
def get_commit_detail(commit_hash: str) -> GitCommitDetailOutput:
    """
    Obtiene el detalle de un commit específico incluyendo archivos cambiados.

    Args:
        commit_hash: Hash del commit (completo o abreviado)
    """
    try:
        # 1. Info básica del commit
        cmd = ["git", "log", "-1", f"--format={_LOG_FORMAT}", commit_hash]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        line = result.stdout.strip()
        if not line:
            return GitCommitDetailOutput(
                success=False, message=f"Commit {commit_hash} no encontrado"
            )

        parts = line.split(_SEP, 6)
        if len(parts) < 7:
            return GitCommitDetailOutput(
                success=False, message=f"Error parseando commit {commit_hash}"
            )

        full_hash, short_hash, author, email, date, parents_str, subject = parts
        parents = parents_str.split() if parents_str else []

        # 2. Mensaje completo
        msg_result = subprocess.run(
            ["git", "log", "-1", "--format=%B", commit_hash],
            capture_output=True,
            text=True,
            check=True,
        )
        message_full = msg_result.stdout.strip()

        # 3. Archivos cambiados con estadísticas
        files = _get_commit_files(full_hash, parents)

        # 4. Stats
        total_add = sum(f.additions for f in files)
        total_del = sum(f.deletions for f in files)

        detail = GitCommitDetail(
            hash=full_hash,
            short_hash=short_hash,
            message_full=message_full,
            author=author,
            author_email=email,
            date=date,
            parents=parents,
            files=files,
            stats={
                "total_additions": total_add,
                "total_deletions": total_del,
                "files_changed": len(files),
            },
        )

        return GitCommitDetailOutput(
            success=True,
            result=detail,
            message=f"Commit {short_hash}: {len(files)} archivos cambiados",
        )

    except subprocess.CalledProcessError as e:
        error_msg = f"Git error: {e.stderr.strip() if e.stderr else str(e)}"
        logger.error(error_msg)
        return GitCommitDetailOutput(success=False, message=error_msg)

    except Exception as e:
        error_msg = f"Error obteniendo detalle del commit: {str(e)}"
        logger.error(error_msg)
        return GitCommitDetailOutput(success=False, message=error_msg)


# ==============================================================================
# PRIVATE HELPERS
# ==============================================================================


def _get_commits(max_count: int, branch: str) -> list[GitCommit]:
    """Obtiene lista de commits parseados desde git log."""
    cmd = [
        "git",
        "log",
        f"--format={_LOG_FORMAT}",
        f"-n{max_count}",
    ]

    if branch:
        cmd.append(branch)
    else:
        cmd.append("--all")

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    lines = [l for l in result.stdout.strip().split("\n") if l]

    commits = []
    for line in lines:
        parts = line.split(_SEP, 6)
        if len(parts) < 7:
            continue

        full_hash, short_hash, author, email, date, parents_str, subject = parts
        parents = parents_str.split() if parents_str else []

        commits.append(
            GitCommit(
                hash=full_hash,
                short_hash=short_hash,
                message=subject,
                author=author,
                author_email=email,
                date=date,
                parents=parents,
                is_merge=len(parents) > 1,
            )
        )

    return commits


def _get_branches() -> list[GitBranch]:
    """Obtiene todas las ramas locales con su HEAD commit."""
    result = subprocess.run(
        ["git", "branch", "-v", "--no-abbrev", "--format=%(refname:short) %(objectname)"],
        capture_output=True,
        text=True,
        check=True,
    )

    branches = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.strip().split(" ", 1)
        if len(parts) == 2:
            name, head = parts
            branches.append(
                GitBranch(
                    name=name,
                    head_commit=head.strip(),
                    is_current=False,
                    is_remote=False,
                )
            )

    return branches


def _get_tag_map() -> dict[str, list[str]]:
    """Obtiene un mapa commit_hash -> [tag_names]."""
    result = subprocess.run(
        ["git", "tag", "-l", "--format=%(objectname) %(refname:short)"],
        capture_output=True,
        text=True,
        check=False,
    )

    tag_map: dict[str, list[str]] = {}
    if result.returncode == 0:
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.strip().split(" ", 1)
            if len(parts) == 2:
                commit_hash, tag_name = parts
                tag_map.setdefault(commit_hash, []).append(tag_name)

    return tag_map


def _get_current_branch() -> str:
    """Obtiene el nombre de la rama actual."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _get_commit_files(commit_hash: str, parents: list[str]) -> list[GitFileChange]:
    """Obtiene los archivos cambiados en un commit con estadísticas de líneas."""
    # Para el commit inicial (sin padres), comparar contra árbol vacío
    if not parents:
        cmd = [
            "git",
            "diff-tree",
            "--no-commit-id",
            "-r",
            "--numstat",
            "--diff-filter=ACDMRT",
            commit_hash,
        ]
    else:
        cmd = [
            "git",
            "diff-tree",
            "--no-commit-id",
            "-r",
            "--numstat",
            "--diff-filter=ACDMRT",
            f"{parents[0]}",
            commit_hash,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return []

    # También obtener status letters
    if not parents:
        status_cmd = [
            "git",
            "diff-tree",
            "--no-commit-id",
            "-r",
            "--name-status",
            "--diff-filter=ACDMRT",
            commit_hash,
        ]
    else:
        status_cmd = [
            "git",
            "diff-tree",
            "--no-commit-id",
            "-r",
            "--name-status",
            "--diff-filter=ACDMRT",
            f"{parents[0]}",
            commit_hash,
        ]

    status_result = subprocess.run(
        status_cmd, capture_output=True, text=True, check=False
    )

    # Parsear status map
    status_map: dict[str, str] = {}
    if status_result.returncode == 0:
        for line in status_result.stdout.strip().split("\n"):
            if not line or "\t" not in line:
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                status_code = parts[0].strip()
                path = parts[-1].strip()
                status_map[path] = _status_letter_to_name(status_code)

    # Parsear numstat
    files = []
    for line in result.stdout.strip().split("\n"):
        if not line or "\t" not in line:
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            add_str, del_str, path = parts[0], parts[1], parts[2]
            additions = int(add_str) if add_str != "-" else 0
            deletions = int(del_str) if del_str != "-" else 0
            status = status_map.get(path, "modified")

            files.append(
                GitFileChange(
                    path=path,
                    status=status,
                    additions=additions,
                    deletions=deletions,
                )
            )

    return files


def _status_letter_to_name(letter: str) -> str:
    """Convierte letra de status git a nombre legible."""
    mapping = {
        "A": "added",
        "M": "modified",
        "D": "deleted",
        "R": "renamed",
        "C": "copied",
        "T": "type_changed",
    }
    # La letra puede tener un número (R100 para rename 100%)
    return mapping.get(letter[0], "modified")
