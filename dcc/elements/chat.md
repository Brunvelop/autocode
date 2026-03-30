# DCC: elements/chat
> Document-Code Compression v1.0
> Componente de chat AI

---

## AXIOMAS

```
A1. Orquestador único
    → AutocodeChat (index.js) es el ÚNICO punto de entrada
    → Compone y coordina todos los sub-componentes

A2. Composición con RefractClient
    → AutocodeChat extiende LitElement directamente
    → Usa this._client = new RefractClient() para toda comunicación con el backend
    → Gestiona su propio estado de params, result y status

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
AutocodeChat extends LitElement:
    // Cliente HTTP (composición)
    _client: RefractClient              // Instancia en constructor
    
    // Estado
    funcInfo: Object                    // Schema de la función 'chat' del registry
    params: Object                      // {message, conversation_history, model, ...}
    result: Object                      // Resultado de la última llamada
    envelope: Object                    // Mismo que result (nomenclatura legacy)
    success: Boolean                    // true/false tras ejecución
    _status: String                     // 'default'|'loading'|'success'|'error'
    _statusMessage: String              // Mensaje de estado actual
    _isExecuting: Boolean               // true durante llamada activa
    
    // Estado del chat
    conversationHistory: [Message]      // Historial de mensajes
    _chatConfig: Object                 // Config cargada de get_chat_config
    _pendingUserMessage: String?        // Mensaje optimista pendiente
    _streamFuncInfo: Object?            // Pre-cargado en connectedCallback()
    _useStreaming: Boolean              // Toggle streaming (desde settings)
    _abortController: AbortController? // Para cancelar stream activo
    
    // Métodos públicos de estado
    setParam(name, value)               // Actualiza param con reactividad
    getParam(name) → Any
    
    // Métodos de comunicación
    _loadFuncInfo()                     // Carga schema 'chat' vía _client.loadSchemas()
    _loadChatConfig()                   // Carga config vía _client.call('get_chat_config')
    _loadStreamFuncInfo()               // Pre-carga chat_stream schema del registry
    _sendMessage(message)               // Decide stream vs sync según _streamFuncInfo
    _sendMessageStream(message)         // SSE streaming vía _client.stream()
    _sendMessageSync(message)           // Fallback síncrono vía _client.call()
    _updateContext()                    // Calcula uso de contexto vía _client.call()
    
    // Eventos escuchados
    'submit' → _handleInputSubmit()
    'settings-change' → _handleSettingsChange()
    'toggle' → _handleWindowToggle()

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
    addStreamingMessage() → id          // Crea mensaje vacío streaming=true, retorna ID
    appendToStreaming(id, chunk)         // Añade chunk de texto a mensaje streaming
    finalizeStreaming(id, envelope)      // Reemplaza contenido con envelope final
    clear()                             // Limpia historial
    getMessages() → [Message]           // Copia del historial
    
    // Message Shape
    Message: { 
        id?: String,                    // Solo para streaming (stream-{timestamp})
        role: 'user'|'assistant'|'error', 
        content: String|Object, 
        streaming?: Boolean,            // true durante streaming activo
        timestamp: Number 
    }

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
    _activeTab: String (state)          // Tab activa: overview|trajectory|history|live|raw
    
    // Tabs
    "overview"   → Métricas + Reasoning
    "trajectory" → Pasos de ReAct (tool calls)
    "history"    → Llamadas LM raw
    "live"       → Status log de streaming (si data._statusLog existe)
    "raw"        → JSON completo
    
    // _parseData() extrae:
    //   info.statusLog ← data._statusLog  (array de {message, timestamp})

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

```

---

## TOPOLOGÍA

```
┌─────────────────────────────────────────────────────────────────────┐
│                     LitElement + RefractClient                      │
│              (composición, no herencia)                             │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ extends + compone
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        AutocodeChat                                 │
│                         (index.js)                                  │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ _client: RefractClient                                        │   │
│  │ conversationHistory, _chatConfig, _pendingUserMessage         │   │
│  │ _handleInputSubmit(), _sendMessage(), _processResult()        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ compone
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌───────────────────┐                  ┌──────────────┐
│    ChatWindow     │                  │ ChatSettings │
│  (chat-window.js) │                  │              │
│  drag + resize    │                  │ dialog modal │
└─────────┬─────────┘                  └──────────────┘
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
└── styles/
    ├── theme.js                    # Re-export de shared
    ├── common.js                   # Utilidades CSS compartidas
    ├── autocode-chat.styles.js
    ├── chat-window.styles.js
    ├── chat-messages.styles.js
    ├── chat-input.styles.js
    ├── chat-settings.styles.js
    ├── chat-debug-info.styles.js
    └── context-bar.styles.js
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

### P4: Dialog Modal Pattern
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

### P5: Streaming Message Pattern
```
Entrada:  Usuario envía mensaje con streaming disponible
Proceso:  
  1. _sendMessage() detecta _streamFuncInfo?.streaming === true
  2. Resetear envelope/result/success (evitar datos stale)
  3. addStreamingMessage() → crea bubble vacía con cursor ▊
  4. _client.stream('chat_stream', params, funcInfo, {signal}) → async iterable SSE
  5. event: token  → appendToStreaming(id, chunk) — texto incremental
  6. event: status → _setStatus('loading', message) + push a statusLog
  7. event: complete → finalizeStreaming(id, envelope) — render normal
  8. event: error → finalizeStreaming(id, errorEnvelope)
