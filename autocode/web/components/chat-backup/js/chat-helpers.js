/**
 * chat-helpers.js
 * Funciones helper compartidas para el componente de chat flotante
 * 
 * ÍNDICE:
 * 1. Context Bar - Gestión de barra de progreso de contexto
 * 2. Loading State - Estados de carga del formulario
 * 3. Messages - Gestión de mensajes en el chat
 * 4. DSPy Modal - Modal de información detallada de DSPy
 * 
 * NOTA: Todas las funciones se exponen mediante el namespace window.chatHelpers
 * para evitar colisiones en el scope global.
 */

// Namespace global para helpers
window.chatHelpers = window.chatHelpers || {};

// ============================================
// SECCIÓN 1: HELPERS DE UI - CONTEXT BAR
// ============================================

/**
 * Actualiza la barra de progreso del contexto con información de tokens
 * Cambia el color según el porcentaje de uso:
 * - Verde: < 70%
 * - Amarillo: 70-90%
 * - Rojo: > 90%
 * 
 * @param {number} current - Tokens actuales usados
 * @param {number} max - Tokens máximos disponibles del modelo
 * @param {number} percentage - Porcentaje de uso (0-100)
 */
window.chatHelpers.updateContextBar = function(current, max, percentage) {
    const contextStats = document.getElementById('contextStats');
    const contextBar = document.getElementById('contextBar');
    
    if (!contextStats || !contextBar) return;
    
    contextStats.textContent = `${current.toLocaleString()} / ${max.toLocaleString()}`;
    contextBar.style.width = `${Math.min(percentage, 100)}%`;
    
    // Cambiar color según uso (verde < 70%, amarillo 70-90%, rojo > 90%)
    if (percentage < 70) {
        contextBar.className = 'h-full bg-green-500 transition-all duration-300';
    } else if (percentage < 90) {
        contextBar.className = 'h-full bg-yellow-500 transition-all duration-300';
    } else {
        contextBar.className = 'h-full bg-red-500 transition-all duration-300';
    }
};

/**
 * Resetea la barra de contexto a su estado inicial
 */
window.chatHelpers.resetContextBar = function() {
    const contextStats = document.getElementById('contextStats');
    const contextBar = document.getElementById('contextBar');
    
    if (contextStats) contextStats.textContent = '0 / 0';
    if (contextBar) {
        contextBar.style.width = '0%';
        contextBar.className = 'h-full bg-green-500 transition-all duration-300';
    }
};

/**
 * SECCIÓN 2: HELPERS DE UI - Loading State
 */

/**
 * Establece el estado de carga del formulario
 * @param {boolean} loading - Si está cargando o no
 */
window.chatHelpers.setLoading = function(loading) {
    const sendBtn = document.getElementById('sendBtn');
    const messageInput = document.getElementById('messageInput');
    
    if (sendBtn) {
        sendBtn.disabled = loading;
        sendBtn.textContent = loading ? 'Pensando... 🤔' : 'Enviar 🚀';
        sendBtn.setAttribute('aria-busy', loading);
    }
    
    if (messageInput) {
        messageInput.disabled = loading;
        messageInput.setAttribute('aria-busy', loading);
    }
};

/**
 * SECCIÓN 3: HELPERS DE MENSAJES
 */

/**
 * Agrega un mensaje al contenedor de mensajes
 * @param {string} role - Rol del mensaje ('user', 'assistant', 'error')
 * @param {string} content - Contenido del mensaje
 * @param {Object|null} dspyOutput - Output de DSPy (opcional)
 */
window.chatHelpers.addMessage = function(role, content, dspyOutput = null) {
    const messagesContainer = document.getElementById('messagesContainer');
    const emptyState = document.getElementById('emptyState');
    
    if (!messagesContainer) return;
    
    // Ocultar estado vacío si existe
    if (emptyState) emptyState.style.display = 'none';
    
    // Crear contenedor del mensaje
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'}`;
    messageDiv.setAttribute('role', 'article');
    messageDiv.setAttribute('aria-label', `Mensaje de ${role === 'user' ? 'usuario' : role === 'error' ? 'error' : 'asistente'}`);
    
    // Crear burbuja del mensaje
    const bubble = document.createElement('div');
    bubble.className = `max-w-[85%] rounded-2xl px-4 py-3 ${
        role === 'user' 
            ? 'bg-indigo-600 text-white shadow-md' 
            : role === 'error'
            ? 'bg-red-50 text-red-800 border border-red-300 ring-1 ring-red-200'
            : 'bg-white text-gray-800 shadow-sm border border-gray-200 ring-1 ring-black/5'
    }`;
    
    // Etiqueta del mensaje
    const label = document.createElement('div');
    label.className = 'font-bold text-sm mb-1';
    label.textContent = role === 'user' ? '👤 Tú' : role === 'error' ? '❌ Error' : '🤖 Asistente';
    
    // Contenido del mensaje
    const text = document.createElement('div');
    text.className = 'whitespace-pre-wrap break-words text-sm';
    text.textContent = content;
    
    bubble.appendChild(label);
    bubble.appendChild(text);
    
    // Botón "Más info" para DSPy output (solo asistente)
    if (role === 'assistant' && dspyOutput && window.chatHelpers.showDspyModal) {
        const moreInfoBtn = document.createElement('button');
        moreInfoBtn.className = 'mt-2 text-xs bg-indigo-100 hover:bg-indigo-200 text-indigo-700 font-semibold py-1 px-3 rounded-full transition';
        moreInfoBtn.textContent = '📊 Más info DSPy';
        moreInfoBtn.setAttribute('aria-label', 'Ver más información de DSPy');
        moreInfoBtn.onclick = () => window.chatHelpers.showDspyModal(dspyOutput);
        bubble.appendChild(moreInfoBtn);
    }
    
    messageDiv.appendChild(bubble);
    messagesContainer.appendChild(messageDiv);
    
    // Auto-scroll al final
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
};

