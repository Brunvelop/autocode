# TODO: Treemap UX — Auto-refresh & Navegación entre Commits

## Contexto

El treemap del `code-dashboard` actualmente:
- Solo carga datos en `connectedCallback()` (requiere refresh manual tras nuevos commits)
- Muestra únicamente el snapshot del estado actual del proyecto
- No tiene forma de navegar entre commits ni comparar dos estados

---

## Problema 1: Refresh manual tras nuevo commit (Bad UX)

Tras un `git commit`, el usuario tiene que recargar la página entera, perdiendo el estado
de zoom, tab activo y navegación.

### Todos:

- [ ] **Auto-detect new commits** — Implementar polling periódico (ej. cada 30s) que compare
  el `commit_short` del snapshot actual con el del servidor; si cambia, disparar re-fetch
  automático o mostrar notificación

- [ ] **Preserve zoom/navigation state on refresh** — En `CodeDashboard.refresh()`, guardar
  `_currentNodeId` y `_viewMode` antes de actualizar; tras reconstruir el árbol, restaurar el
  zoom al mismo nodo (o al padre más cercano si el nodo desapareció)

- [ ] **Smooth data transition en treemap** — Evitar el flash visual de `_rebuildTreemap()`
  completo; usar `d3.join().transition()` para animar el morph del treemap existente al nuevo
  cuando cambian los datos (sin destruir y recrear el SVG)

- [ ] **Visual indicator "New data available"** — Mostrar un toast/badge en `_renderSnapshotInfo`
  cuando se detecta un commit nuevo, con botón "Actualizar" y opción de auto-update configurable

---

## Problema 2: Navegación entre commits (evolución temporal)

No existe forma de ver cómo era el proyecto en commits anteriores.

### Investigación / Backend:

- [ ] **Investigar modelo de datos de snapshots** — Revisar `get_architecture_snapshot` en
  `pipelines.py` y `architecture.py`: ¿acepta un `commit_hash` opcional? Si no, diseñar la
  extensión para calcular el snapshot a un commit histórico (via `git checkout` temporal o
  `git show` para leer archivos sin cambiar working tree)

- [ ] **Endpoint: listar commits disponibles** — Reutilizar `vcs/log.py` para exponer un
  endpoint que retorne la lista de commits recientes (hash, mensaje corto, autor, fecha,
  archivos modificados) que el frontend puede mostrar como opciones

- [ ] **Endpoint: snapshot histórico** — Extender `get_architecture_snapshot(commit='abc123')`
  para calcular métricas del proyecto en ese punto del historial y retornar el mismo formato
  que el snapshot actual

### Frontend — Commit selector:

- [ ] **Timeline/selector de commits** — Añadir un componente (dropdown o timeline horizontal)
  en el header del dashboard que muestre los últimos N commits y permita seleccionar uno

- [ ] **Cargar treemap de commit histórico** — Al seleccionar un commit en el timeline, llamar
  al backend con ese `commit_hash` y reemplazar el árbol del treemap con esos datos históricos

- [ ] **Indicador "estás viendo un snapshot histórico"** — Badge/banner visible cuando el
  usuario NO está viendo el estado actual, con texto tipo "📸 Viendo commit abc123 (hace 2 días)"
  y botón "Volver al actual"

---

## Problema 3: Visualización de delta entre commits

Ver la evolución no es solo ver un snapshot pasado, sino ver QUÉ cambió y en QUÉ DIRECCIÓN.

### Backend:

- [ ] **Endpoint: diff de snapshots** — Endpoint que reciba dos commit hashes y retorne
  la lista de archivos con sus métricas en ambos commits: delta de MI, CC, SLOC, y categoría
  (added / removed / modified / unchanged)

### Frontend — Delta view:

- [ ] **Modo "Delta view" en treemap** — Toggle que coloree los nodos por delta en vez de
  por métrica absoluta:
  - 🟢 Verde = MI mejoró / CC bajó
  - 🔴 Rojo = MI empeoró / CC subió
  - 🔵 Azul = archivo nuevo
  - ⚫ Gris = sin cambios significativos

- [ ] **Badges de cambio en nodos** — En las celdas del treemap con suficiente espacio,
  mostrar el delta: `MI: 45→62 ↑`, `+38 SLOC`, `CC: 12→4 ↓`

- [ ] **Panel "Changes"** — Tab o panel lateral que liste los archivos que cambiaron entre
  los dos commits seleccionados, ordenados por magnitud de cambio (impacto en MI o CC)

- [ ] **Side-by-side comparison** — Modo split-view con dos instancias de `treemap-view`
  lado a lado (commit A vs commit B) sincronizadas en zoom/navegación via `zoomNodeId`

---

## Archivos relevantes

| Archivo | Relevancia |
|---------|-----------|
| `autocode/web/elements/code-dashboard/index.js` | Dashboard principal, `refresh()`, tree building |
| `autocode/web/elements/code-dashboard/treemap-view.js` | Visualización D3, `_rebuildTreemap()` |
| `autocode/core/code/architecture.py` | Genera snapshots, punto de entrada para histórico |
| `autocode/core/vcs/log.py` | Listado de commits del repo |
| `autocode/interfaces/api.py` | Endpoints REST que alimentan el frontend |

## Prioridad sugerida

1. 🔴 **Auto-refresh con preserve de estado** (Problema 1) — UX inmediata, bajo riesgo
2. 🟡 **Commit selector + snapshot histórico** (Problema 2) — Requiere extensión backend
3. 🟢 **Delta view** (Problema 3) — Feature diferencial, construye sobre el commit selector
