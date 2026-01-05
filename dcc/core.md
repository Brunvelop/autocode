# DCC: core
> Document-Code Compression v1.0
> Módulo de lógica de negocio y funciones puras

---

## AXIOMAS

```
A1. Core es agnóstico de interfaces
    → Core NUNCA importa de api.py, cli.py, mcp.py
    → Core SÍ importa de registry.py para @register_function

A2. GenericOutput universal
    → Toda función registrada retorna GenericOutput o subclase tipada

A3. DSPy como motor de IA
    → Signatures declarativas definen inputs/outputs de IA
    → generate_with_dspy() es el único punto de entrada a DSPy

A4. Git como backend de estado
    → Sesiones AI viven en ramas git (ai/*)
    → El working directory ES el estado de la sesión

A5. Utilidades sin efectos secundarios globales
    → utils/* son funciones puras sin estado compartido
    → Excepciones explícitas para errores de I/O
```

---

## CONTRATOS

```python
# === Contrato Base (heredado de interfaces) ===
GenericOutput:
    result: Any
    success: bool
    message: str?

# === Contrato DSPy Output ===
DspyOutput(GenericOutput):
    result: Any              # Outputs de la signature (dict o valor)
    reasoning: str?          # Razonamiento paso a paso (ChainOfThought/ReAct)
    completions: [str]?      # Múltiples completions (Predict n>1)
    trajectory: dict|list?   # Trayectoria ReAct (thoughts, tools, observations)
    history: [dict]?         # Historial completo de llamadas LM

# === Contrato Git Tree Output ===
GitTreeOutput(GenericOutput):
    result: GitTreeGraph?    # Grafo no-recursivo del árbol

GitTreeGraph:
    root_id: str             # "" (string vacío)
    nodes: [GitNodeEntry]    # Lista plana de nodos

GitNodeEntry:
    id: str                  # Path completo (ej: "autocode/core/ai")
    parent_id: str?          # Path del padre (None solo para root)
    name: str                # Nombre del archivo/directorio
    path: str                # Path completo
    type: "file"|"directory"
    size: int                # Bytes (solo archivos)

# === Contrato DSPy Signature ===
dspy.Signature:
    input_fields: {name: InputField}
    output_fields: {name: OutputField}

# === Contrato de Sesión ===
SessionData:
    session_id: str          # Timestamp YYYYMMDD-HHMMSS
    description: str
    base_branch: str
    session_type: "session"|"docs"|"tests"|"review"
    started_at: str          # ISO datetime
    status: "in_progress"|"completed"
    branch: str              # ai/{type}-{timestamp}
```

---

## TOPOLOGÍA

```
┌─────────────────────────────────────────────────────────┐
│                        CORE                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   utils/                    ai/                         │
│   ├─ file_utils.py          ├─ dspy_utils.py           │
│   │  (read/write)           │  (get_dspy_lm,           │
│   └─ openrouter.py          │   generate_with_dspy)    │
│      (fetch models)         ├─ models.py               │
│          ↑                  │  (DspyOutput)            │
│          │                  ├─ signatures.py           │
│          └──────────────────┤  (CodeGen, QA, Chat...)  │
│                             └─ pipelines.py            │
│                                (text_to_code, chat...) │
│                                        ↑               │
│   vcs/                                 │               │
│   ├─ operations.py  ─────────────────→ │               │
│   │  (GitOperations)                   │               │
│   ├─ tree.py                           │               │
│   │  (get_git_tree)                    │               │
│   └─ models.py                         │               │
│      (GitNodeEntry, GitTreeOutput)     │               │
│                                        │               │
│   workflow/                            │               │
│   └─ session.py  ──────────────────────┘               │
│      (AISessionManager, start_ai_session...)           │
│                                                         │
└───────────────────────┬─────────────────────────────────┘
                        │ popula via @register_function
                        ▼
┌─────────────────────────────────────────────────────────┐
│                      REGISTRY                           │
│  (interfaces/registry.py)                               │
└─────────────────────────────────────────────────────────┘

Dependencias internas de core:
  utils/ ← ai/pipelines ← workflow/session
  vcs/operations ← workflow/session
  vcs/models ← vcs/tree
  interfaces/models ← {ai/models, vcs/models}
  interfaces/registry ← {ai/pipelines, vcs/tree, workflow/session}
```

---

## PATRONES

