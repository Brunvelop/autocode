# DCC: elements/code-explorer
> Document-Code Compression v1.0
> Componente de exploración visual de código multi-lenguaje

---

## AXIOMAS

```
A1. Introspección automática
    → La estructura del código se extrae automáticamente via AST
    → 0 configuración manual, vale para cualquier proyecto Python/JS
    → Sigue la filosofía de auto-element-generator: todo automático

A2. Estructura normalizada
    → Python y JavaScript se normalizan al mismo modelo CodeNode
    → El frontend NO conoce las diferencias entre lenguajes
    → El backend abstrae los parsers específicos

A3. Jerarquía natural
    → El código se representa como árbol: directorio → archivo → clase → función
    → Cada nodo tiene métricas y puede expandirse/colapsarse
    → Lazy loading para performance en proyectos grandes

A4. Standalone con backend
    → CodeExplorer extiende LitElement (no AutoFunctionController)
    → Usa AutoFunctionController.executeFunction() para llamar al backend
    → No está atado a una función específica del registry
```

---

## CONTRATOS

```python
# === Backend: Estructura de código normalizada ===
CodeNode:
    id: str                    # Path único (ej: "autocode/core/ai/pipelines.py::chat")
    name: str                  # Nombre display (ej: "chat", "pipelines.py", "ai/")
    type: NodeType             # directory | file | class | function | method | import
    language: str?             # "python" | "javascript" | null (para directorios)
    path: str                  # Path relativo al root
    line_start: int?           # Línea inicio (solo para código interno)
    line_end: int?             # Línea fin (solo para código interno)
    loc: int                   # Lines of code
    children: [CodeNode]?      # Hijos (lazy: puede ser null hasta expandir)
    
    # Metadata adicional según tipo
    decorators: [str]?         # Para funciones/clases Python
    params: [str]?             # Para funciones
    bases: [str]?              # Para clases (herencia)
    exports: bool?             # Para JS: export default, export

# === Backend: Output de la función registrada ===
CodeStructureOutput(GenericOutput):
    result: CodeStructureResult
    
CodeStructureResult:
    root: CodeNode             # Nodo raíz del árbol
    languages: [str]           # Lenguajes detectados
    total_files: int           # Conteo de archivos
    total_loc: int             # LOC total
    total_functions: int       # Conteo de funciones
    total_classes: int         # Conteo de clases

# === Frontend: Contratos del componente ===
CodeExplorer extends LitElement:
    // Propiedades públicas
    path: String               // Path raíz a explorar (default: ".")
    depth: Number              // Profundidad inicial (-1 = todo)
    
    // Estado interno
    _structure: Object         // CodeStructureResult del backend
    _expandedNodes: Set        // IDs de nodos expandidos
    _selectedNode: String?     // ID del nodo seleccionado
    _loading: Boolean          // Estado de carga
    _error: String?            // Mensaje de error
    
    // Métodos públicos
    refresh()                  // Recarga estructura desde backend
    expandNode(id)             // Expande un nodo
    collapseNode(id)           // Colapsa un nodo
    selectNode(id)             // Selecciona un nodo
    expandAll()                // Expande todos
    collapseAll()              // Colapsa todos
    
    // Eventos emitidos
    'node-selected' { node: CodeNode }
    'node-expanded' { node: CodeNode }
    'node-collapsed' { node: CodeNode }
    'structure-loaded' { structure: CodeStructureResult }

# === NodeType enum ===
NodeType: "directory" | "file" | "class" | "function" | "method" | "import" | "variable"
```

---

## TOPOLOGÍA

```
┌─────────────────────────────────────────────────────────────────────┐
│                          BACKEND (Python)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   autocode/core/code/                                               │
│   ├── __init__.py                                                   │
│   ├── models.py              # CodeNode, CodeStructureOutput        │
│   ├── structure.py           # get_code_structure() registrada      │
│   └── parsers/                                                      │
│       ├── __init__.py                                               │
│       ├── base.py            # Parser ABC                           │
│       ├── python_parser.py   # Usa ast module                       │
│       └── js_parser.py       # Usa regex/simple parse               │
│                                                                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ GET /get_code_structure?path=X
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Lit)                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   autocode/web/elements/code-explorer/                              │
│   ├── index.js               # CodeExplorer (componente principal)  │
│   ├── code-tree.js           # Sub-componente: árbol visual         │
│   ├── code-node.js           # Sub-componente: nodo individual      │
│   ├── code-metrics.js        # Sub-componente: resumen métricas     │
│   └── styles/                                                       │
│       ├── theme.js           # Re-export de shared/styles/          │
│       ├── code-explorer.styles.js                                   │
│       ├── code-tree.styles.js                                       │
│       ├── code-node.styles.js                                       │
│       └── code-metrics.styles.js                                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Dependencias frontend:
  shared/styles/theme.js ← code-explorer/styles/theme.js ← todos los .styles.js
  auto-element-generator.js::executeFunction ← code-explorer/index.js

Comunicación:
  CodeExplorer → AutoFunctionController.executeFunction('get_code_structure', {path})
             → Backend parsea código
             → Devuelve CodeStructureResult normalizado
```

