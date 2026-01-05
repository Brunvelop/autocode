# DCC: elements/chat
> Document-Code Compression v1.0
> Componente de chat AI con gestión de sesiones Git

---

## AXIOMAS

```
A1. Orquestador único
    → AutocodeChat (index.js) es el ÚNICO punto de entrada
    → Compone y coordina todos los sub-componentes

A2. Herencia de Controller
    → AutocodeChat extiende AutoFunctionController (no AutoFunctionElement)
    → Reutiliza lógica de estado, params y callAPI()
    → Implementa render() propio en lugar de UI genérica

A3. Separación de estilos
    → Cada componente tiene su archivo .styles.js separado
    → Los estilos NUNCA van inline en el JS
    → common.js contiene patrones reutilizables (buttonBase, inputBase, etc.)

A4. Eventos como comunicación
    → Sub-componentes emiten CustomEvents para notificar al orquestador
    → El orquestador NUNCA llama métodos directos de hijos (excepto API pública)
    → Eventos: bubbles: true, composed: true (atraviesan Shadow DOM)

A5. Design Tokens heredados
    → Todos importan themeTokens de shared/styles/theme.js
    → theme.js local solo re-exporta del shared (single source of truth)
```

---

## CONTRATOS

```javascript
// === Orquestador Principal ===
AutocodeChat extends AutoFunctionController:
    // Configuración heredada
    funcName: "chat"                    // Función del registry a consumir
    funcInfo: Object                    // Metadata cargada automáticamente
    params: Object                      // Estado de parámetros
    
    // Estado local
    conversationHistory: [Message]      // Historial de mensajes
    _chatConfig: Object                 // Config cargada de get_chat_config
    _pendingUserMessage: String?        // Mensaje optimista pendiente
    
    // Eventos escuchados
    'submit' → _handleInputSubmit()
    'settings-change' → _handleSettingsChange()
    'toggle' → _handleWindowToggle()
    'session-changed' → _handleSessionChange()
    'session-started' → _handleSessionStarted()

// === Ventana Flotante ===
ChatWindow extends LitElement:
    // Propiedades
    title: String                       // Título del header
    open: Boolean (reflect)             // Estado abierto/cerrado
    
    // Slots
    "header-actions"                    // Botones en el header
    "content"                           // Área principal (mensajes)
    "footer"                            // Input y context bar
    
    // API Pública
    toggle()                            // Alterna open
    openWindow()                        // Fuerza apertura
    close()                             // Cierra ventana
    
    // Eventos emitidos
    'toggle' { open: Boolean }
    'close'

// === Lista de Mensajes ===
ChatMessages extends LitElement:
    // Propiedades
    messages: [Message]                 // Array de mensajes
    
    // API Pública
    addMessage(role, content)           // Añade mensaje y hace scroll
    clear()                             // Limpia historial
    getMessages() → [Message]           // Copia del historial
    
    // Message Shape
    Message: { role: 'user'|'assistant'|'error', content: String|Object, timestamp: Number }

// === Input de Texto ===
ChatInput extends LitElement:
    // Propiedades
    placeholder: String
    disabled: Boolean
    
    // API Pública
    clear()                             // Limpia input
    focus()                             // Foco en input
    getValue() → String                 // Valor actual
    
    // Eventos emitidos
    'submit' { message: String }

// === Panel de Configuración ===
ChatSettings extends LitElement:
    // Propiedades
    chatConfig: Object                  // Config del backend
    _settings: Object (state)           // Settings actuales
    _funcInfo: Object (state)           // Metadata de función
    _enabledTools: Set (state)          // Tools habilitadas
    
    // API Pública
    configure(funcInfo)                 // Inicializa con metadata
    getSettings() → Object              // Obtiene settings actuales
    
    // Eventos emitidos
    'settings-change' { ...settings }

// === Info de Debug ===
ChatDebugInfo extends LitElement:
    // Propiedades
    data: Object                        // Envelope de respuesta completo
    _activeTab: String (state)          // Tab activa: overview|trajectory|history|raw
    
    // Tabs
    "overview"   → Métricas + Reasoning
    "trajectory" → Pasos de ReAct (tool calls)
    "history"    → Llamadas LM raw
    "raw"        → JSON completo

// === Barra de Contexto ===
ContextBar extends LitElement:
    // Propiedades
    current: Number                     // Tokens usados
    max: Number                         // Tokens máximos
    
    // API Pública
    update(current, max)                // Actualiza valores
    getPercentage() → Number            // % de uso
    
    // Colores automáticos
    < 70%  → verde
    70-90% → amarillo
    > 90%  → rojo

// === Gestión de Sesiones ===
SessionManager extends LitElement:
    // Propiedades
    currentSession: Object? (state)     // Sesión activa o null
    _errorMessage: String? (state)      // Error temporal
    
    // API Pública
    hasActiveSession() → Boolean
    getCurrentSession() → Object?
    saveConversation(messages) → Promise<Boolean>
    refresh() → Promise                 // Fuerza check de sesión
    
    // Eventos emitidos
    'session-changed' { session: Object? }
    'session-started' { session: Object }
    'session-ended' { session, merged_to }
    'session-aborted' { session }
```

