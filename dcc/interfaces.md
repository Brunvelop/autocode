# DCC: interfaces
> Document-Code Compression v1.0
> Módulo de exposición automática de funciones

---

## AXIOMAS

```
A1. Registry es la fuente única de verdad
    → Toda exposición (API/CLI/MCP) deriva exclusivamente del FUNCTION_REGISTRY

A2. Interfaces son "Thin Layers"
    → Solo traducen protocolos, NUNCA contienen lógica de negocio

A3. GenericOutput es el contrato universal
    → Toda función registrada DEBE retornar GenericOutput o subclase

A4. Autodescubrimiento > Configuración
    → Funciones se descubren por introspección AST, no por listas manuales

A5. Decorator como punto único de registro
    → @register_function es la única forma de exponer funciones
```

---

## CONTRATOS

```python
# === Contrato de Salida (inmutable) ===
GenericOutput:
    result: Any          # El valor de retorno
    success: bool        # ¿Operación exitosa?
    message: str?        # Contexto opcional

# === Contrato de Parámetro (runtime) ===
ParamSchema:
    name: str
    type: Any            # Tipo Python (incluye genéricos)
    default: Any?
    required: bool       # True si no hay default
    description: str     # Extraído de docstring
    choices: list?       # Extraído de Literal[...]

# === Contrato de Función (runtime) ===
FunctionInfo:
    name: str            # f.__name__
    func: Callable       # La función real
    description: str     # Docstring.short_description
    params: [ParamSchema]
    http_methods: [str]  # GET, POST...
    interfaces: [str]    # api, cli, mcp
    return_type: Type?   # GenericOutput o subclase
    streaming: bool      # False por defecto; True si soporta SSE streaming

# === Contratos de Serialización (API) ===
ParamSchema:
    name: str
    type: str            # Tipo serializado a string
    default: Any?
    required: bool
    description: str
    choices: list?

FunctionSchema:
    name: str
    description: str
    http_methods: [str]
    parameters: [ParamSchema]
    streaming: bool      # Incluido en /functions/details para el frontend
```

---

## TOPOLOGÍA

```
┌─────────────────────────────────────────────────────────┐
│                        CORE                             │
│  (autocode/core/**/*)                                   │
│  Funciones puras + @register_function                   │
└───────────────────────┬─────────────────────────────────┘
                        │ popula (import time)
                        ▼
┌─────────────────────────────────────────────────────────┐
│                      REGISTRY                           │
│  registry.py                                            │
│  _registry: list[FunctionInfo]                          │
│  _stream_registry: dict[str, Callable]                  │
│  get_functions_for_interface(interface) → filtrado      │
│  get_stream_func(name) → Callable|None                  │
└───────────────────────┬─────────────────────────────────┘
                        │ consulta (runtime)
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
      ┌───────┐    ┌────────┐    ┌────────┐
      │  API  │    │  CLI   │    │  MCP   │
      │api.py │    │cli.py  │    │mcp.py  │
      │FastAPI│    │Click   │    │fastapi │
      └───┬───┘    └───┬────┘    │ _mcp   │
          │            │         └────────┘
          │            │
          ▼            ▼
      HTTP/JSON    stdout/stdin


Dependencias internas:
  models.py ← registry.py ← {api.py, cli.py, mcp.py}
  logging_config.py ← {api.py, cli.py}

Regla de dependencia:
  Core ← Registry ← Adapters
  (Adapters NUNCA importan de Core directamente)
```

---

## PATRONES

### P1: Decorator Registration
```
Entrada:  Función Python con type hints y docstring
Proceso:  @register_function inspecciona signature → genera FunctionInfo
Salida:   Función añadida a FUNCTION_REGISTRY

Invariante: El decorator NO modifica el comportamiento de la función
            Solo registra metadata
```

### P2: Dynamic Model Generation
```
Entrada:  FunctionInfo.params
Proceso:  create_dynamic_model() → Pydantic model
Salida:   Modelo para validación FastAPI (Input/QueryParams)

Invariante: 0 modelos Pydantic escritos manualmente por endpoint
```

### P3: Interface Filtering
```
Entrada:  interface: str ("api" | "cli" | "mcp")
Proceso:  get_functions_for_interface(interface)
Salida:   Dict[str, FunctionInfo] filtrado

Invariante: Toda consulta de funciones pasa por esta función
            Nunca filtrar manualmente con `if "x" in interfaces`
```

### P4: Thin Adapter
```
Entrada:  Request (HTTP body/query, CLI args, MCP call)
Proceso:  Parse → Lookup Registry → Invoke func(**params) → Format Response
Salida:   Response en formato del protocolo

Invariante: Adapter no valida reglas de negocio
            Adapter no transforma datos (solo formatos)
```