---

## PATRONES

### P1: Parser Strategy
```
Entrada:  Archivo con extensión conocida (.py, .js)
Proceso:  Seleccionar parser apropiado según extensión
          Parser extrae AST → normaliza a CodeNode
Salida:   CodeNode con estructura interna del archivo

// Backend
PARSERS = {
    '.py': PythonParser,
    '.js': JavaScriptParser,
}

def parse_file(path: str) -> CodeNode:
    ext = Path(path).suffix
    parser = PARSERS.get(ext)
    if parser:
        return parser().parse(path)
    return CodeNode(type='file', children=[])  # Archivo sin parsear

Invariante: Parser desconocido → archivo sin hijos (no error)
            Cada parser normaliza a CodeNode idéntico
```

### P2: Lazy Tree Loading
```
Entrada:  Usuario expande nodo de directorio
Proceso:  Si children es null → fetch hijos del backend
          Si children existe → solo toggle UI
Salida:   Nodo con hijos cargados

// Frontend
async expandNode(nodeId) {
    const node = this._findNode(nodeId);
    if (node.children === null) {
        // Lazy load
        const children = await this._loadChildren(node.path);
        node.children = children;
    }
    this._expandedNodes.add(nodeId);
}

Invariante: Primera expansión → fetch
            Expansiones siguientes → solo UI
            Memoria controlada en proyectos grandes
```

### P3: Icon Mapping
```
Entrada:  CodeNode.type + CodeNode.language
Proceso:  Mapear a icono/emoji apropiado
Salida:   Visual distintivo por tipo

ICONS = {
    directory: '📁',
    file: { python: '🐍', javascript: '🟨', default: '📄' },
    class: '🔷',
    function: '⚡',
    method: '🔹',
    import: '📥',
}

Invariante: Todo tipo tiene icono
            Lenguaje modifica icono de archivo
```

### P4: Metrics Aggregation
```
Entrada:  Árbol de CodeNodes
Proceso:  Sumar LOC/counts recursivamente hacia arriba
Salida:   Cada nodo padre tiene métricas agregadas

// Backend calcula en construcción
def build_node(path) -> CodeNode:
    node = parse(path)
    if node.children:
        node.loc = sum(child.loc for child in node.children)
    return node

Invariante: node.loc = sum(children.loc) para directorios
            Hoja (función) tiene LOC propio
```

### P5: Event-Driven Selection
```
Entrada:  Click en nodo del árbol
Proceso:  Emitir 'node-selected' con datos del nodo
          Consumidor decide qué hacer (panel detalle, highlight, etc.)
Salida:   Componente padre informado de selección

// En code-node.js
_handleClick() {
    this.dispatchEvent(new CustomEvent('node-selected', {
        detail: { node: this.node },
        bubbles: true,
        composed: true
    }));
}

Invariante: CodeExplorer NO decide qué pasa al seleccionar
            Solo emite evento, consumidor decide
```

---

## INVARIANTES

```
∀ node ∈ CodeNode:
    node.id es único en todo el árbol
    node.id = path::name para código interno
    node.id = path para archivos/directorios
    node.type ∈ {directory, file, class, function, method, import, variable}

∀ archivo parseado:
    archivo.language ∈ {python, javascript}
    archivo.children contiene imports + clases + funciones (nivel top)
    archivo.loc >= sum(children.loc)  // puede haber código suelto

∀ directorio:
    directorio.language = null
    directorio.children = archivos + subdirectorios
    directorio.loc = sum(children.loc)

∀ componente frontend:
    componente.styles incluye themeTokens
    componente usa Shadow DOM
    eventos tienen bubbles: true, composed: true

CodeExplorer:
    this.path default = "."
    refresh() siempre recarga desde backend
    _expandedNodes persiste entre re-renders
```

---

## TRANSFORMACIONES

```
                    PYTHON AST → CodeNode
ast.Module         ──────────────────►  CodeNode(type='file')
ast.ClassDef       ──────────────────►  CodeNode(type='class', bases=[...])
ast.FunctionDef    ──────────────────►  CodeNode(type='function', params=[...])
ast.AsyncFunctionDef ────────────────►  CodeNode(type='function', async=true)
ast.Import         ──────────────────►  CodeNode(type='import', name=module)

                    JS (simple) → CodeNode
class X {}         ──────────────────►  CodeNode(type='class')
function f() {}    ──────────────────►  CodeNode(type='function')
const f = () => {} ──────────────────►  CodeNode(type='function')
import X from Y    ──────────────────►  CodeNode(type='import')
export             ──────────────────►  CodeNode.exports = true

                    CodeNode → UI
type: directory    ──────────────────►  📁 + expandible + LOC badge
type: file         ──────────────────►  🐍/🟨 + expandible + LOC badge
type: class        ──────────────────►  🔷 + expandible (métodos)
type: function     ──────────────────►  ⚡ + params inline
type: import       ──────────────────►  📥 + nombre módulo

                    Métricas → Badges
loc > 500          ──────────────────►  Badge rojo (archivo grande)
loc > 100          ──────────────────►  Badge amarillo
loc <= 100         ──────────────────►  Badge verde/gris
```

