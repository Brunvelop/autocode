# DCC: elements
> Document-Code Compression v1.0
> Infraestructura de Web Components auto-generados

---

## AXIOMAS

```
A1. Controller-View Separation
    → La lógica de estado/API (Controller) está separada de la presentación (View)
    → AutoFunctionController NO tiene render propio, solo gestión de estado

A2. LitElement como fundación
    → Todo componente hereda de LitElement (directa o indirectamente)
    → Propiedades reactivas vía `static properties`

A3. Design Tokens centralizados
    → Todos los valores visuales vienen de shared/styles/theme.js
    → NUNCA hardcodear colores, espaciado, tipografía en componentes

A4. Shadow DOM obligatorio
    → Encapsulación completa de estilos
    → Slots para composición (header, content, footer)

A5. Tres patrones de extensión
    → Con backend + UI genérica: AutoFunctionElement
    → Con backend + UI custom: AutoFunctionController
    → Standalone (sin backend): LitElement directo
```

---

## CONTRATOS

```javascript
// === Contrato de Controller (lógica pura) ===
AutoFunctionController extends LitElement:
    // Configuración
    funcName: String           // Nombre de función en registry
    funcInfo: Object           // Metadata cargada del backend
    
    // Estado
    params: Object             // {paramName: value}
    result: Object             // Payload de respuesta
    envelope: Object           // Respuesta completa (result + success + message)
    success: Boolean           // envelope.success
    message: String            // envelope.message
    errors: Object             // {paramName: errorMessage}
    
    // UI Status
    _status: "default"|"loading"|"success"|"error"
    _isExecuting: Boolean
    
    // Métodos
    setParam(name, value)      // Actualiza param con reactividad
    getParam(name) → Any
    execute() → Promise        // Valida + callAPI + procesa resultado
    validate() → Boolean       // Valida params vs funcInfo
    callAPI(params) → Promise  // HTTP GET/POST según http_methods
    loadFunctionInfo()         // Carga metadata de /functions/details

    // Método estático
    static executeFunction(funcName, params) → Promise  // Llama función sin DOM

// === Contrato de Element (UI genérica) ===
AutoFunctionElement extends AutoFunctionController:
    render() → html            // Tarjeta con form + resultado
    renderParam(param) → html  // Input según tipo
    renderResult() → html      // Resultado formateado

// === Contrato de Generator (fábrica) ===
AutoElementGenerator:
    functions: Object          // {funcName: funcInfo}
    registeredElements: Set    // Nombres de elementos registrados
    
    init() → Promise           // Carga funciones y genera elementos
    loadFunctions() → Promise  // Fetch /functions/details
    generateAllElements()      // Itera y registra custom elements
    generateElement(name, info)// Define `auto-{funcName}`

// === Contrato de Design Tokens ===
themeTokens: css`
    :host {
        // Colores: --design-{primary|text-*|bg-*|border-*|error-*|success|warning|danger}
        // Dark mode: --dark-{bg-*|border|text-*}
        // Espaciado: --design-spacing-{xs|sm|md|lg|xl|2xl|3xl}
        // Radius: --design-radius-{sm|md|lg|xl|full}
        // Sombras: --design-shadow-{xs|sm|md|lg|xl|2xl}
        // Tipografía: --design-font-{family|mono|size-*|weight-*}
        // Transiciones: --design-transition-{fast|base|slow}
        // Z-index: --design-z-{dropdown|modal|tooltip}
    }
`

// === Contrato de Utilidades CSS ===
badgeBase: css`.badge { ... }`       // Estilos para chips/badges
ghostButton: css`.ghost-btn { ... }` // Botón transparente con hover
spinnerStyles: css`.spinner { ... }` // Animación de loading circular
```

---

## TOPOLOGÍA

