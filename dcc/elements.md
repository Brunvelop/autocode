# DCC: elements
> Document-Code Compression v1.0
> Infraestructura de Web Components auto-generados

---

## AXIOMAS

```
A1. LitElement como fundación
    → Todo componente hereda de LitElement (directa o indirectamente)
    → Propiedades reactivas vía `static properties`

A3. Design Tokens centralizados
    → Todos los valores visuales vienen de shared/styles/theme.js
    → NUNCA hardcodear colores, espaciado, tipografía en componentes

A4. Shadow DOM obligatorio
    → Encapsulación completa de estilos
    → Slots para composición (header, content, footer)

A4. Dos patrones de extensión
    → Con backend + UI custom: LitElement + RefractClient (composición)
    → Standalone (sin backend): LitElement directo
```

---

## CONTRATOS

```javascript
// === Contrato de RefractClient (todos los componentes con backend en autocode/web) ===
// Importado desde: import { RefractClient } from '/refract/client.js'
RefractClient:
    call(funcName, params) → Promise   // Llama función vía API
    stream(funcName, params) → EventSource  // Streaming SSE
    loadSchemas() → Promise            // Carga /functions/details

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
          ┌──────────────────────────────────┐
          │                                  │
          ▼                                  ▼
┌──────────────────┐            ┌────────────────────────┐
│ Componentes      │            │ Componentes Custom     │
│ Standalone       │            │ (UI propia + backend)  │
│ (sin backend)    │            │ _client: RefractClient │
└──────────────────┘            └────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       shared/styles/                                │
│  theme.js (themeTokens) ← Importado por TODOS los componentes       │
│  common.js (utilidades) ← Importado según necesidad                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PATRONES

### P1: UI Custom con Backend (composición con RefractClient)
```
Entrada:  Necesidad de UI específica que usa funciones del registry
Proceso:  Extender LitElement → Componer con RefractClient → Implementar UI propia
Salida:   Componente con UI custom que llama funciones del backend

Uso:      Componentes complejos en autocode/web/elements (dashboards, chat)
Patrón:   Composición con RefractClient (no herencia)

Ejemplo:
  import { RefractClient } from '/refract/client.js';
  class MiComponente extends LitElement {
      constructor() {
          super();
          this._client = new RefractClient();
      }
      async _fetchData() {
          return await this._client.call('mi_funcion', { param: value });
      }
  }
```

### P2: Standalone (sin Backend)
```
Entrada:  Componente que NO necesita funciones del registry (UI pura)
Proceso:  Extender LitElement directamente → Encapsular lógica en servicios puros
Salida:   Componente autónomo

Uso:      Utilidades de navegador, media players, visualizaciones
Herencia: MiComponente → LitElement

Ejemplo:
  class MiComponente extends LitElement {
      constructor() { super(); this._service = new MiServicio(); }
  }
```

### P3: Comunicación Inter-funciones
```
Entrada:  Componente necesita ejecutar función sin crear elemento DOM
Proceso:  Instanciar RefractClient → client.call(funcName, params)
Salida:   Resultado de la función

Uso:      Validaciones cruzadas, cálculos auxiliares
Invariante: Misma infraestructura que el patrón P2

Ejemplo:
  const client = new RefractClient();
  const result = await client.call('calculate_context_usage', { model, messages });
```

---

## INVARIANTES

```
∀ component ∈ WebElements:
    component.styles.includes(themeTokens)
    component usa variables CSS de theme.js, no valores hardcodeados
```

---

## TRANSFORMACIONES

```
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
1. CONEXIÓN (Element attached to DOM)
   connectedCallback()
   → Si tiene funcName: loadFunctionInfo()
   → _initParamsWithDefaults()
   → dispatch 'function-connected'

2. INTERACCIÓN (Usuario modifica params)
   input change → setParam(name, value)
   → this.params = {...} (inmutable para reactividad)
   → dispatch 'params-changed'
   → Lit re-render automático

3. EJECUCIÓN (Usuario click execute)
   execute()
   → validate() → errors = {}
   → dispatch 'before-execute' (cancelable)
   → callAPI(params)
   → Parse response → this.result, this.envelope, this.success
   → dispatch 'after-execute' | 'execute-error'

4. VISUALIZACIÓN (Resultado)
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
  → Usar RefractClient como composición: this._client = new RefractClient()

✗ Usar Light DOM en componentes
  → Siempre Shadow DOM para encapsulación

✗ Comunicar entre componentes con referencias directas
  → Usar CustomEvent con bubbles: true, composed: true

✗ Duplicar estilos entre componentes
  → Re-exportar desde shared/styles/

```

---

## EXTENSIÓN

```
AÑADIR COMPONENTE CON BACKEND (UI custom):
1. Crear carpeta component/
2. index.js: class extends LitElement
3. constructor: this._client = new RefractClient()  // composición, no herencia
4. Usar this._client.call('func_name', params) para llamar al backend
5. render(): html con UI propia
6. styles/: importar themeTokens + estilos propios
7. customElements.define('mi-componente', MiComponente)

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
# Tests HTML de infraestructura
autocode/web/tests/integration/function-execution.test.html
```

---

> **Regeneración**: Este DCC + Lit + API backend = autocode/web/elements (infraestructura)
> **Extracción**: inspect(autocode/web/elements/ + shared/) = Este DCC
