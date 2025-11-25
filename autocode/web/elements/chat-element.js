/**
 * chat-element.js
 * Web Component para el chat flotante de Autocode
 */
export class AutocodeChat extends HTMLElement {
    constructor() {
        super();
        this.conversationHistory = [];
        this.config = {
            model: 'openrouter/openai/gpt-4o',
            temperature: 0.7,
            max_tokens: 16000,
            module_type: 'ReAct',
            module_kwargs: {}
        };
    }

    connectedCallback() {
        this.render();
        this.setupEventListeners();
    }

    render() {
        this.innerHTML = `
            <!-- Botón flotante para abrir chat -->
            <button 
                id="chatToggleBtn" 
                class="fixed top-4 left-4 z-[110] bg-white text-indigo-600 rounded-full p-4 shadow-lg hover:shadow-xl ring-1 ring-black/10 transition-transform duration-300 hover:scale-105"
                aria-label="Abrir chat"
            >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
            </button>

            <!-- Panel de Chat -->
            <div id="chatPanel" class="hidden fixed inset-0 z-[100] bg-transparent pointer-events-none">
                <div 
                    id="chatWindow" 
                    class="fixed top-20 right-6 w-[92vw] md:w-[480px] lg:w-[560px] h-[70vh] bg-white rounded-2xl shadow-2xl ring-1 ring-black/10 overflow-hidden flex flex-col pointer-events-auto"
                >
                    <!-- Header con drag handle -->
                    <div 
                        id="chatDragHandle" 
                        class="bg-gradient-to-r from-indigo-600 to-violet-600 p-4 flex items-center justify-between cursor-grab select-none"
                    >
                        <div class="flex items-center gap-3">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                            </svg>
                            <h2 class="text-white font-bold text-xl">Autocode AI Chat</h2>
                        </div>
                        <div class="flex items-center gap-2">
                            <button 
                                id="newChatBtn" 
                                class="text-indigo-100 bg-white/10 hover:bg-white/20 border border-white/20 rounded-full px-3 py-1.5 text-sm font-semibold transition-colors"
                            >
                                Nueva
                            </button>
                            <button 
                                id="chatCloseBtn" 
                                class="text-white hover:bg-indigo-700 rounded-full p-2 transition-colors"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                    </div>

                    <!-- Área de Mensajes -->
                    <div 
                        id="messagesContainer" 
                        class="flex-1 overflow-y-auto p-4 bg-gradient-to-b from-gray-50 to-white space-y-3"
                    >
                        <div class="text-center text-gray-500 italic" id="emptyState">
                            Inicia una conversación... 💬
                        </div>
                    </div>

                    <!-- Área de Input -->
                    <div class="bg-white p-4 border-t border-gray-200">
                        <div class="flex gap-2">
                            <input 
                                type="text" 
                                id="messageInput" 
                                placeholder="Escribe tu mensaje..." 
                                class="flex-1 p-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                                autocomplete="off"
                            />
                            <button 
                                id="sendBtn"
                                class="bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white font-semibold px-5 rounded-xl shadow transition disabled:bg-gray-400 text-sm"
                            >
                                Enviar 🚀
                            </button>
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

                    <!-- Handle de redimensionamiento -->
                    <div 
                        id="chatResizeHandle" 
                        class="absolute bottom-2 right-2 w-4 h-4 cursor-se-resize text-indigo-300/70 hover:text-indigo-400 select-none"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 11L11 21M17 7L7 17" />
                        </svg>
                    </div>
                </div>
            </div>
        `;
    }