### P1: DSPy Signature-to-Pipeline
```
Entrada:  dspy.Signature (declarativa)
Proceso:  generate_with_dspy(signature, inputs, module_type)
Salida:   DspyOutput con todos los campos del signature + metadata

Invariante: La signature define QUÉ generar
            El module_type define CÓMO generar (Predict, ChainOfThought, ReAct)
            generate_with_dspy es el ÚNICO punto de entrada a DSPy
```

### P2: Wrapper Class + Registered Functions
```
Clase interna:        Funciones registradas:
GitOperations         get_git_tree()
AISessionManager      start_ai_session(), finalize_ai_session()...

Invariante: La clase encapsula lógica compleja
            Las funciones @register_function son thin wrappers
            que instancian la clase y delegan
```

### P3: Output Extension Pattern
```
GenericOutput (base)
    ├── DspyOutput (ai/)      → +reasoning, +trajectory, +history
    └── GitTreeOutput (vcs/)  → result tipado como GitTreeGraph

Invariante: Subclases añaden campos específicos del dominio
            Mantienen compatibilidad con GenericOutput base
            El campo 'result' puede especializarse con tipo concreto
```

### P4: Module Introspection
```
Entrada:  ModuleType string ("ChainOfThought", "ReAct", etc.)
Proceso:  get_module_kwargs_schema() → inspecciona __init__ de la clase
Salida:   Schema de parámetros aceptados por el módulo

Invariante: 0 schemas hardcodeados
            Introspección en runtime descubre parámetros
```

### P5: Git Branch as Session State
```
Entrada:  start_ai_session(description, type)
Proceso:  Crear rama ai/{type}-{timestamp}
          Guardar session.json en .ai-context/
Estado:   La rama ES la sesión (commit = checkpoint)
Salida:   finalize_ai_session() → squash merge a main

Invariante: Todo trabajo AI está aislado en rama
            El merge es squash (historia limpia en main)
            .ai-context/ se excluye del merge a main
```

---

## INVARIANTES

```
∀ f ∈ @register_function en core:
    f.return_type ∈ {GenericOutput, DspyOutput, GitTreeOutput, ...}
    f no importa de api.py, cli.py, mcp.py

∀ signature ∈ dspy.Signature:
    len(signature.input_fields) >= 1
    len(signature.output_fields) >= 1
    fields tienen desc para autodocumentación

∀ sesión en workflow:
    branch.startswith("ai/")
    exists(.ai-context/session.json)
    session.status ∈ {"in_progress", "completed"}

∀ output ∈ DspyOutput:
    output.success = True → len(output.result) >= 1
    output.success = False → output.message explica error
```

---

## TRANSFORMACIONES

```
                    AI GENERATION
Signature + Inputs ──────────────────►  DspyOutput
  CodeGenerationSignature               result.python_code
  + {design_text: "..."}                reasoning (si ChainOfThought)

Python Type        ──────────────────►  DSPy Field Type
  str                                   dspy.InputField/OutputField
  bool                                  dspy.InputField

                    GIT TREE
git ls-tree -r -l  ──────────────────►  GitTreeGraph
  "100644 blob <sha> 1234\tpath"        nodes: [GitNodeEntry...]

                    SESSION LIFECYCLE
start_ai_session   ──────────────────►  Rama git + session.json
finalize_session   ──────────────────►  Squash merge a main
abort_session      ──────────────────►  Checkout base + delete branch
```

---

## FLUJO DE VIDA

```
1. DEFINICIÓN DE SIGNATURE (Dev time)
   class MySignature(dspy.Signature):
       input_field: str = dspy.InputField(desc="...")
       output_field: str = dspy.OutputField(desc="...")

2. PIPELINE CON REGISTRO (Dev time)
   @register_function(http_methods=["POST"])
   def my_pipeline(input_text: str) -> GenericOutput:
       output = generate_with_dspy(MySignature, {"input_field": input_text})
       return GenericOutput(success=output.success, result=output.result["output_field"])

3. EJECUCIÓN (Runtime)
   API:  POST /my_pipeline {"input_text": "..."}
   CLI:  autocode my_pipeline --input-text "..."
   MCP:  tool.my_pipeline({input_text: "..."})

4. SESIÓN AI (Workflow completo)
   start_ai_session("Implementar feature X")
   → Rama: ai/session-20260104-214500
   
   [trabajo, commits, chat...]
   
   finalize_ai_session("feat: Añadir feature X")
   → Squash merge a main
   → Rama conservada o eliminada
```

---

## ANTI-PATRONES