Salida:   Texto aparece token a token, luego se reemplaza por envelope rico

// En ChatMessages:
addStreamingMessage() → id               // Crea msg {streaming: true, content: ''}
appendToStreaming(id, chunk)              // content += chunk (inmutable)
finalizeStreaming(id, envelope)           // content = envelope, streaming = false

// Render durante streaming:
html`<div class="text-content">${msg.content}<span class="cursor">▊</span></div>`
// .bubble.streaming tiene border-left indicador

Invariante: envelope se resetea al inicio de cada stream (no stale)
            _streamFuncInfo se pre-carga en connectedCallback() (no lazy)
            Si streaming no disponible → fallback a _sendMessageSync()
            statusLog se pasa en envelope._statusLog al finalizar
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
    this._client = new RefractClient() en constructor
    this.conversationHistory sincronizado con params.conversation_history
    _sendMessage() siempre precedido de setParam('message', msg)

ChatSettings:
    _settings actualizado vía _updateSetting() (no directo)
    getSettings() incluye module_kwargs y enabled_tools si aplica
    configure(funcInfo) debe llamarse antes de usar

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

                    CONTEXT → BAR
{current, max}     ──────────────────►  ContextBar visual
  % < 70                                Barra verde
  70 ≤ % < 90                           Barra amarilla
  % ≥ 90                                Barra roja

                    SSE STREAM → INCREMENTAL UI
SSE events         ──────────────────►  ChatMessages streaming
  event: token                          appendToStreaming(id, chunk)
  event: status                         _setStatus() + statusLog push
  event: complete                       finalizeStreaming(id, envelope)
  event: error                          finalizeStreaming(id, errorEnvelope)
  envelope._statusLog                   ChatDebugInfo tab "Live"
```

---

## FLUJO DE VIDA

```
1. INICIALIZACIÓN (Element attached)
   connectedCallback()
   → _loadFuncInfo() → _client.loadSchemas() + _client.getSchema('chat')
   → _loadChatConfig() → _client.call('get_chat_config')
   → _loadStreamFuncInfo() → _client.getSchema('chat_stream') (pre-carga)
   
   firstUpdated()
   → Obtener referencias: _window, _messages, _input, _settings
   → Setup event listeners en shadowRoot

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
       e. Si _streamFuncInfo?.streaming → _sendMessageStream()
          Sino → _sendMessageSync()
       f. _input.clear(), _updateContext()

3a. ENVÍO STREAMING (_sendMessageStream)
   a. Resetear envelope/result/success (evitar stale)
   b. addStreamingMessage() → streamId
   c. for await (event of callStreamAPI('chat_stream', params)):
      - token → appendToStreaming(streamId, chunk)
      - status → _setStatus('loading', message), push statusLog
      - complete → finalizeStreaming(streamId, envelope), save state
      - error → finalizeStreaming(streamId, errorEnvelope)
   d. Actualizar conversationHistory con texto acumulado

3b. ENVÍO SÍNCRONO (_sendMessageSync)
   a. await this._client.call('chat', this.params, this.funcInfo)
   b. _processResult(data)

4. PROCESAMIENTO DE RESPUESTA (solo sync path)
   _processResult(envelope)
   → Si error: _messages.addMessage('error', envelope)
   → Si ok:
       a. _messages.addMessage('assistant', envelope)
       b. Extraer responseText de envelope
       c. Push user msg a conversationHistory (confirma optimista)
       d. Push assistant msg a conversationHistory
       e. setParam('conversation_history', _formatHistory())

5. CICLO DE CONTEXTO
   _updateContext()
   → Construir mensajes (history + input actual)
   → _client.call('calculate_context_usage', {model, messages})
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
  → Emitir evento al orquestador para que use su _client

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

# Verificar eventos (en consola)
const chat = document.querySelector('autocode-chat');
chat.shadowRoot.addEventListener('submit', e => console.log('submit:', e.detail));
chat.shadowRoot.addEventListener('settings-change', e => console.log('settings:', e.detail));

# Verificar estado del componente
const chat = document.querySelector('autocode-chat');
console.log(chat.funcInfo);                           // {name: 'chat', parameters: [...]}
console.log(chat.params);                             // {message, model, conversation_history, ...}
console.log(chat._client);                            // RefractClient instance
```

---

> **Regeneración**: Este DCC + Lit + RefractClient + API backend = autocode/web/elements/chat
> **Extracción**: inspect(chat/*.js + chat/styles/*) = Este DCC
