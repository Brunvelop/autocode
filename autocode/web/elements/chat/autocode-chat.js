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
 * - ChatSettings: Configuración de modelo y parámetros
 */

// Importar sub-componentes
import './chat-input.js';
import './chat-messages.js';
import './chat-window.js';
import './context-bar.js';
import './chat-settings.js';

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
            this._settings = null;
        }

        connectedCallback() {
            this.render();
            this._setupComponentRefs();
            this._setupEvents();
            
            // Configurar settings dinámicamente con la info de la función
            if (this._settings && this.funcInfo) {
                this._settings.configure(this.funcInfo);
                this._updateModelBadge();
            }
        }

        render() {
            this.innerHTML = `
                <chat-window title="Autocode AI Chat">
                    <!-- Header actions -->
                    <div slot="header-actions" class="flex items-center gap-2">
                        <!-- Model Badge -->
                        <div 
                            data-ref="modelBadge" 
                            class="hidden md:flex items-center gap-1 px-2 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-[10px] font-mono text-indigo-600 truncate max-w-[150px]"
                            title="Modelo actual"
                        >
                            <span class="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                            <span data-ref="modelName">Loading...</span>
                        </div>

                        <chat-settings></chat-settings>
                        <button 
                            data-ref="newChatBtn"
                            class="text-indigo-100 bg-white/10 hover:bg-white/20 border border-white/20 rounded-full px-3 py-1.5 text-sm font-semibold transition-colors"
                        >
                            Nueva
                        </button>
                    </div>
                    
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
            this._settings = this.querySelector('chat-settings');
            
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

            // Escuchar cambios de configuración
            this._settings?.addEventListener('settings-change', () => {
                this._updateSettingsParams();
            });
        }

        async _handleSubmit(message) {
            if (!message?.trim()) return;

            // FIX BUG: Capturar mensaje ANTES de cualquier operación
            this._pendingUserMessage = message;

            // 1. UI Optimista: mostrar mensaje del usuario inmediatamente
            this._messages?.addMessage('user', message);

            // 2. Actualizar el valor del input "message" para el API call
            this._setMessageParam(message);

            // 2.5 Actualizar parámetros de configuración desde chat-settings
            this._updateSettingsParams();

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
            this._setHiddenParam('message', message);
        }

        _updateSettingsParams() {
            if (!this._settings) return;
            
            const settings = this._settings.getSettings();
            
            // Actualizar cada parámetro de configuración
            for (const [key, value] of Object.entries(settings)) {
                this._setHiddenParam(key, value);
            }

            // Actualizar badge también
            this._updateModelBadge();
        }

        _updateModelBadge() {
            const modelNameEl = this.querySelector('[data-ref="modelName"]');
            if (!modelNameEl || !this._settings) return;

            const settings = this._settings.getSettings();
            if (settings.model) {
                // Simplificar nombre del modelo (quitar prefix openrouter/openai/ etc)
                const simpleName = settings.model.split('/').pop();
                modelNameEl.textContent = simpleName;
            }
        }

        /**
         * Sobreescribimos callAPI para obtener la respuesta completa (incluyendo metadatos)
         * y no solo el campo 'result' como hace la clase base.
         */
        async callAPI(params) {
            const method = this.funcInfo.http_methods[0];
            let url = `/${this.funcName}`;
            let options = { 
                method: method.toUpperCase(), 
                headers: { 'Content-Type': 'application/json' } 
            };
            
            if (method.toUpperCase() === 'GET') {
                const queryParams = new URLSearchParams();
                for (const [key, val] of Object.entries(params)) {
                    if (typeof val === 'object' && val !== null) {
                        queryParams.append(key, JSON.stringify(val));
                    } else {
                        queryParams.append(key, val);
                    }
                }
                const queryString = queryParams.toString();
                if (queryString) url += `?${queryString}`;
            } else {
                options.body = JSON.stringify(params);
            }
            
            const response = await fetch(url, options);
            if (!response.ok) {
                let errorMsg = `HTTP ${response.status}`;
                try {
                    const errorData = await response.json();
                    if (errorData.detail) {
                        errorMsg = typeof errorData.detail === 'string' 
                            ? errorData.detail 
                            : JSON.stringify(errorData.detail, null, 2);
                    } else {
                        errorMsg = JSON.stringify(errorData, null, 2);
                    }
                } catch {
                    errorMsg = response.statusText || errorMsg;
                }
                throw new Error(errorMsg);
            }
            
            // Devolver objeto completo (sin extraer .result) para tener acceso a history/usage
            return await response.json();
        }

        _setHiddenParam(name, value) {
            // FIX CRITICO: Solo buscar inputs dentro del contenedor oculto o que sean explícitamente hidden
            // Esto evita seleccionar inputs de UI (como los de chat-settings) que causarían un bucle infinito
            // al disparar eventos change que chat-settings vuelve a capturar.
            
            // 1. Intentar buscar en el contenedor de hidden params (más seguro)
            let input = this.querySelector(`[data-ref="hiddenParams"] input[name="${name}"]`);

            // 2. Si no está ahí, buscar cualquier input hidden directo (legacy support)
            if (!input) {
                input = this.querySelector(`input[name="${name}"][type="hidden"]`);
            }
            
            // 3. Si no existe, CREARLO en el contenedor oculto
            if (!input) {
                const hiddenParams = this.querySelector('[data-ref="hiddenParams"]');
                if (hiddenParams) {
                    input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = name;
                    hiddenParams.appendChild(input);
                }
            }
            
            if (input) {
                // Manejar tipos complejos
                if (typeof value === 'object' && value !== null) {
                    input.value = JSON.stringify(value);
                } else {
                    input.value = value;
                }
                // Disparar change para que auto-element detecte el cambio
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }

        /**
         * Sobreescribimos showResult de la clase base para mostrar en burbujas
         */
        showResult(result, isError = false) {
            // Manejar error explícito de red/sistema
            if (isError) {
                this._messages?.addMessage('error', 
                    typeof result === 'string' ? result : JSON.stringify(result));
                return;
            }

            // Manejar error de backend (DspyOutput con success=False)
            if (result && result.success === false) {
                this._messages?.addMessage('error', result.message || result.error || 'Error desconocido');
                return;
            }

            // Pasar resultado completo a chat-messages para renderizado rico
            // (Si es DspyOutput, contendrá reasoning, trajectory, etc.)
            this._messages?.addMessage('assistant', result);

            // Extraer solo el texto para el historial
            const responseText = result?.result?.response || 
                               result?.response || 
                               (typeof result === 'string' ? result : JSON.stringify(result, null, 2));

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
                // Usar _setHiddenParam logic (buscar el input correcto)
                // Ojo: querySelector simple puede fallar si hay múltiples.
                // Priorizar el input hidden que acabamos de actualizar
                let modelInput = this.querySelector('input[name="model"][type="hidden"]');
                if (!modelInput) modelInput = this.querySelector('[name="model"]');
                
                const model = modelInput?.value || 'openrouter/openai/gpt-4o';
                
                // Llamar al endpoint de cálculo de contexto
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