```
✗ Importar api.py/cli.py desde core
  → Core es agnóstico, solo importa de interfaces/registry

✗ Usar dspy.LM() directamente en pipelines
  → Usar get_dspy_lm() que maneja configuración

✗ Llamar módulos DSPy directamente (dspy.ChainOfThought())
  → Usar generate_with_dspy() como único punto de entrada

✗ Retornar dict crudo desde función registrada
  → Siempre retornar GenericOutput o subclase

✗ Hardcodear schemas de módulos DSPy
  → Usar get_module_kwargs_schema() para introspección

✗ Hacer checkout a ramas de sesión manualmente
  → Usar AISessionManager para gestionar estado

✗ Guardar estado de sesión fuera de git
  → .ai-context/ dentro de la rama es el estado
```

---

## EXTENSIÓN

```
AÑADIR NUEVA SIGNATURE DSPy:
1. Crear clase en autocode/core/ai/signatures.py
2. Añadir a SIGNATURE_MAP en pipelines.py (si aplica)
3. Crear función wrapper con @register_function si se expone

AÑADIR NUEVO PIPELINE AI:
1. Definir signature (o usar existente)
2. @register_function(http_methods=[...], interfaces=[...])
3. Llamar generate_with_dspy() con la signature
4. Transformar DspyOutput a GenericOutput apropiado

AÑADIR OPERACIÓN GIT:
1. Añadir método a GitOperations en vcs/operations.py
2. Si se expone: crear función @register_function en vcs/

AÑADIR TIPO DE SESIÓN:
1. Añadir valor a SessionType Literal
2. Añadir a VALID_SESSION_TYPES
3. (Opcional) Añadir lógica específica en AISessionManager

EXTENDER OUTPUT MODEL:
1. Crear clase que herede de GenericOutput
2. Añadir campos específicos con Field()
3. Usar como return type de función registrada
```

---

## ARCHIVOS

```
autocode/core/
├── __init__.py
├── ai/
│   ├── __init__.py
│   ├── dspy_utils.py        # get_dspy_lm, generate_with_dspy, introspección
│   ├── models.py            # DspyOutput
│   ├── pipelines.py         # Funciones registradas: chat, generate, text_to_code...
│   ├── signatures.py        # DSPy Signatures: CodeGeneration, QA, Chat...
│   └── README.md
├── utils/
│   ├── __init__.py
│   ├── file_utils.py        # read_file, write_file, read_design_document
│   └── openrouter.py        # fetch_models_info
├── vcs/
│   ├── __init__.py
│   ├── models.py            # GitNodeEntry, GitTreeGraph, GitTreeOutput
│   ├── operations.py        # GitOperations (wrapper GitPython)
│   └── tree.py              # get_git_tree() registrada
└── workflow/
    ├── __init__.py
    ├── session.py           # AISessionManager + funciones registradas
    └── README.md
```

---

## VERIFICACIÓN

```bash
# Tests unitarios de core
pytest tests/unit/core/

# Verificar que funciones de core retornan GenericOutput
python -c "
from autocode.interfaces.registry import load_core_functions, FUNCTION_REGISTRY
from autocode.interfaces.models import GenericOutput
load_core_functions()
for name, info in FUNCTION_REGISTRY.items():
    assert info.return_type and issubclass(info.return_type, GenericOutput), \
        f'{name} no retorna GenericOutput'
print(f'✓ {len(FUNCTION_REGISTRY)} funciones verificadas')
"

# Verificar signatures DSPy
python -c "
import dspy
from autocode.core.ai.signatures import (
    CodeGenerationSignature, DesignDocumentSignature, QASignature, ChatSignature
)
for sig in [CodeGenerationSignature, DesignDocumentSignature, QASignature, ChatSignature]:
    assert issubclass(sig, dspy.Signature)
    assert len(sig.input_fields) >= 1
    assert len(sig.output_fields) >= 1
    print(f'✓ {sig.__name__}: {len(sig.input_fields)} inputs, {len(sig.output_fields)} outputs')
"

# Verificar introspección de módulos DSPy
python -c "
from autocode.core.ai.dspy_utils import get_all_module_kwargs_schemas
schemas = get_all_module_kwargs_schemas()
for module, schema in schemas.items():
    print(f'{module}: {len(schema[\"params\"])} params, supports_tools={schema[\"supports_tools\"]}')
"
```

---

> **Regeneración**: Este DCC + DSPy + GitPython + Pydantic = autocode/core
> **Extracción**: inspect(autocode/core) + AST analysis = Este DCC
