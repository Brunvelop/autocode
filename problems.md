
## Lista de problemas del sistema de ejecución de planes

---

### ✅ P1: Frontend se queda en "Ejecutando..." tras completar (Cline) — RESUELTO

**Síntoma**: El backend Cline emite todos los steps (incluido `completion`), pero el stream SSE nunca cierra. La UI muestra "Ejecutando..." indefinidamente con heartbeats activos.

**Causa raíz**: `cline history` es un **TUI interactivo** (muestra `Use ↑↓/j/k to navigate, Enter to select`). No soporta `--json` ni produce salida parseable. Al llamarlo programáticamente sin TTY, `proc.communicate()` cuelga indefinidamente esperando input → `backend.execute()` nunca retorna → `plan_complete` nunca se emite → el stream SSE queda abierto para siempre.

**Fix aplicado**: Eliminados `_fetch_task_history()` (Cline) y `_fetch_session_export()` (OpenCode). Los tokens/cost se acumulan directamente durante el stream desde eventos `api_req_finished` (Cline) y `step_finish` (OpenCode), que ya contenían toda la información necesaria. Los métodos post-ejecución eran redundantes (YAGNI) además de peligrosos.

---

### ✅ P2: Cancelar ejecución no revierte los cambios — RESUELTO

**Síntoma**: Al pulsar "Cancelar", aparece el error pero los archivos siguen modificados en disco.

**Causa 1**: `_revert_changes()` solo hace `git checkout -- .`, que solo revierte cambios unstaged. No deshace commits ni cambios staged del agent.

**Causa 2**: `pre_exec_head` está disponible en el scope pero el handler de cancelación no lo usa. Debería hacer `git reset --hard pre_exec_head`.

**Causa 3**: Si la cancelación ocurre DESPUÉS del loop `_with_heartbeat` (durante review o plan_complete), el `except (CancelledError, GeneratorExit)` ya no aplica — el revert nunca se ejecuta.

**Alcance**: Todos los backends.

**Fix aplicado**: `ExecutionSandbox.revert()` hace `git reset --hard pre_exec_head`. El executor llama `await sandbox.revert()` en el handler de cancelación. Los helpers ad-hoc `_revert_changes()`, `_git_rev_parse_head()`, `_git_reset_mixed()` fueron eliminados de `executor.py`.

---

### ✅ P3: `files_changed` vacío en review humana (DSPy) — RESUELTO

**Síntoma**: DSPy ejecuta correctamente (steps muestran `replace_in_file` ejecutado 3 veces), pero `files_changed: []`. La UI de review no muestra archivos, no permite aprobar ni revertir.

**Causa**: DSPy NO usa `git diff`. Depende 100% de `extract_files_changed(trajectory)` que parsea el dict buscando `Action_N` / `Action_N_args` keys. El formato de trajectory de DSPy no coincide (o cambió entre versiones) → parsing silenciosamente retorna `[]`.

**Alcance**: DSPy.

**Fix aplicado**: `files_changed` se computa en `executor.py` post-ejecución vía `ExecutionSandbox.collect_changes()` (git diff real). Los backends retornan `files_changed=[]` y el executor sobreescribe ese valor.

---

### ✅ P4: `files_changed` vacío en review humana (OpenCode/Cline) — RESUELTO

**Síntoma**: OpenCode y Cline ejecutan correctamente, pero `files_changed: []` en review humana. No se puede aprobar ni revertir.

**Causa**: Ambos backends computan `files_changed` con `git diff --name-only HEAD` DENTRO de `backend.execute()`, ANTES del safety net en `executor.py`. Si el agent hizo commit (HEAD avanzó), `git diff HEAD` = vacío. El safety net (`git reset --mixed pre_exec_head`) ocurre después, pero `files_changed` ya se grabó como `[]`.

**Alcance**: OpenCode, Cline.

**Fix aplicado**: `_git_diff_name_only()` eliminado de Cline y OpenCode. Los backends retornan `files_changed=[]`. `ExecutionSandbox.collect_changes()` en el executor aplica `reset --mixed` si HEAD avanzó y luego diff contra `pre_exec_head`, garantizando la detección correcta en todos los casos.

---

### ✅ P5: `revert_plan` falla cuando `files_changed` vacío — RESUELTO

**Síntoma**: Al pulsar "Revertir cambios" en review, error: "Plan has no files to revert (files_changed is empty)".

**Causa**: `workflow.revert_plan()` depende de `plan.execution.files_changed` para saber qué archivos revertir. Si P3 o P4 causaron `files_changed = []`, no hay nada que revertir. No hay fallback usando `parent_commit` para recomputar los archivos.

**Alcance**: Todos los backends (consecuencia de P3/P4).

