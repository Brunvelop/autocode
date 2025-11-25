/**
 * chat-element.js
 * Web Component para el chat flotante de Autocode
 * Extiende del elemento auto-chat generado dinámicamente
 * REFACTOR: Usa componentes y lógica de la clase base
 */

async function initChatElement() {
    await customElements.whenDefined('auto-chat');
    const AutoChatBase = customElements.get('auto-chat');

    class AutocodeChat extends AutoChatBase {
        constructor() {
            super();
            this.conversationHistory = [];
            // Referencias a inputs especiales
            this._messageInput = null;
            this._historyInput = null;
        }

        connectedCallback() {
            // Renderizamos nuestra UI personalizada
            this.render();
            // Setup events específicos del chat (drag, toggle, etc)
            this.setupChatEvents();
        }

        render() {
            this.innerHTML = '';
            
            // 1. Contenedor Principal (Floating Toggle + Chat Window)
            this.innerHTML = `
                <!-- Botón flotante -->
                <button id="chatToggleBtn" class="fixed top-4 left-4 z-[110] bg-white text-indigo-600 rounded-full p-4 shadow-lg hover:shadow-xl ring-1 ring-black/10 transition-transform duration-300 hover:scale-105">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                </button>

                <!-- Panel de Chat -->
                <div id="chatPanel" class="hidden fixed inset-0 z-[100] bg-transparent pointer-events-none">
                    <div id="chatWindow" class="fixed top-20 right-6 w-[92vw] md:w-[480px] lg:w-[560px] h-[70vh] bg-white rounded-2xl shadow-2xl ring-1 ring-black/10 overflow-hidden flex flex-col pointer-events-auto">
                        
                        <!-- Header -->
                        <div id="chatDragHandle" class="bg-gradient-to-r from-indigo-600 to-violet-600 p-4 flex items-center justify-between cursor-grab select-none">
                            <div class="flex items-center gap-3">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                                </svg>
                                <h2 class="text-white font-bold text-xl">Autocode AI Chat</h2>
                            </div>
                            <div class="flex items-center gap-2">
                                <button id="newChatBtn" class="text-indigo-100 bg-white/10 hover:bg-white/20 border border-white/20 rounded-full px-3 py-1.5 text-sm font-semibold transition-colors">Nueva</button>
                                <button id="chatCloseBtn" class="text-white hover:bg-indigo-700 rounded-full p-2 transition-colors">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>
                        </div>

                        <!-- Área de Mensajes -->
                        <div id="messagesContainer" class="flex-1 overflow-y-auto p-4 bg-gradient-to-b from-gray-50 to-white space-y-3">
                            <div class="text-center text-gray-500 italic" id="emptyState">Inicia una conversación... 💬</div>
                        </div>

                        <!-- Área de Input (Footer) -->
                        <div class="bg-white p-4 border-t border-gray-200">
                            <div class="flex gap-2" id="inputArea">
                                <!-- Aquí inyectaremos el input 'message' y el botón 'execute' -->
                            </div>
                            <!-- Context bar -->
                            <div class="mt-3">
                                <div class="flex items-center justify-between text-xs text-gray-600 mb-1">
                                    <span>Ventana de contexto</span>
                                    <span id="contextStats" class="font-mono">0 / 0</span>
                                </div>
                                <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                                    <div id="contextBar" class="h-full bg-green-500 transition-all duration-300" style="width: 0%"></div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Contenedor oculto para otros parámetros -->
                        <div id="hiddenParams" class="hidden"></div>

                        <!-- Handle Resize -->
                        <div id="chatResizeHandle" class="absolute bottom-2 right-2 w-4 h-4 cursor-se-resize text-indigo-300/70 hover:text-indigo-400 select-none">
                            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 11L11 21M17 7L7 17" />
                            </svg>
                        </div>
                    </div>
                </div>
            `;
            
            this.injectGeneratedComponents();
        }

        injectGeneratedComponents() {
            const inputArea = this.querySelector('#inputArea');
            const hiddenParams = this.querySelector('#hiddenParams');
            
            // 1. Message Input
            const messageParam = this.funcInfo.parameters.find(p => p.name === 'message');
            if (messageParam) {
                const messageContainer = this.createParamElement(messageParam);
                
                // Personalizar el input generado para que parezca un chat
                const input = messageContainer.querySelector('input');
                if (input) {
                    input.id = 'messageInput';
                    input.placeholder = "Escribe tu mensaje...";
                    input.className = "flex-1 p-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm";
                    
                    // Eliminar label y description
                    messageContainer.querySelectorAll('label, p').forEach(el => el.remove());
                    // Eliminar clases del contenedor para que no afecten layout flex
                    messageContainer.className = "flex-1";
                    
                    inputArea.appendChild(messageContainer);
                    this._messageInput = input;
                    
                    // Bind Enter key
                    input.addEventListener('keypress', (e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            this.execute();
                        }
                    });
                }
            }

            // 2. Execute Button (Send)
            const sendBtn = this.createExecuteButton();
            sendBtn.id = 'sendBtn';
            sendBtn.textContent = 'Enviar 🚀';
            sendBtn.className = "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white font-semibold px-5 rounded-xl shadow transition disabled:bg-gray-400 text-sm";
            inputArea.appendChild(sendBtn);

            // 3. Other Params (Hidden)
            this.funcInfo.parameters.forEach(param => {
                if (param.name === 'message') return;
                
                const el = this.createParamElement(param);
                if (param.name === 'conversation_history') {
                    this._historyInput = el.querySelector('input, select, textarea');
                }
                hiddenParams.appendChild(el);
            });
        }

        async execute() {
            const userMsg = this._messageInput?.value?.trim();
            if (!userMsg) return;

            // 1. UI Optimista
            this.addMessage('user', userMsg);
            
            // 2. Ejecutar lógica del padre
            try {
                await super.execute();
                // El padre llama a showResult, que sobreescribimos
            } catch (error) {
                // El padre ya maneja el error visualmente en execute() -> showResult(error, true)
                // Nosotros sobreescribimos showResult para usar burbujas de chat
            }
        }

        // Sobreescribimos showResult para integrar con el historial del chat
        showResult(result, isError = false) {
            if (isError) {
                this.addMessage('error', result);
                return;
            }

            // result es un DspyOutput o similar. Asumimos que tiene 'response'
            const responseText = result.result?.response || result.response || 
                               (typeof result === 'string' ? result : JSON.stringify(result));

            // UI Asistente
            this.addMessage('assistant', responseText);

            // Actualizar Historial Interno
            // Necesitamos recuperar el mensaje del usuario que se acaba de enviar
            // Como execute() no limpia el input hasta el final, podemos leerlo
            // O mejor, lo guardamos antes. Pero simplifiquemos:
            // Al ser exitoso, asumimos que el último mensaje user en UI corresponde a la respuesta.
            
            // Mejor: leer del input antes de limpiar
            const userMsg = this._messageInput.value;
            
            this.conversationHistory.push({ role: 'user', content: userMsg });
            this.conversationHistory.push({ role: 'assistant', content: responseText });

            // Actualizar input oculto para la próxima llamada
            if (this._historyInput) {
                this._historyInput.value = this.formatHistory();
                this._historyInput.dispatchEvent(new Event('change'));
            }

            // Limpiar input y update context
            this._messageInput.value = '';
            this.updateContext();
        }

        // --- Lógica UI específica del Chat (Drag, Resize, Bubbles) ---

        setupChatEvents() {
            const chatToggleBtn = this.querySelector('#chatToggleBtn');
            const chatPanel = this.querySelector('#chatPanel');
            const chatCloseBtn = this.querySelector('#chatCloseBtn');
            const newChatBtn = this.querySelector('#newChatBtn');
            const chatDragHandle = this.querySelector('#chatDragHandle');
            const chatWindow = this.querySelector('#chatWindow');

            chatToggleBtn.addEventListener('click', () => {
                chatPanel.classList.toggle('hidden');
                if (!chatPanel.classList.contains('hidden')) {
                    setTimeout(() => this._messageInput?.focus(), 100);
                }
            });

            chatCloseBtn.addEventListener('click', () => chatPanel.classList.add('hidden'));

            newChatBtn.addEventListener('click', () => {
                this.conversationHistory = [];
                if (this._historyInput) {
                    this._historyInput.value = '';
                    this._historyInput.dispatchEvent(new Event('change'));
                }
                const container = this.querySelector('#messagesContainer');
                container.innerHTML = '<div class="text-center text-gray-500 italic" id="emptyState">Inicia una conversación... 💬</div>';
                this.updateContextBar(0, 0, 0);
            });

            // Drag logic simplificada
            let isDragging = false;
            let offsetX, offsetY;

            chatDragHandle.addEventListener('pointerdown', (e) => {
                isDragging = true;
                const rect = chatWindow.getBoundingClientRect();
                offsetX = e.clientX - rect.left;
                offsetY = e.clientY - rect.top;
                chatDragHandle.setPointerCapture(e.pointerId);
            });

            chatDragHandle.addEventListener('pointermove', (e) => {
                if (!isDragging) return;
                const x = Math.max(0, Math.min(e.clientX - offsetX, window.innerWidth - chatWindow.offsetWidth));
                const y = Math.max(0, Math.min(e.clientY - offsetY, window.innerHeight - chatWindow.offsetHeight));
                chatWindow.style.left = `${x}px`;
                chatWindow.style.top = `${y}px`;
            });

            chatDragHandle.addEventListener('pointerup', (e) => {
                isDragging = false;
                chatDragHandle.releasePointerCapture(e.pointerId);
            });
        }

        addMessage(role, content) {
            const messagesContainer = this.querySelector('#messagesContainer');
            const emptyState = this.querySelector('#emptyState');
            if (emptyState) emptyState.remove();

            const messageDiv = document.createElement('div');
            messageDiv.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'}`;
            
            const bubble = document.createElement('div');
            bubble.className = `max-w-[85%] rounded-2xl px-4 py-3 ${
                role === 'user' 
                    ? 'bg-indigo-600 text-white shadow-md' 
                    : role === 'error'
                    ? 'bg-red-50 text-red-800 border border-red-300'
                    : 'bg-white text-gray-800 shadow-sm border border-gray-200'
            }`;
            
            bubble.innerHTML = `
                <div class="font-bold text-sm mb-1">${role === 'user' ? '👤 Tú' : role === 'error' ? '❌ Error' : '🤖 Asistente'}</div>
                <div class="whitespace-pre-wrap break-words text-sm">${content}</div>
            `;
            
            messageDiv.appendChild(bubble);
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        formatHistory() {
            return this.conversationHistory.map(msg => 
                `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`
            ).join(' | ');
        }

        async updateContext() {
            // Reutilizamos la lógica existente de context stats
            // Podríamos intentar usar una función del registry si existiera, 
            // pero calculate_context_usage es una función registrada!
            // Podríamos llamar a this.callAPI({ model, messages }) contra esa función?
            // No, porque this.callAPI llama a /chat (la función de ESTE elemento).
            // Así que mantenemos el fetch manual aquí o creamos un nuevo auto-element para esto.
            // Mantenemos fetch manual por simplicidad.
            
            const messages = [...this.conversationHistory];
            if (this._messageInput?.value) messages.push({ role: 'user', content: this._messageInput.value });
            if (messages.length === 0) {
                this.updateContextBar(0, 0, 0);
                return;
            }

            try {
                // Aquí usamos fetch directo porque estamos llamando a OTRA función
                const model = this.funcInfo.parameters.find(p => p.name === 'model')?.default || 'openrouter/openai/gpt-4o';
                
                const response = await fetch('/calculate_context_usage', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model, messages })
                });
                
                const data = await response.json();
                const { current = 0, max = 0, percentage = 0 } = data.result || {};
                this.updateContextBar(current, max, percentage);
            } catch (error) {
                console.error('Error updating context:', error);
            }
        }

        updateContextBar(current, max, percentage) {
            const contextStats = this.querySelector('#contextStats');
            const contextBar = this.querySelector('#contextBar');
            if (!contextStats || !contextBar) return;

            contextStats.textContent = `${current.toLocaleString()} / ${max.toLocaleString()}`;
            contextBar.style.width = `${Math.min(percentage, 100)}%`;
            contextBar.className = `h-full transition-all duration-300 ${percentage < 70 ? 'bg-green-500' : percentage < 90 ? 'bg-yellow-500' : 'bg-red-500'}`;
        }
    }

    if (!customElements.get('autocode-chat')) {
        customElements.define('autocode-chat', AutocodeChat);
    }
}

initChatElement();
