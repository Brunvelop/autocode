/**
 * index.js (autocode-chat)
 * Orquestador del chat que compone todos los sub-componentes.
 * Extiende AutoFunctionController para reutilizar la lógica de estado y API,
 * pero implementa su propia UI (ChatWindow) en lugar de la tarjeta genérica.
 * 
 * REFACTORIZACIÓN: Lógica pura separada de estilos siguiendo el patrón estándar de Lit
 */

import { html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { AutoFunctionController } from '../auto-element-generator.js';
import { themeTokens } from './styles/theme.js';
import { badgeBase, ghostButton } from './styles/common.js';
import { autocodeChatStyles } from './styles/autocode-chat.styles.js';

// Importar sub-componentes
import './chat-input.js';
import './chat-messages.js';
import './chat-window.js';
import './context-bar.js';
import './chat-settings.js';

export class AutocodeChat extends AutoFunctionController {
    static properties = {
        ...AutoFunctionController.properties,
        _chatConfig: { state: true }
    };

    static styles = [themeTokens, badgeBase, ghostButton, autocodeChatStyles];

    constructor() {
        super();
        this.funcName = 'chat'; // Hardcoded para este componente específico
        
        // Estado local del chat
        this.conversationHistory = [];
        this._pendingUserMessage = null;
        this._chatConfig = null;
        this._useStreaming = true; // Toggle streaming (controlado desde settings)
        
        // Inicializar params vacíos (se llenarán con defaults al cargar funcInfo)
        this.params = {
            message: '',
            conversation_history: '',
            model: ''
        };
    }

    connectedCallback() {
        super.connectedCallback();
        this._loadChatConfig();
        this._loadStreamFuncInfo();
    }

    firstUpdated() {
        // Crear referencias a sub-componentes usando shadowRoot
        this._window = this.shadowRoot.querySelector('chat-window');
        this._messages = this.shadowRoot.querySelector('chat-messages');
        this._input = this.shadowRoot.querySelector('chat-input');
        this._contextBar = this.shadowRoot.querySelector('context-bar');
        this._settings = this.shadowRoot.querySelector('chat-settings');
        
        // Setup event listeners
        this.shadowRoot.addEventListener('submit', this._handleInputSubmit.bind(this));
        this.shadowRoot.addEventListener('settings-change', this._handleSettingsChange.bind(this));
        this.shadowRoot.addEventListener('toggle', this._handleWindowToggle.bind(this));
        // Click en botón Nueva
        const newBtn = this.shadowRoot.querySelector('[data-ref="newChatBtn"]');
        if (newBtn) {
            newBtn.addEventListener('click', () => this._handleNewChat());
        }
    }

    /**
     * Hook de Lit: se ejecuta cuando las propiedades reactivas cambian.
     * Aquí configuramos los settings cuando funcInfo se carga.
     */
    updated(changedProperties) {
        super.updated(changedProperties);
        
        // Cuando funcInfo se carga, configurar el panel de settings
        if (changedProperties.has('funcInfo') && this.funcInfo && this._settings) {
            this._settings.configure(this.funcInfo);
        }
    }

    render() {
        return html`
            <chat-window title="Autocode AI Chat">
                <!-- Header actions -->
                <div slot="header-actions" class="header-actions">
                    <div class="model-badge" title="Modelo actual">
                        <span class="model-indicator"></span>
                        <span>${this._getSimpleModelName()}</span>
                    </div>

                    <chat-settings .chatConfig=${this._chatConfig}></chat-settings>
                    
                    <button 
                        data-ref="newChatBtn"
                        class="new-chat-btn"
                    >
                        Nueva
                    </button>
                </div>
                
                <!-- Content: mensajes -->
                <chat-messages slot="content"></chat-messages>
                
                <!-- Footer: input y context bar -->
                <div slot="footer" class="footer-container">
                    <chat-input placeholder="Escribe tu mensaje..."></chat-input>
                    <context-bar current="0" max="0"></context-bar>
                </div>
            </chat-window>
        `;
    }

    // ========================================================================
    // EVENT HANDLERS
    // ========================================================================

    _handleInputSubmit(e) {
        // El evento submit viene del chat-input
        if (e.target.tagName.toLowerCase() === 'chat-input') {
            this._sendMessage(e.detail.message);
        }
    }

    _handleSettingsChange(e) {
        const settings = { ...e.detail };
        
        // Extraer flags frontend-only antes de guardar como params del backend
        if ('use_streaming' in settings) {
            this._useStreaming = settings.use_streaming !== false;
            delete settings.use_streaming;
        }
        
        // Actualizar params con los settings del backend
        Object.entries(settings).forEach(([key, value]) => {
            this.setParam(key, value);
        });
        this.requestUpdate(); // Para actualizar el badge del modelo
    }

    _handleWindowToggle(e) {
        if (e.detail.open && this._input) {
            setTimeout(() => this._input.focus(), 100);
        }
    }

    _handleNewChat() {
        this.conversationHistory = [];
        this._pendingUserMessage = null;
        this.setParam('conversation_history', '');
        
        if (this._messages) this._messages.clear();
        if (this._contextBar) this._contextBar.update(0, 0);
    }

    async _loadChatConfig() {
        try {
            const result = await AutoFunctionController.executeFunction('get_chat_config', {});
            this._chatConfig = result;
        } catch (error) {
            console.warn('⚠️ Error loading chat config:', error);
        }
    }

    /**
     * Pre-carga la info de chat_stream del registry para evitar latencia en el primer mensaje.
     * Si chat_stream no está disponible, _streamFuncInfo queda null y se usa fallback síncrono.
     */
    async _loadStreamFuncInfo() {
        try {
            const response = await fetch('/functions/details');
            const data = await response.json();
            this._streamFuncInfo = data.functions['chat_stream'] || null;
        } catch (e) {
            console.warn('⚠️ Could not pre-load chat_stream info');
            this._streamFuncInfo = null;
        }
    }

    // ========================================================================
    // LOGIC & HELPERS
    // ========================================================================

    /**
     * Procesa el resultado de la ejecución y actualiza el historial y la UI
     */
    _processResult(envelopeOrPayload) {
        if (!envelopeOrPayload) return;

        // A partir de ahora el Controller expone:
        // - this.result: payload (data.result)
        // - this.envelope: envelope completo (data)
        // Preferimos procesar/mostrar el envelope para conservar metadatos.
        const envelope = (envelopeOrPayload && typeof envelopeOrPayload === 'object' && Object.prototype.hasOwnProperty.call(envelopeOrPayload, 'result'))
            ? envelopeOrPayload
            : (this.envelope || envelopeOrPayload);

        const isError = envelope?._isError || envelope?.success === false || this.success === false;

        if (isError) {
            // Pasar el objeto completo si es posible para mantener metadatos (history, debug info)
            // Si no es objeto, usar el string de error
            const content = (typeof envelope === 'object' && envelope !== null)
                ? envelope
                : (envelope?._message || envelope?.message || envelope?.error || 'Error desconocido');

            if (this._messages) {
                this._messages.addMessage('error', content);
            }
            return;
        }

        // Mostrar respuesta
        if (this._messages) {
            this._messages.addMessage('assistant', envelope);
        }

        // Actualizar historial interno
        const responseText = envelope?.result?.response ||
                           envelope?.response ||
                           (typeof envelope === 'string' ? envelope : JSON.stringify(envelope?.result || envelope, null, 2));

        if (this._pendingUserMessage) {
            this.conversationHistory.push({ role: 'user', content: this._pendingUserMessage });
            this._pendingUserMessage = null;
        }
        
        this.conversationHistory.push({ role: 'assistant', content: responseText });

        // Sincronizar historial con params para la próxima vuelta
        this.setParam('conversation_history', this._formatHistory());
    }

    _formatHistory() {
        return this.conversationHistory.map(msg => 
            `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`
        ).join(' | ');
    }

    _getSimpleModelName() {
        const model = this.getParam('model') || 'Loading...';
        return model.split('/').pop();
    }

    /**
     * Calcula y actualiza el uso de la ventana de contexto.
     * Usa AutoFunctionController.executeFunction() para llamar al endpoint.
     */
    async _updateContext() {
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
            // Usar el método estático del Controller en lugar de fetch directo
            const result = await AutoFunctionController.executeFunction(
                'calculate_context_usage',
                { 
                    model: this.getParam('model') || 'openrouter/openai/gpt-4o',
                    messages 
                }
            );
            
            const { current = 0, max = 0 } = result;
            this._contextBar?.update(current, max);
        } catch (e) {
            console.warn('⚠️ Error calculating context:', e);
            // No es crítico, solo log del error
        }
    }

    async _sendMessage(message) {
        if (!message?.trim()) return;

        this._pendingUserMessage = message;
        
        // 1. UI Optimista
        if (this._messages) {
            this._messages.addMessage('user', message);
        }

        // 2. Actualizar Params (State)
        this.setParam('message', message);
        
        // Sincronizar settings actuales por si acaso
        if (this._settings) {
            const settings = this._settings.getSettings();
            Object.entries(settings).forEach(([key, value]) => {
                this.setParam(key, value);
            });
        }

        // 3. Usar streaming si disponible Y habilitado, sino fallback síncrono
        if (this._streamFuncInfo?.streaming && this._useStreaming) {
            await this._sendMessageStream(message);
        } else {
            await this._sendMessageSync(message);
        }

        // 4. Limpieza
        if (this._input) this._input.clear();
        this._updateContext();
    }

    /**
     * Envía mensaje usando streaming SSE (chat_stream endpoint).
     * Muestra tokens incrementalmente conforme llegan del servidor.
     */
    async _sendMessageStream(message) {
        const streamId = this._messages.addStreamingMessage();
        let fullText = '';
        const statusLog = [];
        let streamFailed = false;

        // Resetear envelope para evitar guardar datos stale si hay error
        this.envelope = null;
        this.result = null;
        this.success = undefined;

        try {
            this._setStatus('loading', 'Conectando...');

            for await (const event of this.callStreamAPI('chat_stream', this.params, this._streamFuncInfo)) {
                switch (event.event) {
                    case 'token':
                        fullText += event.data.chunk;
                        this._messages.appendToStreaming(streamId, event.data.chunk);
                        break;

                    case 'status':
                        this._setStatus('loading', event.data.message);
                        statusLog.push({
                            message: event.data.message,
                            timestamp: Date.now()
                        });
                        this._messages.updateStreamingStatus(streamId, event.data.message);
                        break;

                    case 'complete': {
                        const envelope = { ...event.data, _statusLog: statusLog };
                        this._messages.finalizeStreaming(streamId, envelope);
                        this.envelope = envelope;
                        this.result = event.data.result;
                        this.success = event.data.success;
                        this._setStatus('success', 'Completado');
                        // Notify other components (e.g. git-dashboard) that plans may have changed
                        window.dispatchEvent(new CustomEvent('plans-changed'));
                        break;
                    }

                    case 'error':
                        if (event.data.streaming_incompatible) {
                            // Modelo no soporta streaming → fallback automático a sync
                            this._messages.updateStreamingStatus(streamId, 
                                '⚠️ ' + event.data.message
                            );
                            this._messages.finalizeStreaming(streamId, {
                                message: event.data.message,
                                _statusLog: statusLog
                            });
                            this._setStatus('loading', 'Reintentando en modo estándar...');
                            streamFailed = true;
                        } else {
                            this._messages.finalizeStreaming(streamId, {
                                ...event.data, _isError: true, _statusLog: statusLog
                            });
                            this._setStatus('error', event.data.message);
                        }
                        break;
                }
            }

            // Fallback automático: reintentar con endpoint síncrono
            if (streamFailed) {
                await this._sendMessageSync(message);
                return;
            }

            // Actualizar historial de conversación
            const responseText = fullText || this.result?.response || '';
            if (this._pendingUserMessage) {
                this.conversationHistory.push({ role: 'user', content: this._pendingUserMessage });
                this._pendingUserMessage = null;
            }
            this.conversationHistory.push({ role: 'assistant', content: responseText });
            this.setParam('conversation_history', this._formatHistory());

        } catch (error) {
            this._messages.finalizeStreaming(streamId, {
                _isError: true, _message: error.message, _statusLog: statusLog
            });
            this._setStatus('error', error.message);
        }
    }

    /**
     * Fallback síncrono: ejecuta chat() normal sin streaming.
     * Usado cuando chat_stream no está disponible en el registry.
     */
    async _sendMessageSync(message) {
        try {
            await this.execute();
            // Procesar siempre el envelope para conservar success/message + metadata DSPy
            this._processResult(this.envelope || this.result);

            // Notify other components (e.g. git-dashboard) that plans may have changed
            window.dispatchEvent(new CustomEvent('plans-changed'));

        } catch (error) {
            if (this._messages) {
                this._messages.addMessage('error', error.message || 'Error desconocido');
            }
        }
    }
}

// Registrar el custom element
if (!customElements.get('autocode-chat')) {
    customElements.define('autocode-chat', AutocodeChat);
}
