# AI-Assisted Development Workflow (KISS MVP)

Este documento define la arquitectura y metodología de trabajo para el desarrollo de software asistido por IA en Autocode. El objetivo es establecer un flujo donde el **Diseño** sea la fuente de la verdad y el **Código** sea una implementación derivada.

## 1. Filosofía

### Principios Core

1. **El Blueprint (YAML) define QUÉ hacer**
2. **El Código (Python/JS) es CÓMO hacerlo**
3. **La IA traduce el QUÉ al CÓMO**
4. **El Humano aprueba antes de merge**
5. **Solo la IA genera código** (el humano diseña, no codifica)

### Regla de Oro

> No hay código sin blueprint. No hay merge sin aprobación humana.

---

## 2. Estructura del Proyecto

```
proyecto/
├── src/                      # Código fuente ejecutable
│   └── core/
│       └── processor.py
├── tests/                    # Tests ejecutables
│   └── core/
│       └── test_processor.py
├── design/                   # Blueprints (espejo 1:1 de src/ y tests/)
│   ├── src/
│   │   └── core/
│   │       └── processor.yaml
│   └── tests/
│       └── core/
│           └── test_processor.yaml
└── .ai-context/              # Solo existe en ramas ai/session-*
    ├── session.json          # Metadata de sesión
    ├── conversation.json     # Historial de chat
    └── change_request.yaml   # DCR + Plan de implementación
```

### Reglas de Estructura

- **`design/`**: Espejo exacto de `src/` y `tests/`
  - `src/core/processor.py` → `design/src/core/processor.yaml`
  - `tests/core/test_processor.py` → `design/tests/core/test_processor.yaml`
- **`.ai-context/`**: Solo vive en ramas `ai/session-*`, nunca se mergea a `main`

---

## 3. Estrategia de Ramas

### `main` (Producción)

- **Contenido:** Código + Diseño sincronizados y testeados
- **Regla:** Solo recibe merges aprobados por humano
- **Inmutable:** Nunca se edita directamente

### `ai/session-*` (Trabajo)

- **Contenido:** Todo el trabajo en progreso (diseño + código + contexto)
- **Ciclo de vida:** Efímera
  - **Nace de:** `main`
  - **Contiene:** Cambios en `design/`, `src/`, `tests/`, `.ai-context/`
  - **Muere:** Al mergearse a `main` (squash merge, `.ai-context/` se excluye)

### Beneficios de Una Sola Rama de Trabajo

| Aspecto | Beneficio |
|---------|-----------|
| Atomicidad | Cambios en design + código van juntos |
| Rollback | `git revert` único deshace todo |
| Simplicidad | Sin sincronización entre ramas |
| Trazabilidad | Historia completa en una rama |

---

## 4. Schemas de Documentos

### 4.1 Design Blueprint (Código)

```yaml
# design/src/core/processor.yaml
# =====================================================
# DESIGN BLUEPRINT - Especificación de processor.py
# =====================================================

meta:
  file_path: "src/core/processor.py"
  language: "python"
  description: "Procesa datos de entrada y normaliza salidas."
  version: "1.0.0"  # Opcional

# --- SECCIÓN AUTOMATIZABLE (extraído del código via AST) ---
dependencies:
  - logging
  - typing
  - pandas

classes:
  DataProcessor:
    docstring: "Clase principal para procesamiento de datos."
    methods:
      process:
        signature:
          args:
            - data: "Dict[str, Any]"
            - strict: "bool = False"
          returns: "DataFrame"
        metrics:
          loc: 45
          complexity: 5

functions:
  validate_input:
    signature:
      args:
        - data: "Dict[str, Any]"
      returns: "bool"
    metrics:
      loc: 12
      complexity: 2

# --- SECCIÓN DE DISEÑO (humano/IA) ---
logic:
  DataProcessor.process: |
    1. Validar que 'data' no esté vacío
    2. Si strict=True, verificar schema con Pydantic
    3. Normalizar columnas usando 'standard_mapping'
    4. Retornar DataFrame de Pandas
  
  validate_input: |
    1. Verificar tipo de 'data'
    2. Verificar que contenga keys requeridas
    3. Retornar True si válido, False si no

tests:
  - function: "DataProcessor.process"
    name: "Empty Data"
    input: {}
    expect: "raises ValueError"
  
  - function: "DataProcessor.process"
    name: "Valid Data"
    input: 
      id: 1
      val: "A"
    expect: "DataFrame with 1 row"
  
  - function: "validate_input"
    name: "Invalid Type"
    input: "not a dict"
    expect: "returns False"
```