**Fix aplicado**: `workflow.revert_plan()` ahora tiene fallback: si `files_changed` está vacío pero existe `parent_commit`, recomputa la lista vía `git diff --name-only parent_commit`. Error solo si ambos están vacíos.

---

### ✅ P6: Cada backend reimplementa detección de archivos y helpers git — RESUELTO

**Síntoma**: Código duplicado, cada backend tiene su propia `_git_diff_name_only` async. `executor.py` tiene `_revert_changes`, `_git_rev_parse_head`, `_git_reset_mixed` ad-hoc. Mientras `vcs/git.py` tiene helpers centralizados que nadie usa aquí.

**Causa**: Los backends se desarrollaron independientemente. No hay una capa unificada post-ejecución que maneje git state.

**Consecuencia**: La lógica de `files_changed` se computa diferente en cada backend (DSPy: trajectory parsing, OpenCode/Cline: `git diff HEAD`), todos con bugs diferentes. Debería ser UNA sola implementación en `executor.py`, post-safety-net, usando `git diff --name-only {pre_exec_head}`.

**Fix aplicado**: `autocode/core/vcs/execution.py` centraliza todas las primitivas async (`async_rev_parse_head`, `async_diff_name_only`, `async_reset_mixed`, `async_reset_hard`) y la clase `ExecutionSandbox`. Los backends ya no contienen lógica git propia. Exportado desde `autocode/core/vcs/__init__.py`.

---

### 🐛 P7: Fragilidad general del approach subprocess

**Síntoma**: Múltiples problemas de lifecycle (hangs, parsing, cancelación) que son inherentes a controlar agents via subprocess + NDJSON.

**Problemas concretos**:
- Parsing NDJSON depende del formato de output de cada CLI (puede cambiar entre versiones)
- Secuencias complejas de wait → terminate → kill con timeouts en cascada
- Queries post-ejecución (`cline history`, `opencode export`) frágiles
- Cancelación mata el proceso pero no limpia estado
- No bidireccional (no podemos pedir al agent info o señalar intención)

**Alternativa**: Tanto Cline como OpenCode soportan ACP (Agent Client Protocol) — JSON-RPC sobre stdio con tipos estándar, sesiones, cancelación limpia y MCP forwarding nativo.

---

### 🐛 P8: Tokens y coste no se calculan correctamente con Cline (Kleene)

**Síntoma**: Al ejecutar un plan con el backend Cline (Kleene), los tokens consumidos y el coste asociado se muestran incorrectos o como cero. Con OpenCode el cálculo sí parece funcionar correctamente.

**Causa (hipótesis)**: El mecanismo de acumulación de tokens en el backend de Cline depende de parsear eventos `api_req_finished` del stream NDJSON. Es posible que:
- El formato del evento haya cambiado entre versiones de Kleene y los campos de tokens/coste no se extraigan correctamente.
- Los campos del evento (`tokensIn`, `tokensOut`, `cost` u otros) tengan nombres distintos a los esperados.
- Algunos eventos `api_req_finished` lleguen malformados o incompletos y se descarten silenciosamente.
- El acumulador se inicialice o resetee en un momento incorrecto del ciclo de vida del plan.

OpenCode usa un mecanismo diferente (eventos `step_finish`) que sí funciona, lo que sugiere que el problema es específico del parsing de eventos de Cline.

**Alcance**: Cline (Kleene).

---

### Resumen

| # | Problema | Backends afectados | Categoría |
|---|---------|-------------------|-----------|
| ~~P1~~ | ~~Stream SSE nunca cierra (post-execution hang)~~ | ~~Cline, OpenCode~~ | ✅ Resuelto |
| ~~P2~~ | ~~Cancel no revierte cambios~~ | ~~Todos~~ | ✅ Resuelto |
| ~~P3~~ | ~~`files_changed = []` (trajectory parsing)~~ | ~~DSPy~~ | ✅ Resuelto |
| ~~P4~~ | ~~`files_changed = []` (git diff timing)~~ | ~~OpenCode, Cline~~ | ✅ Resuelto |
| ~~P5~~ | ~~`revert_plan` falla sin files~~ | ~~Todos (consecuencia)~~ | ✅ Resuelto |
| ~~P6~~ | ~~Duplicación de git helpers~~ | ~~Todos~~ | ✅ Resuelto |
| P7 | Fragilidad subprocess general | OpenCode, Cline | Arquitectura / ACP |
| P8 | Tokens/coste incorrectos | Cline (Kleene) | Token accounting |

**Solución unificada para P3+P4+P5+P6**: Mover `files_changed` detection a `executor.py`, post-safety-net, con `git diff --name-only {pre_exec_head}`. Si el agent committeó, primero `git reset --mixed pre_exec_head` (ya existe), luego diff. Una sola implementación para todos los backends.

¿Falta algún problema que hayas observado? ¿Quieres que documente esto en un archivo `todo/` del proyecto?
