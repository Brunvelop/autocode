# DCC: autocode
> Document-Code Compression v1.0
> Documento generativo bidireccional

---

## AXIOMAS

```
A1. Una función, una verdad
    → La signature Python ES la documentación, validación y schema

A2. Core es agnóstico
    → Core NO importa de interfaces, web, ni conoce cómo se consume

A3. Interfaces son espejos
    → API/CLI/MCP son transformaciones 1:1 del Registry, sin lógica propia

A4. Output universal
    → Toda función retorna GenericOutput{result, success, message}

A5. Generación > Configuración
    → Preferir introspección automática sobre archivos de config manuales
```

---

## CONTRATOS

```python
# === Contrato de Salida (inmutable) ===
GenericOutput:
    result: Any          # El valor de retorno
    success: bool        # ¿Operación exitosa?
    message: str?        # Contexto opcional

# === Contrato de Registro ===
@register_function(http_methods?, interfaces?)
def f(params: typed) -> GenericOutput

# === Contrato de Parámetro ===
ParamSchema:
    name: str
    type: Type           # Inferido de signature
    default: Any?
    required: bool       # True si no hay default
    description: str     # Inferido de docstring
    choices: list?       # Inferido de Literal[...]

# === Contrato de Función ===
FunctionInfo:
    name: str            # f.__name__
    func: Callable       # La función real
    description: str     # Docstring.short_description
    params: [ParamSchema]
    http_methods: [str]  # GET, POST...
    interfaces: [str]    # api, cli, mcp
```

---

## TOPOLOGÍA

```
┌─────────────────────────────────────────────────────────┐
│                        CORE                             │
│  (Funciones puras + @register_function)                 │
│  ai/ · utils/ · vcs/ · workflow/                        │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼ popula
┌─────────────────────────────────────────────────────────┐
│                      REGISTRY                           │
│  FUNCTION_REGISTRY: Dict[str, FunctionInfo]             │
│  (Fuente única de verdad)                               │
└───────────────────────┬─────────────────────────────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
      ┌───────┐    ┌────────┐    ┌────────┐
      │  API  │    │  CLI   │    │  MCP   │
      │FastAPI│    │Typer   │    │Protocol│
      └───┬───┘    └────────┘    └────────┘
          │
          ▼ expone /functions/details
┌─────────────────────────────────────────────────────────┐
│                    WEB ELEMENTS                         │
│  AutoFunctionController → AutoFunctionElement           │
│  (Genera <auto-{func}> dinámicamente)                   │
└─────────────────────────────────────────────────────────┘

Regla de dependencia:
  Core ← Registry ← Interfaces ← Web
  (Las flechas apuntan hacia lo que se conoce)
```

---

## PATRONES

### P1: Registry-Driven Generation
```
Entrada:  Función Python decorada
Proceso:  Introspección → Metadata → Generación dinámica
Salida:   Endpoint API + Comando CLI + Tool MCP + Web Component

Invariante: 0 líneas de código manual por función nueva
```

### P2: Thin Adapter
```
Entrada:  Request (HTTP/CLI args/MCP call)
Proceso:  Parse → Lookup Registry → Invoke → Format Response
Salida:   Response en formato del protocolo

Invariante: Adapter no contiene lógica de dominio
            Adapter no valida reglas de negocio
```

### P3: Controller-View Separation (Web)
```
AutoFunctionController    AutoFunctionElement
├─ params (state)         ├─ render()
├─ result (state)         └─ renderParam()
├─ execute()
├─ validate()
└─ callAPI()

Herencia:
  LitElement ← AutoFunctionController ← AutoFunctionElement
                                      ← CustomComponent (Chat, etc.)
```

### P4: Shared Design Tokens
```
shared/styles/theme.js    →  Variables CSS
shared/styles/common.js   →  Utilidades (spinner, badge)

Consumo: Cada componente importa tokens, no define valores
```

---

## INVARIANTES

```
∀ f ∈ FUNCTION_REGISTRY:
    f.return_type ⊆ GenericOutput
    f.params inferidos de inspect.signature(f)
    f.description inferido de docstring_parser(f)

∀ adapter ∈ {API, CLI, MCP}:
    adapter.endpoints = transform(FUNCTION_REGISTRY)
    adapter.logic ∩ domain_logic = ∅

∀ component ∈ WebElements:
    component.styles ⊇ themeTokens
    component extends AutoFunctionController ∨ LitElement
```

---

## TRANSFORMACIONES

```
                    BACKEND
Python Type    ──────────────────►  JSON Schema Type
  int                                 "integer"
  str                                 "string"
  List[T]                             {"type": "array", "items": T}
  Literal["a","b"]                    {"enum": ["a","b"]}
  Optional[T]                         T + nullable

Docstring      ──────────────────►  Metadata
  short_description                   FunctionInfo.description
  Args.param_name                     ParamSchema.description

                    FRONTEND
JSON Schema    ──────────────────►  HTML Input
  "string"                            <input type="text">
  "integer"                           <input type="number">
  "boolean"                           <input type="checkbox">
  {"enum": [...]}                     <select>
  "dict" / "json"                     <textarea> + JSON parse
```

---

## FLUJO DE VIDA

```
1. DEFINICIÓN (Dev time)
   def hello(name: str) -> GenericOutput:
       """Saluda a alguien."""
       return GenericOutput(result=f"Hola {name}", success=True)

2. REGISTRO (Import time)
   @register_function  →  FUNCTION_REGISTRY["hello"] = FunctionInfo(...)

3. EXPOSICIÓN (Runtime)
   API:  GET/POST /hello?name=X  →  {"result": "Hola X", "success": true}
   CLI:  autocode hello --name X  →  stdout: "Hola X"
   MCP:  tool.hello({name: X})   →  GenericOutput

4. CONSUMO (Browser)
   <auto-hello> genera form + ejecuta + muestra resultado
```

---

## ANTI-PATRONES

```
✗ Editar api.py para añadir endpoint
  → Usar @register_function en core

✗ Hardcodear colores/espaciado en componente
  → Importar de shared/styles/theme.js

✗ Validar negocio en adapter
  → La función en core valida y retorna GenericOutput(success=False)

✗ Crear modelo Pydantic manual por endpoint
  → Se genera dinámicamente desde FunctionInfo.params

✗ Import circular core → interfaces
  → Core nunca importa de interfaces
```

---

## EXTENSIÓN

```
AÑADIR FUNCIÓN:
1. Crear archivo en core/
2. Decorar con @register_function
3. Fin (API+CLI+MCP+Web disponibles)

AÑADIR INTERFAZ:
1. Crear adapter en interfaces/
2. Leer de FUNCTION_REGISTRY
3. Transformar a protocolo destino

AÑADIR COMPONENTE CUSTOM:
1. Extender AutoFunctionController
2. Override render()
3. Importar themeTokens
```

---

## VERIFICACIÓN

```bash
# Los invariantes son testeables:
pytest tests/unit/interfaces/test_registry.py  # Contratos
pytest tests/unit/interfaces/test_models.py    # Tipos

# Verificar que toda función registrada retorna GenericOutput:
∀ name, info in FUNCTION_REGISTRY.items():
    assert issubclass(info.return_type, GenericOutput)
```

---

> **Regeneración**: Este documento + Python stdlib + FastAPI + Lit = autocode
> **Extracción**: inspect(autocode) + AST analysis = Este documento
