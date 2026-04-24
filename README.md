# Autocode

Minimalistic, registry-driven framework for code quality and AI-assisted development.

Write a Python function, decorate it with `@register_function`, and it's instantly available as a **REST endpoint**, a **CLI command**, an **MCP tool** for AI assistants, and a **web component** — with zero boilerplate.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Quick Start

> Autocode uses [uv](https://docs.astral.sh/uv/) as its package manager. Install it with:
> `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Install

```bash
# Add to your project
uv add git+https://github.com/Brunvelop/autocode.git
```

### Run

```bash
# Start the unified server (API + MCP + Web Dashboard)
uv run autocode serve

# Open in browser
#   Dashboard:      http://localhost:8000
#   API Docs:       http://localhost:8000/docs       (auto-generated OpenAPI/Swagger)
#   Functions UI:   http://localhost:8000/dashboard  (auto-generated from Refract)
```

### Other ways to interact

```bash
# CLI — list all registered functions
uv run autocode list

# CLI — run code health quality gates
uv run autocode health-check

# CLI — any registered function becomes a command
uv run autocode generate --signature-type qa --inputs '{"question": "What is Python?"}'

# pytest plugin — zero config (requires pytest: uv add --dev pytest)
uv run pytest --autocode-health
```

### For development

```bash
git clone https://github.com/Brunvelop/autocode.git
cd autocode
uv sync

uv run autocode serve --reload
```

---

## How It Works

Autocode uses a **Registry-Driven Architecture**. The registry is the single source of truth:

```python
from pydantic import BaseModel
from refract import register_function

class MyResult(BaseModel):
    value: int
    label: str

@register_function(http_methods=["GET", "POST"])
def my_function(x: int, y: str = "default") -> MyResult:
    """Does something useful.

    Args:
        x: First parameter
        y: Second parameter
    """
    return MyResult(value=x, label=y)
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

### MCP design goals

Autocode's MCP surface is optimized for **compact code analysis that agents can chain together efficiently**.

- **Compact outputs** — prefer summaries, counts, short lists, and small structured payloads
- **High signal density** — return operational information, not large narrative blobs
- **Token efficiency** — avoid exposing heavyweight responses by default when a compact answer is enough
- **Agent composition** — make it easy to combine multiple MCP calls during exploration and debugging

That means the MCP is intentionally narrower than the full API/UI surface: planning workflows and heavier historical/detail views may still exist elsewhere in the product, while MCP stays focused on low-token, high-utility analysis.

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
| `generate_code_metrics` | Generate metrics snapshot (CC, MI, SLOC) | API |
| `get_metrics_snapshots` | List saved metrics snapshots | API |
| `get_commit_metrics` | Metrics for a specific commit | API |
| `get_metrics_history` | Metrics over time | API |
| `get_architecture_snapshot` | Dependency graph and architecture | API |
| `get_health_check` | Compact code health summary | API, CLI, MCP |
| `get_dependency_cycles` | Compact real dependency cycles at file level | MCP |
| `get_dependency_slice` | Compact local dependency slice around a target file | MCP |
| `get_architecture_hotspots` | Compact hotspot ranking for architectural triage | MCP |

Dependency analysis is the main direction for architecture-focused MCP tools: the goal is to expose compact, agent-friendly dependency insights rather than forcing agents to consume full architecture snapshots.

Example MCP workflows:

- `get_dependency_cycles(path="autocode/core", max_cycles=10)` → shortlist the most relevant file-level cycles
- `get_dependency_slice(target="autocode/core/code/architecture.py", direction="both", max_depth=2)` → inspect local impact around one file without requesting the whole graph
- `get_architecture_hotspots(path="autocode/core", limit=10)` → rank the files most likely to need architectural attention first

### 🔀 Git / VCS

| Function | Description | Interfaces |
|----------|-------------|------------|
| `get_git_tree` | Full repository file tree | API |
| `get_git_status` | Detailed working directory status | API |
| `get_git_status_summary` | Compact status summary | API, MCP |
| `get_git_log` | Commit history | API |
| `get_git_log_summary` | Compact commit log | API, MCP |
| `get_commit_detail` | Full diff and metadata for a commit | API |

### 📋 Planning

Planning remains available through the product, but it is not the primary MCP use case. The MCP is being narrowed toward compact code-analysis workflows for agents, while planning continues to fit better in API/UI-driven flows.

| Function | Description | Interfaces |
|----------|-------------|------------|
| `create_commit_plan` | AI-assisted commit plan creation | API |
| `list_commit_plans` | List plans by status | API |
| `get_commit_plan` | Get plan details | API |
| `update_commit_plan` | Modify plan | API |
| `delete_commit_plan` | Delete plan | API |
| `approve_plan` | Approve and execute plan | API |
| `revert_plan` | Revert executed plan | API |
| `get_plan_review_metrics` | Plan review metrics | API |

### 📁 File Operations

| Function | Description | Interfaces |
|----------|-------------|------------|
| `read_file_content` | Read file content | MCP |
| `write_file_content` | Write file content | MCP |
| `replace_in_file` | Search & replace in file | MCP |
| `delete_file` | Delete file | MCP |

---

## Pytest Plugin: Code Health Quality Gates

Autocode includes a pytest plugin that runs **code health quality gates** against **your project**. Once autocode is installed, the plugin auto-registers — no configuration needed. Just add pytest and run:

```bash
# 1. Add autocode (if not already installed)
uv add git+https://github.com/Brunvelop/autocode.git

# 2. Add pytest as a dev dependency
uv add --dev pytest

# 3. Run health gates against your project's code
uv run pytest --autocode-health
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
- **Functions** (`/dashboard`) — Auto-generated UI for every registered function (served by Refract)
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
├── app.py                   # Refract application instance (entry point)
├── core/                    # Business logic (the only place to add features)
│   ├── ai/                     # AI chat & generation (DSPy-based)
│   ├── code/                   # Code analysis, metrics, health checks
│   ├── planning/               # Commit planning & file operations
│   ├── vcs/                    # Git integration
│   └── utils/                  # File I/O, OpenRouter client
├── testing/                 # Pytest plugin for code health
│   ├── plugin.py               # pytest11 entry point
│   └── gates.py                # Quality gate test classes
└── web/                     # Frontend
    ├── views/                  # HTML pages (index.html — autocode's own UI)
    └── elements/               # Lit web components (custom dashboards, chat)
```

**Key principle:** Add functions in `core/`, Refract exposes them automatically to the interfaces you choose (REST API, CLI, MCP, and web components via `/dashboard`). You never write adapter code.

---

## Extending Autocode

### Add a new function

1. Create your function in `autocode/core/`:

```python
from pydantic import BaseModel, Field
from refract import register_function

class GreetingResult(BaseModel):
    greeting: str = Field(..., description="Generated greeting text")

@register_function(
    http_methods=["GET", "POST"],       # REST methods
    interfaces=["api", "cli", "mcp"],   # Where to expose
)
def my_new_feature(name: str, count: int = 5) -> GreetingResult:
    """Short description shown in help and OpenAPI.

    Args:
        name: Who to greet
        count: How many times
    """
    greeting = f"Hello {name}! " * count
    return GreetingResult(greeting=greeting)
```

2. That's it. Restart the server and you have:
   - `GET /my_new_feature?name=World`
   - `POST /my_new_feature` with `{"name": "World", "count": 3}`
   - `autocode my-new-feature --name World --count 3`
   - MCP tool `my_new_feature` discovered by AI assistants (when exposed through the MCP interface)
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
- **[uv](https://docs.astral.sh/uv/)** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **OPENROUTER_API_KEY** environment variable (for AI features only)

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
