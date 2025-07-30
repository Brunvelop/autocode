"""
Formatters for documentation check results.
These functions transform DocCheckResult into different output formats.
"""

from typing import Dict, Any, List
from pathlib import Path

from .types import DocCheckResult, DocStatus, DocType, StatusType


def format_cli_output(result: DocCheckResult) -> str:
    """
    Format documentation check result for CLI display.
    Returns human-readable string output.
    """
    if not result.has_issues:
        return "✅ All documentation is up to date!"
    
    lines = []
    
    # Group issues by status type
    outdated = result.outdated_docs
    missing = result.missing_docs
    orphaned = result.orphaned_docs
    
    # Format outdated documentation
    if outdated:
        lines.append("📝 Documentación desactualizada:")
        for status in outdated:
            formatted_line = _format_status_line(status, result.project_root)
            lines.append(f"   - {formatted_line}")
    
    # Format missing documentation
    if missing:
        if outdated:
            lines.append("")  # Empty line separator
        lines.append("❌ Archivos sin documentación:")
        for status in missing:
            formatted_line = _format_status_line(status, result.project_root)
            lines.append(f"   - {formatted_line}")
    
    # Format orphaned documentation
    if orphaned:
        if outdated or missing:
            lines.append("")  # Empty line separator
        lines.append("🗑️  Documentación huérfana (código eliminado):")
        for status in orphaned:
            formatted_line = _format_orphaned_line(status, result.project_root)
            lines.append(f"   - {formatted_line}")
    
    # Add summary
    lines.append("")
    summary = result.summary
    total_issues = summary.issues_count
    lines.append(
        f"📊 Total: {total_issues} archivo{'s' if total_issues != 1 else ''} "
        f"requiere{'n' if total_issues != 1 else ''} atención"
    )
    
    return "\n".join(lines)


def format_json_output(result: DocCheckResult) -> Dict[str, Any]:
    """
    Format documentation check result for JSON/API output.
    Returns structured dictionary suitable for JSON serialization.
    """
    return {
        "timestamp": result.timestamp.isoformat(),
        "project_root": str(result.project_root),
        "docs_root": str(result.docs_root),
        "summary": {
            "total_files": result.summary.total_files,
            "has_issues": result.summary.has_issues,
            "issues_count": result.summary.issues_count,
            "outdated_count": result.summary.outdated_count,
            "missing_count": result.summary.missing_count,
            "orphaned_count": result.summary.orphaned_count,
            "up_to_date_count": result.summary.up_to_date_count
        },
        "issues": [
            _format_status_for_json(status, result.project_root)
            for status in result.issues
        ],
        "details": {
            "outdated": [
                _format_status_for_json(status, result.project_root)
                for status in result.outdated_docs
            ],
            "missing": [
                _format_status_for_json(status, result.project_root)
                for status in result.missing_docs
            ],
            "orphaned": [
                _format_status_for_json(status, result.project_root)
                for status in result.orphaned_docs
            ]
        }
    }


def format_summary_only(result: DocCheckResult) -> str:
    """
    Format only the summary for quick status display.
    Useful for dashboard or status bar displays.
    """
    summary = result.summary
    
    if not result.has_issues:
        return f"✅ {summary.total_files} files documented"
    
    issues = []
    if summary.outdated_count > 0:
        issues.append(f"{summary.outdated_count} outdated")
    if summary.missing_count > 0:
        issues.append(f"{summary.missing_count} missing")
    if summary.orphaned_count > 0:
        issues.append(f"{summary.orphaned_count} orphaned")
    
    return f"⚠️  {', '.join(issues)} ({summary.up_to_date_count} up to date)"


def format_for_github_pr(result: DocCheckResult) -> str:
    """
    Format documentation check result for GitHub PR comments.
    Returns markdown-formatted string.
    """
    if not result.has_issues:
        return "✅ **Documentation Check**: All documentation is up to date!"
    
    lines = ["## 📚 Documentation Check Results"]
    lines.append("")
    
    summary = result.summary
    lines.append("### Summary")
    lines.append(f"- **Total files checked**: {summary.total_files}")
    lines.append(f"- **Issues found**: {summary.issues_count}")
    lines.append(f"- **Up to date**: {summary.up_to_date_count}")
    lines.append("")
    
    if result.outdated_docs:
        lines.append("### 📝 Outdated Documentation")
        for status in result.outdated_docs:
            lines.append(f"- `{_get_relative_path(status, result.project_root)}`")
        lines.append("")
    
    if result.missing_docs:
        lines.append("### ❌ Missing Documentation")
        for status in result.missing_docs:
            lines.append(f"- `{_get_relative_path(status, result.project_root)}`")
        lines.append("")
    
    if result.orphaned_docs:
        lines.append("### 🗑️ Orphaned Documentation")
        for status in result.orphaned_docs:
            lines.append(f"- `{_get_relative_doc_path(status, result.project_root)}`")
        lines.append("")
    
    return "\n".join(lines)