---

## FLUJO DE VIDA

```
1. INICIALIZACIÓN (Element attached)
   connectedCallback()
   → this.path default a "."
   → this._expandedNodes = new Set()
   → this.refresh()  // Carga inicial

2. CARGA DE ESTRUCTURA
   refresh()
   → this._loading = true
   → AutoFunctionController.executeFunction('get_code_structure', {path, depth})
   → this._structure = response
   → this._loading = false
   → dispatch 'structure-loaded'

3. RENDERIZADO DEL ÁRBOL
   render()
   → Si _loading: mostrar spinner
   → Si _error: mostrar mensaje error
   → Si _structure: renderizar <code-tree>

4. INTERACCIÓN CON NODOS
   Click en nodo:
   → Si es expandible: toggle _expandedNodes
   → dispatch 'node-selected'
   
   Doble click (futuro):
   → Abrir archivo en editor

5. ACTUALIZACIÓN
   Usuario cambia this.path
   → updated() detecta cambio
   → this.refresh()
```

---

## ANTI-PATRONES

```
✗ Parsear código en el frontend
  → Todo el parsing en backend Python (ast es robusto)

✗ Cargar árbol completo en proyectos grandes
  → Usar lazy loading con depth inicial limitado

✗ Hardcodear colores de badges/iconos
  → Usar variables CSS de themeTokens

✗ Guardar estado de expansión en el backend
  → Estado de UI (_expandedNodes) es solo frontend

✗ Crear parser específico por cada sintaxis JS (ESM, CJS, TS)
  → Parser JS simple con regex, no intenta ser completo

✗ Fallar si hay archivo con sintaxis inválida
  → Capturar excepciones, devolver nodo vacío con warning

✗ Importar el componente chat o auto-element-generator completo
  → Solo importar executeFunction estático si se necesita

✗ Usar Light DOM
  → Siempre Shadow DOM para encapsulación de estilos
```

---

## EXTENSIÓN

```
AÑADIR NUEVO LENGUAJE:
1. Crear autocode/core/code/parsers/{lang}_parser.py
2. Implementar parse(path) → CodeNode
3. Registrar extensión en PARSERS dict
4. (Frontend) Añadir icono en ICONS map

AÑADIR NUEVA MÉTRICA:
1. Añadir campo a CodeNode (ej: complexity: int)
2. Calcular en parser
3. (Frontend) Mostrar en badge/tooltip

AÑADIR VISTA DE DETALLE:
1. Crear code-detail.js sub-componente
2. Escuchar 'node-selected' en CodeExplorer
3. Mostrar info expandida del nodo seleccionado

AÑADIR BÚSQUEDA:
1. Crear code-search.js sub-componente
2. Filtrar _structure.root recursivamente
3. Highlight matches en el árbol

AÑADIR DIAGRAMA DE CLASES (futuro):
1. Crear code-diagram.js
2. Extraer relaciones de herencia de CodeNodes
3. Renderizar con SVG/Canvas
```

---

## ARCHIVOS

```
# Backend
autocode/core/code/
├── __init__.py
├── models.py                  # CodeNode, CodeStructureOutput
├── structure.py               # get_code_structure() registrada
└── parsers/
    ├── __init__.py            # PARSERS registry
    ├── base.py                # BaseParser ABC
    ├── python_parser.py       # PythonParser (usa ast)
    └── js_parser.py           # JSParser (regex simple)

# Frontend
autocode/web/elements/code-explorer/
├── index.js                   # CodeExplorer (orquestador)
├── code-tree.js               # Árbol interactivo
├── code-node.js               # Nodo individual
├── code-metrics.js            # Resumen de métricas
└── styles/
    ├── theme.js               # Re-export de shared
    ├── code-explorer.styles.js
    ├── code-tree.styles.js
    ├── code-node.styles.js
    └── code-metrics.styles.js

# Tests
autocode/web/tests/elements/code-explorer/
└── code-explorer.test.html
```

---

## VERIFICACIÓN

```bash
# Backend: Verificar que get_code_structure funciona
python -c "
from autocode.core.code.structure import get_code_structure
result = get_code_structure('autocode/core')
print(f'Files: {result.result.total_files}')
print(f'LOC: {result.result.total_loc}')
print(f'Languages: {result.result.languages}')
"

# Backend: Verificar parsers
python -c "
from autocode.core.code.parsers import PythonParser, JSParser
py_node = PythonParser().parse('autocode/core/ai/pipelines.py')
print(f'Python: {len(py_node.children)} top-level items')
"

# Frontend: Verificar en consola del navegador
const explorer = document.querySelector('code-explorer');
console.log(explorer._structure);        // Debe mostrar CodeStructureResult
console.log(explorer._expandedNodes);    // Set de IDs expandidos
explorer.refresh();                      // Debe recargar

# Test HTML
autocode/web/tests/elements/code-explorer/code-explorer.test.html
```

---

> **Regeneración**: Este DCC + Python ast + Lit + API backend = autocode/web/elements/code-explorer
> **Extracción**: inspect(code-explorer/*.js + core/code/*) = Este DCC
