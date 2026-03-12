# Autocode

Minimalistic, registry-driven framework for code quality and AI-assisted development.

Write a Python function, decorate it with `@register_function`, and it's instantly available as a **REST endpoint**, a **CLI command**, an **MCP tool** for AI assistants, and a **web component** — with zero boilerplate.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Quick Start

```bash
# Clone & install
git clone https://github.com/Brunvelop/autocode.git
cd autocode
uv sync            # or: pip install -e .

# Start the unified server (API + MCP + Web Dashboard)
uv run autocode serve

# Open in browser
#   Dashboard:      http://localhost:8000
#   API Docs:       http://localhost:8000/docs      (auto-generated OpenAPI/Swagger)
#   Functions UI:   http://localhost:8000/functions
```

### Other ways to interact

```bash
# CLI — list all registered functions
uv run autocode list

# CLI — run code health quality gates
uv run autocode health-check

# CLI — any registered function becomes a command
uv run autocode generate --signature-type qa --inputs '{"question": "What is Python?"}'

# pytest plugin — zero config
uv run pytest --autocode-health
```

---

## How It Works

Autocode uses a **Registry-Driven Architecture**. The registry is the single source of truth:

```python
from autocode.core.registry import register_function
from autocode.core.models import GenericOutput

@register_function(http_methods=["GET", "POST"])
def my_function(x: int, y: str = "default") -> GenericOutput:
    """Does something useful.

    Args:
        x: First parameter
        y: Second parameter
    """
    return GenericOutput(success=True, result=x, message=y)
```

That single decorator gives you:

| Interface | What you get | Zero config? |
|-----------|-------------|:---:|
| **REST API** | `GET /my_function?x=5` and `POST /my_function` with JSON body | ✅ |
| **CLI** | `autocode my-function --x 5 --y hello` | ✅ |
| **MCP** | AI assistants discover and call it as a tool | ✅ |
| **Web UI** | `<auto-my-function>` web component auto-generated | ✅ |
| **OpenAPI** | Full schema at `/docs` with params, types, descriptions | ✅ |

Type hints become validations. Docstrings become help text. No glue code.

---

## Features

### 🤖 AI / Chat

| Function | Description | Interfaces |
|----------|-------------|------------|
| `generate` | Generic generator with signature selection (code, design, QA) | API, CLI |
| `chat` | Conversational AI with context and history | API, CLI |
| `chat_stream` | Streaming chat via SSE | API |
| `calculate_context_usage` | Token usage calculation for context window | API, CLI |
| `get_chat_config` | Current chat configuration | API |

### 📊 Code Analysis

| Function | Description | Interfaces |
|----------|-------------|------------|
| `get_code_structure` | Full code structure tree | API |
| `get_code_summary` | Compact code summary | API, MCP |
| `generate_code_metrics` | Generate metrics snapshot (CC, MI, SLOC) | API, MCP |
| `get_metrics_snapshots` | List saved metrics snapshots | API, MCP |
| `get_commit_metrics` | Metrics for a specific commit | API, MCP |
| `get_metrics_history` | Metrics over time | API, MCP |
| `get_architecture_snapshot` | Dependency graph and architecture | API |

### 🔀 Git / VCS

| Function | Description | Interfaces |
|----------|-------------|------------|
| `get_git_tree` | Full repository file tree | API |
| `get_git_status` | Detailed working directory status | API |
| `get_git_status_summary` | Compact status summary | API, MCP |
| `get_git_log` | Commit history | API |
| `get_git_log_summary` | Compact commit log | API, MCP |
| `get_commit_detail` | Full diff and metadata for a commit | API, MCP |

### 📋 Planning

| Function | Description | Interfaces |
|----------|-------------|------------|
| `create_commit_plan` | AI-assisted commit plan creation | API, MCP |
| `list_commit_plans` | List plans by status | API, MCP |
| `get_commit_plan` | Get plan details | API, MCP |
| `update_commit_plan` | Modify plan | API, MCP |
| `delete_commit_plan` | Delete plan | API, MCP |
| `approve_plan` | Approve and execute plan | API, MCP |
| `revert_plan` | Revert executed plan | API, MCP |
| `get_plan_review_metrics` | Plan review metrics | API |

