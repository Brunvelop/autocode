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
import './session-manager.js';

export class AutocodeChat extends AutoFunctionController {
    static properties = {
        ...AutoFunctionController.properties
    };

    static styles = [themeTokens, badgeBase, ghostButton, autocodeChatStyles];

    constructor() {
        super();
        this.funcName = 'chat'; // Hardcoded para este componente específico
        
        // Estado local del chat
        this.conversationHistory = [];
        this._pendingUserMessage = null;
        
        // Inicializar params vacíos (se llenarán con defaults al cargar funcInfo)
        this.params = {
            message: '',
            conversation_history: '',
            model: ''
        };
    }

    firstUpdated() {
        // Crear referencias a sub-componentes usando shadowRoot
        this._window = this.shadowRoot.querySelector('chat-window');
        this._messages = this.shadowRoot.querySelector('chat-messages');
        this._input = this.shadowRoot.querySelector('chat-input');
        this._contextBar = this.shadowRoot.querySelector('context-bar');
        this._settings = this.shadowRoot.querySelector('chat-settings');
        this._sessionManager = this.shadowRoot.querySelector('session-manager');
        
        // Setup event listeners
        this.shadowRoot.addEventListener('submit', this._handleInputSubmit.bind(this));
        this.shadowRoot.addEventListener('settings-change', this._handleSettingsChange.bind(this));
        this.shadowRoot.addEventListener('toggle', this._handleWindowToggle.bind(this));
        this.shadowRoot.addEventListener('session-changed', this._handleSessionChange.bind(this));
        this.shadowRoot.addEventListener('session-started', this._handleSessionStarted.bind(this));
        
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

                    <chat-settings></chat-settings>
                    
                    <!-- Session Manager: Reemplaza toda la lógica de sesiones -->
                    <session-manager></session-manager>
                    
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
        const settings = e.detail;
        // Actualizar params con los nuevos settings
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

    // ========================================================================
    // LOGIC & HELPERS
    // ========================================================================

    /**
     * Procesa el resultado de la ejecución y actualiza el historial y la UI
     */
    _processResult(result) {
        if (!result) return;
        
        const isError = result._isError || result.success === false;

        if (isError) {
            const msg = result._message || result.message || result.error || 'Error desconocido';
            if (this._messages) {
                this._messages.addMessage('error', msg);
            }
            return;
        }

        // Mostrar respuesta
        if (this._messages) {
            this._messages.addMessage('assistant', result);
        }

        // Actualizar historial interno
        const responseText = result?.result?.response || 
                           result?.response || 
                           (typeof result === 'string' ? result : JSON.stringify(result, null, 2));

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

    // ========================================================================
    // SESSION MANAGEMENT (Delegado a session-manager)
    // ========================================================================

    _handleSessionChange(e) {
        // El session-manager notifica cambios en la sesión
        console.log('📊 Sesión cambió:', e.detail.session);
    }

    _handleSessionStarted(e) {
        console.log('✅ Sesión iniciada:', e.detail.session);
        // Aquí podrías agregar lógica adicional si es necesario
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

        // 3. Ejecutar (usa this.execute del Controller)
        try {
            await this.execute();
            // El resultado se maneja en 'after-execute' o chequeando result
            this._processResult(this.result);
            
            // 4. Auto-save si estamos en sesión (después de respuesta del asistente)
            if (this._sessionManager?.hasActiveSession() && this.result && !this.result._isError) {
                await this._sessionManager.saveConversation(this.conversationHistory);
            }
        } catch (error) {
            if (this._messages) {
                this._messages.addMessage('error', error.message || 'Error desconocido');
            }
        }

        // 5. Limpieza
        if (this._input) this._input.clear();
        this._updateContext();
    }
}

// Registrar el custom element
if (!customElements.get('autocode-chat')) {
    customElements.define('autocode-chat', AutocodeChat);
}
