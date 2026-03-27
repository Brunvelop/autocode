"""
Central Refract application instance for Autocode.

This module defines the singleton ``app`` that owns the registry, CLI,
API and MCP surfaces for the autocode project.  It is the single entry
point referenced by ``pyproject.toml`` and consumed by every interface.

Usage (CLI entry point in pyproject.toml)::

    [project.scripts]
    autocode = "autocode.app:app.run_cli"

Usage (programmatic)::

    from autocode.app import app

    fastapi_app = app.api()   # REST API with autocode views
    mcp_app     = app.mcp()   # REST API + MCP with autocode views
    cli_group   = app.cli()   # Click group
"""
import os

import click
from refract import Refract

# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(__file__)        # autocode/
_WEB = os.path.join(_HERE, "web")       # autocode/web/

# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------

app = Refract(
    "autocode",
    discover=["autocode.core"],
    views={
        "/": os.path.join(_WEB, "views", "index.html"),
        "/tests": os.path.join(_WEB, "tests", "index.html"),
    },
    static_dirs=[
        ("/elements", os.path.join(_WEB, "elements")),
        ("/tests", os.path.join(_WEB, "tests")),
    ],
)

# ---------------------------------------------------------------------------
# Custom CLI commands
# ---------------------------------------------------------------------------

@app.command(name="health-check")
@click.option(
    "--format", "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    show_default=True,
    help="Output format: table (human-readable) or json (machine-readable).",
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Use strict default thresholds, ignoring any [tool.codehealth] in pyproject.toml.",
)
@click.option(
    "--project-root",
    type=click.Path(exists=True),
    default=".",
    show_default=True,
    help="Root directory of the project to analyze.",
)
def health_check(output_format: str, strict: bool, project_root: str):
    """Run code health quality gates against the current project.

    Analyzes all files tracked by git and checks them against quality thresholds
    defined in [tool.codehealth] of pyproject.toml (or strict defaults with --strict).

    Exit code 0 = all gates passed, 1 = critical violations found.

    \b
    Examples:
        autocode health-check
        autocode health-check --format json
        autocode health-check --strict
        autocode health-check --project-root /path/to/project
    """
    import sys

    from autocode.core.code.health import get_health_check

    output = get_health_check(strict=strict, project_root=project_root)
    result = output.result

    if output_format == "json":
        _print_health_json(result)
    else:
        _print_health_table(result)

    sys.exit(0 if result.passed else 1)


# ---------------------------------------------------------------------------
# Private helpers — health output formatters
# ---------------------------------------------------------------------------

def _print_health_json(result) -> None:
    """Print HealthCheckResult as JSON to stdout.

    Args:
        result: HealthCheckResult from run_health_check()
    """
    import json

    data = {
        "passed": result.passed,
        "summary": result.summary,
        "violations": [
            {
                "rule": v.rule,
                "level": v.level,
                "path": v.path,
                "value": v.value,
                "threshold": v.threshold,
                "detail": v.detail,
            }
            for v in result.violations
        ],
    }
    click.echo(json.dumps(data, indent=2))


def _print_health_table(result) -> None:
    """Print HealthCheckResult as a human-readable Unicode box table.

    Args:
        result: HealthCheckResult from run_health_check()
    """
    width = 56
    sep = "═" * width
    status = "✅  ALL GATES PASSED" if result.passed else "❌  GATES FAILED"

    click.echo(f"\n╔{sep}╗")
    click.echo(f"║{'  CODE HEALTH QUALITY GATES':^{width}}║")
    click.echo(f"╠{sep}╣")

    for key, value in result.summary.items():
        content = f"  {key:<26} {value}"
        click.echo(f"║{content:<{width}}║")

    criticals = [v for v in result.violations if v.level == "critical"]
    warnings = [v for v in result.violations if v.level == "warning"]

    if criticals:
        click.echo(f"╠{sep}╣")
        click.echo(f"║  ❌ CRITICAL VIOLATIONS ({len(criticals)}){'':<{width - 30}}║")
        for v in criticals[:10]:  # cap at 10 to avoid flooding
            line = f"    [{v.rule}] {v.path}: {v.value:.1f} > {v.threshold:.1f}"
            click.echo(f"║{line:<{width}}║")
            if v.detail:
                detail_line = f"      → {v.detail}"
                if len(detail_line) > width:
                    detail_line = detail_line[: width - 3] + "..."
                click.echo(f"║{detail_line:<{width}}║")
        if len(criticals) > 10:
            more_line = f"    … and {len(criticals) - 10} more critical violations"
            click.echo(f"║{more_line:<{width}}║")

    if warnings:
        click.echo(f"╠{sep}╣")
        click.echo(f"║  ⚠️  WARNINGS ({len(warnings)}){'':<{width - 22}}║")

    click.echo(f"╠{sep}╣")
    click.echo(f"║{'  ' + status:<{width}}║")
    click.echo(f"╚{sep}╝\n")
