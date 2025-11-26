# Cambios en staging (cached)

Generado: 2025-11-26 01:25:08
Rama: easy

---

```diff
diff --git a/autocode/interfaces/api.py b/autocode/interfaces/api.py
index 16767c8..c3e31a3 100644
--- a/autocode/interfaces/api.py
+++ b/autocode/interfaces/api.py
@@ -130,6 +130,7 @@ def _register_standard_endpoints(app: FastAPI):
     
     current_dir = os.path.dirname(__file__)
     views_dir = os.path.join(current_dir, "..", "web", "views")
+    tests_dir = os.path.join(current_dir, "..", "web", "tests")
     
     @app.get("/")
     async def root():
@@ -146,6 +147,11 @@ def _register_standard_endpoints(app: FastAPI):
         """Serve the custom elements demo page."""
         return FileResponse(os.path.join(views_dir, "demo.html"))
 
+    @app.get("/tests")
+    async def tests_dashboard():
+        """Serve the test dashboard page."""
+        return FileResponse(os.path.join(tests_dir, "index.html"))
+
     @app.get("/functions/details", response_model=FunctionDetailsResponse)
     async def list_functions_details():
         """Get detailed information about all registered functions."""
@@ -169,6 +175,11 @@ def _register_static_files(app: FastAPI):
     if os.path.exists(elements_dir):
         app.mount("/elements", StaticFiles(directory=elements_dir), name="elements")
 
+    # Mount tests directory for browser-based tests
+    tests_dir = os.path.join(web_dir, "tests")
+    if os.path.exists(tests_dir):
+        app.mount("/tests", StaticFiles(directory=tests_dir, html=True), name="tests")
+
     # Mount static directory for general assets
     static_dir = os.path.join(web_dir, "static")
     if os.path.exists(static_dir):
diff --git a/autocode/web/elements/chat-element.js b/autocode/web/elements/chat-element.js
deleted file mode 100644
index 6d8a652..0000000
--- a/autocode/web/elements/chat-element.js
+++ /dev/null
@@ -1,346 +0,0 @@
-/**
- * chat-element.js
- * Web Component para el chat flotante de Autocode
- * Extiende del elemento auto-chat generado dinámicamente
- * REFACTOR: Usa componentes y lógica de la clase base
- */
-
-async function initChatElement() {
-    await customElements.whenDefined('auto-chat');
-    const AutoChatBase = customElements.get('auto-chat');
-
-    class AutocodeChat extends AutoChatBase {
-        constructor() {
-            super();
-            this.conversationHistory = [];
-            // Referencias a inputs especiales
-            this._messageInput = null;
-            this._historyInput = null;
-        }
-
-        connectedCallback() {
-            // Renderizamos nuestra UI personalizada
-            this.render();
-            // Setup events específicos del chat (drag, toggle, etc)
-            this.setupChatEvents();
-        }
-
-        render() {
-            this.innerHTML = '';
-            
-            // 1. Contenedor Principal (Floating Toggle + Chat Window)
-            this.innerHTML = `
-                <!-- Botón flotante -->
-                <button id="chatToggleBtn" class="fixed top-4 left-4 z-[110] bg-white text-indigo-600 rounded-full p-4 shadow-lg hover:shadow-xl ring-1 ring-black/10 transition-transform duration-300 hover:scale-105">
-                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
-                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
-                    </svg>
-                </button>
-
-                <!-- Panel de Chat -->
-                <div id="chatPanel" class="hidden fixed inset-0 z-[100] bg-transparent pointer-events-none">
-                    <div id="chatWindow" class="fixed top-20 right-6 w-[92vw] md:w-[480px] lg:w-[560px] h-[70vh] bg-white rounded-2xl shadow-2xl ring-1 ring-black/10 overflow-hidden flex flex-col pointer-events-auto">
-                        
-                        <!-- Header -->
-                        <div id="chatDragHandle" class="bg-gradient-to-r from-indigo-600 to-violet-600 p-4 flex items-center justify-between cursor-grab select-none">
-                            <div class="flex items-center gap-3">
-                                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
-                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
-                                </svg>
-                                <h2 class="text-white font-bold text-xl">Autocode AI Chat</h2>
-                            </div>
-                            <div class="flex items-center gap-2">
-                                <button id="newChatBtn" class="text-indigo-100 bg-white/10 hover:bg-white/20 border border-white/20 rounded-full px-3 py-1.5 text-sm font-semibold transition-colors">Nueva</button>
-                                <button id="chatCloseBtn" class="text-white hover:bg-indigo-700 rounded-full p-2 transition-colors">
-                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
-                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
-                                    </svg>
-                                </button>
-                            </div>
-                        </div>
-
-                        <!-- Área de Mensajes -->
-                        <div id="messagesContainer" class="flex-1 overflow-y-auto p-4 bg-gradient-to-b from-gray-50 to-white space-y-3">
-                            <div class="text-center text-gray-500 italic" id="emptyState">Inicia una conversación... 💬</div>
-                        </div>
-
-                        <!-- Área de Input (Footer) -->
-                        <div class="bg-white p-4 border-t border-gray-200">
-                            <div class="flex gap-2" id="inputArea">
-                                <!-- Aquí inyectaremos el input 'message' y el botón 'execute' -->
-                            </div>
-                            <!-- Context bar -->
-                            <div class="mt-3">
-                                <div class="flex items-center justify-between text-xs text-gray-600 mb-1">
-                                    <span>Ventana de contexto</span>
-                                    <span id="contextStats" class="font-mono">0 / 0</span>
-                                </div>
-                                <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
-                                    <div id="contextBar" class="h-full bg-green-500 transition-all duration-300" style="width: 0%"></div>
-                                </div>
-                            </div>
-                        </div>
-                        
-                        <!-- Contenedor oculto para otros parámetros -->
-                        <div id="hiddenParams" class="hidden"></div>
-
-                        <!-- Handle Resize -->
-                        <div id="chatResizeHandle" class="absolute bottom-2 right-2 w-4 h-4 cursor-se-resize text-indigo-300/70 hover:text-indigo-400 select-none">
-                            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
-                                <path d="M21 11L11 21M17 7L7 17" />
-                            </svg>
-                        </div>
-                    </div>
-                </div>
-            `;
-            
-            this.injectGeneratedComponents();
-        }
-
-        injectGeneratedComponents() {
-            const inputArea = this.querySelector('#inputArea');
-            const hiddenParams = this.querySelector('#hiddenParams');
-            
-            // 1. Message Input
-            const messageParam = this.funcInfo.parameters.find(p => p.name === 'message');
-            if (messageParam) {
-                const messageContainer = this.createParamElement(messageParam);
-                
-                // Personalizar el input generado para que parezca un chat
-                const input = messageContainer.querySelector('input');
-                if (input) {
-                    input.id = 'messageInput';
-                    input.placeholder = "Escribe tu mensaje...";
-                    input.className = "flex-1 p-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm";
-                    
-                    // Eliminar label y description
-                    messageContainer.querySelectorAll('label, p').forEach(el => el.remove());
-                    // Eliminar clases del contenedor para que no afecten layout flex
-                    messageContainer.className = "flex-1";
-                    
-                    inputArea.appendChild(messageContainer);
-                    this._messageInput = input;
-                    
-                    // Bind Enter key
-                    input.addEventListener('keypress', (e) => {
-                        if (e.key === 'Enter' && !e.shiftKey) {
-                            e.preventDefault();
-                            this.execute();
-                        }
-                    });
-                }
-            }
-
-            // 2. Execute Button (Send)
-            const sendBtn = this.createExecuteButton();
-            sendBtn.id = 'sendBtn';
-            sendBtn.textContent = 'Enviar 🚀';
-            sendBtn.className = "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white font-semibold px-5 rounded-xl shadow transition disabled:bg-gray-400 text-sm";
-            inputArea.appendChild(sendBtn);
-
-            // 3. Other Params (Hidden)
-            this.funcInfo.parameters.forEach(param => {
-                if (param.name === 'message') return;
-                
-                const el = this.createParamElement(param);
-                if (param.name === 'conversation_history') {
-                    this._historyInput = el.querySelector('input, select, textarea');
-                }
-                hiddenParams.appendChild(el);
-            });
-        }
-
-        async execute() {
-            const userMsg = this._messageInput?.value?.trim();
-            if (!userMsg) return;
-
-            // 1. UI Optimista
-            this.addMessage('user', userMsg);
-            
-            // 2. Ejecutar lógica del padre
-            try {
-                await super.execute();
-                // El padre llama a showResult, que sobreescribimos
-            } catch (error) {
-                // El padre ya maneja el error visualmente en execute() -> showResult(error, true)
-                // Nosotros sobreescribimos showResult para usar burbujas de chat
-            }
-        }
-
-        // Sobreescribimos showResult para integrar con el historial del chat
-        showResult(result, isError = false) {
-            if (isError) {
-                this.addMessage('error', result);
-                return;
-            }
-
-            // result es un DspyOutput o similar. Asumimos que tiene 'response'
-            const responseText = result.result?.response || result.response || 
-                               (typeof result === 'string' ? result : JSON.stringify(result));
-
-            // UI Asistente
-            this.addMessage('assistant', responseText);
-
-            // Actualizar Historial Interno
-            // Necesitamos recuperar el mensaje del usuario que se acaba de enviar
-            // Como execute() no limpia el input hasta el final, podemos leerlo
-            // O mejor, lo guardamos antes. Pero simplifiquemos:
-            // Al ser exitoso, asumimos que el último mensaje user en UI corresponde a la respuesta.
-            
-            // Mejor: leer del input antes de limpiar
-            const userMsg = this._messageInput.value;
-            
-            this.conversationHistory.push({ role: 'user', content: userMsg });
-            this.conversationHistory.push({ role: 'assistant', content: responseText });
-
-            // Actualizar input oculto para la próxima llamada
-            if (this._historyInput) {
-                this._historyInput.value = this.formatHistory();
-                this._historyInput.dispatchEvent(new Event('change'));
-            }
-
-            // Limpiar input y update context
-            this._messageInput.value = '';
-            this.updateContext();
-        }
-
-        // --- Lógica UI específica del Chat (Drag, Resize, Bubbles) ---
-
-        setupChatEvents() {
-            const chatToggleBtn = this.querySelector('#chatToggleBtn');
-            const chatPanel = this.querySelector('#chatPanel');
-            const chatCloseBtn = this.querySelector('#chatCloseBtn');
-            const newChatBtn = this.querySelector('#newChatBtn');
-            const chatDragHandle = this.querySelector('#chatDragHandle');
-            const chatWindow = this.querySelector('#chatWindow');
-
-            chatToggleBtn.addEventListener('click', () => {
-                chatPanel.classList.toggle('hidden');
-                if (!chatPanel.classList.contains('hidden')) {
-                    setTimeout(() => this._messageInput?.focus(), 100);
-                }
-            });
-
-            chatCloseBtn.addEventListener('click', () => chatPanel.classList.add('hidden'));
-
-            newChatBtn.addEventListener('click', () => {
-                this.conversationHistory = [];
-                if (this._historyInput) {
-                    this._historyInput.value = '';
-                    this._historyInput.dispatchEvent(new Event('change'));
-                }
-                const container = this.querySelector('#messagesContainer');
-                container.innerHTML = '<div class="text-center text-gray-500 italic" id="emptyState">Inicia una conversación... 💬</div>';
-                this.updateContextBar(0, 0, 0);
-            });
-
-            // Drag logic simplificada
-            let isDragging = false;
-            let offsetX, offsetY;
-
-            chatDragHandle.addEventListener('pointerdown', (e) => {
-                isDragging = true;
-                const rect = chatWindow.getBoundingClientRect();
-                offsetX = e.clientX - rect.left;
-                offsetY = e.clientY - rect.top;
-                chatDragHandle.setPointerCapture(e.pointerId);
-            });
-
-            chatDragHandle.addEventListener('pointermove', (e) => {
-                if (!isDragging) return;
-                const x = Math.max(0, Math.min(e.clientX - offsetX, window.innerWidth - chatWindow.offsetWidth));
-                const y = Math.max(0, Math.min(e.clientY - offsetY, window.innerHeight - chatWindow.offsetHeight));
-                chatWindow.style.left = `${x}px`;
-                chatWindow.style.top = `${y}px`;
-            });
-
-            chatDragHandle.addEventListener('pointerup', (e) => {
-                isDragging = false;
-                chatDragHandle.releasePointerCapture(e.pointerId);
-            });
-        }
-
-        addMessage(role, content) {
-            const messagesContainer = this.querySelector('#messagesContainer');
-            const emptyState = this.querySelector('#emptyState');
-            if (emptyState) emptyState.remove();
-
-            const messageDiv = document.createElement('div');
-            messageDiv.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'}`;
-            
-            const bubble = document.createElement('div');
-            bubble.className = `max-w-[85%] rounded-2xl px-4 py-3 ${
-                role === 'user' 
-                    ? 'bg-indigo-600 text-white shadow-md' 
-                    : role === 'error'
-                    ? 'bg-red-50 text-red-800 border border-red-300'
-                    : 'bg-white text-gray-800 shadow-sm border border-gray-200'
-            }`;
-            
-            bubble.innerHTML = `
-                <div class="font-bold text-sm mb-1">${role === 'user' ? '👤 Tú' : role === 'error' ? '❌ Error' : '🤖 Asistente'}</div>
-                <div class="whitespace-pre-wrap break-words text-sm">${content}</div>
-            `;
-            
-            messageDiv.appendChild(bubble);
-            messagesContainer.appendChild(messageDiv);
-            messagesContainer.scrollTop = messagesContainer.scrollHeight;
-        }
-
-        formatHistory() {
-            return this.conversationHistory.map(msg => 
-                `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`
-            ).join(' | ');
-        }
-
-        async updateContext() {
-            // Reutilizamos la lógica existente de context stats
-            // Podríamos intentar usar una función del registry si existiera, 
-            // pero calculate_context_usage es una función registrada!
-            // Podríamos llamar a this.callAPI({ model, messages }) contra esa función?
-            // No, porque this.callAPI llama a /chat (la función de ESTE elemento).
-            // Así que mantenemos el fetch manual aquí o creamos un nuevo auto-element para esto.
-            // Mantenemos fetch manual por simplicidad.
-            
-            const messages = [...this.conversationHistory];
-            if (this._messageInput?.value) messages.push({ role: 'user', content: this._messageInput.value });
-            if (messages.length === 0) {
-                this.updateContextBar(0, 0, 0);
-                return;
-            }
-
-            try {
-                // Aquí usamos fetch directo porque estamos llamando a OTRA función
-                const model = this.funcInfo.parameters.find(p => p.name === 'model')?.default || 'openrouter/openai/gpt-4o';
-                
-                const response = await fetch('/calculate_context_usage', {
-                    method: 'POST',
-                    headers: { 'Content-Type': 'application/json' },
-                    body: JSON.stringify({ model, messages })
-                });
-                
-                const data = await response.json();
-                const { current = 0, max = 0, percentage = 0 } = data.result || {};
-                this.updateContextBar(current, max, percentage);
-            } catch (error) {
-                console.error('Error updating context:', error);
-            }
-        }
-
-        updateContextBar(current, max, percentage) {
-            const contextStats = this.querySelector('#contextStats');
-            const contextBar = this.querySelector('#contextBar');
-            if (!contextStats || !contextBar) return;
-
-            contextStats.textContent = `${current.toLocaleString()} / ${max.toLocaleString()}`;
-            contextBar.style.width = `${Math.min(percentage, 100)}%`;
-            contextBar.className = `h-full transition-all duration-300 ${percentage < 70 ? 'bg-green-500' : percentage < 90 ? 'bg-yellow-500' : 'bg-red-500'}`;
-        }
-    }
-
-    if (!customElements.get('autocode-chat')) {
-        customElements.define('autocode-chat', AutocodeChat);
-    }
-}
-
-initChatElement();
diff --git a/autocode/web/elements/chat/autocode-chat.js b/autocode/web/elements/chat/autocode-chat.js
new file mode 100644
index 0000000..242dbb8
--- /dev/null
+++ b/autocode/web/elements/chat/autocode-chat.js
@@ -0,0 +1,273 @@
+/**
+ * autocode-chat.js
+ * Orquestador del chat que compone todos los sub-componentes
+ * Hereda de auto-chat (generado por AutoElementGenerator) para reutilizar API calls
+ * 
+ * Composición:
+ * - ChatWindow: Ventana flotante con drag/resize
+ * - ChatMessages: Lista de mensajes con scroll
+ * - ChatInput: Input y botón de envío
+ * - ContextBar: Barra de uso de tokens
+ */
+
+// Importar sub-componentes
+import './chat-input.js';
+import './chat-messages.js';
+import './chat-window.js';
+import './context-bar.js';
+
+async function initAutocodeChat() {
+    // Esperar a que auto-chat esté definido (generado por AutoElementGenerator)
+    await customElements.whenDefined('auto-chat');
+    const AutoChatBase = customElements.get('auto-chat');
+
+    class AutocodeChat extends AutoChatBase {
+        constructor() {
+            super();
+            this.conversationHistory = [];
+            this._pendingUserMessage = null; // Fix bug: capturar mensaje antes de execute
+            
+            // Referencias a sub-componentes
+            this._window = null;
+            this._messages = null;
+            this._input = null;
+            this._contextBar = null;
+            this._historyInput = null;
+        }
+
+        connectedCallback() {
+            this.render();
+            this._setupComponentRefs();
+            this._setupEvents();
+        }
+
+        render() {
+            this.innerHTML = `
+                <chat-window title="Autocode AI Chat">
+                    <!-- Header actions -->
+                    <button 
+                        slot="header-actions"
+                        data-ref="newChatBtn"
+                        class="text-indigo-100 bg-white/10 hover:bg-white/20 border border-white/20 rounded-full px-3 py-1.5 text-sm font-semibold transition-colors"
+                    >
+                        Nueva
+                    </button>
+                    
+                    <!-- Content: mensajes -->
+                    <chat-messages slot="content" style="flex: 1;"></chat-messages>
+                    
+                    <!-- Footer: input y context bar -->
+                    <div slot="footer" class="p-4 space-y-3">
+                        <chat-input placeholder="Escribe tu mensaje..."></chat-input>
+                        <context-bar current="0" max="0"></context-bar>
+                    </div>
+                </chat-window>
+                
+                <!-- Contenedor oculto para otros parámetros de la función chat -->
+                <div data-ref="hiddenParams" class="hidden"></div>
+            `;
+        }
+
+        _setupComponentRefs() {
+            this._window = this.querySelector('chat-window');
+            this._messages = this.querySelector('chat-messages');
+            this._input = this.querySelector('chat-input');
+            this._contextBar = this.querySelector('context-bar');
+            
+            // Inyectar parámetros ocultos de la función chat (model, conversation_history, etc.)
+            this._injectHiddenParams();
+        }
+
+        _injectHiddenParams() {
+            const hiddenParams = this.querySelector('[data-ref="hiddenParams"]');
+            if (!hiddenParams || !this.funcInfo?.parameters) return;
+
+            this.funcInfo.parameters.forEach(param => {
+                // Saltamos 'message' porque lo manejamos con chat-input
+                if (param.name === 'message') return;
+
+                const el = this.createParamElement(param);
+                
+                // Guardar referencia a conversation_history
+                if (param.name === 'conversation_history') {
+                    this._historyInput = el.querySelector('input, select, textarea');
+                }
+                
+                hiddenParams.appendChild(el);
+            });
+        }
+
+        _setupEvents() {
+            // Submit desde chat-input
+            this._input?.addEventListener('submit', (e) => {
+                this._handleSubmit(e.detail.message);
+            });
+
+            // Nueva conversación
+            const newChatBtn = this.querySelector('[data-ref="newChatBtn"]');
+            newChatBtn?.addEventListener('click', () => this._handleNewChat());
+
+            // Focus en input cuando se abre la ventana
+            this._window?.addEventListener('toggle', (e) => {
+                if (e.detail.open) {
+                    setTimeout(() => this._input?.focus(), 100);
+                }
+            });
+        }
+
+        async _handleSubmit(message) {
+            if (!message?.trim()) return;
+
+            // FIX BUG: Capturar mensaje ANTES de cualquier operación
+            this._pendingUserMessage = message;
+
+            // 1. UI Optimista: mostrar mensaje del usuario inmediatamente
+            this._messages?.addMessage('user', message);
+
+            // 2. Actualizar el valor del input "message" para el API call
+            // Necesitamos encontrar o crear el input que usará super.execute()
+            this._setMessageParam(message);
+
+            // 3. Ejecutar llamada a la API via clase base
+            try {
+                await super.execute();
+                // showResult será llamado por la clase base, nosotros lo sobreescribimos
+            } catch (error) {
+                // La clase base ya maneja el error
+            }
+
+            // 4. Limpiar input y actualizar contexto
+            this._input?.clear();
+            this._updateContext();
+        }
+
+        _setMessageParam(message) {
+            // Buscar el input 'message' en los parámetros ocultos o crearlo
+            let messageInput = this.querySelector('[name="message"]');
+            
+            if (!messageInput) {
+                // Crear input oculto para el parámetro message
+                const hiddenParams = this.querySelector('[data-ref="hiddenParams"]');
+                const input = document.createElement('input');
+                input.type = 'hidden';
+                input.name = 'message';
+                hiddenParams?.appendChild(input);
+                messageInput = input;
+            }
+            
+            messageInput.value = message;
+        }
+
+        /**
+         * Sobreescribimos showResult de la clase base para mostrar en burbujas
+         */
+        showResult(result, isError = false) {
+            if (isError) {
+                this._messages?.addMessage('error', 
+                    typeof result === 'string' ? result : JSON.stringify(result));
+                return;
+            }
+
+            // Extraer respuesta del resultado (DspyOutput o similar)
+            const responseText = result?.result?.response || 
+                               result?.response || 
+                               (typeof result === 'string' ? result : JSON.stringify(result, null, 2));
+
+            // Mostrar respuesta del asistente
+            this._messages?.addMessage('assistant', responseText);
+
+            // Actualizar historial conversacional con el mensaje que capturamos ANTES
+            if (this._pendingUserMessage) {
+                this.conversationHistory.push({ 
+                    role: 'user', 
+                    content: this._pendingUserMessage 
+                });
+                this._pendingUserMessage = null;
+            }
+            
+            this.conversationHistory.push({ 
+                role: 'assistant', 
+                content: responseText 
+            });
+
+            // Sincronizar historial con el input oculto
+            this._syncHistoryInput();
+        }
+
+        _syncHistoryInput() {
+            if (this._historyInput) {
+                this._historyInput.value = this._formatHistory();
+                this._historyInput.dispatchEvent(new Event('change'));
+            }
+        }
+
+        _formatHistory() {
+            return this.conversationHistory.map(msg => 
+                `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`
+            ).join(' | ');
+        }
+
+        _handleNewChat() {
+            this.conversationHistory = [];
+            this._pendingUserMessage = null;
+            
+            // Limpiar historial en el input oculto
+            if (this._historyInput) {
+                this._historyInput.value = '';
+                this._historyInput.dispatchEvent(new Event('change'));
+            }
+            
+            // Limpiar mensajes visuales
+            this._messages?.clear();
+            
+            // Reset context bar
+            this._contextBar?.update(0, 0);
+        }
+
+        async _updateContext() {
+            // Construir lista de mensajes para calcular contexto
+            const messages = [...this.conversationHistory];
+            const currentInput = this._input?.getValue();
+            if (currentInput) {
+                messages.push({ role: 'user', content: currentInput });
+            }
+            
+            if (messages.length === 0) {
+                this._contextBar?.update(0, 0);
+                return;
+            }
+
+            try {
+                // Obtener modelo de los parámetros
+                const modelInput = this.querySelector('[name="model"]');
+                const model = modelInput?.value || 'openrouter/openai/gpt-4o';
+                
+                // Llamar al endpoint de cálculo de contexto
+                // TODO: En el futuro usar <auto-calculate_context_usage> para consistencia
+                const response = await fetch('/calculate_context_usage', {
+                    method: 'POST',
+                    headers: { 'Content-Type': 'application/json' },
+                    body: JSON.stringify({ model, messages })
+                });
+                
+                if (response.ok) {
+                    const data = await response.json();
+                    const { current = 0, max = 0 } = data.result || data || {};
+                    this._contextBar?.update(current, max);
+                }
+            } catch (error) {
+                console.warn('Error calculando contexto:', error);
+            }
+        }
+    }
+
+    // Registrar el custom element
+    if (!customElements.get('autocode-chat')) {
+        customElements.define('autocode-chat', AutocodeChat);
+    }
+}
+
+// Inicializar
+initAutocodeChat().catch(console.error);
+
+export { initAutocodeChat };
diff --git a/autocode/web/elements/chat/chat-input.js b/autocode/web/elements/chat/chat-input.js
new file mode 100644
index 0000000..e42cf0f
--- /dev/null
+++ b/autocode/web/elements/chat/chat-input.js
@@ -0,0 +1,121 @@
+/**
+ * chat-input.js
+ * Componente de entrada para el chat
+ * 
+ * Atributos:
+ * - placeholder: Texto placeholder del input
+ * - disabled: Desactiva input y botón
+ * 
+ * Eventos:
+ * - submit: Emitido al hacer click o Enter, con detail: { message }
+ * 
+ * Métodos:
+ * - clear(): Limpia el input
+ * - focus(): Enfoca el input
+ * - getValue(): Retorna el valor actual
+ */
+
+class ChatInput extends HTMLElement {
+    static get observedAttributes() {
+        return ['placeholder', 'disabled'];
+    }
+
+    constructor() {
+        super();
+        this._input = null;
+        this._button = null;
+    }
+
+    connectedCallback() {
+        this.render();
+        this.setupEvents();
+    }
+
+    attributeChangedCallback(name, oldValue, newValue) {
+        if (oldValue === newValue) return;
+        
+        if (name === 'placeholder' && this._input) {
+            this._input.placeholder = newValue || '';
+        }
+        
+        if (name === 'disabled') {
+            const isDisabled = newValue !== null;
+            if (this._input) this._input.disabled = isDisabled;
+            if (this._button) this._button.disabled = isDisabled;
+        }
+    }
+
+    render() {
+        const placeholder = this.getAttribute('placeholder') || 'Escribe tu mensaje...';
+        const isDisabled = this.hasAttribute('disabled');
+
+        this.innerHTML = `
+            <div class="flex gap-2 w-full">
+                <input 
+                    type="text" 
+                    placeholder="${placeholder}"
+                    ${isDisabled ? 'disabled' : ''}
+                    class="flex-1 p-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
+                    data-ref="input"
+                >
+                <button 
+                    ${isDisabled ? 'disabled' : ''}
+                    class="bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white font-semibold px-5 py-3 rounded-xl shadow transition disabled:opacity-50 disabled:cursor-not-allowed text-sm"
+                    data-ref="button"
+                >
+                    Enviar 🚀
+                </button>
+            </div>
+        `;
+
+        this._input = this.querySelector('[data-ref="input"]');
+        this._button = this.querySelector('[data-ref="button"]');
+    }
+
+    setupEvents() {
+        // Click en botón
+        this._button.addEventListener('click', () => this._submit());
+
+        // Enter en input
+        this._input.addEventListener('keypress', (e) => {
+            if (e.key === 'Enter' && !e.shiftKey) {
+                e.preventDefault();
+                this._submit();
+            }
+        });
+    }
+
+    _submit() {
+        const message = this._input.value.trim();
+        if (!message) return;
+
+        this.dispatchEvent(new CustomEvent('submit', {
+            detail: { message },
+            bubbles: true,
+            composed: true
+        }));
+    }
+
+    // API Pública
+    clear() {
+        if (this._input) {
+            this._input.value = '';
+        }
+    }
+
+    focus() {
+        if (this._input) {
+            this._input.focus();
+        }
+    }
+
+    getValue() {
+        return this._input?.value || '';
+    }
+}
+
+if (!customElements.get('chat-input')) {
+    customElements.define('chat-input', ChatInput);
+}
+
+export { ChatInput };
diff --git a/autocode/web/elements/chat/chat-messages.js b/autocode/web/elements/chat/chat-messages.js
new file mode 100644
index 0000000..a2a56a9
--- /dev/null
+++ b/autocode/web/elements/chat/chat-messages.js
@@ -0,0 +1,135 @@
+/**
+ * chat-messages.js
+ * Componente para mostrar mensajes del chat
+ * 
+ * Métodos:
+ * - addMessage(role, content): Añade un mensaje (role: 'user' | 'assistant' | 'error')
+ * - clear(): Elimina todos los mensajes
+ * - getMessages(): Retorna array de mensajes
+ */
+
+class ChatMessages extends HTMLElement {
+    constructor() {
+        super();
+        this._messages = [];
+        this._container = null;
+    }
+
+    connectedCallback() {
+        this.render();
+    }
+
+    render() {
+        this.innerHTML = `
+            <div 
+                data-ref="container"
+                class="flex-1 overflow-y-auto p-4 bg-gradient-to-b from-gray-50 to-white space-y-3 min-h-[200px]"
+            >
+                <div class="text-center text-gray-500 italic" data-ref="emptyState">
+                    Inicia una conversación... 💬
+                </div>
+            </div>
+        `;
+        
+        this._container = this.querySelector('[data-ref="container"]');
+    }
+
+    /**
+     * Añade un mensaje al chat
+     * @param {'user' | 'assistant' | 'error'} role - Rol del mensaje
+     * @param {string} content - Contenido del mensaje
+     */
+    addMessage(role, content) {
+        // Remover empty state si existe
+        const emptyState = this.querySelector('[data-ref="emptyState"]');
+        if (emptyState) emptyState.remove();
+
+        // Guardar en array interno
+        this._messages.push({ role, content, timestamp: Date.now() });
+
+        // Crear elemento del mensaje
+        const messageDiv = document.createElement('div');
+        messageDiv.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'}`;
+        messageDiv.dataset.role = role;
+
+        const bubble = document.createElement('div');
+        bubble.className = this._getBubbleClasses(role);
+
+        const header = document.createElement('div');
+        header.className = 'font-bold text-sm mb-1';
+        header.textContent = this._getRoleLabel(role);
+
+        const body = document.createElement('div');
+        body.className = 'whitespace-pre-wrap break-words text-sm';
+        body.textContent = content;
+
+        bubble.appendChild(header);
+        bubble.appendChild(body);
+        messageDiv.appendChild(bubble);
+        this._container.appendChild(messageDiv);
+
+        // Auto-scroll al final
+        this._scrollToBottom();
+    }
+
+    _getBubbleClasses(role) {
+        const base = 'max-w-[85%] rounded-2xl px-4 py-3';
+        
+        switch (role) {
+            case 'user':
+                return `${base} bg-indigo-600 text-white shadow-md`;
+            case 'error':
+                return `${base} bg-red-50 text-red-800 border border-red-300`;
+            case 'assistant':
+            default:
+                return `${base} bg-white text-gray-800 shadow-sm border border-gray-200`;
+        }
+    }
+
+    _getRoleLabel(role) {
+        switch (role) {
+            case 'user':
+                return '👤 Tú';
+            case 'error':
+                return '❌ Error';
+            case 'assistant':
+            default:
+                return '🤖 Asistente';
+        }
+    }
+
+    _scrollToBottom() {
+        // Usar requestAnimationFrame para asegurar que el DOM se ha actualizado
+        requestAnimationFrame(() => {
+            if (this._container) {
+                this._container.scrollTop = this._container.scrollHeight;
+            }
+        });
+    }
+
+    /**
+     * Elimina todos los mensajes
+     */
+    clear() {
+        this._messages = [];
+        this._container.innerHTML = `
+            <div class="text-center text-gray-500 italic" data-ref="emptyState">
+                Inicia una conversación... 💬
+            </div>
+        `;
+    }
+
+    /**
+     * Retorna todos los mensajes
+     * @returns {Array<{role: string, content: string, timestamp: number}>}
+     */
+    getMessages() {
+        return [...this._messages];
+    }
+}
+
+if (!customElements.get('chat-messages')) {
+    customElements.define('chat-messages', ChatMessages);
+}
+
+export { ChatMessages };
diff --git a/autocode/web/elements/chat/chat-window.js b/autocode/web/elements/chat/chat-window.js
new file mode 100644
index 0000000..9b37f2d
--- /dev/null
+++ b/autocode/web/elements/chat/chat-window.js
@@ -0,0 +1,393 @@
+/**
+ * chat-window.js
+ * Ventana flotante para el chat con drag y resize
+ * 
+ * Usa Shadow DOM para que los slots funcionen correctamente
+ * 
+ * Atributos:
+ * - title: Título de la ventana
+ * - open: Si la ventana está visible (boolean attribute)
+ * 
+ * Eventos:
+ * - toggle: Emitido al abrir/cerrar
+ * - close: Emitido al cerrar
+ * 
+ * Métodos:
+ * - open(): Abre la ventana
+ * - close(): Cierra la ventana
+ * - toggle(): Alterna visibilidad
+ * 
+ * Slots:
+ * - header-actions: Acciones adicionales en el header
+ * - content: Contenido principal
+ * - footer: Pie de la ventana
+ */
+
+class ChatWindow extends HTMLElement {
+    static get observedAttributes() {
+        return ['title', 'open'];
+    }
+
+    constructor() {
+        super();
+        this._isOpen = false;
+        this._isDragging = false;
+        this._isResizing = false;
+        this._dragOffset = { x: 0, y: 0 };
+        
+        // Crear Shadow DOM para que los slots funcionen
+        this.attachShadow({ mode: 'open' });
+    }
+
+    connectedCallback() {
+        this.render();
+        this._setupEvents();
+    }
+
+    attributeChangedCallback(name, oldValue, newValue) {
+        if (oldValue === newValue) return;
+        
+        if (name === 'title') {
+            const titleEl = this.shadowRoot.querySelector('[data-ref="title"]');
+            if (titleEl) titleEl.textContent = newValue || 'Chat';
+        }
+        
+        if (name === 'open') {
+            this._isOpen = newValue !== null;
+            this._updateVisibility();
+        }
+    }
+
+    render() {
+        const title = this.getAttribute('title') || 'Autocode AI Chat';
+        
+        this.shadowRoot.innerHTML = `
+            <style>
+                :host {
+                    display: contents;
+                }
+                
+                .toggle-btn {
+                    position: fixed;
+                    top: 1rem;
+                    left: 1rem;
+                    z-index: 110;
+                    background: white;
+                    color: #4f46e5;
+                    border-radius: 9999px;
+                    padding: 1rem;
+                    box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
+                    border: none;
+                    cursor: pointer;
+                    transition: transform 0.3s, box-shadow 0.3s;
+                }
+                
+                .toggle-btn:hover {
+                    transform: scale(1.05);
+                    box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1);
+                }
+                
+                .panel {
+                    position: fixed;
+                    inset: 0;
+                    z-index: 100;
+                    background: transparent;
+                    pointer-events: none;
+                }
+                
+                .panel.hidden {
+                    display: none;
+                }
+                
+                .window {
+                    position: fixed;
+                    top: 5rem;
+                    right: 1.5rem;
+                    width: min(92vw, 560px);
+                    height: 70vh;
+                    min-width: 320px;
+                    min-height: 300px;
+                    background: white;
+                    border-radius: 1rem;
+                    box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.25);
+                    overflow: hidden;
+                    display: flex;
+                    flex-direction: column;
+                    pointer-events: auto;
+                }
+                
+                .header {
+                    background: linear-gradient(to right, #4f46e5, #7c3aed);
+                    padding: 1rem;
+                    display: flex;
+                    align-items: center;
+                    justify-content: space-between;
+                    cursor: grab;
+                    user-select: none;
+                }
+                
+                .header:active {
+                    cursor: grabbing;
+                }
+                
+                .header-left {
+                    display: flex;
+                    align-items: center;
+                    gap: 0.75rem;
+                }
+                
+                .header-title {
+                    color: white;
+                    font-weight: bold;
+                    font-size: 1.25rem;
+                    margin: 0;
+                }
+                
+                .header-right {
+                    display: flex;
+                    align-items: center;
+                    gap: 0.5rem;
+                }
+                
+                .close-btn {
+                    color: white;
+                    background: transparent;
+                    border: none;
+                    border-radius: 9999px;
+                    padding: 0.5rem;
+                    cursor: pointer;
+                    transition: background 0.2s;
+                }
+                
+                .close-btn:hover {
+                    background: rgba(79, 70, 229, 0.8);
+                }
+                
+                .content {
+                    flex: 1;
+                    overflow: hidden;
+                    display: flex;
+                    flex-direction: column;
+                }
+                
+                .footer {
+                    background: white;
+                    border-top: 1px solid #e5e7eb;
+                }
+                
+                .resize-handle {
+                    position: absolute;
+                    bottom: 0.5rem;
+                    right: 0.5rem;
+                    width: 1rem;
+                    height: 1rem;
+                    cursor: se-resize;
+                    color: rgba(99, 102, 241, 0.5);
+                    user-select: none;
+                }
+                
+                .resize-handle:hover {
+                    color: rgba(99, 102, 241, 0.8);
+                }
+                
+                /* Estilos para contenido slotted */
+                ::slotted([slot="content"]) {
+                    flex: 1;
+                    overflow: hidden;
+                    display: flex;
+                    flex-direction: column;
+                }
+                
+                /* Tailwind-like utility for header-actions slot */
+                ::slotted([slot="header-actions"]) {
+                    color: rgba(238, 242, 255, 0.9);
+                    background: rgba(255, 255, 255, 0.1);
+                    border: 1px solid rgba(255, 255, 255, 0.2);
+                    border-radius: 9999px;
+                    padding: 0.375rem 0.75rem;
+                    font-size: 0.875rem;
+                    font-weight: 600;
+                    cursor: pointer;
+                    transition: background 0.2s;
+                }
+                
+                ::slotted([slot="header-actions"]:hover) {
+                    background: rgba(255, 255, 255, 0.2);
+                }
+            </style>
+            
+            <!-- Botón flotante de toggle -->
+            <button data-ref="toggleBtn" class="toggle-btn">
+                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
+                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
+                </svg>
+            </button>
+
+            <!-- Panel de la ventana -->
+            <div data-ref="panel" class="panel hidden">
+                <div data-ref="window" class="window">
+                    <!-- Header con drag handle -->
+                    <div data-ref="dragHandle" class="header">
+                        <div class="header-left">
+                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="white">
+                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
+                            </svg>
+                            <h2 data-ref="title" class="header-title">${title}</h2>
+                        </div>
+                        <div class="header-right">
+                            <slot name="header-actions"></slot>
+                            <button data-ref="closeBtn" class="close-btn">
+                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
+                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
+                                </svg>
+                            </button>
+                        </div>
+                    </div>
+
+                    <!-- Content slot -->
+                    <div data-ref="content" class="content">
+                        <slot name="content"></slot>
+                    </div>
+
+                    <!-- Footer slot -->
+                    <div data-ref="footer" class="footer">
+                        <slot name="footer"></slot>
+                    </div>
+
+                    <!-- Resize handle -->
+                    <div data-ref="resizeHandle" class="resize-handle">
+                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
+                            <path d="M21 11L11 21M17 7L7 17" />
+                        </svg>
+                    </div>
+                </div>
+            </div>
+        `;
+    }
+
+    _setupEvents() {
+        const toggleBtn = this.shadowRoot.querySelector('[data-ref="toggleBtn"]');
+        const closeBtn = this.shadowRoot.querySelector('[data-ref="closeBtn"]');
+        const dragHandle = this.shadowRoot.querySelector('[data-ref="dragHandle"]');
+        const resizeHandle = this.shadowRoot.querySelector('[data-ref="resizeHandle"]');
+        const windowEl = this.shadowRoot.querySelector('[data-ref="window"]');
+
+        // Toggle button
+        toggleBtn?.addEventListener('click', () => this.toggle());
+
+        // Close button
+        closeBtn?.addEventListener('click', () => this.close());
+
+        // Drag functionality
+        if (dragHandle && windowEl) {
+            this._setupDrag(dragHandle, windowEl);
+        }
+
+        // Resize functionality
+        if (resizeHandle && windowEl) {
+            this._setupResize(resizeHandle, windowEl);
+        }
+    }
+
+    _setupDrag(handle, windowEl) {
+        handle.addEventListener('pointerdown', (e) => {
+            if (e.target.closest('button')) return; // No drag si click en botón
+            
+            this._isDragging = true;
+            const rect = windowEl.getBoundingClientRect();
+            this._dragOffset.x = e.clientX - rect.left;
+            this._dragOffset.y = e.clientY - rect.top;
+            
+            handle.setPointerCapture(e.pointerId);
+        });
+
+        handle.addEventListener('pointermove', (e) => {
+            if (!this._isDragging) return;
+            
+            const x = Math.max(0, Math.min(e.clientX - this._dragOffset.x, globalThis.innerWidth - windowEl.offsetWidth));
+            const y = Math.max(0, Math.min(e.clientY - this._dragOffset.y, globalThis.innerHeight - windowEl.offsetHeight));
+            
+            windowEl.style.left = `${x}px`;
+            windowEl.style.top = `${y}px`;
+            windowEl.style.right = 'auto';
+        });
+
+        handle.addEventListener('pointerup', (e) => {
+            this._isDragging = false;
+            handle.releasePointerCapture(e.pointerId);
+        });
+    }
+
+    _setupResize(handle, windowEl) {
+        handle.addEventListener('pointerdown', (e) => {
+            this._isResizing = true;
+            handle.setPointerCapture(e.pointerId);
+            e.preventDefault();
+        });
+
+        handle.addEventListener('pointermove', (e) => {
+            if (!this._isResizing) return;
+            
+            const rect = windowEl.getBoundingClientRect();
+            const newWidth = Math.max(320, e.clientX - rect.left);
+            const newHeight = Math.max(300, e.clientY - rect.top);
+            
+            windowEl.style.width = `${newWidth}px`;
+            windowEl.style.height = `${newHeight}px`;
+        });
+
+        handle.addEventListener('pointerup', (e) => {
+            this._isResizing = false;
+            handle.releasePointerCapture(e.pointerId);
+        });
+    }
+
+    _updateVisibility() {
+        const panel = this.shadowRoot.querySelector('[data-ref="panel"]');
+        if (!panel) return;
+
+        if (this._isOpen) {
+            panel.classList.remove('hidden');
+        } else {
+            panel.classList.add('hidden');
+        }
+    }
+
+    // API Pública
+    open() {
+        this._isOpen = true;
+        this._updateVisibility();
+        this.dispatchEvent(new CustomEvent('toggle', { 
+            detail: { open: true },
+            bubbles: true 
+        }));
+    }
+
+    close() {
+        this._isOpen = false;
+        this._updateVisibility();
+        this.dispatchEvent(new CustomEvent('close', { bubbles: true }));
+        this.dispatchEvent(new CustomEvent('toggle', { 
+            detail: { open: false },
+            bubbles: true 
+        }));
+    }
+
+    toggle() {
+        if (this._isOpen) {
+            this.close();
+        } else {
+            this.open();
+        }
+    }
+
+    isOpen() {
+        return this._isOpen;
+    }
+}
+
+if (!customElements.get('chat-window')) {
+    customElements.define('chat-window', ChatWindow);
+}
+
+export { ChatWindow };
diff --git a/autocode/web/elements/chat/context-bar.js b/autocode/web/elements/chat/context-bar.js
new file mode 100644
index 0000000..3aa82eb
--- /dev/null
+++ b/autocode/web/elements/chat/context-bar.js
@@ -0,0 +1,105 @@
+/**
+ * context-bar.js
+ * Barra de progreso para mostrar uso de la ventana de contexto
+ * 
+ * Atributos:
+ * - current: Tokens actuales usados
+ * - max: Tokens máximos disponibles
+ * 
+ * La barra cambia de color según el porcentaje:
+ * - Verde: < 70%
+ * - Amarillo: 70-90%
+ * - Rojo: > 90%
+ */
+
+class ContextBar extends HTMLElement {
+    static get observedAttributes() {
+        return ['current', 'max'];
+    }
+
+    constructor() {
+        super();
+        this._current = 0;
+        this._max = 0;
+    }
+
+    connectedCallback() {
+        this.render();
+        this._updateDisplay();
+    }
+
+    attributeChangedCallback(name, oldValue, newValue) {
+        if (oldValue === newValue) return;
+        
+        if (name === 'current') {
+            this._current = parseInt(newValue) || 0;
+        }
+        if (name === 'max') {
+            this._max = parseInt(newValue) || 0;
+        }
+        
+        this._updateDisplay();
+    }
+
+    render() {
+        this.innerHTML = `
+            <div class="w-full">
+                <div class="flex items-center justify-between text-xs text-gray-600 mb-1">
+                    <span>Ventana de contexto</span>
+                    <span data-ref="stats" class="font-mono">0 / 0</span>
+                </div>
+                <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
+                    <div 
+                        data-ref="bar" 
+                        class="h-full bg-green-500 transition-all duration-300" 
+                        style="width: 0%"
+                    ></div>
+                </div>
+            </div>
+        `;
+    }
+
+    _updateDisplay() {
+        const stats = this.querySelector('[data-ref="stats"]');
+        const bar = this.querySelector('[data-ref="bar"]');
+        
+        if (!stats || !bar) return;
+
+        // Formatear números con separador de miles
+        const currentFormatted = this._current.toLocaleString();
+        const maxFormatted = this._max.toLocaleString();
+        stats.textContent = `${currentFormatted} / ${maxFormatted}`;
+
+        // Calcular porcentaje
+        const percentage = this._max > 0 ? (this._current / this._max) * 100 : 0;
+        bar.style.width = `${Math.min(percentage, 100)}%`;
+
+        // Actualizar color según porcentaje
+        bar.classList.remove('bg-green-500', 'bg-yellow-500', 'bg-red-500');
+        
+        if (percentage < 70) {
+            bar.classList.add('bg-green-500');
+        } else if (percentage < 90) {
+            bar.classList.add('bg-yellow-500');
+        } else {
+            bar.classList.add('bg-red-500');
+        }
+    }
+
+    // API Pública
+    update(current, max) {
+        this._current = current;
+        this._max = max;
+        this._updateDisplay();
+    }
+
+    getPercentage() {
+        return this._max > 0 ? (this._current / this._max) * 100 : 0;
+    }
+}
+
+if (!customElements.get('context-bar')) {
+    customElements.define('context-bar', ContextBar);
+}
+
+export { ContextBar };
diff --git a/autocode/web/tests/components/chat.test.html b/autocode/web/tests/components/chat.test.html
new file mode 100644
index 0000000..8e55ef4
--- /dev/null
+++ b/autocode/web/tests/components/chat.test.html
@@ -0,0 +1,561 @@
+<!DOCTYPE html>
+<html lang="es">
+<head>
+    <meta charset="UTF-8">
+    <meta name="viewport" content="width=device-width, initial-scale=1.0">
+    <title>Chat Components - Unit Tests</title>
+    <script src="https://cdn.tailwindcss.com"></script>
+    <style>
+        .test-container { margin: 20px 0; padding: 10px; border: 1px solid #ddd; border-radius: 8px; }
+    </style>
+</head>
+<body class="p-8 bg-gray-100 min-h-screen">
+    <div class="flex items-center gap-4 mb-2">
+        <a href="/tests" class="text-indigo-600 hover:text-indigo-800">← Tests</a>
+        <h1 class="text-3xl font-bold">🧪 Chat Components - Unit Tests</h1>
+    </div>
+    <p class="text-gray-600 mb-6">TDD: Los tests definen el comportamiento esperado de cada componente.</p>
+    
+    <div id="summary" class="mb-6 p-4 bg-white rounded-lg shadow"></div>
+    <div id="results" class="space-y-2"></div>
+    
+    <!-- Contenedores para tests visuales -->
+    <div class="mt-8 grid grid-cols-2 gap-4">
+        <div class="test-container">
+            <h3 class="font-bold mb-2">ChatInput Test Area</h3>
+            <div id="test-chat-input"></div>
+        </div>
+        <div class="test-container">
+            <h3 class="font-bold mb-2">ChatMessages Test Area</h3>
+            <div id="test-chat-messages"></div>
+        </div>
+        <div class="test-container">
+            <h3 class="font-bold mb-2">ContextBar Test Area</h3>
+            <div id="test-context-bar"></div>
+        </div>
+        <div class="test-container">
+            <h3 class="font-bold mb-2">ChatWindow Test Area</h3>
+            <div id="test-chat-window" class="h-64"></div>
+        </div>
+    </div>
+
+    <script type="module">
+        // ============================================
+        // TEST RUNNER
+        // ============================================
+        const results = document.getElementById('results');
+        const summary = document.getElementById('summary');
+        let passed = 0, failed = 0, pending = 0;
+        const testResults = [];
+
+        function test(name, fn) {
+            testResults.push({ name, fn });
+        }
+
+        function assertEqual(actual, expected, msg = '') {
+            if (actual !== expected) {
+                throw new Error(`Expected "${expected}", got "${actual}". ${msg}`);
+            }
+        }
+
+        function assertTrue(value, msg = '') {
+            if (!value) throw new Error(`Expected truthy value. ${msg}`);
+        }
+
+        function assertFalse(value, msg = '') {
+            if (value) throw new Error(`Expected falsy value. ${msg}`);
+        }
+
+        async function runTests() {
+            for (const { name, fn } of testResults) {
+                try {
+                    await fn();
+                    results.innerHTML += `<div class="p-2 bg-green-100 text-green-800 rounded flex items-center gap-2">
+                        <span class="text-lg">✅</span> <span class="font-medium">${name}</span>
+                    </div>`;
+                    passed++;
+                } catch (e) {
+                    if (e.message === 'PENDING') {
+                        results.innerHTML += `<div class="p-2 bg-yellow-100 text-yellow-800 rounded flex items-center gap-2">
+                            <span class="text-lg">⏳</span> <span class="font-medium">${name}</span> <span class="text-sm">(pendiente)</span>
+                        </div>`;
+                        pending++;
+                    } else {
+                        results.innerHTML += `<div class="p-2 bg-red-100 text-red-800 rounded">
+                            <div class="flex items-center gap-2">
+                                <span class="text-lg">❌</span> <span class="font-medium">${name}</span>
+                            </div>
+                            <div class="text-sm mt-1 ml-6">${e.message}</div>
+                        </div>`;
+                        failed++;
+                    }
+                }
+            }
+            
+            const total = passed + failed + pending;
+            summary.innerHTML = `
+                <div class="flex gap-6 items-center">
+                    <span class="text-2xl font-bold">${total} tests</span>
+                    <span class="text-green-600 font-medium">✅ ${passed} passed</span>
+                    <span class="text-red-600 font-medium">❌ ${failed} failed</span>
+                    <span class="text-yellow-600 font-medium">⏳ ${pending} pending</span>
+                </div>
+            `;
+        }
+
+        function pend() {
+            throw new Error('PENDING');
+        }
+
+        // Esperar a que los custom elements se definan
+        async function waitForElement(tagName, timeout = 2000) {
+            const start = Date.now();
+            while (!customElements.get(tagName)) {
+                if (Date.now() - start > timeout) {
+                    throw new Error(`Timeout waiting for <${tagName}> to be defined`);
+                }
+                await new Promise(r => setTimeout(r, 50));
+            }
+        }
+
+        // ============================================
+        // TESTS: chat-input
+        // ============================================
+        
+        test('ChatInput: se registra como custom element', async () => {
+            await waitForElement('chat-input');
+            assertTrue(customElements.get('chat-input'));
+        });
+
+        test('ChatInput: renderiza input y botón', async () => {
+            await waitForElement('chat-input');
+            const el = document.createElement('chat-input');
+            document.getElementById('test-chat-input').appendChild(el);
+            
+            const input = el.querySelector('input') || el.shadowRoot?.querySelector('input');
+            const button = el.querySelector('button') || el.shadowRoot?.querySelector('button');
+            
+            assertTrue(input, 'Debe tener un input');
+            assertTrue(button, 'Debe tener un botón');
+        });
+
+        test('ChatInput: placeholder configurable via atributo', async () => {
+            await waitForElement('chat-input');
+            const el = document.createElement('chat-input');
+            el.setAttribute('placeholder', 'Test placeholder');
+            document.getElementById('test-chat-input').appendChild(el);
+            
+            const input = el.querySelector('input') || el.shadowRoot?.querySelector('input');
+            assertEqual(input.placeholder, 'Test placeholder');
+        });
+
+        test('ChatInput: emite evento submit con mensaje al hacer click', async () => {
+            await waitForElement('chat-input');
+            const el = document.createElement('chat-input');
+            document.getElementById('test-chat-input').appendChild(el);
+            
+            let receivedMessage = null;
+            el.addEventListener('submit', (e) => {
+                receivedMessage = e.detail.message;
+            });
+            
+            const input = el.querySelector('input') || el.shadowRoot?.querySelector('input');
+            const button = el.querySelector('button') || el.shadowRoot?.querySelector('button');
+            
+            input.value = 'Test message';
+            button.click();
+            
+            assertEqual(receivedMessage, 'Test message');
+        });
+
+        test('ChatInput: emite evento submit con Enter', async () => {
+            await waitForElement('chat-input');
+            const el = document.createElement('chat-input');
+            document.getElementById('test-chat-input').appendChild(el);
+            
+            let receivedMessage = null;
+            el.addEventListener('submit', (e) => {
+                receivedMessage = e.detail.message;
+            });
+            
+            const input = el.querySelector('input') || el.shadowRoot?.querySelector('input');
+            input.value = 'Enter test';
+            input.dispatchEvent(new KeyboardEvent('keypress', { key: 'Enter', bubbles: true }));
+            
+            assertEqual(receivedMessage, 'Enter test');
+        });
+
+        test('ChatInput: clear() limpia el input', async () => {
+            await waitForElement('chat-input');
+            const el = document.createElement('chat-input');
+            document.getElementById('test-chat-input').appendChild(el);
+            
+            const input = el.querySelector('input') || el.shadowRoot?.querySelector('input');
+            input.value = 'Some text';
+            
+            el.clear();
+            assertEqual(input.value, '');
+        });
+
+        test('ChatInput: focus() enfoca el input', async () => {
+            await waitForElement('chat-input');
+            const el = document.createElement('chat-input');
+            document.getElementById('test-chat-input').appendChild(el);
+            
+            el.focus();
+            const input = el.querySelector('input') || el.shadowRoot?.querySelector('input');
+            assertEqual(document.activeElement, input);
+        });
+
+        test('ChatInput: disabled desactiva input y botón', async () => {
+            await waitForElement('chat-input');
+            const el = document.createElement('chat-input');
+            el.setAttribute('disabled', '');
+            document.getElementById('test-chat-input').appendChild(el);
+            
+            const input = el.querySelector('input') || el.shadowRoot?.querySelector('input');
+            const button = el.querySelector('button') || el.shadowRoot?.querySelector('button');
+            
+            assertTrue(input.disabled, 'Input debe estar disabled');
+            assertTrue(button.disabled, 'Botón debe estar disabled');
+        });
+
+        // ============================================
+        // TESTS: chat-messages
+        // ============================================
+        
+        test('ChatMessages: se registra como custom element', async () => {
+            await waitForElement('chat-messages');
+            assertTrue(customElements.get('chat-messages'));
+        });
+
+        test('ChatMessages: addMessage() añade mensaje de usuario', async () => {
+            await waitForElement('chat-messages');
+            const el = document.createElement('chat-messages');
+            document.getElementById('test-chat-messages').appendChild(el);
+            
+            el.addMessage('user', 'Hola mundo');
+            
+            const messages = el.querySelectorAll('[data-role="user"]');
+            assertEqual(messages.length, 1);
+            assertTrue(messages[0].textContent.includes('Hola mundo'));
+        });
+
+        test('ChatMessages: addMessage() añade mensaje de asistente', async () => {
+            await waitForElement('chat-messages');
+            const el = document.createElement('chat-messages');
+            document.getElementById('test-chat-messages').appendChild(el);
+            
+            el.addMessage('assistant', 'Respuesta AI');
+            
+            const messages = el.querySelectorAll('[data-role="assistant"]');
+            assertEqual(messages.length, 1);
+            assertTrue(messages[0].textContent.includes('Respuesta AI'));
+        });
+
+        test('ChatMessages: addMessage() añade mensaje de error', async () => {
+            await waitForElement('chat-messages');
+            const el = document.createElement('chat-messages');
+            document.getElementById('test-chat-messages').appendChild(el);
+            
+            el.addMessage('error', 'Algo salió mal');
+            
+            const messages = el.querySelectorAll('[data-role="error"]');
+            assertEqual(messages.length, 1);
+        });
+
+        test('ChatMessages: clear() elimina todos los mensajes', async () => {
+            await waitForElement('chat-messages');
+            const el = document.createElement('chat-messages');
+            document.getElementById('test-chat-messages').appendChild(el);
+            
+            el.addMessage('user', 'Mensaje 1');
+            el.addMessage('assistant', 'Mensaje 2');
+            el.clear();
+            
+            const messages = el.querySelectorAll('[data-role]');
+            assertEqual(messages.length, 0);
+        });
+
+        test('ChatMessages: auto-scroll al añadir mensaje', async () => {
+            await waitForElement('chat-messages');
+            const el = document.createElement('chat-messages');
+            el.style.height = '100px';
+            el.style.overflow = 'auto';
+            document.getElementById('test-chat-messages').appendChild(el);
+            
+            // El contenedor interno es el que tiene scroll
+            const container = el.querySelector('[data-ref="container"]');
+            if (container) {
+                container.style.height = '100px';
+                container.style.overflow = 'auto';
+            }
+            
+            // Añadir varios mensajes para forzar scroll
+            for (let i = 0; i < 10; i++) {
+                el.addMessage('user', `Mensaje largo ${i} que ocupa espacio`);
+            }
+            
+            // Esperar que requestAnimationFrame procese el scroll
+            await new Promise(r => setTimeout(r, 150));
+            
+            // Verificar que hay contenido con scroll (scrollHeight > clientHeight)
+            const scrollContainer = container || el;
+            assertTrue(scrollContainer.scrollHeight > scrollContainer.clientHeight, 'Debe tener contenido scrolleable');
+        });
+
+        // ============================================
+        // TESTS: context-bar
+        // ============================================
+        
+        test('ContextBar: se registra como custom element', async () => {
+            await waitForElement('context-bar');
+            assertTrue(customElements.get('context-bar'));
+        });
+
+        test('ContextBar: muestra current/max correctamente', async () => {
+            await waitForElement('context-bar');
+            const el = document.createElement('context-bar');
+            el.setAttribute('current', '5000');
+            el.setAttribute('max', '10000');
+            document.getElementById('test-context-bar').appendChild(el);
+            
+            const stats = el.querySelector('[data-ref="stats"]') || el.shadowRoot?.querySelector('[data-ref="stats"]');
+            // Verificar formato "X / Y" (independiente del locale para separadores de miles)
+            assertTrue(stats.textContent.includes('/'), 'Debe mostrar formato current / max');
+            assertTrue(stats.textContent.includes('5'), 'Debe contener el valor 5000');
+            assertTrue(stats.textContent.includes('10'), 'Debe contener el valor 10000');
+        });
+
+        test('ContextBar: barra verde cuando < 70%', async () => {
+            await waitForElement('context-bar');
+            const el = document.createElement('context-bar');
+            el.setAttribute('current', '3000');
+            el.setAttribute('max', '10000');
+            document.getElementById('test-context-bar').appendChild(el);
+            
+            const bar = el.querySelector('[data-ref="bar"]') || el.shadowRoot?.querySelector('[data-ref="bar"]');
+            assertTrue(bar.classList.contains('bg-green-500'), 'Debe ser verde bajo 70%');
+        });
+
+        test('ContextBar: barra amarilla cuando 70-90%', async () => {
+            await waitForElement('context-bar');
+            const el = document.createElement('context-bar');
+            el.setAttribute('current', '8000');
+            el.setAttribute('max', '10000');
+            document.getElementById('test-context-bar').appendChild(el);
+            
+            const bar = el.querySelector('[data-ref="bar"]') || el.shadowRoot?.querySelector('[data-ref="bar"]');
+            assertTrue(bar.classList.contains('bg-yellow-500'), 'Debe ser amarillo entre 70-90%');
+        });
+
+        test('ContextBar: barra roja cuando > 90%', async () => {
+            await waitForElement('context-bar');
+            const el = document.createElement('context-bar');
+            el.setAttribute('current', '9500');
+            el.setAttribute('max', '10000');
+            document.getElementById('test-context-bar').appendChild(el);
+            
+            const bar = el.querySelector('[data-ref="bar"]') || el.shadowRoot?.querySelector('[data-ref="bar"]');
+            assertTrue(bar.classList.contains('bg-red-500'), 'Debe ser rojo sobre 90%');
+        });
+
+        test('ContextBar: actualiza al cambiar atributos', async () => {
+            await waitForElement('context-bar');
+            const el = document.createElement('context-bar');
+            el.setAttribute('current', '1000');
+            el.setAttribute('max', '10000');
+            document.getElementById('test-context-bar').appendChild(el);
+            
+            el.setAttribute('current', '9000');
+            
+            await new Promise(r => setTimeout(r, 50)); // Esperar actualización
+            const bar = el.querySelector('[data-ref="bar"]') || el.shadowRoot?.querySelector('[data-ref="bar"]');
+            assertTrue(bar.classList.contains('bg-yellow-500') || bar.classList.contains('bg-red-500'));
+        });
+
+        // ============================================
+        // TESTS: chat-window (usa Shadow DOM)
+        // ============================================
+        
+        test('ChatWindow: se registra como custom element', async () => {
+            await waitForElement('chat-window');
+            assertTrue(customElements.get('chat-window'));
+        });
+
+        test('ChatWindow: tiene shadowRoot', async () => {
+            await waitForElement('chat-window');
+            const el = document.createElement('chat-window');
+            document.getElementById('test-chat-window').appendChild(el);
+            
+            assertTrue(el.shadowRoot, 'Debe tener shadowRoot');
+        });
+
+        test('ChatWindow: toggle abre/cierra ventana', async () => {
+            await waitForElement('chat-window');
+            const el = document.createElement('chat-window');
+            document.getElementById('test-chat-window').appendChild(el);
+            
+            const panel = el.shadowRoot.querySelector('[data-ref="panel"]');
+            
+            assertTrue(panel.classList.contains('hidden'), 'Debe empezar cerrado');
+            
+            el.toggle();
+            assertFalse(panel.classList.contains('hidden'), 'Debe abrirse con toggle');
+            
+            el.toggle();
+            assertTrue(panel.classList.contains('hidden'), 'Debe cerrarse con toggle');
+        });
+
+        test('ChatWindow: open/close métodos funcionan', async () => {
+            await waitForElement('chat-window');
+            const el = document.createElement('chat-window');
+            document.getElementById('test-chat-window').appendChild(el);
+            
+            const panel = el.shadowRoot.querySelector('[data-ref="panel"]');
+            
+            el.open();
+            assertFalse(panel.classList.contains('hidden'), 'open() debe abrir');
+            
+            el.close();
+            assertTrue(panel.classList.contains('hidden'), 'close() debe cerrar');
+        });
+
+        test('ChatWindow: emite evento close al cerrar', async () => {
+            await waitForElement('chat-window');
+            const el = document.createElement('chat-window');
+            document.getElementById('test-chat-window').appendChild(el);
+            
+            let closeEmitted = false;
+            el.addEventListener('close', () => closeEmitted = true);
+            
+            el.open();
+            el.close();
+            
+            assertTrue(closeEmitted, 'Debe emitir evento close');
+        });
+
+        test('ChatWindow: title configurable via atributo', async () => {
+            await waitForElement('chat-window');
+            const el = document.createElement('chat-window');
+            el.setAttribute('title', 'Mi Chat');
+            document.getElementById('test-chat-window').appendChild(el);
+            
+            const title = el.shadowRoot.querySelector('[data-ref="title"]');
+            assertTrue(title.textContent.includes('Mi Chat'));
+        });
+
+        test('ChatWindow: acepta elementos hijos con atributos slot', async () => {
+            await waitForElement('chat-window');
+            const el = document.createElement('chat-window');
+            el.innerHTML = `
+                <span slot="header-actions">Custom Action</span>
+                <div slot="content">Custom Content</div>
+                <div slot="footer">Custom Footer</div>
+            `;
+            document.getElementById('test-chat-window').appendChild(el);
+            
+            // En Light DOM, los elementos con slot existen como hijos del host
+            assertTrue(el.querySelector('[slot="content"]'), 'Debe contener elemento con slot content');
+            assertTrue(el.querySelector('[slot="header-actions"]'), 'Debe contener elemento con slot header-actions');
+            assertTrue(el.querySelector('[slot="footer"]'), 'Debe contener elemento con slot footer');
+        });
+
+        // ============================================
+        // TESTS: chat-window con contenido slotted
+        // ============================================
+        
+        test('ChatWindow: preserva contenido slotted después de render', async () => {
+            await waitForElement('chat-window');
+            const el = document.createElement('chat-window');
+            
+            // Simular lo que hace autocode-chat: poner contenido con slots
+            el.innerHTML = `
+                <button slot="header-actions">Test Action</button>
+                <div slot="content" data-test="content">Content Area</div>
+                <div slot="footer" data-test="footer">
+                    <input type="text" placeholder="Test input">
+                </div>
+            `;
+            
+            document.getElementById('test-chat-window').appendChild(el);
+            
+            // Esperar a que connectedCallback termine
+            await new Promise(r => setTimeout(r, 50));
+            
+            // El contenido slotted debe existir y ser accesible
+            const footerContent = el.querySelector('[data-test="footer"]');
+            const inputInFooter = el.querySelector('[slot="footer"] input');
+            
+            assertTrue(footerContent, 'El footer slotted debe existir después del render');
+            assertTrue(inputInFooter, 'El input dentro del footer slot debe existir');
+        });
+
+        test('ChatWindow: slots proyectan contenido correctamente', async () => {
+            await waitForElement('chat-window');
+            const el = document.createElement('chat-window');
+            el.innerHTML = `
+                <span slot="header-actions">Custom Button</span>
+                <chat-messages slot="content"></chat-messages>
+                <div slot="footer">
+                    <chat-input placeholder="Test"></chat-input>
+                </div>
+            `;
+            
+            document.getElementById('test-chat-window').appendChild(el);
+            el.open();
+            
+            await new Promise(r => setTimeout(r, 50));
+            
+            // Verificar que chat-input está visible y funcional
+            const chatInput = el.querySelector('chat-input');
+            assertTrue(chatInput, 'chat-input debe existir en el slot footer');
+            
+            // Verificar que el input interno existe
+            const input = chatInput?.querySelector('input');
+            assertTrue(input, 'El input interno de chat-input debe existir');
+        });
+
+        // ============================================
+        // NOTA: Tests de autocode-chat están en tests/e2e/
+        // porque requieren el servidor corriendo (auto-chat 
+        // es generado dinámicamente por auto-element-generator)
+        // ============================================
+
+        // ============================================
+        // IMPORTAR COMPONENTES Y EJECUTAR TESTS
+        // ============================================
+        
+        // Importar componentes desde rutas absolutas
+        try {
+            await import('/elements/chat/chat-input.js');
+        } catch (e) {
+            console.warn('chat-input.js no encontrado:', e.message);
+        }
+        
+        try {
+            await import('/elements/chat/chat-messages.js');
+        } catch (e) {
+            console.warn('chat-messages.js no encontrado:', e.message);
+        }
+        
+        try {
+            await import('/elements/chat/context-bar.js');
+        } catch (e) {
+            console.warn('context-bar.js no encontrado:', e.message);
+        }
+        
+        try {
+            await import('/elements/chat/chat-window.js');
+        } catch (e) {
+            console.warn('chat-window.js no encontrado:', e.message);
+        }
+        
+        // autocode-chat.js no se importa aquí porque depende de auto-chat
+        // que es generado por auto-element-generator cuando hay servidor
+
+        // Ejecutar todos los tests
+        await runTests();
+    </script>
+</body>
+</html>
diff --git a/autocode/web/tests/index.html b/autocode/web/tests/index.html
new file mode 100644
index 0000000..7395b9d
--- /dev/null
+++ b/autocode/web/tests/index.html
@@ -0,0 +1,120 @@
+<!DOCTYPE html>
+<html lang="es">
+<head>
+    <meta charset="UTF-8">
+    <meta name="viewport" content="width=device-width, initial-scale=1.0">
+    <title>🧪 Autocode - Test Dashboard</title>
+    <script src="https://cdn.tailwindcss.com"></script>
+</head>
+<body class="bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
+    <div class="max-w-4xl mx-auto p-8">
+        <!-- Header -->
+        <div class="text-center mb-12">
+            <h1 class="text-4xl font-bold text-gray-800 mb-2">🧪 Test Dashboard</h1>
+            <p class="text-gray-600">Hub central para todos los tests del proyecto Autocode</p>
+            <a href="/" class="inline-block mt-4 text-indigo-600 hover:text-indigo-800 text-sm">
+                ← Volver a la app
+            </a>
+        </div>
+
+        <!-- Test Suites Grid -->
+        <div class="grid gap-6 md:grid-cols-2">
+            
+            <!-- Unit Tests: Chat Components -->
+            <a href="/tests/components/chat.test.html" 
+               class="block p-6 bg-white rounded-2xl shadow-lg hover:shadow-xl transition-shadow border border-gray-100 group">
+                <div class="flex items-start gap-4">
+                    <div class="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
+                        🧩
+                    </div>
+                    <div class="flex-1">
+                        <h2 class="text-xl font-bold text-gray-800 mb-1">Chat Components</h2>
+                        <p class="text-gray-500 text-sm mb-3">Tests unitarios de web components</p>
+                        <div class="flex gap-2 flex-wrap">
+                            <span class="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">chat-input</span>
+                            <span class="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">chat-messages</span>
+                            <span class="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">chat-window</span>
+                            <span class="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">context-bar</span>
+                        </div>
+                    </div>
+                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-300 group-hover:text-indigo-500 transition-colors" viewBox="0 0 20 20" fill="currentColor">
+                        <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
+                    </svg>
+                </div>
+            </a>
+
+            <!-- Integration Tests (placeholder) -->
+            <div class="p-6 bg-white rounded-2xl shadow-lg border border-gray-100 opacity-60">
+                <div class="flex items-start gap-4">
+                    <div class="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center text-2xl">
+                        🔗
+                    </div>
+                    <div class="flex-1">
+                        <h2 class="text-xl font-bold text-gray-800 mb-1">Integration Tests</h2>
+                        <p class="text-gray-500 text-sm mb-3">Tests de integración (requieren servidor)</p>
+                        <div class="flex gap-2 flex-wrap">
+                            <span class="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs">⏳ Próximamente</span>
+                        </div>
+                    </div>
+                </div>
+            </div>
+
+            <!-- E2E Tests Info -->
+            <div class="p-6 bg-white rounded-2xl shadow-lg border border-gray-100">
+                <div class="flex items-start gap-4">
+                    <div class="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center text-2xl">
+                        🎭
+                    </div>
+                    <div class="flex-1">
+                        <h2 class="text-xl font-bold text-gray-800 mb-1">E2E Tests (Playwright)</h2>
+                        <p class="text-gray-500 text-sm mb-3">Tests automatizados con Playwright</p>
+                        <div class="p-3 bg-gray-50 rounded-lg">
+                            <code class="text-xs text-gray-600 font-mono">uv run pytest tests/e2e/ -v</code>
+                        </div>
+                    </div>
+                </div>
+            </div>
+
+            <!-- Python Unit Tests Info -->
+            <div class="p-6 bg-white rounded-2xl shadow-lg border border-gray-100">
+                <div class="flex items-start gap-4">
+                    <div class="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center text-2xl">
+                        🐍
+                    </div>
+                    <div class="flex-1">
+                        <h2 class="text-xl font-bold text-gray-800 mb-1">Python Tests</h2>
+                        <p class="text-gray-500 text-sm mb-3">Tests unitarios del backend</p>
+                        <div class="p-3 bg-gray-50 rounded-lg">
+                            <code class="text-xs text-gray-600 font-mono">uv run pytest tests/unit/ -v</code>
+                        </div>
+                    </div>
+                </div>
+            </div>
+        </div>
+
+        <!-- Info Section -->
+        <div class="mt-12 p-6 bg-white/50 rounded-2xl border border-gray-200">
+            <h3 class="font-bold text-gray-700 mb-3">📋 Tipos de Tests</h3>
+            <div class="grid gap-4 md:grid-cols-3 text-sm">
+                <div>
+                    <div class="font-semibold text-green-700">Unit Tests (Browser)</div>
+                    <p class="text-gray-500">Tests de componentes aislados que se ejecutan directamente en el navegador sin servidor.</p>
+                </div>
+                <div>
+                    <div class="font-semibold text-blue-700">Integration Tests</div>
+                    <p class="text-gray-500">Tests que verifican la interacción entre componentes con el servidor corriendo.</p>
+                </div>
+                <div>
+                    <div class="font-semibold text-purple-700">E2E Tests</div>
+                    <p class="text-gray-500">Tests automatizados con Playwright que simulan interacción real del usuario.</p>
+                </div>
+            </div>
+        </div>
+
+        <!-- Footer -->
+        <div class="mt-8 text-center text-gray-400 text-sm">
+            <p>Autocode Test Framework • TDD Approach</p>
+        </div>
+    </div>
+</body>
+</html>
diff --git a/autocode/web/views/demo.html b/autocode/web/views/demo.html
index 0e28997..c7cfb7c 100644
--- a/autocode/web/views/demo.html
+++ b/autocode/web/views/demo.html
@@ -9,7 +9,7 @@
     <script src="https://cdn.tailwindcss.com"></script>
     
     <!-- Custom Elements -->
-    <script type="module" src="/elements/chat-element.js"></script>
+    <script type="module" src="/elements/chat/autocode-chat.js"></script>
     <script type="module" src="/elements/auto-element-generator.js"></script>
 
     <style>
diff --git a/autocode/web/views/functions.html b/autocode/web/views/functions.html
index c8e0cd6..eeb51ea 100644
--- a/autocode/web/views/functions.html
+++ b/autocode/web/views/functions.html
@@ -7,7 +7,7 @@
     <script src="https://cdn.tailwindcss.com"></script>
     
     <!-- Custom Elements -->
-    <script type="module" src="/elements/chat-element.js"></script>
+    <script type="module" src="/elements/chat/autocode-chat.js"></script>
     <script type="module" src="/elements/auto-element-generator.js"></script>
 </head>
 <body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
diff --git a/autocode/web/views/index.html b/autocode/web/views/index.html
index 219e100..b981f0e 100644
--- a/autocode/web/views/index.html
+++ b/autocode/web/views/index.html
@@ -7,7 +7,7 @@
     <script src="https://cdn.tailwindcss.com"></script>
     
     <!-- Custom Elements -->
-    <script type="module" src="/elements/chat-element.js"></script>
+    <script type="module" src="/elements/chat/autocode-chat.js"></script>
     <script type="module" src="/elements/auto-element-generator.js"></script>
 </head>
 <body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
@@ -27,6 +27,9 @@
                 <a href="/health" class="bg-white text-green-700 ring-1 ring-green-200 hover:bg-green-50 font-semibold py-2.5 px-5 rounded-full shadow-sm hover:shadow transition text-sm">
                     💚 Health Check
                 </a>
+                <a href="/tests" class="bg-white text-purple-700 ring-1 ring-purple-200 hover:bg-purple-50 font-semibold py-2.5 px-5 rounded-full shadow-sm hover:shadow transition text-sm">
+                    🧪 Tests
+                </a>
             </div>
         </div>
 
diff --git a/tests/e2e/__init__.py b/tests/e2e/__init__.py
new file mode 100644
index 0000000..a75a850
--- /dev/null
+++ b/tests/e2e/__init__.py
@@ -0,0 +1 @@
+# Tests E2E para componentes web
diff --git a/tests/e2e/conftest.py b/tests/e2e/conftest.py
new file mode 100644
index 0000000..27ad1ff
--- /dev/null
+++ b/tests/e2e/conftest.py
@@ -0,0 +1,94 @@
+"""
+Fixtures para tests E2E con Playwright.
+
+Para ejecutar estos tests necesitas:
+1. Instalar playwright: uv add --dev playwright
+2. Instalar browsers: playwright install chromium
+3. Tener el servidor corriendo: uv run uvicorn autocode.interfaces.api:app --reload
+
+Ejecutar tests:
+    uv run pytest tests/e2e/ -v
+"""
+
+import pytest
+from typing import Generator
+import subprocess
+import time
+import os
+
+# Intentar importar playwright, si no está disponible los tests se saltarán
+try:
+    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
+    PLAYWRIGHT_AVAILABLE = True
+except ImportError:
+    PLAYWRIGHT_AVAILABLE = False
+
+
+# Skip si playwright no está instalado
+pytestmark = pytest.mark.skipif(
+    not PLAYWRIGHT_AVAILABLE,
+    reason="Playwright no está instalado. Ejecuta: uv add --dev playwright && playwright install chromium"
+)
+
+
+@pytest.fixture(scope="session")
+def browser() -> Generator[Browser, None, None]:
+    """Fixture que proporciona un browser de Playwright para toda la sesión."""
+    if not PLAYWRIGHT_AVAILABLE:
+        pytest.skip("Playwright no disponible")
+    
+    with sync_playwright() as p:
+        browser = p.chromium.launch(headless=True)
+        yield browser
+        browser.close()
+
+
+@pytest.fixture(scope="function")
+def context(browser: Browser) -> Generator[BrowserContext, None, None]:
+    """Fixture que proporciona un contexto de browser limpio por test."""
+    context = browser.new_context(
+        viewport={"width": 1280, "height": 720}
+    )
+    yield context
+    context.close()
+
+
+@pytest.fixture(scope="function")
+def page(context: BrowserContext) -> Generator[Page, None, None]:
+    """Fixture que proporciona una página limpia por test."""
+    page = context.new_page()
+    yield page
+    page.close()
+
+
+@pytest.fixture(scope="session")
+def base_url() -> str:
+    """URL base del servidor de desarrollo."""
+    return os.environ.get("TEST_BASE_URL", "http://localhost:8000")
+
+
+@pytest.fixture(scope="function")
+def chat_page(page: Page, base_url: str) -> Page:
+    """Fixture que navega a la página principal con el chat."""
+    page.goto(f"{base_url}/")
+    # Esperar a que los custom elements estén definidos
+    page.wait_for_function("""
+        () => customElements.get('autocode-chat') !== undefined
+    """, timeout=10000)
+    return page
+
+
+@pytest.fixture(scope="function")
+def demo_page(page: Page, base_url: str) -> Page:
+    """Fixture que navega a la página de demo."""
+    page.goto(f"{base_url}/demo")
+    page.wait_for_load_state("networkidle")
+    return page
+
+
+@pytest.fixture(scope="function")
+def test_page(page: Page, base_url: str) -> Page:
+    """Fixture que navega a la página de tests de componentes."""
+    page.goto(f"{base_url}/elements/chat/tests.html")
+    page.wait_for_load_state("networkidle")
+    return page
diff --git a/tests/e2e/test_chat_components.py b/tests/e2e/test_chat_components.py
new file mode 100644
index 0000000..a718c8d
--- /dev/null
+++ b/tests/e2e/test_chat_components.py
@@ -0,0 +1,209 @@
+"""
+Tests E2E para los componentes del chat.
+
+Ejecutar con:
+    uv run pytest tests/e2e/test_chat_components.py -v
+
+Requiere:
+    - Servidor corriendo: uv run uvicorn autocode.interfaces.api:app --reload
+    - Playwright instalado: uv add --dev playwright && playwright install chromium
+"""
+
+import pytest
+import re
+
+# Importar solo si playwright está disponible
+try:
+    from playwright.sync_api import Page, expect
+    PLAYWRIGHT_AVAILABLE = True
+except ImportError:
+    PLAYWRIGHT_AVAILABLE = False
+
+
+pytestmark = pytest.mark.skipif(
+    not PLAYWRIGHT_AVAILABLE,
+    reason="Playwright no está instalado"
+)
+
+
+class TestChatWindow:
+    """Tests para el componente chat-window."""
+
+    def test_toggle_button_visible(self, chat_page: Page):
+        """El botón de toggle debe ser visible al cargar la página."""
+        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
+        expect(toggle_btn).to_be_visible()
+
+    def test_chat_opens_on_toggle_click(self, chat_page: Page):
+        """El chat debe abrirse al hacer click en el botón de toggle."""
+        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
+        panel = chat_page.locator('chat-window [data-ref="panel"]')
+        
+        # Inicialmente oculto
+        expect(panel).to_have_class(re.compile(r"hidden"))
+        
+        # Click para abrir
+        toggle_btn.click()
+        expect(panel).not_to_have_class(re.compile(r"hidden"))
+
+    def test_chat_closes_on_close_button(self, chat_page: Page):
+        """El chat debe cerrarse al hacer click en el botón de cerrar."""
+        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
+        close_btn = chat_page.locator('chat-window [data-ref="closeBtn"]')
+        panel = chat_page.locator('chat-window [data-ref="panel"]')
+        
+        # Abrir primero
+        toggle_btn.click()
+        expect(panel).not_to_have_class(re.compile(r"hidden"))
+        
+        # Cerrar
+        close_btn.click()
+        expect(panel).to_have_class(re.compile(r"hidden"))
+
+    def test_drag_window(self, chat_page: Page):
+        """La ventana debe poder arrastrarse."""
+        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
+        toggle_btn.click()
+        
+        window = chat_page.locator('chat-window [data-ref="window"]')
+        drag_handle = chat_page.locator('chat-window [data-ref="dragHandle"]')
+        
+        # Obtener posición inicial
+        initial_box = window.bounding_box()
+        
+        # Arrastrar
+        drag_handle.drag_to(chat_page.locator('body'), 
+                          source_position={"x": 50, "y": 20},
+                          target_position={"x": 200, "y": 200})
+        
+        # Verificar que se movió
+        final_box = window.bounding_box()
+        assert final_box["x"] != initial_box["x"] or final_box["y"] != initial_box["y"]
+
+
+class TestChatInput:
+    """Tests para el componente chat-input."""
+
+    def test_input_visible_when_chat_open(self, chat_page: Page):
+        """El input debe ser visible cuando el chat está abierto."""
+        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
+        toggle_btn.click()
+        
+        chat_input = chat_page.locator('chat-input input')
+        expect(chat_input).to_be_visible()
+
+    def test_send_button_visible(self, chat_page: Page):
+        """El botón de enviar debe ser visible."""
+        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
+        toggle_btn.click()
+        
+        send_btn = chat_page.locator('chat-input button')
+        expect(send_btn).to_be_visible()
+        expect(send_btn).to_contain_text('Enviar')
+
+
+class TestChatMessages:
+    """Tests para el componente chat-messages."""
+
+    def test_empty_state_visible_initially(self, chat_page: Page):
+        """El estado vacío debe mostrarse inicialmente."""
+        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
+        toggle_btn.click()
+        
+        empty_state = chat_page.locator('chat-messages [data-ref="emptyState"]')
+        expect(empty_state).to_be_visible()
+        expect(empty_state).to_contain_text('Inicia una conversación')
+
+
+class TestContextBar:
+    """Tests para el componente context-bar."""
+
+    def test_context_bar_visible(self, chat_page: Page):
+        """La barra de contexto debe ser visible."""
+        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
+        toggle_btn.click()
+        
+        context_bar = chat_page.locator('context-bar')
+        expect(context_bar).to_be_visible()
+
+    def test_context_bar_shows_stats(self, chat_page: Page):
+        """La barra de contexto debe mostrar estadísticas."""
+        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
+        toggle_btn.click()
+        
+        stats = chat_page.locator('context-bar [data-ref="stats"]')
+        expect(stats).to_be_visible()
+        expect(stats).to_contain_text('/')
+
+
+class TestChatIntegration:
+    """Tests de integración del chat completo."""
+
+    def test_new_chat_button_clears_messages(self, chat_page: Page):
+        """El botón 'Nueva' debe limpiar los mensajes."""
+        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
+        toggle_btn.click()
+        
+        new_btn = chat_page.locator('[data-ref="newChatBtn"]')
+        expect(new_btn).to_be_visible()
+        
+        # Click en nueva conversación
+        new_btn.click()
+        
+        # Verificar que aparece el empty state
+        empty_state = chat_page.locator('chat-messages [data-ref="emptyState"]')
+        expect(empty_state).to_be_visible()
+
+    def test_full_chat_flow(self, chat_page: Page):
+        """Test del flujo completo de envío de mensaje."""
+        # Abrir chat
+        toggle_btn = chat_page.locator('chat-window [data-ref="toggleBtn"]')
+        toggle_btn.click()
+        
+        # Escribir mensaje
+        chat_input = chat_page.locator('chat-input input')
+        chat_input.fill('Hola, esto es un test')
+        
+        # El empty state debería desaparecer después de enviar
+        send_btn = chat_page.locator('chat-input button')
+        send_btn.click()
+        
+        # Esperar a que aparezca el mensaje del usuario
+        user_message = chat_page.locator('chat-messages [data-role="user"]')
+        expect(user_message).to_be_visible(timeout=5000)
+        expect(user_message).to_contain_text('Hola, esto es un test')
+        
+        # El input debería estar vacío después de enviar
+        expect(chat_input).to_have_value('')
+
+
+class TestUnitTestsPage:
+    """Tests que verifican que los tests unitarios en tests.html pasan."""
+
+    def test_unit_tests_page_loads(self, test_page: Page):
+        """La página de tests debe cargar correctamente."""
+        title = test_page.locator('h1')
+        expect(title).to_contain_text('Chat Components')
+
+    def test_unit_tests_summary_exists(self, test_page: Page):
+        """Debe existir un resumen de tests."""
+        summary = test_page.locator('#summary')
+        # Esperar a que los tests terminen
+        test_page.wait_for_timeout(3000)
+        expect(summary).to_be_visible()
+
+    def test_no_failed_tests(self, test_page: Page):
+        """No debe haber tests fallidos (solo si los componentes existen)."""
+        # Esperar a que los tests terminen
+        test_page.wait_for_timeout(5000)
+        
+        # Contar tests fallidos
+        failed = test_page.locator('.bg-red-100')
+        failed_count = failed.count()
+        
+        # Si hay tests fallidos, obtener los mensajes para debug
+        if failed_count > 0:
+            failed_texts = []
+            for i in range(failed_count):
+                failed_texts.append(failed.nth(i).text_content())
+            pytest.fail(f"Tests fallidos: {failed_texts}")

```

