/**
 * autocode-chat.js
 * Orquestador del chat que compone todos los sub-componentes
 * Hereda de auto-chat (generado por AutoElementGenerator) para reutilizar API calls
 * 
 * Composición:
 * - ChatWindow: Ventana flotante con drag/resize
 * - ChatMessages: Lista de mensajes con scroll
 * - ChatInput: Input y botón de envío
 * - ContextBar: Barra de uso de tokens
 */

// Importar sub-componentes
import './chat-input.js';
import './chat-messages.js';
import './chat-window.js';
import './context-bar.js';

async function initAutocodeChat() {
    // Esperar a que auto-chat esté definido (generado por AutoElementGenerator)
    await customElements.whenDefined('auto-chat');
    const AutoChatBase = customElements.get('auto-chat');

    class AutocodeChat extends AutoChatBase {
        constructor() {
            super();
            this.conversationHistory = [];
            this._pendingUserMessage = null; // Fix bug: capturar mensaje antes de execute
            
            // Referencias a sub-componentes
            this._window = null;
            this._messages = null;
            this._input = null;
            this._contextBar = null;
            this._historyInput = null;
        }

        connectedCallback() {
            this.render();
            this._setupComponentRefs();
            this._setupEvents();
        }

        render() {
            this.innerHTML = `
                <chat-window title="Autocode AI Chat">
                    <!-- Header actions -->
                    <button 
                        slot="header-actions"
                        data-ref="newChatBtn"
                        class="text-indigo-100 bg-white/10 hover:bg-white/20 border border-white/20 rounded-full px-3 py-1.5 text-sm font-semibold transition-colors"
                    >
                        Nueva
                    </button>
                    
                    <!-- Content: mensajes -->
                    <chat-messages slot="content" style="flex: 1;"></chat-messages>
                    
                    <!-- Footer: input y context bar -->
                    <div slot="footer" class="p-4 space-y-3">
                        <chat-input placeholder="Escribe tu mensaje..."></chat-input>
                        <context-bar current="0" max="0"></context-bar>
                    </div>
                </chat-window>
                
                <!-- Contenedor oculto para otros parámetros de la función chat -->
                <div data-ref="hiddenParams" class="hidden"></div>
            `;
        }

        _setupComponentRefs() {
            this._window = this.querySelector('chat-window');
            this._messages = this.querySelector('chat-messages');
            this._input = this.querySelector('chat-input');
            this._contextBar = this.querySelector('context-bar');
            
            // Inyectar parámetros ocultos de la función chat (model, conversation_history, etc.)
            this._injectHiddenParams();
        }

        _injectHiddenParams() {
            const hiddenParams = this.querySelector('[data-ref="hiddenParams"]');
            if (!hiddenParams || !this.funcInfo?.parameters) return;

            this.funcInfo.parameters.forEach(param => {
                // Saltamos 'message' porque lo manejamos con chat-input
                if (param.name === 'message') return;

                const el = this.createParamElement(param);
                
                // Guardar referencia a conversation_history
                if (param.name === 'conversation_history') {
                    this._historyInput = el.querySelector('input, select, textarea');
                }
                
                hiddenParams.appendChild(el);
            });
        }

        _setupEvents() {
            // Submit desde chat-input
            this._input?.addEventListener('submit', (e) => {
                this._handleSubmit(e.detail.message);
            });

            // Nueva conversación
            const newChatBtn = this.querySelector('[data-ref="newChatBtn"]');
            newChatBtn?.addEventListener('click', () => this._handleNewChat());

            // Focus en input cuando se abre la ventana
            this._window?.addEventListener('toggle', (e) => {
                if (e.detail.open) {
                    setTimeout(() => this._input?.focus(), 100);
                }
            });
        }

        async _handleSubmit(message) {
            if (!message?.trim()) return;

            // FIX BUG: Capturar mensaje ANTES de cualquier operación
            this._pendingUserMessage = message;

            // 1. UI Optimista: mostrar mensaje del usuario inmediatamente
            this._messages?.addMessage('user', message);

            // 2. Actualizar el valor del input "message" para el API call
            // Necesitamos encontrar o crear el input que usará super.execute()
            this._setMessageParam(message);

            // 3. Ejecutar llamada a la API via clase base
            try {
                await super.execute();
                // showResult será llamado por la clase base, nosotros lo sobreescribimos
            } catch (error) {
                // La clase base ya maneja el error
            }

            // 4. Limpiar input y actualizar contexto
            this._input?.clear();
            this._updateContext();
        }

        _setMessageParam(message) {
            // Buscar el input 'message' en los parámetros ocultos o crearlo
            let messageInput = this.querySelector('[name="message"]');
            
            if (!messageInput) {
                // Crear input oculto para el parámetro message
                const hiddenParams = this.querySelector('[data-ref="hiddenParams"]');
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'message';
                hiddenParams?.appendChild(input);
                messageInput = input;
            }
            
            messageInput.value = message;
        }

        /**
         * Sobreescribimos showResult de la clase base para mostrar en burbujas
         */
        showResult(result, isError = false) {
            if (isError) {
                this._messages?.addMessage('error', 
                    typeof result === 'string' ? result : JSON.stringify(result));
                return;
            }

            // Extraer respuesta del resultado (DspyOutput o similar)
            const responseText = result?.result?.response || 
                               result?.response || 
                               (typeof result === 'string' ? result : JSON.stringify(result, null, 2));

            // Mostrar respuesta del asistente
            this._messages?.addMessage('assistant', responseText);

            // Actualizar historial conversacional con el mensaje que capturamos ANTES
            if (this._pendingUserMessage) {
                this.conversationHistory.push({ 
                    role: 'user', 
                    content: this._pendingUserMessage 
                });
                this._pendingUserMessage = null;
            }
            
            this.conversationHistory.push({ 
                role: 'assistant', 
                content: responseText 
            });

            // Sincronizar historial con el input oculto
            this._syncHistoryInput();
        }

        _syncHistoryInput() {
            if (this._historyInput) {
                this._historyInput.value = this._formatHistory();
                this._historyInput.dispatchEvent(new Event('change'));
            }
        }

        _formatHistory() {
            return this.conversationHistory.map(msg => 
                `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`
            ).join(' | ');
        }

        _handleNewChat() {
            this.conversationHistory = [];
            this._pendingUserMessage = null;
            
            // Limpiar historial en el input oculto
            if (this._historyInput) {
                this._historyInput.value = '';
                this._historyInput.dispatchEvent(new Event('change'));
            }
            
            // Limpiar mensajes visuales
            this._messages?.clear();
            
            // Reset context bar
            this._contextBar?.update(0, 0);
        }

        async _updateContext() {
            // Construir lista de mensajes para calcular contexto
            const messages = [...this.conversationHistory];
            const currentInput = this._input?.getValue();
            if (currentInput) {
                messages.push({ role: 'user', content: currentInput });
            }
            
            if (messages.length === 0) {
                this._contextBar?.update(0, 0);
                return;
            }

            try {
                // Obtener modelo de los parámetros
                const modelInput = this.querySelector('[name="model"]');
                const model = modelInput?.value || 'openrouter/openai/gpt-4o';
                
                // Llamar al endpoint de cálculo de contexto
                // TODO: En el futuro usar <auto-calculate_context_usage> para consistencia
                const response = await fetch('/calculate_context_usage', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model, messages })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    const { current = 0, max = 0 } = data.result || data || {};
                    this._contextBar?.update(current, max);
                }
            } catch (error) {
                console.warn('Error calculando contexto:', error);
            }
        }
    }

    // Registrar el custom element
    if (!customElements.get('autocode-chat')) {
        customElements.define('autocode-chat', AutocodeChat);
    }
}

// Inicializar
initAutocodeChat().catch(console.error);

export { initAutocodeChat };
