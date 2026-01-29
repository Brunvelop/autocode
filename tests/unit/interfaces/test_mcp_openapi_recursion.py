"""Regression test: ensure MCP OpenAPI conversion does not crash on git tree schema.

Historically, recursive response models (like a tree with children: List[Node]) cause
`fastapi_mcp` to raise RecursionError while resolving $refs.

We changed get_git_tree() to return a non-recursive graph to keep OpenAPI acyclic.
"""

from fastapi.openapi.utils import get_openapi


def test_fastapi_mcp_convert_openapi_to_mcp_tools_does_not_recurse(populated_registry):
    from autocode.interfaces.api import create_api_app
    from fastapi_mcp.openapi.convert import convert_openapi_to_mcp_tools

    app = create_api_app()
    schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )

    # Should not raise RecursionError
    tools, operation_map = convert_openapi_to_mcp_tools(schema)

    assert isinstance(tools, list)
    assert isinstance(operation_map, dict)

