# Workflow Module - AI-Assisted Development Workflows

Este módulo proporciona herramientas para gestionar workflows de desarrollo asistidos por IA, con enfoque en sesiones de trabajo aisladas mediante Git.

## 📦 Arquitectura

```
workflow/
├── __init__.py              # Exports públicos
├── session.py               # AISessionManager + funciones registradas
└── README.md               # Este archivo
```

### Separación de Responsabilidades

- **session.py**: Orquestación de sesiones y gestión de archivos.
- **git_utils.py** (en utils/): Operaciones Git reutilizables.

## 🎯 Características

### 1. AISessionManager

Clase principal que orquesta todo el workflow de sesiones:

```python
from autocode.core.workflow import AISessionManager

manager = AISessionManager()

# Iniciar sesión (crea rama ai/session-TIMESTAMP)
result = manager.start_session(
    description="Add JWT authentication",
    base_branch="main",
    session_type="session"
)

# Guardar conversación (commit en rama actual)
manager.save_conversation_to_session(messages=[...])

# Finalizar sesión (squash merge a main)
manager.finalize_session(
    commit_message="feat: Add JWT authentication",
    merge_to="main",
    keep_branch=True
)
```

## 🔧 API Registrada

Las siguientes funciones están registradas y disponibles via API/CLI/MCP:

### `start_ai_session()`
Inicia una nueva sesión AI con branch aislada.

**Parámetros:**
- `description` (str): Descripción de la sesión
- `base_branch` (str): Branch base (default: "main")
- `session_type` (Literal): Tipo de sesión ("session", "docs", "tests", "review")

### `save_conversation()`
Guarda conversación en la sesión actual.

**Parámetros:**
- `messages` (List[Dict]): Lista de mensajes

### `finalize_ai_session()`
Finaliza sesión con merge selectivo (código → main, contexto → branch).

**Parámetros:**
- `commit_message` (str): Mensaje para el commit en main
- `merge_to` (str): Branch destino (default: "main")
- `keep_branch` (bool): Mantener branch después (default: True)

### `get_current_session()`
Obtiene metadata de la sesión actual leyendo `.ai-context/session.json`.

### `list_ai_sessions()`
Lista todas las sesiones activas escaneando las ramas `ai/*`.

## 🔄 Flujo Típico de Trabajo

1. **Start**: Crea rama `ai/feature-x`, crea `.ai-context/session.json`, commit.
2. **Chat**: Escribe en `.ai-context/conversation.json`, commit automático.
3. **Finalize**: Checkout main, merge squash (trae cambios de código), reset de `.ai-context/`, commit solo código. La rama de sesión se queda ahí preservando el contexto.

## 🏗️ Integración con Git

### Estructura de Archivos

Durante una sesión activa:
```
.ai-context/
├── session.json          # Metadata de la sesión
└── conversation.json     # Historial de chat
```

No se usa `index.json` global; la verdad está en las ramas de git.

### Merge Selectivo

El módulo implementa un merge selectivo para separar código de contexto:

1. **Squash merge** de la sesión a main
2. **Reset** de `.ai-context/` del staging
3. **Commit** solo código en main
4. `.ai-context/` permanece en la branch de sesión

Esto mantiene:
- ✅ Código limpio en main
- ✅ Contexto completo en branch de sesión
