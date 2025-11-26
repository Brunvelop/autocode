/**
 * chat-input.js
 * Componente de entrada para el chat
 * 
 * Atributos:
 * - placeholder: Texto placeholder del input
 * - disabled: Desactiva input y botón
 * 
 * Eventos:
 * - submit: Emitido al hacer click o Enter, con detail: { message }
 * 
 * Métodos:
 * - clear(): Limpia el input
 * - focus(): Enfoca el input
 * - getValue(): Retorna el valor actual
 */

class ChatInput extends HTMLElement {
    static get observedAttributes() {
        return ['placeholder', 'disabled'];
    }

    constructor() {
        super();
        this._input = null;
        this._button = null;
    }

    connectedCallback() {
        this.render();
        this.setupEvents();
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue === newValue) return;
        
        if (name === 'placeholder' && this._input) {
            this._input.placeholder = newValue || '';
        }
        
        if (name === 'disabled') {
            const isDisabled = newValue !== null;
            if (this._input) this._input.disabled = isDisabled;
            if (this._button) this._button.disabled = isDisabled;
        }
    }

    render() {
        const placeholder = this.getAttribute('placeholder') || 'Escribe tu mensaje...';
        const isDisabled = this.hasAttribute('disabled');

        this.innerHTML = `
            <div class="flex gap-2 w-full">
                <input 
                    type="text" 
                    placeholder="${placeholder}"
                    ${isDisabled ? 'disabled' : ''}
                    class="flex-1 p-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
                    data-ref="input"
                >
                <button 
                    ${isDisabled ? 'disabled' : ''}
                    class="bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white font-semibold px-5 py-3 rounded-xl shadow transition disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                    data-ref="button"
                >
                    Enviar 🚀
                </button>
            </div>
        `;

        this._input = this.querySelector('[data-ref="input"]');
        this._button = this.querySelector('[data-ref="button"]');
    }

    setupEvents() {
        // Click en botón
        this._button.addEventListener('click', () => this._submit());

        // Enter en input
        this._input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this._submit();
            }
        });
    }

    _submit() {
        const message = this._input.value.trim();
        if (!message) return;

        this.dispatchEvent(new CustomEvent('submit', {
            detail: { message },
            bubbles: true,
            composed: true
        }));
    }

    // API Pública
    clear() {
        if (this._input) {
            this._input.value = '';
        }
    }

    focus() {
        if (this._input) {
            this._input.focus();
        }
    }

    getValue() {
        return this._input?.value || '';
    }
}

if (!customElements.get('chat-input')) {
    customElements.define('chat-input', ChatInput);
}

export { ChatInput };
