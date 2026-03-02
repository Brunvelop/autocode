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

    /**
     * Crea un mensaje de streaming vacío (se irá llenando con appendToStreaming).
     * @returns {string} ID único del mensaje para referenciar en append/finalize
     */
    addStreamingMessage() {
        const id = `stream-${Date.now()}`;
        this.messages = [...this.messages, {
            id, role: 'assistant', content: '',
            streaming: true, timestamp: Date.now()
        }];
        this.updateComplete.then(() => this._scrollToBottom());
        return id;
    }

    /**
     * Añade un chunk de texto a un mensaje de streaming existente.
     * @param {string} id - ID del mensaje de streaming
     * @param {string} chunk - Texto a añadir
     */
    appendToStreaming(id, chunk) {
        this.messages = this.messages.map(msg =>
            msg.id === id
                ? { ...msg, content: msg.content + chunk }
                : msg
        );
        this.updateComplete.then(() => this._scrollToBottom());
    }

    /**
     * Finaliza un mensaje de streaming, reemplazando su contenido con el envelope final.
     * @param {string} id - ID del mensaje de streaming
     * @param {object} envelope - Datos finales del mensaje (result, reasoning, etc.)
     */
    finalizeStreaming(id, envelope) {
        this.messages = this.messages.map(msg =>
            msg.id === id
                ? { ...msg, content: envelope, streaming: false }
                : msg
        );
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
                <div class="bubble ${msg.role} ${msg.streaming ? 'streaming' : ''}">
                    <div class="role-label">${this._getRoleLabel(msg.role)}</div>
                    <div class="message-body">
                        ${msg.streaming
                            ? html`<div class="text-content">${msg.content}<span class="cursor">▊</span></div>`
                            : this._renderContent(msg.role, msg.content)
                        }
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