### P5: AST-Based Discovery
```
Entrada:  autocode/core/**/*.py
Proceso:  Parsear AST → buscar @register_function → importar módulo
Salida:   Módulos con funciones registradas cargados

Invariante: Solo se importan módulos con el decorator
            Evita imports innecesarios (utils, models, etc.)
```

### P6: SSE Streaming Adapter
```
Entrada:  FunctionInfo con streaming=True
Proceso:  1. register_function(streaming=True, stream_func=fn) 
             → Valida: streaming=True requiere stream_func (RegistryError si no)
             → Almacena stream_func en _stream_registry[name] (dict separado)
          2. _register_dynamic_endpoints() detecta streaming=True
             → get_stream_func(name) obtiene el async generator
             → _create_stream_handler(func_info, stream_func) crea handler SSE
          3. Handler retorna StreamingResponse(media_type="text/event-stream")
Salida:   Endpoint POST que retorna SSE stream

Estado privado:
  _stream_registry: dict[str, Callable]  # Separado de _registry
  get_stream_func(name) → Callable|None  # Función pública de acceso
  clear_registry() limpia _stream_registry también

Invariante: stream_func NO se almacena en FunctionInfo (Pydantic)
            Solo en _stream_registry (dict simple)
            streaming=True sin stream_func → RegistryError
            stream_func sin streaming=True → se almacena pero no se usa
            _create_stream_handler genera modelo Pydantic dinámico igual que handlers normales
```

---

## INVARIANTES

```
∀ f ∈ FUNCTION_REGISTRY:
    issubclass(f.return_type, GenericOutput)
    f.params = inspect.signature(f.func).parameters (procesado)
    f.description = docstring_parser(f.func).short_description

∀ adapter ∈ {api.py, cli.py, mcp.py}:
    adapter.functions = get_functions_for_interface(adapter.name)
    adapter.business_logic = ∅

∀ endpoint ∈ API:
    endpoint.input_model = create_dynamic_model(FunctionInfo)
    endpoint.response_model = FunctionInfo.return_type

∀ command ∈ CLI:
    command.options = FunctionInfo.params → Click.option
    command.help = FunctionInfo.description
```

---

## TRANSFORMACIONES

```
                    REGISTRO
Python Signature   ──────────────────►  ParamSchema
  name: str                              name="name"
  param.annotation                       type=str
  param.default                          default=None/value
  docstring.Args.name                    description="..."

                    SERIALIZACIÓN
ParamSchema      ──────────────────►  ParamSchema
  type: Type                             type: str (serializado)
  (resto igual)                          (resto igual)

                    API
FunctionInfo       ──────────────────►  FastAPI Endpoint
  name                                   path=f"/{name}"
  http_methods                           methods=[GET, POST]
  params → DynamicModel                  Body/Query params
  return_type                            response_model

                    CLI
FunctionInfo       ──────────────────►  Click Command
  name                                   @app.command(name)
  description                            help=description
  params                                 @click.option(...)

                    MCP
FunctionInfo       ──────────────────►  MCP Tool
  (via FastAPI)                          tags=["mcp-tools"]
  fastapi_mcp                            include_tags filter

                    SSE STREAMING
FunctionInfo       ──────────────────►  SSE Endpoint
  streaming=True                         POST /{name}
  _stream_registry[name]                 StreamingResponse
  → _create_stream_handler()             media_type=text/event-stream
                                         Cache-Control: no-cache
```

---

## FLUJO DE VIDA

```
1. DEFINICIÓN (Dev time - autocode/core/)
   @register_function(http_methods=["GET"], interfaces=["api", "mcp"])
   def hello(name: str) -> GenericOutput:
       """Saluda a alguien."""
       return GenericOutput(result=f"Hola {name}", success=True)

2. AUTODESCUBRIMIENTO (Import time - load_core_functions)
   walk_packages(autocode.core)
   → _has_register_decorator(module_path) via AST
   → importlib.import_module(module_name)
   → Decorator ejecuta → FUNCTION_REGISTRY["hello"] = FunctionInfo(...)

3. EXPOSICIÓN (App creation time)
   API:  create_api_app() → register_dynamic_endpoints()
         → GET/POST /hello con modelo dinámico
   CLI:  _initialize_cli() → _register_commands()
         → `autocode hello --name X`
   MCP:  create_mcp_app() → _register_mcp_endpoints()
         → Tool "hello" en MCP server

4. INVOCACIÓN (Runtime)
   HTTP:  POST /hello {"name": "X"}
          → create_handler() → execute_function_with_params()
          → func(**params) → GenericOutput → JSON response
   
   CLI:   autocode hello --name X
          → _create_handler() → func(**params)
          → click.echo(result)
   
   MCP:   tool.call("hello", {name: "X"})
          → FastAPI endpoint → GenericOutput
```

