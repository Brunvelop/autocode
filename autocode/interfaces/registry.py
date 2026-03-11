"""
Backward-compatible re-exports. Real code lives in autocode.core.registry.

Moved to autocode.core.registry to break the circular dependency:
  autocode.core → autocode.interfaces (was wrong direction)
  autocode.interfaces → autocode.core (natural direction ✅)
"""
from autocode.core.registry import (  # noqa: F401
    RegistryError,
    register_function,
    get_all_functions,
    get_functions_for_interface,
    get_all_schemas,
    load_functions,
    get_stream_func,
    clear_registry,
    function_count,
    get_function_by_name,
    _registry,
    _stream_registry,
    _loaded,
    _ensure_loaded,
    _generate_function_info,
    _extract_param_info,
    _get_module_file_path,
    _has_register_decorator,
)