### 📁 File Operations

| Function | Description | Interfaces |
|----------|-------------|------------|
| `read_file_content` | Read file content | MCP |
| `write_file_content` | Write file content | MCP |
| `replace_in_file` | Search & replace in file | MCP |
| `delete_file` | Delete file | MCP |

### 🔄 Workflow / Sessions

| Function | Description | Interfaces |
|----------|-------------|------------|
| `start_ai_session` | Start tracked AI session | API, CLI |
| `save_conversation` | Save conversation to session | API, CLI |
| `finalize_ai_session` | Finalize session with summary | API, CLI |
| `abort_ai_session` | Abort session | API, CLI |
| `get_current_session` | Get active session | API, CLI |
| `list_ai_sessions` | List all sessions | API, CLI |

---

## Pytest Plugin: Code Health Quality Gates

Autocode includes a pytest plugin that runs **code health quality gates** against your project. It installs automatically and activates with a single flag:

```bash
pytest --autocode-health
```

Output:
```
╔══════════════════════════════════════════════════════╗
║            CODE HEALTH QUALITY GATES                 ║
╠══════════════════════════════════════════════════════╣
║  Files analyzed           42                         ║
║  Avg MI                   67.3 ✅                    ║
║  Avg CC                   2.43 ✅                    ║
║  Rank F functions         0 ✅                       ║
║  Circular deps            0 ✅                       ║
╠══════════════════════════════════════════════════════╣
║  ✅  ALL GATES PASSED                                ║
╚══════════════════════════════════════════════════════╝
```

### What it checks

| Level | Gate | What it measures |
|-------|------|-----------------|
| File | **Maintainability Index** | Composite index (0-100). Higher = more maintainable |
| File | **SLOC** | Source lines of code per file |
| File | **Avg CC** | Average cyclomatic complexity per file |
| Function | **Cyclomatic Complexity** | Independent execution paths per function |
| Function | **Nesting Depth** | Max nesting level (if/for/while/try) |
| Project | **Rank F Budget** | Number of functions with CC > 25 |
| Project | **Avg MI / Avg CC** | Project-wide trends |
| Project | **Circular Dependencies** | Cycles in the package dependency graph |

### Configuration

Add to your `pyproject.toml`:

```toml
[tool.codehealth]
critical_mi = 20.0
warning_mi = 40.0
critical_function_cc = 25
warning_function_cc = 15
critical_nesting = 8
warning_nesting = 5
critical_file_sloc = 1000
warning_file_sloc = 500
max_rank_f_functions = 0
max_circular_deps = 0
exclude = ["tests/*"]
```

`critical` = test **fails** (exit code 1). `warning` = visible warning in output.

> 📖 Full documentation: [`autocode/testing/README.md`](autocode/testing/README.md)

---

## CLI Reference

```bash
autocode serve                    # Start unified server (API + MCP + Web) [recommended]
autocode serve-api                # Start API-only server
autocode serve-mcp                # Start API + MCP server
autocode list                     # List all registered functions with parameters
autocode health-check             # Run quality gates (standalone, no pytest needed)
autocode health-check --format json   # Machine-readable output for CI
autocode health-check --strict        # Ignore pyproject.toml, use strict defaults
autocode <function-name> [--params]   # Execute any registered function
```

Options for `serve*`:
```bash
--host TEXT     Host to bind to (default: 0.0.0.0)
--port INT      Port (default: 8000)
--reload        Auto-reload on code changes
```

---

## Web Dashboard

The web UI is served automatically by `autocode serve` at the root URL. It includes:

- **Dashboard** (`/`) — Overview with code metrics, git status, and chat
- **Functions** (`/functions`) — Auto-generated UI for every registered function
- **API Docs** (`/docs`) — Interactive OpenAPI/Swagger documentation
- **Tests** (`/tests`) — Browser-based test runner for web components