```
┌─────────────────────────────────────────────────────────────────────┐
│                          LitElement (Lit)                           │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────────┐  ┌─────────────────┐
│ AutoFunction    │  │ Componentes         │  │                 │
│ Controller      │  │ Standalone          │  │ (otros)         │
│ (lógica pura)   │  │ (sin backend)       │  │                 │
└────────┬────────┘  └─────────────────────┘  └─────────────────┘
         │
         ├─────────────────────────────────────┐
         │                                     │
         ▼                                     ▼
┌─────────────────────────┐          ┌─────────────────────────┐
│ AutoFunctionElement     │          │ Componentes Custom      │
│ (UI genérica tarjeta)   │          │ (UI propia + backend)   │
└────────┬────────────────┘          └─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│ GeneratedElements       │
│ (auto-{funcName})       │
└─────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       shared/styles/                                │
│  theme.js (themeTokens) ← Importado por TODOS los componentes       │
│  common.js (utilidades) ← Importado según necesidad                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PATRONES

### P1: UI Genérica (AutoFunctionElement)
```
Entrada:  Función registrada en backend
Proceso:  AutoElementGenerator detecta → genera clase → registra custom element
Salida:   <auto-{funcName}> con form auto-generado

Uso:      Funciones simples sin necesidad de UI personalizada
Herencia: AutoFunctionElement → AutoFunctionController → LitElement
```

### P2: UI Custom con Backend (AutoFunctionController)
```
Entrada:  Necesidad de UI específica que usa registry
Proceso:  Extender Controller → Override render() → Implementar UI propia
Salida:   Componente con lógica heredada + UI custom

Uso:      Componentes complejos que consumen funciones del backend
Herencia: MiComponente → AutoFunctionController → LitElement

Ejemplo:
  class MiComponente extends AutoFunctionController {
      constructor() { super(); this.funcName = 'mi_funcion'; }
      render() { return html`<mi-ui>...</mi-ui>`; }
  }
```

### P3: Standalone (sin Backend)
```
Entrada:  Componente que NO necesita registry (UI pura)
Proceso:  Extender LitElement directamente → Encapsular lógica en servicios puros
Salida:   Componente autónomo

Uso:      Utilidades de navegador, media players, visualizaciones
Herencia: MiComponente → LitElement

Ejemplo:
  class MiComponente extends LitElement {
      constructor() { super(); this._service = new MiServicio(); }
  }
```

### P4: Comunicación Inter-funciones
```
Entrada:  Componente necesita ejecutar función sin crear elemento DOM
Proceso:  AutoFunctionController.executeFunction(funcName, params)
Salida:   Resultado de la función

Uso:      Validaciones cruzadas, cálculos auxiliares
Invariante: Misma infraestructura que execute(), sin contaminar DOM
```

---

## INVARIANTES

```
∀ component ∈ WebElements:
    component.styles.includes(themeTokens)
    component usa variables CSS de theme.js, no valores hardcodeados

∀ component extends AutoFunctionController:
    component.funcName → carga funcInfo automáticamente en connectedCallback
    component.execute() → valida params antes de llamar API
    component emite eventos: function-connected, params-changed, 
                            before-execute, after-execute, execute-error

∀ element ∈ GeneratedElements:
    customElements.get(`auto-${funcName}`) !== undefined
    element extends AutoFunctionElement
```

---

## TRANSFORMACIONES

```
                    BACKEND → FRONTEND
FunctionInfo       ──────────────────►  Custom Element
  name: "hello"                          <auto-hello>
  parameters: [...]                      form con inputs
  http_methods: ["GET"]                  fetch GET con query params

                    PARAMS → INPUTS
ParamSchema        ──────────────────►  HTML Input
  type: "string"                         <input type="text">
  type: "int"|"float"                    <input type="number">
  type: "bool"                           <input type="checkbox">
  choices: [...]                         <select>
  type: "dict"|"list"|"json"             <textarea> + JSON.parse

                    RESULT → UI
GenericOutput      ──────────────────►  Visual
  success: true                          .result-success (verde)
  success: false                         .result-error (rojo)
  result: {...}                          JSON.stringify formateado

                    DESIGN TOKENS
CSS Variable       ──────────────────►  Valor
  --design-primary                       #4f46e5
  --design-spacing-md                    0.75rem
  --dark-bg-primary                      #020617
```

---

## FLUJO DE VIDA

```
1. INICIALIZACIÓN (Page load)
   DOMContentLoaded → AutoElementGenerator.init()
   → fetch /functions/details
   → Para cada función: generateElement()
   → customElements.define(`auto-${name}`, class extends AutoFunctionElement)

2. CONEXIÓN (Element attached to DOM)
   connectedCallback()
   → Si tiene funcName: loadFunctionInfo()
   → _initParamsWithDefaults()
   → dispatch 'function-connected'

