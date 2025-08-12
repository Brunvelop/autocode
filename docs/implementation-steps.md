# Pasos para Crear el Esqueleto de Autocode

Este documento detalla los pasos iterativos para implementar el esqueleto con hello world expuesto en CLI, API, MCP y UI. Usar tools como write_to_file para crear archivos, confirmando cada uno. Orden: core primero, luego registry, layers, y web.

## Preparación
- Asegura dependencias: uv add typer fastapi uvicorn fastapi_mcp.
- uv sync.
- Crea dirs: mkdir core/hello, interfaces, web, docs, tests (si no existen).

## Paso 1: Crear Core Función (core/hello/hello_world.py)
- Contenido: Función pura hello_world(name: str = "World") -> str.
- Verifica: Importa y prueba manualmente.

## Paso 2: Crear Registry (interfaces/registry.py)
- Contenido: Dict INTERFACES con entrada para "hello" (func ref, desc, metadata para layers).
- Verifica: Importa y chequea que reference core func.

## Paso 3: Crear CLI (interfaces/cli.py)
- Contenido: Typer app con loop sobre registry para comandos dinámicos + @cli.command("serve") que lanza uvicorn.run(api.app).
- Verifica: Corre `python interfaces/cli.py hello --name Bruno` (debe imprimir "Hello, Bruno!").

## Paso 4: Crear API (interfaces/api.py)
- Contenido: FastAPI app con loop sobre registry para endpoints + mount("/ui", StaticFiles(directory="../web", html=True)).
- Verifica: Importa registry, asegura endpoints como GET /hello.

## Paso 5: Crear MCP (interfaces/mcp.py)
- Contenido: def setup_mcp() que crea FastApiMCP(app), loop sobre registry para add_tool, y setup_server().
- Ajuste: En api.py, llama setup_mcp() al inicializar app.
- Verifica: Una vez lanzado, chequea MCP tools disponibles.

## Paso 6: Crear Web UI (web/index.html)
- Contenido: HTML simple con input, button y JS fetch a /hello.
- Verifica: Lanza server, accede /ui/index.html, prueba el botón.

## Paso 7: Testing y Docs
- Añade test básico en tests/core/test_hello.py (usa pytest).
- Actualiza docs/project-overview.md con cambios.
- Verifica todo: uv sync, pytest, autocode serve, prueba endpoints/UI.

Tiempo estimado: 30-60 min. Expandir con más funcs repitiendo pasos 1-2.