### 4.2 Design Blueprint (Tests)

```yaml
# design/tests/core/test_processor.yaml
# =====================================================
# TEST BLUEPRINT - Diseño de tests para processor.py
# =====================================================

meta:
  file_path: "tests/core/test_processor.py"
  tests_for: "src/core/processor.py"
  framework: "pytest"

# --- AUTOMATIZABLE (extraído del código de tests) ---
fixtures:
  - name: "sample_data"
    scope: "function"
  - name: "processor_instance"
    scope: "module"

test_functions:
  - name: "test_process_empty_data"
    markers: ["unit"]
  - name: "test_process_valid_data"
    markers: ["unit"]
  - name: "test_process_strict_mode"
    markers: ["unit", "slow"]

# --- DISEÑO (humano/IA) ---
test_cases:
  test_process_empty_data:
    description: "Verifica que datos vacíos lanzan ValueError"
    given: "Un diccionario vacío {}"
    when: "Se llama a processor.process(data)"
    then: "Lanza ValueError con mensaje 'Data cannot be empty'"
    
  test_process_valid_data:
    description: "Verifica procesamiento correcto de datos válidos"
    given: "Un diccionario con id=1, val='A'"
    when: "Se llama a processor.process(data)"
    then: |
      - Retorna un DataFrame
      - El DataFrame tiene 1 fila
      - Las columnas están normalizadas

  test_process_strict_mode:
    description: "Verifica validación estricta de schema"
    given: "Datos válidos pero sin campo opcional 'timestamp'"
    when: "Se llama con strict=True"
    then: "Lanza ValidationError"
```

### 4.3 Change Request (DCR + Plan)

```yaml
# .ai-context/change_request.yaml
# =====================================================
# CHANGE REQUEST - DCR + Plan de implementación
# =====================================================

meta:
  id: "CR-20240115-001"
  created_at: "2024-01-15T10:30:00"
  session_branch: "ai/session-20240115-103000"
  status: "implementing"  # draft | designing | approved | implementing | completed | rejected

# --- SECCIÓN 1: REQUEST (el QUÉ) ---
request:
  title: "Añadir validación de email a processor"
  human_input: |
    Quiero que process_data valide que los emails 
    tengan formato correcto antes de procesar.
    Usar regex estándar para validación.
  
  scope:
    affected_files:
      - "src/core/processor.py"
      - "tests/core/test_processor.py"
    new_files: []
    deleted_files: []

# --- SECCIÓN 2: DESIGN CHANGES (cambios en design/) ---
design_changes:
  - file: "design/src/core/processor.yaml"
    action: "modify"
    diff:
      logic:
        "DataProcessor.process":
          add_step: "2.5. Validar formato de email con regex RFC 5322"
      tests:
        add:
          - function: "DataProcessor.process"
            name: "Invalid Email Format"
            input: {email: "invalid-email"}
            expect: "raises EmailValidationError"

  - file: "design/tests/core/test_processor.yaml"
    action: "modify"
    diff:
      test_cases:
        add:
          test_email_validation:
            description: "Verifica validación de formato de email"
            given: "Datos con email inválido 'not-an-email'"
            when: "Se llama a processor.process(data)"
            then: "Lanza EmailValidationError"

# --- SECCIÓN 3: IMPLEMENTATION PLAN (el CÓMO) ---
implementation_plan:
  steps:
    - id: 1
      action: "Crear EmailValidationError en src/core/exceptions.py"
      status: "done"  # pending | in_progress | done | blocked | skipped
      
    - id: 2
      action: "Añadir función validate_email() en processor.py"
      status: "in_progress"
      notes: "Usando regex: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
      
    - id: 3
      action: "Integrar validate_email en DataProcessor.process()"
      status: "pending"
      depends_on: [2]
      
    - id: 4
      action: "Escribir test_email_validation en test_processor.py"
      status: "pending"
      depends_on: [2, 3]
      
    - id: 5
      action: "Correr tests y verificar"
      status: "pending"
      depends_on: [4]

# --- SECCIÓN 4: HISTORY (auditoría) ---
history:
  - timestamp: "2024-01-15T10:30:00"
    event: "created"
    by: "human"
    
  - timestamp: "2024-01-15T10:32:00"
    event: "design_proposed"
    by: "ai"
    details: "Propuesta inicial de cambios en design/"
    
  - timestamp: "2024-01-15T10:35:00"
    event: "design_approved"
    by: "human"
    
  - timestamp: "2024-01-15T10:40:00"
    event: "step_completed"
    step_id: 1
    by: "ai"
```