3. INTERACCIÓN (Usuario modifica params)
   input change → setParam(name, value)
   → this.params = {...} (inmutable para reactividad)
   → dispatch 'params-changed'
   → Lit re-render automático

4. EJECUCIÓN (Usuario click execute)
   execute()
   → validate() → errors = {}
   → dispatch 'before-execute' (cancelable)
   → callAPI(params)
   → Parse response → this.result, this.envelope, this.success
   → dispatch 'after-execute' | 'execute-error'

5. VISUALIZACIÓN (Resultado)
   render() detecta this.result !== null
   → renderResult() con JSON formateado
   → Clase CSS según success/error
```

---

## ANTI-PATRONES

```
✗ Hardcodear valores visuales en componente
  → Importar themeTokens, usar variables CSS

✗ Modificar this.params directamente
  → Usar setParam(name, value) para reactividad

✗ Hacer fetch directo a API desde componente custom
  → Extender AutoFunctionController, usar execute()

✗ Crear custom element manualmente para función registrada
  → AutoElementGenerator lo hace automáticamente

✗ Usar Light DOM en componentes
  → Siempre Shadow DOM para encapsulación

✗ Comunicar entre componentes con referencias directas
  → Usar CustomEvent con bubbles: true, composed: true

✗ Duplicar estilos entre componentes
  → Re-exportar desde shared/styles/

✗ Extender AutoFunctionElement para UI custom
  → Extender AutoFunctionController en su lugar
```

---

## EXTENSIÓN

```
AÑADIR COMPONENTE CON BACKEND (UI custom):
1. Crear carpeta component/
2. index.js: class extends AutoFunctionController
3. constructor: this.funcName = 'mi_funcion'
4. render(): html con UI propia
5. styles/: importar themeTokens + estilos propios
6. customElements.define('mi-componente', MiComponente)

AÑADIR COMPONENTE STANDALONE (sin backend):
1. Crear carpeta component/
2. index.js: class extends LitElement
3. Crear servicio de lógica pura (service.js)
4. styles/: importar themeTokens
5. customElements.define('mi-componente', MiComponente)

AÑADIR UTILIDAD CSS COMPARTIDA:
1. Añadir a shared/styles/common.js
2. export const miUtilidad = css`...`
3. Importar donde se necesite

AÑADIR TOKEN DE DISEÑO:
1. Editar shared/styles/theme.js
2. Añadir variable CSS en :host
3. Documentar en comentarios
```

---

## ARCHIVOS

```
autocode/web/elements/
├── auto-element-generator.js    # Controller + Element + Generator
├── ARCHITECTURE.md              # Documentación narrativa
├── shared/
│   └── styles/
│       ├── theme.js             # themeTokens (100+ variables CSS)
│       └── common.js            # Utilidades: badge, button, spinner
│
└── {component}/                 # Componentes específicos (DCC propio si aplica)
    ├── index.js                 # Punto de entrada
    ├── *.js                     # Sub-componentes (opcional)
    └── styles/
        ├── theme.js             # Re-exporta de shared/styles/
        └── *.styles.js          # Estilos del componente
```

---

## VERIFICACIÓN

```bash
# Verificar que el generador carga funciones
# (en consola del navegador con API corriendo)
console.log(window.autoElementGenerator.functions);
console.log(window.autoElementGenerator.registeredElements);

# Verificar custom element generado
const el = document.createElement('auto-hello');
document.body.appendChild(el);
console.log(el.funcInfo); // Debe mostrar metadata

# Verificar ejecución inter-funciones
const result = await AutoFunctionController.executeFunction(
    'hello_world',
    { name: 'Test' }
);
console.log(result);

# Verificar tokens de diseño
const styles = getComputedStyle(document.querySelector('auto-function-element'));
console.log(styles.getPropertyValue('--design-primary')); // #4f46e5

# Tests HTML de infraestructura
autocode/web/tests/integration/auto-element-generator.test.html
autocode/web/tests/integration/function-execution.test.html
```

---

> **Regeneración**: Este DCC + Lit + API backend = autocode/web/elements (infraestructura)
> **Extracción**: inspect(auto-element-generator.js + shared/) = Este DCC
