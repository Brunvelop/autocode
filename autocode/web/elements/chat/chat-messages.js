/**
 * chat-messages.js
 * Componente para mostrar mensajes del chat
 * 
 * Métodos:
 * - addMessage(role, content): Añade un mensaje (role: 'user' | 'assistant' | 'error')
 * - clear(): Elimina todos los mensajes
 * - getMessages(): Retorna array de mensajes
 */

class ChatMessages extends HTMLElement {
    constructor() {
        super();
        this._messages = [];
        this._container = null;
    }

    connectedCallback() {
        this.render();
    }

    render() {
        this.innerHTML = `
            <div 
                data-ref="container"
                class="flex-1 overflow-y-auto p-4 bg-gradient-to-b from-gray-50 to-white space-y-3 min-h-[200px]"
            >
                <div class="text-center text-gray-500 italic" data-ref="emptyState">
                    Inicia una conversación... 💬
                </div>
            </div>
        `;
        
        this._container = this.querySelector('[data-ref="container"]');
    }

    /**
     * Añade un mensaje al chat
     * @param {'user' | 'assistant' | 'error'} role - Rol del mensaje
     * @param {string} content - Contenido del mensaje
     */
    addMessage(role, content) {
        // Remover empty state si existe
        const emptyState = this.querySelector('[data-ref="emptyState"]');
        if (emptyState) emptyState.remove();

        // Guardar en array interno
        this._messages.push({ role, content, timestamp: Date.now() });

        // Crear elemento del mensaje
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'}`;
        messageDiv.dataset.role = role;

        const bubble = document.createElement('div');
        bubble.className = this._getBubbleClasses(role);

        const header = document.createElement('div');
        header.className = 'font-bold text-sm mb-1';
        header.textContent = this._getRoleLabel(role);

        const body = document.createElement('div');
        body.className = 'whitespace-pre-wrap break-words text-sm';
        body.textContent = content;

        bubble.appendChild(header);
        bubble.appendChild(body);
        messageDiv.appendChild(bubble);
        this._container.appendChild(messageDiv);

        // Auto-scroll al final
        this._scrollToBottom();
    }

    _getBubbleClasses(role) {
        const base = 'max-w-[85%] rounded-2xl px-4 py-3';
        
        switch (role) {
            case 'user':
                return `${base} bg-indigo-600 text-white shadow-md`;
            case 'error':
                return `${base} bg-red-50 text-red-800 border border-red-300`;
            case 'assistant':
            default:
                return `${base} bg-white text-gray-800 shadow-sm border border-gray-200`;
        }
    }

    _getRoleLabel(role) {
        switch (role) {
            case 'user':
                return '👤 Tú';
            case 'error':
                return '❌ Error';
            case 'assistant':
            default:
                return '🤖 Asistente';
        }
    }

    _scrollToBottom() {
        // Usar requestAnimationFrame para asegurar que el DOM se ha actualizado
        requestAnimationFrame(() => {
            if (this._container) {
                this._container.scrollTop = this._container.scrollHeight;
            }
        });
    }

    /**
     * Elimina todos los mensajes
     */
    clear() {
        this._messages = [];
        this._container.innerHTML = `
            <div class="text-center text-gray-500 italic" data-ref="emptyState">
                Inicia una conversación... 💬
            </div>
        `;
    }

    /**
     * Retorna todos los mensajes
     * @returns {Array<{role: string, content: string, timestamp: number}>}
     */
    getMessages() {
        return [...this._messages];
    }
}

if (!customElements.get('chat-messages')) {
    customElements.define('chat-messages', ChatMessages);
}

export { ChatMessages };