/**
 * Limpia todos los mensajes del contenedor
 */
window.chatHelpers.clearMessages = function() {
    const messagesContainer = document.getElementById('messagesContainer');
    const emptyState = document.getElementById('emptyState');
    
    if (!messagesContainer) return;
    
    messagesContainer.innerHTML = '';
    
    // Restaurar estado vacío si existe
    if (emptyState) {
        emptyState.style.display = '';
        messagesContainer.appendChild(emptyState);
    }
};

/**
 * SECCIÓN 4: MODAL DE DSPy OUTPUT
 */

/**
 * Muestra un modal con el output detallado de DSPy
 * @param {Object} dspyOutput - Objeto con datos de DSPy
 */
window.chatHelpers.showDspyModal = function(dspyOutput) {
    if (!dspyOutput) return;
    
    // Crear modal overlay
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 z-[120] bg-black/50 flex items-center justify-center p-4';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'dspy-modal-title');
    modal.onclick = (e) => {
        if (e.target === modal) modal.remove();
    };
    
    // Contenido del modal
    const modalContent = document.createElement('div');
    modalContent.className = 'bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden flex flex-col';
    
    // Header
    const modalHeader = document.createElement('div');
    modalHeader.className = 'bg-gradient-to-r from-indigo-600 to-violet-600 p-4 flex items-center justify-between';
    modalHeader.innerHTML = `
        <h3 id="dspy-modal-title" class="text-white font-bold text-lg">📊 DSPy Output & Metadata</h3>
        <button class="text-white hover:bg-white/20 rounded-full p-2 transition" 
                onclick="this.closest('[role=dialog]').remove()" 
                aria-label="Cerrar modal">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
        </button>
    `;
    
    // Body
    const modalBody = document.createElement('div');
    modalBody.className = 'flex-1 overflow-y-auto p-6 space-y-4';
    
    // Helper para crear secciones
    const createSection = (title, content, icon = '📄') => {
        if (!content) return '';
        const value = typeof content === 'object' ? JSON.stringify(content, null, 2) : content;
        return `
            <div class="border border-gray-200 rounded-xl p-4 bg-gray-50">
                <h4 class="font-bold text-gray-800 mb-2">${icon} ${title}</h4>
                <pre class="bg-white p-3 rounded-lg text-xs overflow-x-auto border border-gray-300"><code>${value}</code></pre>
            </div>
        `;
    };
    
    // Construir contenido
    let sections = '';
    
    // Estado de éxito
    sections += `
        <div class="flex items-center gap-2 p-3 rounded-xl ${dspyOutput.success ? 'bg-green-50 border border-green-300' : 'bg-red-50 border border-red-300'}">
            <span class="text-2xl">${dspyOutput.success ? '✅' : '❌'}</span>
            <span class="font-bold">${dspyOutput.success ? 'Success' : 'Failed'}</span>
            ${dspyOutput.message ? `<span class="text-sm text-gray-600">- ${dspyOutput.message}</span>` : ''}
        </div>
    `;
    
    // Secciones de datos
    if (dspyOutput.result) sections += createSection('Result', dspyOutput.result, '🎯');
    if (dspyOutput.reasoning) sections += createSection('Reasoning', dspyOutput.reasoning, '🧠');
    if (dspyOutput.completions?.length > 0) sections += createSection('Completions', dspyOutput.completions, '📝');
    if (dspyOutput.observations?.length > 0) sections += createSection('Observations', dspyOutput.observations, '👁️');
    
    // History con detalles expandibles
    if (dspyOutput.history?.length > 0) {
        sections += `
            <div class="border border-indigo-200 rounded-xl p-4 bg-indigo-50">
                <h4 class="font-bold text-indigo-900 mb-3">🔍 LM History (${dspyOutput.history.length} calls)</h4>
                <div class="space-y-3">
                    ${dspyOutput.history.map((entry, idx) => `
                        <details class="bg-white rounded-lg border border-indigo-200">
                            <summary class="cursor-pointer p-3 font-semibold text-indigo-700 hover:bg-indigo-50">
                                Call #${idx + 1} - ${entry.model || 'Unknown model'}
                            </summary>
                            <div class="p-3 space-y-2 border-t border-indigo-100">
                                ${entry.usage ? `<div class="text-sm"><strong>Usage:</strong> <code class="bg-gray-100 px-2 py-1 rounded">${JSON.stringify(entry.usage)}</code></div>` : ''}
                                ${entry.cost ? `<div class="text-sm"><strong>Cost:</strong> <code class="bg-green-100 px-2 py-1 rounded text-green-800">$${entry.cost}</code></div>` : ''}
                                ${entry.timestamp ? `<div class="text-sm"><strong>Timestamp:</strong> ${entry.timestamp}</div>` : ''}
                                <details class="mt-2">
                                    <summary class="cursor-pointer text-sm font-semibold text-gray-700">Full Entry JSON</summary>
                                    <pre class="mt-2 bg-gray-50 p-2 rounded text-xs overflow-x-auto border"><code>${JSON.stringify(entry, null, 2)}</code></pre>
                                </details>
                            </div>
                        </details>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    modalBody.innerHTML = sections;
    
    // Ensamblar modal
    modalContent.appendChild(modalHeader);
    modalContent.appendChild(modalBody);
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
};