---

## TOPOLOGÍA

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AutoFunctionController                          │
│              (auto-element-generator.js)                            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ extends
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        AutocodeChat                                 │
│                         (index.js)                                  │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ conversationHistory, _chatConfig, _pendingUserMessage         │   │
│  │ _handleInputSubmit(), _sendMessage(), _processResult()        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ compone
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
┌───────────────────┐  ┌──────────────┐  ┌─────────────────┐
│    ChatWindow     │  │ ChatSettings │  │ SessionManager  │
│  (chat-window.js) │  │              │  │                 │
│  drag + resize    │  │ dialog modal │  │ git workflow    │
└─────────┬─────────┘  └──────────────┘  └─────────────────┘
          │
          │ slots
          ├─────────────────────────────────────┐
          ▼                                     ▼
┌─────────────────────┐              ┌─────────────────────┐
│    ChatMessages     │              │ ChatInput           │
│ (chat-messages.js)  │              │ (chat-input.js)     │
│                     │              │                     │
│  ┌───────────────┐  │              │ ContextBar          │
│  │ChatDebugInfo  │  │              │ (context-bar.js)    │
│  │(dentro de msg)│  │              │                     │
│  └───────────────┘  │              │                     │
└─────────────────────┘              └─────────────────────┘


Estructura de archivos:
chat/
├── index.js              # AutocodeChat (orquestador)
├── chat-window.js        # Ventana flotante
├── chat-messages.js      # Lista de mensajes
├── chat-input.js         # Input de texto
├── chat-settings.js      # Panel de configuración
├── chat-debug-info.js    # Metadata técnica
├── context-bar.js        # Barra de uso de contexto
├── session-manager.js    # Gestión de sesiones Git
└── styles/
    ├── theme.js                    # Re-export de shared
    ├── common.js                   # Utilidades CSS compartidas
    ├── autocode-chat.styles.js
    ├── chat-window.styles.js
    ├── chat-messages.styles.js
    ├── chat-input.styles.js
    ├── chat-settings.styles.js
    ├── chat-debug-info.styles.js
    ├── context-bar.styles.js
    └── session-manager.styles.js
```

---

## PATRONES

### P1: Slot Composition
```
Entrada:  Componentes hijos que deben ir en posiciones específicas
Proceso:  ChatWindow define slots → Hijos se asignan via slot="nombre"
Salida:   Composición flexible sin acoplamiento

// En ChatWindow:
<slot name="header-actions"></slot>
<slot name="content"></slot>
<slot name="footer"></slot>

// En AutocodeChat:
<chat-window>
    <chat-settings slot="header-actions">
    <chat-messages slot="content">
    <div slot="footer">
        <chat-input>
        <context-bar>
    </div>
</chat-window>

Invariante: El contenedor NO conoce qué componentes van en cada slot
```

### P2: Event Delegation
```
Entrada:  Acción del usuario en sub-componente
Proceso:  Hijo emite CustomEvent → Burbujea → Orquestador escucha
Salida:   Orquestador ejecuta lógica coordinada

// En ChatInput:
this.dispatchEvent(new CustomEvent('submit', {
    detail: { message },
    bubbles: true,
    composed: true  // Atraviesa Shadow DOM
}));

// En AutocodeChat.firstUpdated():
this.shadowRoot.addEventListener('submit', this._handleInputSubmit.bind(this));

Invariante: Hijos NUNCA importan ni referencian al padre
            Padre NUNCA llama métodos internos de hijos
```

### P3: Optimistic UI
```
Entrada:  Usuario envía mensaje
Proceso:  
  1. Guardar mensaje pendiente
  2. Mostrar en UI inmediatamente (rol: 'user')
  3. Llamar API
  4. Al responder, añadir a historial real
Salida:   UX fluida sin espera

// En _sendMessage():
this._pendingUserMessage = message;
this._messages.addMessage('user', message);  // Optimista
await this.execute();                        // API call
this._processResult(this.envelope);          // Confirma

Invariante: Si falla, _pendingUserMessage se descarta
            El historial solo contiene mensajes confirmados
```

### P4: Controller Extension
```
Entrada:  Necesidad de UI custom con lógica de registry
Proceso:  Extender AutoFunctionController (no Element)
Salida:   Heredamos state management, NO heredamos render()

