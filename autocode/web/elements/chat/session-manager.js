/**
 * session-manager.js
 * Sub-componente para gestionar sesiones AI con Git workflow.
 * 
 * Responsabilidades:
 * - Chequeo de sesión activa al montar y en puntos clave
 * - Iniciar nueva sesión
 * - Finalizar sesión actual
 * - Auto-guardado de conversaciones
 * - UI compacta con indicador y botones
 * 
 * Eventos emitidos:
 * - 'session-changed': Cuando cambia el estado de sesión (null o session data)
 * - 'session-started': Cuando se inicia una nueva sesión
 * - 'session-ended': Cuando se finaliza una sesión
 * - 'session-aborted': Cuando se cancela una sesión
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { AutoFunctionController } from '../auto-element-generator.js';
import { sessionManagerStyles } from './styles/session-manager.styles.js';

export class SessionManager extends LitElement {
    static properties = {
        currentSession: { type: Object, state: true },
        _errorMessage: { type: String, state: true }
    };

    static styles = [sessionManagerStyles];

    constructor() {
        super();
        this.currentSession = null;
        this._errorMessage = null;
    }

    connectedCallback() {
        super.connectedCallback();
        // Check inicial al montar - sin polling
        this._checkCurrentSession();
    }

    render() {
        return html`
            <div class="session-manager">
                ${this._errorMessage ? this._renderError() : ''}
                ${this.currentSession ? this._renderActiveSession() : this._renderNewSessionButton()}
            </div>
        `;
    }

    _renderError() {
        return html`
            <div class="session-error" @click=${this._dismissError} title="Click para cerrar">
                <span class="error-icon">⚠️</span>
                <span class="error-text">${this._errorMessage}</span>
                <span class="error-dismiss">✕</span>
            </div>
        `;
    }

    _dismissError() {
        this._errorMessage = null;
    }

    _showError(message) {
        this._errorMessage = message;
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (this._errorMessage === message) {
                this._errorMessage = null;
            }
        }, 5000);
    }

    _renderActiveSession() {
        return html`
            <div class="session-badge" title="Sesión activa: ${this.currentSession.description}">
                <span class="session-dot"></span>
                <span class="session-icon">📍</span>
                <span class="session-description">${this.currentSession.description}</span>
            </div>
            <button 
                class="end-session-btn"
                @click=${this._handleEndSession}
                title="Finalizar y mergear a main"
            >
                Finalizar
            </button>
            <button 
                class="abort-session-btn"
                @click=${this._handleAbortSession}
                title="Cancelar sin guardar"
            >
                Cancelar
            </button>
        `;
    }

    _renderNewSessionButton() {
        return html`
            <button 
                class="new-session-btn"
                @click=${this._handleNewSession}
                title="Iniciar nueva sesión"
            >
                Nueva Sesión
            </button>
        `;
    }

    // ========================================================================
    // SESSION API CALLS
    // ========================================================================

    async _checkCurrentSession() {
        try {
            const result = await AutoFunctionController.executeFunction(
                'get_current_session',
                {}
            );
            
            const previousSession = this.currentSession;
            this.currentSession = result;

            // Emitir evento si cambió
            if (JSON.stringify(previousSession) !== JSON.stringify(result)) {
                this.dispatchEvent(new CustomEvent('session-changed', {
                    detail: { session: result },
                    bubbles: true,
                    composed: true
                }));
            }
        } catch (e) {
            console.warn('⚠️ Error checking session:', e);
        }
    }

    /**
     * Genera un nombre de sesión legible automáticamente.
     */
    _generateSessionName() {
        const now = new Date();
        return `Chat ${now.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })} ${now.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}`;
    }

    async _handleNewSession() {
        // Nombre automático sin prompt
        const description = this._generateSessionName();
        
        try {
            const result = await AutoFunctionController.executeFunction(
                'start_ai_session',
                { description, session_type: 'session' }
            );
            
            if (result && result.branch) {
                this.currentSession = result;
                this._errorMessage = null; // Limpiar error anterior
                
                this.dispatchEvent(new CustomEvent('session-started', {
                    detail: { session: result },
                    bubbles: true,
                    composed: true
                }));
            } else {
                this._showError('No se pudo iniciar la sesión');
            }
        } catch (e) {
            this._showError(e.message || 'Error al iniciar sesión');
        }
    }

    async _handleEndSession() {
        const commit_msg = prompt('Mensaje de commit para main:');
        if (!commit_msg) return;
        
        try {
            const result = await AutoFunctionController.executeFunction(
                'finalize_ai_session',
                { commit_message: commit_msg }
            );
            
            if (result && result.merged_to) {
                const endedSession = this.currentSession;
                this.currentSession = null;
                this._errorMessage = null;
                
                this.dispatchEvent(new CustomEvent('session-ended', {
                    detail: { 
                        session: endedSession,
                        merged_to: result.merged_to 
                    },
                    bubbles: true,
                    composed: true
                }));
            } else {
                this._showError('No se pudo finalizar la sesión');
            }
        } catch (e) {
            this._showError(e.message || 'Error al finalizar sesión');
        }
    }

    async _handleAbortSession() {
        if (!confirm('¿Cancelar sesión sin guardar cambios en main?')) return;
        
        try {
            const result = await AutoFunctionController.executeFunction(
                'abort_ai_session',
                { delete_branch: true }
            );
            
            if (result && result.returned_to) {
                const abortedSession = this.currentSession;
                this.currentSession = null;
                this._errorMessage = null;
                
                this.dispatchEvent(new CustomEvent('session-aborted', {
                    detail: { session: abortedSession },
                    bubbles: true,
                    composed: true
                }));
            } else {
                this._showError('No se pudo cancelar la sesión');
            }
        } catch (e) {
            this._showError(e.message || 'Error al cancelar sesión');
        }
    }

    // ========================================================================
    // PUBLIC API
    // ========================================================================

    /**
     * Guarda la conversación actual en la sesión activa.
     * Debe ser llamado por el componente padre cuando hay nueva actividad.
     */
    async saveConversation(messages) {
        if (!this.currentSession) {
            console.warn('⚠️ No hay sesión activa, no se puede guardar');
            return false;
        }

        try {
            const formattedMessages = messages.map(msg => ({
                role: msg.role,
                content: msg.content,
                timestamp: msg.timestamp || new Date().toISOString()
            }));
            
            await AutoFunctionController.executeFunction(
                'save_conversation',
                { messages: formattedMessages }
            );
            
            console.log('✅ Conversación auto-guardada');
            return true;
        } catch (e) {
            console.warn('⚠️ Error auto-guardando conversación:', e);
            return false;
        }
    }

    /**
     * Verifica si hay una sesión activa.
     */
    hasActiveSession() {
        return this.currentSession !== null;
    }

    /**
     * Obtiene la sesión actual.
     */
    getCurrentSession() {
        return this.currentSession;
    }

    /**
     * Fuerza un refresh del estado de sesión.
     * Útil cuando el componente padre necesita actualizar el estado.
     */
    async refresh() {
        await this._checkCurrentSession();
    }
}

// Registrar el custom element
if (!customElements.get('session-manager')) {
    customElements.define('session-manager', SessionManager);
}