---

## ANTI-PATRONES

```
✗ Editar api.py/cli.py/mcp.py para añadir endpoint/comando
  → Usar @register_function en autocode/core/

✗ Filtrar funciones manualmente: `if "api" in func.interfaces`
  → Usar get_functions_for_interface("api")

✗ Crear modelo Pydantic manual para endpoint
  → Se genera dinámicamente desde FunctionInfo.params

✗ Validar negocio en adapter (api.py)
  → La función en core valida y retorna GenericOutput(success=False)

✗ Importar módulos de core sin @register_function
  → Usar _has_register_decorator() para filtrar

✗ Hardcodear lista de módulos a cargar
  → Usar autodescubrimiento con pkgutil.walk_packages + AST

✗ Retornar dict/str desde función registrada
  → SIEMPRE retornar GenericOutput o subclase
```

---

## EXTENSIÓN

```
AÑADIR FUNCIÓN NUEVA:
1. Crear archivo en autocode/core/
2. from autocode.interfaces.registry import register_function
3. from autocode.interfaces.models import GenericOutput
4. @register_function(http_methods=[...], interfaces=[...])
5. def mi_funcion(param: type) -> GenericOutput:
6. Fin (API+CLI+MCP disponibles según interfaces)

EXPONER SOLO EN API (no CLI/MCP):
@register_function(interfaces=["api"])

EXPONER SOLO VIA GET:
@register_function(http_methods=["GET"])

AÑADIR NUEVO ADAPTER (ej: GraphQL):
1. Crear autocode/interfaces/graphql.py
2. from registry import get_functions_for_interface, load_core_functions
3. Iterar get_functions_for_interface("graphql")
4. Transformar FunctionInfo → resolvers GraphQL
5. Añadir "graphql" como opción válida en interfaces

CUSTOM OUTPUT MODEL:
class MyOutput(GenericOutput):
    extra_field: str

@register_function
def my_func() -> MyOutput:
    return MyOutput(result=..., success=True, extra_field=...)

AÑADIR FUNCIÓN STREAMING:
1. Crear async generator en core/ai/streaming.py (yields SSE strings)
2. @register_function(
       http_methods=["POST"],
       interfaces=["api"],          # Streaming solo aplica a API
       streaming=True,
       stream_func=mi_stream_func
   )
3. La función síncrona es fallback (ej: delega a versión no-streaming)
4. api.py registra automáticamente como endpoint SSE
5. Frontend detecta streaming=True en /functions/details
```

---

## VERIFICACIÓN

```bash
# Tests de contratos y registry
pytest tests/unit/interfaces/test_registry.py
pytest tests/unit/interfaces/test_models.py

# Tests de API
pytest tests/unit/interfaces/test_api.py

# Tests de CLI
pytest tests/unit/interfaces/test_cli.py

# Tests de MCP
pytest tests/unit/interfaces/test_mcp.py

# Verificar que toda función retorna GenericOutput:
python -c "
from autocode.interfaces.registry import load_core_functions, FUNCTION_REGISTRY
from autocode.interfaces.models import GenericOutput
load_core_functions()
for name, info in FUNCTION_REGISTRY.items():
    assert info.return_type and issubclass(info.return_type, GenericOutput), \
        f'{name} no retorna GenericOutput'
print(f'✓ {len(FUNCTION_REGISTRY)} funciones verificadas')
"

# Listar funciones disponibles
python -m autocode.interfaces.cli list
```

---

## ARCHIVOS

```
autocode/interfaces/
├── __init__.py          # Package marker
├── models.py            # Contratos: GenericOutput, ParamSchema, FunctionInfo
├── registry.py          # FUNCTION_REGISTRY + @register_function + autodiscovery
├── api.py               # Adapter FastAPI (create_api_app, register_dynamic_endpoints)
├── cli.py               # Adapter Click (app, _register_commands)
├── mcp.py               # Adapter MCP (create_mcp_app, fastapi_mcp integration)
├── logging_config.py    # Configuración logging (ThirdPartyLogFilter)
└── ARCHITECTURE.md      # Documentación narrativa
```

---

> **Regeneración**: Este DCC + Python stdlib + FastAPI + Click + fastapi_mcp = autocode/interfaces
> **Extracción**: inspect(autocode/interfaces) + AST analysis = Este DCC