class AutocodeChat extends AutoFunctionController {
    constructor() {
        super();
        this.funcName = 'chat';  // ← Única configuración necesaria
    }
    
    render() {
        // UI completamente custom
        return html`<chat-window>...</chat-window>`;
    }
}

Invariante: execute(), setParam(), getParam(), callAPI() disponibles
            funcInfo se carga automáticamente en connectedCallback()
```

### P5: Dialog Modal Pattern
```
Entrada:  Panel de configuración complejo
Proceso:  Usar <dialog> nativo con showModal()
Salida:   Modal accesible con backdrop automático

// En ChatSettings:
<dialog class="settings-dialog" @click=${this._handleDialogClick}>
    ...
</dialog>

_openSettings() {
    this.shadowRoot.querySelector('dialog').showModal();
}

_handleDialogClick(e) {
    if (e.target.tagName === 'DIALOG') this._closeSettings(); // Click fuera
}

Invariante: dialog::backdrop para overlay
            Escape cierra automáticamente
```

---

## INVARIANTES

```
∀ component ∈ chat/*:
    component.styles.includes(themeTokens)
    component usa Shadow DOM (no Light DOM)
    component.styles separado en styles/*.styles.js

∀ event emitido por sub-componente:
    event.bubbles = true
    event.composed = true
    event.detail contiene datos necesarios

∀ mensaje en conversationHistory:
    mensaje.role ∈ {'user', 'assistant', 'error'}
    mensaje.content ∈ {String, Object}
    mensaje.timestamp = Number (Date.now())

AutocodeChat:
    this.funcName = 'chat' (hardcoded)
    this.conversationHistory sincronizado con params.conversation_history
    execute() siempre precedido de setParam('message', msg)

ChatSettings:
    _settings actualizado vía _updateSetting() (no directo)
    getSettings() incluye module_kwargs y enabled_tools si aplica
    configure(funcInfo) debe llamarse antes de usar

SessionManager:
    currentSession = null ∨ Object con {branch, description, ...}
    saveConversation() solo funciona si hasActiveSession()
    Eventos de sesión siempre incluyen session en detail
```

---

## TRANSFORMACIONES

```
                    MENSAJE → UI
Message            ──────────────────►  Bubble
  role: 'user'                          .bubble.user (azul, derecha)
  role: 'assistant'                     .bubble.assistant (blanco, izquierda)
  role: 'error'                         .bubble.error (rojo, izquierda)

                    ENVELOPE → DEBUG INFO
DspyOutput         ──────────────────►  ChatDebugInfo tabs
  result                                _extractMainText() → texto principal
  reasoning                             tab "overview" → reasoning box
  trajectory                            tab "trajectory" → lista de pasos
  history                               tab "history" → llamadas LM
  (completo)                            tab "raw" → JSON formateado

                    SETTINGS → PARAMS
ChatSettings       ──────────────────►  AutocodeChat.params
  model, temperature, max_tokens        params directos
  module_kwargs.*                       params.module_kwargs = {}
  enabled_tools                         params.enabled_tools = []

                    SESSION → UI
SessionData        ──────────────────►  SessionManager UI
  null                                  Botón "Nueva Sesión"
  {description, ...}                    Badge verde + "Finalizar" + "Cancelar"

                    CONTEXT → BAR
{current, max}     ──────────────────►  ContextBar visual
  % < 70                                Barra verde
  70 ≤ % < 90                           Barra amarilla
  % ≥ 90                                Barra roja
```

---

## FLUJO DE VIDA

```
1. INICIALIZACIÓN (Element attached)
   connectedCallback()
   → AutoFunctionController.connectedCallback()
     → loadFunctionInfo() para 'chat'
   → _loadChatConfig() → fetch get_chat_config
   
   firstUpdated()
   → Obtener referencias: _window, _messages, _input, _settings, _sessionManager
   → Setup event listeners en shadowRoot
   → SessionManager._checkCurrentSession()

2. CONFIGURACIÓN (funcInfo loaded)
   updated(changedProperties)
   → Si funcInfo cambió: _settings.configure(funcInfo)
   → Settings inicializa _settings con defaults de params

3. ENVÍO DE MENSAJE
   Usuario escribe + Enter/Click
   → ChatInput emite 'submit' { message }
   → AutocodeChat._handleInputSubmit()
   → _sendMessage(message):
       a. _pendingUserMessage = message (optimista)
       b. _messages.addMessage('user', message)
       c. setParam('message', message)
       d. Sincronizar settings actuales
       e. await this.execute() → callAPI()
       f. _processResult(envelope)
       g. Si sesión activa: sessionManager.saveConversation()
       h. _input.clear(), _updateContext()

4. PROCESAMIENTO DE RESPUESTA
   _processResult(envelope)
   → Si error: _messages.addMessage('error', envelope)
   → Si ok:
       a. _messages.addMessage('assistant', envelope)
       b. Extraer responseText de envelope
       c. Push user msg a conversationHistory (confirma optimista)
       d. Push assistant msg a conversationHistory
       e. setParam('conversation_history', _formatHistory())

5. GESTIÓN DE SESIONES
   SessionManager:
   → "Nueva Sesión" → start_ai_session() → branch ai/session-*
   → "Finalizar" → finalize_ai_session() → squash merge a main
   → "Cancelar" → abort_ai_session() → delete branch
   → Cada respuesta exitosa: saveConversation() auto-guarda

6. CICLO DE CONTEXTO
   _updateContext()
   → Construir mensajes (history + input actual)
   → executeFunction('calculate_context_usage', {model, messages})
   → _contextBar.update(current, max)
```

---

## ANTI-PATRONES

```
✗ Importar AutocodeChat desde sub-componentes
  → Los hijos NO conocen al padre, solo emiten eventos

✗ Llamar métodos internos de hijos (ej: _settings._updateSetting())
  → Usar solo API pública documentada

✗ Hardcodear estilos en el JS del componente
  → Crear archivo en styles/*.styles.js

✗ Modificar conversationHistory directamente
  → Siempre reasignar: this.conversationHistory = [...this.conversationHistory, msg]

✗ Usar Light DOM en componentes del chat
  → Siempre Shadow DOM para encapsulación

✗ Hacer fetch directo a API desde sub-componentes
  → Usar AutoFunctionController.executeFunction() o emitir evento

✗ Pasar referencias de componentes como props
  → Usar eventos y slots para comunicación

✗ Crear dialog/modal sin <dialog> nativo
  → Usar <dialog> con showModal() para accesibilidad

✗ Olvidar bubbles: true, composed: true en eventos
  → Sin esto los eventos no atraviesan Shadow DOM
```

---

## EXTENSIÓN

```
AÑADIR NUEVO SUB-COMPONENTE:
1. Crear chat/mi-componente.js
2. Crear chat/styles/mi-componente.styles.js
3. Importar themeTokens de ./styles/theme.js
4. Emitir eventos con bubbles: true, composed: true
5. Importar en index.js
6. Añadir en slot apropiado de ChatWindow

AÑADIR NUEVA CONFIGURACIÓN:
1. Backend: Añadir parámetro a función 'chat'
2. ChatSettings: Se genera automáticamente desde funcInfo
3. Si es especial: Añadir render custom en _renderControl()

AÑADIR NUEVO TAB DE DEBUG:
1. En ChatDebugInfo._renderActiveTab(): añadir case
2. Crear método _renderMiTab()
3. Añadir botón en tabs si hay datos

CAMBIAR COMPORTAMIENTO DE SESIÓN:
1. SessionManager maneja todo el workflow
2. Para nuevo tipo: Añadir a session_type en backend
3. Para nueva acción: Añadir método _handle* + API call

PERSONALIZAR ESTILOS:
1. Nunca modificar shared/styles/theme.js para un componente
2. Override en el .styles.js específico usando variables CSS
3. Añadir nuevas utilidades a styles/common.js si son reutilizables
```

---

## VERIFICACIÓN

```bash
# Tests HTML de componentes individuales
autocode/web/tests/elements/chat/*.test.html

# Tests de integración
autocode/web/tests/integration/autocode-chat.test.html

# Verificar que todos los componentes cargan
# (en consola del navegador)
customElements.get('autocode-chat')     // AutocodeChat
customElements.get('chat-window')       // ChatWindow
customElements.get('chat-messages')     // ChatMessages
customElements.get('chat-input')        // ChatInput
customElements.get('chat-settings')     // ChatSettings
customElements.get('chat-debug-info')   // ChatDebugInfo
customElements.get('context-bar')       // ContextBar
customElements.get('session-manager')   // SessionManager

# Verificar eventos (en consola)
const chat = document.querySelector('autocode-chat');
chat.shadowRoot.addEventListener('submit', e => console.log('submit:', e.detail));
chat.shadowRoot.addEventListener('settings-change', e => console.log('settings:', e.detail));

# Verificar herencia
const chat = document.querySelector('autocode-chat');
console.log(chat instanceof AutoFunctionController);  // true
console.log(chat.funcName);                           // 'chat'
console.log(chat.funcInfo);                           // {name: 'chat', parameters: [...]}
```

---

> **Regeneración**: Este DCC + Lit + AutoFunctionController + API backend = autocode/web/elements/chat
> **Extracción**: inspect(chat/*.js + chat/styles/*) = Este DCC