Web components are built with [Lit](https://lit.dev/) and auto-generated from the function registry. Custom components include:
- `<autocode-chat>` — AI chat with streaming, context tracking, and session management
- `<code-dashboard>` — Metrics visualization with treemap, charts, and dependency graph
- `<git-dashboard>` — Git status, commit history, and commit plan management
- `<code-explorer>` — Interactive code structure browser
- `<screen-recorder>` — In-browser screen recording utility

> 📖 Architecture details: [`autocode/web/elements/ARCHITECTURE.md`](autocode/web/elements/ARCHITECTURE.md)

---

## Architecture

```
autocode/
├── core/                    # Business logic (the only place to add features)
│   ├── registry.py             # Central function registry (source of truth)
│   ├── models.py               # Shared models (GenericOutput, FunctionInfo, etc.)
│   ├── ai/                     # AI chat & generation (DSPy-based)
│   ├── code/                   # Code analysis, metrics, health checks
│   ├── planning/               # Commit planning & file operations
│   ├── vcs/                    # Git integration
│   ├── workflow/               # AI session management
│   └── utils/                  # File I/O, OpenRouter client
├── interfaces/              # Auto-generated interfaces (stable, don't touch)
│   ├── api.py                  # FastAPI — dynamic endpoints from registry
│   ├── cli.py                  # Click — dynamic commands from registry
│   └── mcp.py                  # MCP — dynamic tools from registry
├── testing/                 # Pytest plugin for code health
│   ├── plugin.py               # pytest11 entry point
│   └── gates.py                # Quality gate test classes
└── web/                     # Frontend
    ├── views/                  # HTML pages
    └── elements/               # Lit web components (auto-generated + custom)
```

**Key principle:** Add functions in `core/`, the interfaces adapt automatically. You never edit `api.py` to add an endpoint.

> 📖 Interface architecture: [`autocode/interfaces/ARCHITECTURE.md`](autocode/interfaces/ARCHITECTURE.md)

---

## Extending Autocode

### Add a new function

1. Create your function in `autocode/core/`:

```python
from autocode.core.registry import register_function
from autocode.core.models import GenericOutput

@register_function(
    http_methods=["GET", "POST"],       # REST methods
    interfaces=["api", "cli", "mcp"],   # Where to expose
)
def my_new_feature(name: str, count: int = 5) -> GenericOutput:
    """Short description shown in help and OpenAPI.

    Args:
        name: Who to greet
        count: How many times
    """
    greeting = f"Hello {name}! " * count
    return GenericOutput(success=True, result=greeting, message="Done")
```

2. That's it. Restart the server and you have:
   - `GET /my_new_feature?name=World`
   - `POST /my_new_feature` with `{"name": "World", "count": 3}`
   - `autocode my-new-feature --name World --count 3`
   - MCP tool `my_new_feature` discovered by AI assistants
   - `<auto-my-new-feature>` web component

### Add a new quality gate

See [`autocode/testing/README.md`](autocode/testing/README.md#añadir-un-nuevo-quality-gate).

---

## Development

```bash
# Install dev dependencies
uv sync

# Run all tests
uv run pytest

# Run only health gates
uv run pytest --autocode-health

# Run unit tests only
uv run pytest tests/unit/ -v

# Start with auto-reload
uv run autocode serve --reload
```

---

## Requirements

- **Python 3.12+**
- **[uv](https://github.com/astral-sh/uv)** (recommended) or pip
- **OPENROUTER_API_KEY** environment variable (for AI features)

### Key dependencies

| Package | Purpose |
|---------|---------|
| FastAPI + Uvicorn | REST API server |
| Click | CLI framework |
| fastapi-mcp | MCP protocol integration |
| DSPy | AI pipeline framework |
| LiteLLM | Multi-provider LLM routing |
| GitPython | Git operations |
| Lizard | Code complexity analysis |
| Pydantic | Data validation and serialization |

---

## License

MIT — see [LICENSE](LICENSE).
