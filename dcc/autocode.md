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

A3. Refract como capa de exposición
    → API/CLI/MCP/WebUI son generados por Refract desde el registry de funciones
    → `from refract import register_function` es el único punto de registro

A4. Output tipado (en transición)
    → Las funciones registradas devuelven GenericOutput o subclase tipada
    → Objetivo: devolver modelos de dominio directos con errores vía excepciones
    → Ver: dcc/core.md para detalles del modelo de salida

A5. Generación > Configuración
    → Preferir introspección automática sobre archivos de config manuales
```

---

## CONTRATOS

```python
# === Contrato de Salida (actual) ===
GenericOutput:
    result: Any          # El valor de retorno (idealmente tipado en subclases)
    success: bool        # ¿Operación exitosa?
    message: str?        # Contexto opcional

# === Contrato de Registro ===
from refract import register_function

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
│  ai/ · utils/ · vcs/ · code/ · planning/               │
└───────────────────────┬─────────────────────────────────┘
                        │ from refract import register_function
                        ▼ popula
┌─────────────────────────────────────────────────────────┐
│                      REFRACT                            │
│  Registry + API + CLI + MCP + WebUI (/dashboard)        │
│  (Capa de exposición unificada)                         │
└───────────────────────┬─────────────────────────────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
      ┌───────┐    ┌────────┐    ┌────────┐
      │  API  │    │  CLI   │    │  MCP   │
      │FastAPI│    │Click   │    │Protocol│
      └───┬───┘    └────────┘    └────────┘
          │
          ▼ expone /functions/details
┌─────────────────────────────────────────────────────────┐
│                    WEB ELEMENTS                         │
│  autocode/web/: index.html + custom dashboards          │
│  refract/web/: /dashboard con <auto-{func}> generados   │
└─────────────────────────────────────────────────────────┘

Regla de dependencia:
  Core ← Refract ← Web
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

### P3: Composición en Web Components
```
Componentes Custom (autocode/web/):
LitElement
    ↑
MiComponente
└─ this._client = new RefractClient()
└─ render(), _fetchData(), ...

RefractClient:
    call(funcName, params) → Promise
    stream(funcName, params) → AsyncIterable
    loadSchemas() → Promise
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
    f.params inferidos de inspect.signature(f)
    f.description inferido de docstring_parser(f)
    f.return_type ∈ {GenericOutput, subclase de GenericOutput}  # en transición

∀ adapter ∈ {API, CLI, MCP}:
    adapter.endpoints = transform(FUNCTION_REGISTRY)
    adapter.logic ∩ domain_logic = ∅

∀ component ∈ autocode/web/elements:
    component.styles ⊇ themeTokens
    component usa RefractClient para llamar al backend
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

AÑADIR COMPONENTE CUSTOM (con backend):
1. Extender LitElement directamente
2. Componer con RefractClient: this._client = new RefractClient()
3. Usar this._client.call('func_name', params) para llamar al backend
4. Importar themeTokens
```

---

## VERIFICACIÓN

```bash
# Tests unitarios
pytest tests/unit/

# Verificar que toda función registrada retorna GenericOutput:
python -c "
from refract import FUNCTION_REGISTRY
from autocode.core.models import GenericOutput
for name, info in FUNCTION_REGISTRY.items():
    if info.return_type:
        assert issubclass(info.return_type, GenericOutput), \
            f'{name} no retorna GenericOutput'
print(f'✓ {len(FUNCTION_REGISTRY)} funciones verificadas')
"
```

---

> **Regeneración**: Este documento + Python stdlib + FastAPI + Lit = autocode
> **Extracción**: inspect(autocode) + AST analysis = Este documento
