# Implementation Plan

[Overview]
Refactor the registry to simplify it by inferring parameters and models from function signatures, reducing duplication while maintaining automatic generation of CLI commands, API endpoints, and MCP tools.

The current registry duplicates information like parameters and input/output models that can be derived from the function definitions using Python's inspect module and typing hints. This refactoring aims to make the registry more minimalistic, aligning with the project's principles of simplicity and reusability as outlined in docs/project-overview.md. By inferring params and dynamically handling models, we eliminate redundancy, make it easier to add new functions, and ensure the layers (CLI, API, MCP) can still auto-generate interfaces. This fits into the existing system by enhancing the Functional Core / Imperative Shell architecture, keeping the core pure and layers thin.

[Types]  
Update FunctionInfo to remove explicit params and models, adding fields for inferred data if needed.

- FunctionInfo (in autocode/autocode/interfaces/models.py): Modify to include:
  - name: str
  - func: Callable
  - description: str
  - http_methods: List[str] = ["GET", "POST"]
  - (Remove params, input_model, output_model)
- Introduce InferenceUtils (new class in autocode/autocode/interfaces/utils.py) for deriving:
  - Parameters: List[Dict[str, Any]] with name, type, default, required, description (from docstrings if available)
  - InputModel: Dynamically generated Pydantic model or use GenericInput
  - OutputModel: Dynamically generated or use GenericOutput based on return type annotation

[Files]
Modify existing files to use inference, create a new utils file for inference logic, and update related interfaces.

- New files to be created:
  - autocode/autocode/interfaces/utils.py: Contains InferenceUtils class for parameter and model inference using inspect and typing.
- Existing files to be modified:
  - autocode/autocode/interfaces/registry.py: Simplify FUNCTION_REGISTRY to only include name, func, description, http_methods. Update helper functions to use inference.
  - autocode/autocode/interfaces/models.py: Remove specific models like HelloInput/Output, AddInput/Output, etc. Keep base classes and generics.
  - autocode/autocode/interfaces/api.py: Adapt endpoint creation to use inferred params and dynamic models for dependencies and responses.
  - autocode/autocode/interfaces/cli.py: Update command registration to use inferred params for options.
  - autocode/autocode/interfaces/mcp.py: (Assuming it exists based on project-overview) Update tool generation to use inferred schemas.
- Files to be deleted or moved: None.
- Configuration file updates: None.

[Functions]
Refactor registry functions to incorporate inference, update interface handlers to use new inferred data.

- New functions:
  - infer_parameters(func: Callable) -> List[Dict[str, Any]] (in utils.py): Extracts param info using inspect.signature.
  - infer_input_model(func: Callable) -> Type[BaseModel] (in utils.py): Dynamically creates Pydantic model from signature.
  - infer_output_model(func: Callable) -> Type[BaseModel] (in utils.py): Creates model based on return annotation.
- Modified functions:
  - get_function_info(name: str) -> FunctionInfo (in registry.py): Now computes inferred data on-the-fly or caches it.
  - create_dynamic_dependency(input_model) (in api.py): Adapt to handle dynamically generated models.
  - register_commands() (in cli.py): Use inferred params to generate click.options.
- Removed functions: get_input_model, get_output_model (from registry.py), as they will be replaced by inference.

[Classes]
Modify FunctionInfo and introduce InferenceUtils; update models to be more generic.

- New classes:
  - InferenceUtils (in utils.py): Utility class with static methods for inference.
- Modified classes:
  - FunctionInfo (in models.py): Remove params, input_model, output_model fields.
  - BaseFunctionInput, BaseFunctionOutput (in models.py): Keep as-is for generics.
- Removed classes: Specific models like HelloInput, HelloOutput, etc. (from models.py).

[Dependencies]
No new dependencies required, as inference uses stdlib (inspect, typing) and existing pydantic.

Existing dependencies (fastapi, click, etc.) remain unchanged.

[Testing]
Add unit tests for inference logic and update existing tests for registry and interfaces.

- New test files: tests/interfaces/test_utils.py for InferenceUtils.
- Modify existing tests: tests/core/test_hello.py to verify inference; add tests in tests/interfaces/ for registry, api, cli using mocked functions.
- Validation: Ensure 100% coverage; test dynamic generation for various function signatures (with/without defaults, types).

[Implementation Order]
Implement in a sequence that maintains functionality, starting with inference utils and ending with interface updates.

1. Create utils.py with InferenceUtils and inference methods.
2. Refactor models.py to remove specific models and adjust bases.
3. Update registry.py to simplify FUNCTION_REGISTRY and integrate inference.
4. Adapt api.py to use inferred data for endpoints.
5. Adapt cli.py to use inferred params for commands.
6. Update mcp.py similarly if applicable.
7. Add and run tests for all changes.