def _format_status_line(status: DocStatus, project_root: Path) -> str:
    """Format a single status for CLI display."""
    if status.doc_type == DocType.INDEX:
        return "docs/_index.md (documentación principal del proyecto)"
    
    elif status.doc_type == DocType.MODULE:
        relative_code = _get_relative_path(status, project_root)
        relative_doc = _get_relative_doc_path(status, project_root)
        return f"{relative_code}/ → {relative_doc}"
    
    else:  # FILE
        relative_code = _get_relative_path(status, project_root)
        relative_doc = _get_relative_doc_path(status, project_root)
        return f"{relative_code} → {relative_doc}"


def _format_orphaned_line(status: DocStatus, project_root: Path) -> str:
    """Format an orphaned documentation line for CLI display."""
    relative_doc = _get_relative_doc_path(status, project_root)
    
    if status.doc_type == DocType.MODULE:
        relative_code = _get_relative_path(status, project_root)
        return f"{relative_doc} (directorio {relative_code}/ ya no existe)"
    else:
        relative_code = _get_relative_path(status, project_root)
        return f"{relative_doc} (archivo {relative_code} ya no existe)"


def _format_status_for_json(status: DocStatus, project_root: Path) -> Dict[str, Any]:
    """Format a single status for JSON output."""
    base_data = {
        "status": status.status.value,
        "doc_type": status.doc_type.value,
        "code_path": _get_relative_path(status, project_root),
        "doc_path": _get_relative_doc_path(status, project_root) if status.doc else None
    }
    
    # Add timestamps if available
    if hasattr(status.code, 'last_modified'):
        base_data["code_last_modified"] = status.code.last_modified.isoformat()
    
    if status.doc:
        base_data["doc_last_modified"] = status.doc.last_modified.isoformat()
    
    return base_data


def _get_relative_path(status: DocStatus, project_root: Path) -> str:
    """Get relative path for code entity."""
    if isinstance(status.code, Path):
        # For index docs, code is the project root
        return str(project_root.name) if status.code == project_root else str(status.code.relative_to(project_root))
    
    # For CodeFile and CodeDirectory objects
    return str(status.code.path.relative_to(project_root))


def _get_relative_doc_path(status: DocStatus, project_root: Path) -> str:
    """Get relative path for documentation file."""
    if status.doc:
        return str(status.doc.path.relative_to(project_root))
    
    # For missing docs, we need to construct the expected path
    if status.doc_type == DocType.INDEX:
        return "docs/_index.md"
    elif status.doc_type == DocType.MODULE:
        code_rel = _get_relative_path(status, project_root)
        return f"docs/{code_rel}/_module.md"
    else:  # FILE
        code_rel = _get_relative_path(status, project_root)
        # Replace extension with .md
        code_path = Path(code_rel)
        return f"docs/{code_path.with_suffix('.md')}"


def format_issues_count(result: DocCheckResult) -> str:
    """Get a simple count string for issues."""
    if not result.has_issues:
        return "0 issues"
    
    count = result.summary.issues_count
    return f"{count} issue{'s' if count != 1 else ''}"


def format_status_emoji(status: StatusType) -> str:
    """Get emoji representation for status type."""
    emoji_map = {
        StatusType.UP_TO_DATE: "✅",
        StatusType.OUTDATED: "📝",
        StatusType.MISSING: "❌",
        StatusType.ORPHANED: "🗑️"
    }
    return emoji_map.get(status, "❓")


def format_doc_type_emoji(doc_type: DocType) -> str:
    """Get emoji representation for documentation type."""
    emoji_map = {
        DocType.INDEX: "📋",
        DocType.MODULE: "📁",
        DocType.FILE: "📄"
    }
    return emoji_map.get(doc_type, "❓")