    setupEventListeners() {
        const chatToggleBtn = this.querySelector('#chatToggleBtn');
        const chatPanel = this.querySelector('#chatPanel');
        const chatCloseBtn = this.querySelector('#chatCloseBtn');
        const newChatBtn = this.querySelector('#newChatBtn');
        const chatWindow = this.querySelector('#chatWindow');
        const chatDragHandle = this.querySelector('#chatDragHandle');
        const chatResizeHandle = this.querySelector('#chatResizeHandle');
        const messageInput = this.querySelector('#messageInput');
        const sendBtn = this.querySelector('#sendBtn');
        const messagesContainer = this.querySelector('#messagesContainer');

        // Toggle Chat
        chatToggleBtn.addEventListener('click', () => {
            chatPanel.classList.toggle('hidden');
            if (!chatPanel.classList.contains('hidden')) {
                setTimeout(() => messageInput.focus(), 100);
            }
        });

        chatCloseBtn.addEventListener('click', () => {
            chatPanel.classList.add('hidden');
        });

        // Nueva Conversación
        newChatBtn.addEventListener('click', () => {
            this.conversationHistory = [];
            messagesContainer.innerHTML = '<div class="text-center text-gray-500 italic" id="emptyState">Inicia una conversación... 💬</div>';
            messageInput.value = '';
            this.updateContextBar(0, 0, 0);
        });

        // Drag Window
        let isDragging = false;
        let offsetX = 0, offsetY = 0;

        chatDragHandle.addEventListener('pointerdown', (e) => {
            if (e.button !== 0) return;
            isDragging = true;
            const rect = chatWindow.getBoundingClientRect();
            offsetX = e.clientX - rect.left;
            offsetY = e.clientY - rect.top;
            chatDragHandle.classList.add('cursor-grabbing');
            
            // Capture pointer events on handle
            chatDragHandle.setPointerCapture(e.pointerId);
        });

        chatDragHandle.addEventListener('pointermove', (e) => {
            if (!isDragging) return;
            let x = e.clientX - offsetX;
            let y = e.clientY - offsetY;
            const maxX = window.innerWidth - chatWindow.offsetWidth;
            const maxY = window.innerHeight - chatWindow.offsetHeight;
            x = Math.min(Math.max(0, x), maxX);
            y = Math.min(Math.max(0, y), maxY);
            chatWindow.style.left = `${x}px`;
            chatWindow.style.top = `${y}px`;
            chatWindow.style.right = 'auto';
            chatWindow.style.bottom = 'auto';
        });

        chatDragHandle.addEventListener('pointerup', (e) => {
            if (!isDragging) return;
            isDragging = false;
            chatDragHandle.classList.remove('cursor-grabbing');
            chatDragHandle.releasePointerCapture(e.pointerId);
        });

        // Resize Window
        let isResizing = false;
        let startX = 0, startY = 0, startW = 0, startH = 0;

        chatResizeHandle.addEventListener('pointerdown', (e) => {
            if (e.button !== 0) return;
            const rect = chatWindow.getBoundingClientRect();
            // Ensure width/height are set in styles
            chatWindow.style.width = `${rect.width}px`;
            chatWindow.style.height = `${rect.height}px`;
            startX = e.clientX;
            startY = e.clientY;
            startW = rect.width;
            startH = rect.height;
            isResizing = true;
            chatResizeHandle.setPointerCapture(e.pointerId);
        });

        chatResizeHandle.addEventListener('pointermove', (e) => {
            if (!isResizing) return;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            let newW = Math.max(320, startW + dx);
            let newH = Math.max(400, startH + dy);
            chatWindow.style.width = `${newW}px`;
            chatWindow.style.height = `${newH}px`;
        });

        chatResizeHandle.addEventListener('pointerup', (e) => {
            isResizing = false;
            chatResizeHandle.releasePointerCapture(e.pointerId);
        });

        // Enviar Mensaje
        sendBtn.addEventListener('click', () => this.sendMessage());
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Debounced context update
        let debounceTimer;
        messageInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => this.updateContext(), 300);
        });
    }

    async sendMessage() {
        const messageInput = this.querySelector('#messageInput');
        const sendBtn = this.querySelector('#sendBtn');
        const message = messageInput.value.trim();

        if (!message) return;

        this.addMessage('user', message);
        messageInput.value = '';
        messageInput.disabled = true;
        sendBtn.disabled = true;
        sendBtn.textContent = 'Pensando... 🤔';

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    conversation_history: this.formatHistory(),
                    model: this.config.model,
                    max_tokens: this.config.max_tokens,
                    temperature: this.config.temperature,
                    module_type: this.config.module_type,
                    module_kwargs: this.config.module_kwargs
                })
            });

            const data = await response.json();
            
            if (data.result?.response) {
                this.addMessage('assistant', data.result.response);
                this.conversationHistory.push({ role: 'user', content: message });
                this.conversationHistory.push({ role: 'assistant', content: data.result.response });
                await this.updateContext();
            } else {
                this.addMessage('error', 'Error: No se recibió respuesta');
            }
        } catch (error) {
            this.addMessage('error', `Error: ${error.message}`);
        } finally {
            messageInput.disabled = false;
            sendBtn.disabled = false;
            sendBtn.textContent = 'Enviar 🚀';
            messageInput.focus();
        }
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
        
        const label = document.createElement('div');
        label.className = 'font-bold text-sm mb-1';
        label.textContent = role === 'user' ? '👤 Tú' : role === 'error' ? '❌ Error' : '🤖 Asistente';
        
        const text = document.createElement('div');
        text.className = 'whitespace-pre-wrap break-words text-sm';
        text.textContent = content;
        
        bubble.appendChild(label);
        bubble.appendChild(text);
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
        const messageInput = this.querySelector('#messageInput');
        const messages = [...this.conversationHistory];
        const currentMsg = messageInput.value.trim();
        if (currentMsg) messages.push({ role: 'user', content: currentMsg });

        if (messages.length === 0) {
            this.updateContextBar(0, 0, 0);
            return;
        }

        try {
            const response = await fetch('/calculate_context_usage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: this.config.model, messages })
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
        
        if (percentage < 70) {
            contextBar.className = 'h-full bg-green-500 transition-all duration-300';
        } else if (percentage < 90) {
            contextBar.className = 'h-full bg-yellow-500 transition-all duration-300';
        } else {
            contextBar.className = 'h-full bg-red-500 transition-all duration-300';
        }
    }
}

customElements.define('autocode-chat', AutocodeChat);
