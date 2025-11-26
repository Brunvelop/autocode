/**
 * chat-messages.js
 * Componente para mostrar mensajes del chat
 * 
 * Métodos:
 * - addMessage(role, content): Añade un mensaje (role: 'user' | 'assistant' | 'error')
 * - clear(): Elimina todos los mensajes
 * - getMessages(): Retorna array de mensajes
 */

import './chat-debug-info.js';

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
     * @param {string|object} content - Contenido del mensaje (texto o DspyOutput result)
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
        body.className = 'text-sm space-y-2';
        
        // Renderizar contenido rico
        if (typeof content === 'object' && content !== null) {
            // Renderizar Reasoning (Chain of Thought)
            if (content.reasoning) {
                body.appendChild(this._renderReasoning(content.reasoning));
            }

            // Renderizar Trajectory (ReAct)
            if (content.trajectory) {
                body.appendChild(this._renderTrajectory(content.trajectory));
            }

            // Renderizar Respuesta Principal
            // DspyOutput pone la respuesta en result.response o result
            let mainText = '';
            if (content.result && typeof content.result === 'string') mainText = content.result;
            else if (content.result && content.result.response) mainText = content.result.response;
            else if (content.response) mainText = content.response;
            else mainText = JSON.stringify(content.result || content, null, 2);

            const textDiv = document.createElement('div');
            textDiv.className = 'whitespace-pre-wrap break-words';
            textDiv.textContent = mainText;
            body.appendChild(textDiv);

            // Renderizar Debug Info (solo para assistant y si hay objeto complejo)
            if (role === 'assistant') {
                const debugInfo = document.createElement('chat-debug-info');
                debugInfo.data = content;
                body.appendChild(debugInfo);
            }
        } else {
            // Texto plano
            const textDiv = document.createElement('div');
            textDiv.className = 'whitespace-pre-wrap break-words';
            textDiv.textContent = content;
            body.appendChild(textDiv);
        }

        bubble.appendChild(header);
        bubble.appendChild(body);
        messageDiv.appendChild(bubble);
        this._container.appendChild(messageDiv);

        // Auto-scroll al final
        this._scrollToBottom();
    }

    _renderReasoning(reasoning) {
        const details = document.createElement('details');
        details.className = 'group bg-gray-50 rounded-lg border border-gray-200 overflow-hidden';
        details.dataset.type = 'reasoning'; // Para testing
        
        const summary = document.createElement('summary');
        summary.className = 'px-3 py-2 cursor-pointer bg-gray-100 hover:bg-gray-200 transition-colors text-xs font-semibold text-gray-600 flex items-center select-none';
        summary.innerHTML = `
            <span class="mr-2">🧠</span> Ver proceso de pensamiento
            <svg class="w-4 h-4 ml-auto transform group-open:rotate-180 transition-transform text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
        `;
        
        const content = document.createElement('div');
        content.className = 'p-3 bg-white text-gray-700 whitespace-pre-wrap font-mono text-xs border-t border-gray-200';
        content.textContent = reasoning;
        
        details.appendChild(summary);
        details.appendChild(content);
        return details;
    }

    _renderTrajectory(trajectory) {
        const container = document.createElement('div');
        container.className = 'space-y-2 mb-3';

        // La trayectoria viene normalizada del backend como lista de pasos
        // Si no es array, lo envolvemos (ej: un solo paso o formato desconocido)
        let steps = Array.isArray(trajectory) ? trajectory : [trajectory];
        
        // Si trajectory es null o vacio
        if (!trajectory || (Array.isArray(trajectory) && trajectory.length === 0)) return container;

        if (steps.length === 0) return container;

        const title = document.createElement('div');
        title.className = 'text-xs font-semibold text-gray-500 mb-1 flex items-center gap-1';
        title.innerHTML = '<span>🛠️ Uso de Herramientas</span>';
        container.appendChild(title);

        steps.forEach((step, index) => {
            // Intentar normalizar estructura del paso (puede variar según módulo DSPy)
            const toolName = step.tool_name || step.tool || 'Unknown Tool';
            const toolInput = step.tool_input || step.input || step.args || '';
            const thought = step.thought || '';
            const observation = step.observation || step.result || '';

            const stepDiv = document.createElement('div');
            stepDiv.className = 'text-xs border-l-2 border-indigo-200 pl-3 py-1 space-y-1';
            
            if (thought) {
                stepDiv.innerHTML += `<div class="text-gray-500 italic">💭 ${thought}</div>`;
            }
            
            stepDiv.innerHTML += `
                <div class="font-mono text-indigo-600 bg-indigo-50 px-2 py-1 rounded inline-block">
                    ${toolName}(${typeof toolInput === 'string' ? toolInput : JSON.stringify(toolInput)})
                </div>
            `;
            
            if (observation) {
                const obsDiv = document.createElement('details');
                obsDiv.className = 'mt-1';
                obsDiv.innerHTML = `
                    <summary class="cursor-pointer text-gray-400 hover:text-gray-600 select-none">Ver resultado</summary>
                    <div class="mt-1 p-2 bg-gray-50 rounded border border-gray-200 font-mono text-gray-600 whitespace-pre-wrap max-h-32 overflow-y-auto">
                        ${typeof observation === 'string' ? observation : JSON.stringify(observation, null, 2)}
                    </div>
                `;
                stepDiv.appendChild(obsDiv);
            }

            container.appendChild(stepDiv);
        });

        return container;
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