---

## 5. Flujo de Trabajo

### Caso 0: Sincronización Inicial

> Solo se ejecuta una vez, cuando no existe `design/` o al migrar código legacy.

```
┌─────────────────────────────────────────────────────────────────┐
│  SYNC INICIAL                                                   │
│  ─────────────────────────────────────────────────────────────  │
│  1. sync_design_from_code()                                     │
│     → Escanea src/ y tests/                                     │
│     → Genera YAMLs con: meta, dependencies, signatures, metrics │
│     → Marca campos 'logic' como 'NEEDS_LOGIC'                   │
│                                                                 │
│  2. generate_logic_for_blueprint() [por cada YAML]              │
│     → IA lee el código existente                                │
│     → Genera descripción en lenguaje natural                    │
│     → Completa campo 'logic'                                    │
│                                                                 │
│  3. check_design_consistency()                                  │
│     → Verifica 1:1 entre código y blueprints                    │
│     → Reporta inconsistencias                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo Normal de Desarrollo

```
┌─────────────────────────────────────────────────────────────────┐
│  FASE 1: DISEÑO                                                 │
│  Contexto: rama ai/session-*                                    │
│  ─────────────────────────────────────────────────────────────  │
│  1. Humano describe intención en lenguaje natural               │
│  2. create_change_request()                                     │
│     → IA genera DCR con design_changes propuestos               │
│     → IA genera implementation_plan                             │
│  3. Humano revisa change_request.yaml                           │
│  4. Humano aprueba o solicita cambios                           │
│  5. IA actualiza design/*.yaml según DCR aprobado               │
│  6. Commit: "design: {título del cambio}"                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FASE 2: IMPLEMENTACIÓN                                         │
│  Contexto: misma rama ai/session-*                              │
│  ─────────────────────────────────────────────────────────────  │
│  1. execute_plan_step(1) → IA ejecuta paso 1                    │
│  2. execute_plan_step(2) → IA ejecuta paso 2                    │
│  ...                                                            │
│  N. IA corre tests                                              │
│     - Si pasan → continúa                                       │
│     - Si fallan → IA corrige código (NO diseño)                 │
│     - Si imposible → propone cambio de diseño (vuelve a Fase 1) │
│  Commit: "impl: {descripción del paso}"                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FASE 3: MERGE                                                  │
│  ─────────────────────────────────────────────────────────────  │
│  1. Todos los tests pasan                                       │
│  2. IA propone merge                                            │
│  3. Humano revisa:                                              │
│     - design/*.yaml (¿la intención es correcta?)                │
│     - .ai-context/change_request.yaml (¿los pasos razonables?)  │
│     - src/*.py (¿el código es aceptable?)                       │
│  4. Decisión:                                                   │
│     ✅ Aprueba → squash merge a main (.ai-context/ excluido)    │
│     ❌ Rechaza → feedback → vuelve a Fase 1 o 2 (misma rama)    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Funciones del Sistema

### 6.1 Sincronización (`autocode/core/design/sync.py`)

```python
@register_function(http_methods=["POST"])
def sync_design_from_code(
    src_path: str = "src/",
    design_path: str = "design/",
    overwrite_logic: bool = False
) -> GenericOutput:
    """
    Genera/actualiza blueprints YAML desde código existente.
    
    - Extrae signatures, dependencies, metrics via AST
    - Si overwrite_logic=False, preserva sección 'logic' existente
    - Marca archivos nuevos sin 'logic' como 'NEEDS_LOGIC'
    """

@register_function(http_methods=["GET"])
def check_design_consistency(
    src_path: str = "src/",
    design_path: str = "design/"
) -> GenericOutput:
    """
    Verifica consistencia entre código y diseño.
    
    - Compara signatures del código vs YAML
    - Detecta funciones/clases sin blueprint
    - Detecta blueprints huérfanos (sin código)
    - Retorna lista de inconsistencias
    """
```

### 6.2 Generación IA (`autocode/core/design/generate.py`)

```python
@register_function(http_methods=["POST"])
def generate_logic_for_blueprint(
    blueprint_path: str,
    code_path: str,
    model: ModelType = 'openrouter/openai/gpt-4o'
) -> GenericOutput:
    """
    Genera/actualiza la sección 'logic' de un blueprint.
    
    - Lee el código existente como contexto
    - Genera descripción en lenguaje natural de cada función
    - Actualiza el YAML preservando estructura
    """

@register_function(http_methods=["POST"])
def generate_code_from_blueprint(
    blueprint_path: str,
    output_path: str,
    model: ModelType = 'openrouter/openai/gpt-4o'
) -> GenericOutput:
    """
    Genera código Python desde un blueprint.
    
    - Lee signature + logic + tests del YAML
    - Genera código que cumpla la especificación
    - Escribe en output_path
    """

@register_function(http_methods=["POST"])
def generate_tests_from_blueprint(
    blueprint_path: str,
    test_blueprint_path: str,
    output_path: str,
    model: ModelType = 'openrouter/openai/gpt-4o'
) -> GenericOutput:
    """
    Genera tests desde blueprints de código y tests.
    
    - Lee test_cases del blueprint de tests
    - Genera pytest code
    """
```

### 6.3 Change Request (`autocode/core/design/change_request.py`)

```python
@register_function(http_methods=["POST"])
def create_change_request(
    title: str,
    human_input: str,
    model: ModelType = 'openrouter/openai/gpt-4o'
) -> GenericOutput:
    """
    Crea un nuevo Change Request.
    
    - IA analiza el input y propone design_changes
    - Genera implementation_plan inicial
    - Guarda en .ai-context/change_request.yaml
    """

@register_function(http_methods=["POST"])
def update_plan_step(
    step_id: int,
    status: Literal["pending", "in_progress", "done", "blocked", "skipped"],
    notes: str = ""
) -> GenericOutput:
    """
    Actualiza el estado de un paso del plan.
    
    - Modifica change_request.yaml
    - Añade entrada en history
    """

@register_function(http_methods=["POST"])
def execute_plan_step(
    step_id: int,
    model: ModelType = 'openrouter/openai/gpt-4o'
) -> GenericOutput:
    """
    Ejecuta un paso del plan automáticamente.
    
    - Lee la acción del paso
    - Genera código/tests según corresponda
    - Actualiza status a 'done' si exitoso
    """
```

---

## 7. Integración con AISessionManager

El flujo se integra con el sistema de sesiones existente (`autocode/core/workflow/session.py`):

```python
# Flujo típico

# 1. Iniciar sesión
start_ai_session(
    description="Añadir validación de email",
    session_type="session"
)
# → Crea rama ai/session-20240115-103000
# → Crea .ai-context/session.json

# 2. Crear change request
create_change_request(
    title="Validación de email en processor",
    human_input="Quiero validar emails antes de procesar..."
)
# → Crea .ai-context/change_request.yaml
# → Commit automático

# 3. Ejecutar pasos del plan
for step in plan.steps:
    execute_plan_step(step.id)
# → Modifica src/, tests/, design/
# → Commits automáticos por paso

# 4. Finalizar sesión
finalize_ai_session(
    commit_message="feat: Add email validation to processor",
    merge_to="main"
)
# → Squash merge a main (sin .ai-context/)
# → Rama ai/session-* preservada con contexto completo
```

---

## 8. Manejo de Excepciones

### Si la IA descubre que el diseño es imposible

```
┌─────────────────────────────────────────────────────────────────┐
│  DURANTE FASE 2 (Implementación)                                │
│  ─────────────────────────────────────────────────────────────  │
│  1. IA detecta problema (ej: dependencia circular)              │
│  2. IA pausa implementación                                     │
│  3. IA actualiza change_request.yaml:                           │
│     - status: "blocked"                                         │
│     - Añade entrada en history con explicación                  │
│     - Propone design_changes alternativos                       │
│  4. Humano revisa y aprueba nuevo diseño                        │
│  5. IA continúa desde donde pausó                               │
└─────────────────────────────────────────────────────────────────┘
```

### Si el humano rechaza el merge

```
┌─────────────────────────────────────────────────────────────────┐
│  DURANTE FASE 3 (Merge)                                         │
│  ─────────────────────────────────────────────────────────────  │
│  1. Humano da feedback en la misma rama                         │
│  2. Según el tipo de feedback:                                  │
│     - Problema de diseño → vuelve a Fase 1                      │
│     - Problema de implementación → vuelve a Fase 2              │
│  3. IA corrige en la misma rama ai/session-*                    │
│  4. Nuevo intento de merge                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Lo que NO incluye este MVP

Estos elementos se consideran para versiones futuras (V2+):

| Elemento | Razón de exclusión |
|----------|-------------------|
| UI web (Design Studio) | Empezar con YAML en editor |
| Sync Up automático periódico | Empezar manual |
| Grafo de dependencias entre blueprints | Complejidad adicional |
| Métricas de complejidad automáticas | Nice-to-have |
| Múltiples ramas paralelas | Una rama de trabajo es suficiente |
| Versionado semántico de blueprints | Usar git tags |
| Validación de diagramas Mermaid | V2 |

---

## 10. Checklist de Implementación

### Fase 1: Core

- [ ] Crear módulo `autocode/core/design/`
- [ ] Implementar `sync_design_from_code()` (AST parsing)
- [ ] Implementar `check_design_consistency()`
- [ ] Definir DSPy signatures para generación de logic

### Fase 2: Generación IA

- [ ] Implementar `generate_logic_for_blueprint()`
- [ ] Implementar `generate_code_from_blueprint()`
- [ ] Implementar `generate_tests_from_blueprint()`

### Fase 3: Change Requests

- [ ] Implementar `create_change_request()`
- [ ] Implementar `update_plan_step()`
- [ ] Implementar `execute_plan_step()`

### Fase 4: Integración

- [ ] Integrar con `AISessionManager`
- [ ] Añadir comandos CLI
- [ ] Documentar API endpoints

---

## Referencias

- `autocode/core/workflow/session.py` - Sistema de sesiones existente
- `autocode/core/ai/` - Módulo de generación con DSPy
- `autocode/core/vcs/` - Operaciones Git
