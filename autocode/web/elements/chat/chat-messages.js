/**
 * chat-messages.js
 * Componente para mostrar mensajes del chat
 * Refactorizado: Lógica pura separada de estilos
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { chatMessagesStyles } from './styles/chat-messages.styles.js';
import { themeTokens } from './styles/theme.js';
import './chat-debug-info.js';

export class ChatMessages extends LitElement {
    static properties = {
        messages: { type: Array }
    };

    static styles = [themeTokens, chatMessagesStyles];

    constructor() {
        super();
        this.messages = [];
    }

    /**
     * Añade un mensaje al chat
     * @param {'user' | 'assistant' | 'error'} role
     * @param {string|object} content
     */
    addMessage(role, content) {
        this.messages = [...this.messages, { role, content, timestamp: Date.now() }];
        this.updateComplete.then(() => this._scrollToBottom());
    }

    clear() {
        this.messages = [];
    }

    getMessages() {
        return [...this.messages];
    }

    _scrollToBottom() {
        const container = this.shadowRoot.getElementById('container');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }

    render() {
        return html`
            <div class="container" id="container">
                ${this.messages.length === 0 
                    ? html`<div class="empty-state">Inicia una conversación... 💬</div>`
                    : this.messages.map(msg => this._renderMessage(msg))
                }
            </div>
        `;
    }

    _renderMessage(msg) {
        return html`
            <div class="message-row ${msg.role}" data-role="${msg.role}">
                <div class="bubble ${msg.role}">
                    <div class="role-label">${this._getRoleLabel(msg.role)}</div>
                    <div class="message-body">
                        ${this._renderContent(msg.role, msg.content)}
                    </div>
                </div>
            </div>
        `;
    }

    _renderContent(role, content) {
        if (typeof content === 'object' && content !== null) {
            // Toda la info técnica (reasoning, trajectory, etc) se delega al chat-debug-info
            return html`
                <div class="text-content">${this._extractMainText(content)}</div>

                ${(role === 'assistant' || role === 'error') 
                    ? html`<chat-debug-info .data=${content}></chat-debug-info>` 
                    : ''}
            `;
        }
        
        return html`<div class="text-content">${content}</div>`;
    }

    _extractMainText(content) {
        // Estrategias de extracción del texto principal:
        // 1) Priorizar el payload si existe (GenericOutput/DspyOutput: result)
        if (content.result && typeof content.result === 'string') return content.result;
        if (content.result && content.result.response) return content.result.response;
        if (content.response) return content.response;

        // 2) Errores explícitos
        if (content.error) return content.error;

        // 3) Mensaje (message) suele ser metadata del envelope; usarlo como fallback
        if (content.message) return content.message;
        
        // 4) Fallback a JSON string
        return JSON.stringify(content.result || content, null, 2);
    }

    _getRoleLabel(role) {
        switch (role) {
            case 'user': return '👤 Tú';
            case 'error': return '❌ Error';
            case 'assistant': default: return '🤖 Asistente';
        }
    }
}

if (!customElements.get('chat-messages')) {
    customElements.define('chat-messages', ChatMessages);
}
