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

    fastapi_app = app.api()        # REST API (refract default views)
    fastapi_app = create_autocode_app()   # REST API with autocode custom views
    mcp_app     = app.mcp()        # REST API + MCP (refract default views)
    mcp_app     = create_autocode_mcp_app()  # REST API + MCP with autocode views
    cli_group   = app.cli()        # Click group
"""
import os

import click
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from refract import Refract


# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------

app = Refract("autocode", discover=["autocode.core"])

# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(__file__)                    # autocode/
_WEB_DIR = os.path.join(_HERE, "web")               # autocode/web/
_VIEWS_DIR = os.path.join(_WEB_DIR, "views")        # autocode/web/views/
_ELEMENTS_DIR = os.path.join(_WEB_DIR, "elements")  # autocode/web/elements/
_TESTS_DIR = os.path.join(_WEB_DIR, "tests")        # autocode/web/tests/

# refract's own web directory (where client.js, controller.js, etc. live)
import refract as _refract_pkg
_REFRACT_WEB_DIR = os.path.join(os.path.dirname(_refract_pkg.__file__), "web")


# ---------------------------------------------------------------------------
# App factories
# ---------------------------------------------------------------------------

def create_autocode_app() -> FastAPI:
    """Create a FastAPI application with autocode's own HTML views.

    Uses ``app.router()`` (refract's dynamic endpoints only) and adds
    autocode-specific HTML pages, static file mounts and the test dashboard.

    Route layout
    ~~~~~~~~~~~~
    ``/``                → ``autocode/web/views/index.html``  (Code Garden)
    ``/functions``       → ``autocode/web/views/functions.html``
    ``/demo``            → ``autocode/web/views/demo.html``
    ``/tests``           → ``autocode/web/tests/index.html``
    ``/functions/details`` → refract dynamic endpoint (function schemas)
    ``/health``          → refract dynamic endpoint

    Static mounts
    ~~~~~~~~~~~~~
    ``/elements/client.js``     → refract framework JS (explicit route)
    ``/elements/controller.js`` → refract framework JS (explicit route)
    ``/elements/element.js``    → refract framework JS (explicit route)
    ``/elements/generator.js``  → refract framework JS (explicit route)
    ``/elements``               → ``autocode/web/elements/`` (custom components)
    ``/tests``                  → ``autocode/web/tests/`` (test HTML files)

    Returns:
        A configured ``FastAPI`` application.
    """
    try:
        from importlib.metadata import version as pkg_version
        _version = pkg_version("autocode")
    except Exception:
        _version = "unknown"

    fastapi_app = FastAPI(
        title="Autocode API",
        description="Autocode — AI-powered development assistant",
        version=_version,
    )

    # ------------------------------------------------------------------
    # 1. Dynamic API endpoints from refract (functions + /functions/details
    #    + /health).  Excludes refract's dashboard.html and /elements mount.
    # ------------------------------------------------------------------
    fastapi_app.include_router(app.router())

    # ------------------------------------------------------------------
    # 2. Autocode's HTML views
    # ------------------------------------------------------------------

    @fastapi_app.get("/", include_in_schema=False)
    async def root() -> FileResponse:
        return FileResponse(os.path.join(_VIEWS_DIR, "index.html"))

    @fastapi_app.get("/functions", include_in_schema=False)
    async def functions_page() -> FileResponse:
        return FileResponse(os.path.join(_VIEWS_DIR, "functions.html"))

    @fastapi_app.get("/demo", include_in_schema=False)
    async def demo_page() -> FileResponse:
        return FileResponse(os.path.join(_VIEWS_DIR, "demo.html"))

    @fastapi_app.get("/tests", include_in_schema=False)
    async def tests_page() -> FileResponse:
        return FileResponse(os.path.join(_TESTS_DIR, "index.html"))

    # ------------------------------------------------------------------
    # 3. Refract framework JS served as explicit routes under /elements/
    #    Explicit routes take priority over the StaticFiles mount below,
    #    so /elements/client.js → refract, /elements/chat/ → autocode.
    # ------------------------------------------------------------------

    for _js_file in ("client.js", "controller.js", "element.js", "generator.js"):
        _js_path = os.path.join(_REFRACT_WEB_DIR, _js_file)

        def _make_route(path: str):
            async def _serve_js() -> FileResponse:
                return FileResponse(path, media_type="application/javascript")
            return _serve_js

        fastapi_app.add_api_route(
            f"/elements/{_js_file}",
            _make_route(_js_path),
            methods=["GET"],
            include_in_schema=False,
        )

    # ------------------------------------------------------------------
    # 4. Static mounts (after explicit routes so the routes win)
    # ------------------------------------------------------------------

    # autocode's custom web elements (chat/, git-dashboard/, code-dashboard/, …)
    if os.path.exists(_ELEMENTS_DIR):
        fastapi_app.mount(
            "/elements",
            StaticFiles(directory=_ELEMENTS_DIR),
            name="autocode-elements",
        )

    # test HTML files served as static (individual test HTML files use
    # relative imports; /tests route above serves the dashboard index)
    if os.path.exists(_TESTS_DIR):
        fastapi_app.mount(
            "/tests",
            StaticFiles(directory=_TESTS_DIR),
            name="autocode-tests",
        )

    return fastapi_app


def create_autocode_mcp_app() -> FastAPI:
    """Create a FastAPI application with autocode views + MCP integration.

    Builds on top of :func:`create_autocode_app` and adds MCP tool
    endpoints (same as ``app.mcp()`` but using autocode's custom views
    instead of refract's ``dashboard.html``).

    Returns:
        A configured ``FastAPI`` application with MCP support.
    """
    try:
        from fastapi_mcp import FastApiMCP
    except ImportError as exc:
        raise RuntimeError(
            "fastapi-mcp is required for MCP support. "
            "Install it with: pip install fastapi-mcp"
        ) from exc

    fastapi_app = create_autocode_app()
    fastapi_app.title = "Autocode API + MCP Server"
    fastapi_app.description = "Autocode API and MCP server"

    # Register MCP-specific endpoints (functions tagged with "mcp" interface)
    _register_mcp_endpoints(fastapi_app)

    # Mount the MCP server
    mcp = FastApiMCP(
        fastapi_app,
        name="Autocode MCP Server",
        description="MCP server for Autocode functions",
        include_tags=["mcp-tools"],
    )
    mcp.mount_http()

    return fastapi_app


def _register_mcp_endpoints(fastapi_app: FastAPI) -> None:
    """Register MCP-specific function endpoints on the given FastAPI app.

    Mirrors ``refract.mcp._register_mcp_endpoints`` but works with the
    autocode ``app`` instance.

    Args:
        fastapi_app: FastAPI application to register MCP endpoints on.
    """
    # Re-use refract's internal helper by delegating through app.mcp() logic.
    # We register MCP endpoints the same way refract does: add the function
    # routes tagged "mcp-tools" so FastApiMCP can discover them.
    try:
        from refract.api import create_handler
        from refract.mcp import _register_mcp_endpoints as _refract_mcp_endpoints
        _refract_mcp_endpoints(fastapi_app, app)
    except (ImportError, AttributeError):
        # Graceful fallback: no MCP-specific endpoints, but MCP server still
        # mounts via FastApiMCP scanning all existing routes.
        pass


# ---------------------------------------------------------------------------
# Custom CLI commands
# ---------------------------------------------------------------------------

@app.command(name="serve-api")
@click.option("--host", default="127.0.0.1", show_default=True, help="Host to bind to.")
@click.option("--port", default=8000, type=int, show_default=True, help="Port to bind to.")
def serve_api_cmd(host: str, port: int):
    """Start the API server with autocode's own web views.

    Serves autocode's custom dashboard (/) and functions (/functions) pages
    instead of refract's generic dashboard.html.

    \b
    Examples:
        autocode serve-api
        autocode serve-api --host 0.0.0.0 --port 8080
    """
    import uvicorn
    click.echo(f"Starting Autocode API server on http://{host}:{port}")
    fastapi_app = create_autocode_app()
    uvicorn.run(fastapi_app, host=host, port=port)


@app.command(name="serve")
@click.option("--host", default="0.0.0.0", show_default=True, help="Host to bind to.")
@click.option("--port", default=8000, type=int, show_default=True, help="Port to bind to.")
def serve_cmd(host: str, port: int):
    """Start the unified server with autocode views + API + MCP (recommended).

    Serves autocode's custom web UI and exposes both REST API and MCP tool
    endpoints.

    \b
    Examples:
        autocode serve
        autocode serve --host 127.0.0.1 --port 8001
    """
    import uvicorn
    click.echo(f"Starting Autocode unified server (API + MCP) on http://{host}:{port}")
    fastapi_app = create_autocode_mcp_app()
    uvicorn.run(fastapi_app, host=host, port=port)


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
    from pathlib import Path

    from autocode.core.code.analyzer import analyze_file_metrics
    from autocode.core.code.coupling import analyze_coupling
    from autocode.core.code.health import HealthConfig, load_thresholds, run_health_check
    from autocode.core.vcs.git import get_tracked_files

    root = Path(project_root).resolve()
    config = HealthConfig() if strict else load_thresholds(root)

    _ALL_EXTENSIONS = (".py", ".js", ".mjs", ".jsx")
    files = get_tracked_files(*_ALL_EXTENSIONS, cwd=str(root))

    file_metrics = []
    for fpath in files:
        if any(Path(fpath).match(pattern) for pattern in config.exclude):
            continue
        try:
            content = (root / fpath).read_text(encoding="utf-8")
            file_metrics.append(analyze_file_metrics(fpath, content))
        except Exception:
            pass

    coupling = analyze_coupling(files)
    result = run_health_check(config, file_metrics, coupling_result=coupling)

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
