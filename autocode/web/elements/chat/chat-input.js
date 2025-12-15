/**
 * chat-input.js
 * Componente de entrada para el chat
 * Refactorizado: Lógica pura separada de estilos
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { chatInputStyles } from './styles/chat-input.styles.js';
import { themeTokens } from './styles/theme.js';

export class ChatInput extends LitElement {
    static properties = {
        placeholder: { type: String },
        disabled: { type: Boolean }
    };

    static styles = [themeTokens, chatInputStyles];

    constructor() {
        super();
        this.placeholder = 'Escribe tu mensaje...';
        this.disabled = false;
    }

    render() {
        return html`
            <div class="container">
                <input 
                    type="text" 
                    id="input"
                    .placeholder=${this.placeholder}
                    ?disabled=${this.disabled}
                    @keypress=${this._handleKeyPress}
                >
                <button 
                    id="button"
                    ?disabled=${this.disabled}
                    @click=${this._submit}
                >
                    Enviar 🚀
                </button>
            </div>
        `;
    }

    _handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this._submit();
        }
    }

    _submit() {
        const input = this.shadowRoot.getElementById('input');
        const message = input.value.trim();
        
        if (!message) return;

        this.dispatchEvent(new CustomEvent('submit', {
            detail: { message },
            bubbles: true,
            composed: true
        }));
    }

    // API Pública
    clear() {
        const input = this.shadowRoot.getElementById('input');
        if (input) input.value = '';
    }

    focus() {
        const input = this.shadowRoot.getElementById('input');
        if (input) input.focus();
    }

    getValue() {
        const input = this.shadowRoot.getElementById('input');
        return input ? input.value : '';
    }
}

if (!customElements.get('chat-input')) {
    customElements.define('chat-input', ChatInput);
}
