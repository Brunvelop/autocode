🔄 Sobre ACP vs Subprocess
Tienes razón en que el subprocess es frágil. Aquí el análisis:

Problemas fundamentales del approach de subprocess:

Problema	Descripción
Parsing NDJSON frágil	Dependemos del formato de output de cada CLI que puede cambiar entre versiones
Lifecycle management	Secuencias complejas de wait → terminate → kill, timeouts en cascada
Post-execution queries	cline history / opencode export sin timeout, pueden colgar
files_changed	Cada backend lo computa diferente (git diff vs trajectory), todos fallan
Cancelación	abort() mata el proceso pero no limpia estado git correctamente
No bidireccional	Subprocess es fire-and-forget, no podemos pedir al agent que haga cosas
ACP resolvería:

Beneficio	Cómo
Protocolo estructurado	JSON-RPC en vez de NDJSON parsing ad-hoc
Eventos tipados	Tool calls, progress, completion son tipos estándar
Sesiones	Gestión de sesiones nativa, múltiples concurrent
Cancelación limpia	El protocolo soporta cancelación de sesiones
Bidireccional	El agent puede pedir permisos, el editor puede inspeccionar estado
MCP forwarding	Las MCP tools se pasan como config, no hace falta reimplementar
Pero ACP tiene limitaciones actuales:

"Full support for remote agents is a work in progress"
Es relativamente nuevo — la API puede cambiar
Solo cline y opencode por ahora (DSPy NO soporta ACP)
🎯 Mi recomendación
Fase 1 (ahora): Arreglar los bugs críticos SIN migrar a ACP Porque los bugs son problemas de lógica/git que existirían igual con ACP:

files_changed centralizado en executor.py — NO en los backends

Después del safety net, computar files_changed con git diff --name-only {pre_exec_head} (compara contra el HEAD original, no contra el HEAD actual)
Esto funciona para TODOS los backends (cline, opencode, dspy)
Los backends ya no necesitan _git_diff_name_only
Timeouts en post-execution — _fetch_task_history y _fetch_session_export con asyncio.wait_for(timeout=5)

Cancel handler robusto — usar git reset --hard pre_exec_head en vez de git checkout -- .

revert_plan fallback — si files_changed vacío pero tiene parent_commit, usar git diff --name-only {parent_commit} para recomputar los archivos

Timeout general — en _run_backend() envolver con timeout configurable

Fase 2 (futuro): Migrar cline/opencode a ACP

Crear AcpBackend que use JSON-RPC sobre stdio
Mantener DspyReactBackend como está (DSPy no soporta ACP)
Los beneficios principales serían: parsing robusto, cancelación limpia, y eliminar las queries post-execution (cline history, opencode export)
