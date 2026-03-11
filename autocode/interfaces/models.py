"""
Backward-compatible re-exports. Real code lives in autocode.core.models.

Moved to autocode.core.models to break the circular dependency:
  autocode.core → autocode.interfaces (was wrong direction)
  autocode.interfaces → autocode.core (natural direction ✅)
"""
from autocode.core.models import (  # noqa: F401
    HttpMethod,
    Interface,
    DEFAULT_HTTP_METHODS,
    DEFAULT_INTERFACES,
    ParamSchema,
    FunctionSchema,
    FunctionInfo,
    GenericOutput,
)
