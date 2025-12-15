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
            return html`
                ${content.reasoning ? this._renderReasoning(content.reasoning) : ''}
                ${content.trajectory ? this._renderTrajectory(content.trajectory) : ''}
                
                <div class="text-content">${this._extractMainText(content)}</div>

                ${role === 'assistant' 
                    ? html`<chat-debug-info .data=${content}></chat-debug-info>` 
                    : ''}
            `;
        }
        
        return html`<div class="text-content">${content}</div>`;
    }

    _renderReasoning(reasoning) {
        return html`
            <details class="reasoning" data-type="reasoning">
                <summary>
                    <span style="margin-right: 0.5rem">🧠</span> Ver proceso de pensamiento
                </summary>
                <div class="content">${reasoning}</div>
            </details>
        `;
    }

    _renderTrajectory(trajectory) {
        let steps = Array.isArray(trajectory) ? trajectory : [trajectory];
        if (!trajectory || (Array.isArray(trajectory) && trajectory.length === 0)) return '';

        return html`
            <div class="trajectory">
                <div class="trajectory-title">
                    <span>🛠️ Uso de Herramientas</span>
                </div>
                ${steps.map(step => this._renderStep(step))}
            </div>
        `;
    }

    _renderStep(step) {
        const toolName = step.tool_name || step.tool || 'Unknown Tool';
        const toolInput = step.tool_input || step.input || step.args || '';
        const thought = step.thought || '';
        const observation = step.observation || step.result || '';

        return html`
            <div class="step">
                ${thought ? html`<div class="step-thought">💭 ${thought}</div>` : ''}
                
                <div class="tool-call">
                    ${toolName}(${typeof toolInput === 'string' ? toolInput : JSON.stringify(toolInput)})
                </div>
                
                ${observation ? html`
                    <details class="observation">
                        <summary>Ver resultado</summary>
                        <div class="observation-content">${typeof observation === 'string' ? observation : JSON.stringify(observation, null, 2)}</div>
                    </details>
                ` : ''}
            </div>
        `;
    }

    _extractMainText(content) {
        if (content.result && typeof content.result === 'string') return content.result;
        if (content.result && content.result.response) return content.result.response;
        if (content.response) return content.response;
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
