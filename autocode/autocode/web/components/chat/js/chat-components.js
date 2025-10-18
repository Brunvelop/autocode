/**
 * chat-components.js
 * Inicialización de componentes individuales del chat
 * Organización: Event listeners y funcionalidades específicas por componente
 * 
 * ÍNDICE:
 * 1. Chat Toggle Button - Apertura/cierre del panel
 * 2. Model Selector - Sincronización de selector de modelo
 * 3. Resize Handle - Redimensionamiento con throttling
 * 4. Inicialización Global - DOMContentLoaded
 */

// ============================================
// SECCIÓN 1: CHAT TOGGLE BUTTON
// ============================================

/**
 * Inicializa el botón flotante que abre/cierra el panel de chat
 */
function initChatToggleButton() {
    const chatToggleBtn = document.getElementById('chatToggleBtn');
    const chatPanel = document.getElementById('chatPanel');
    
    if (!chatToggleBtn || !chatPanel) return;
    
    chatToggleBtn.addEventListener('click', () => {
        const wasHidden = chatPanel.classList.contains('hidden');
        chatPanel.classList.toggle('hidden');
        
        // Actualizar aria-expanded
        chatToggleBtn.setAttribute('aria-expanded', wasHidden ? 'true' : 'false');
        
        // Focus en input si se abre el chat
        if (wasHidden) {
            const messageInput = document.getElementById('messageInput');
            if (messageInput) {
                // Delay para asegurar que el panel esté visible
                setTimeout(() => messageInput.focus(), 100);
            }
        }
    });
}

// ============================================
// SECCIÓN 2: MODEL SELECTOR
// ============================================

/**
 * Inicializa el selector de modelo y sincroniza con la configuración
 * Escucha cambios tanto del usuario como de la configuración guardada
 */
function initModelSelector() {
    const modelSelect = document.getElementById('modelSelect');
    
    if (!modelSelect) return;
    
    // Función para actualizar el selector desde la configuración
    const updateFromConfig = () => {
        if (window.floatingChat?.config?.model) {
            modelSelect.value = window.floatingChat.config.model;
        }
    };
    
    // Inicializar con el modelo configurado cuando FloatingChat esté listo
    // Usar un pequeño delay para asegurar que FloatingChat se haya inicializado
    setTimeout(updateFromConfig, 50);
    
    // Escuchar evento personalizado cuando se actualiza la configuración
    window.addEventListener('chatConfigUpdated', (e) => {
        if (e.detail?.model) {
            modelSelect.value = e.detail.model;
        }
    });
    
    // Actualizar config y contexto cuando el usuario cambia el modelo
    modelSelect.addEventListener('change', () => {
        if (window.floatingChat) {
            window.floatingChat.config.model = modelSelect.value;
            window.floatingChat.updateContextUsage();
        }
    });
}

// ============================================
// SECCIÓN 3: RESIZE HANDLE
// ============================================

/**
 * Función de throttling para optimizar eventos de alta frecuencia
 * @param {Function} func - Función a throttlear
 * @param {number} limit - Tiempo mínimo entre ejecuciones (ms)
 * @returns {Function} Función throttleada
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Inicializa el handle de redimensionamiento de la ventana de chat
 * Usa throttling para optimizar rendimiento durante el resize
 */
function initResizeHandle() {
    const chatWindow = document.getElementById('chatWindow');
    const chatResizeHandle = document.getElementById('chatResizeHandle');
    
    if (!chatWindow || !chatResizeHandle) return;
    
    let isResizing = false;
    let startX = 0, startY = 0, startW = 0, startH = 0;
    
    /**
     * Función de resize con cálculo de límites
     */
    const performResize = (e) => {
        if (!isResizing) return;
        
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        
        const rect = chatWindow.getBoundingClientRect();
        let newW = startW + dx;
        let newH = startH + dy;
        
        const top = rect.top;
        const left = rect.left;
        const viewportW = window.innerWidth;
        const viewportH = window.innerHeight;
        const margin = 8;
        
        // Tamaños mínimos responsivos
        const minW = viewportW < 420 ? Math.max(280, viewportW - margin * 2) : 420;
        const minH = viewportH < 600 ? Math.max(260, viewportH - margin * 2) : 300;
        
        // Tamaños máximos
        const maxW = viewportW - margin;
        const maxH = viewportH - margin;
        
        newW = Math.min(Math.max(minW, newW), maxW);
        newH = Math.min(Math.max(minH, newH), maxH);
        
        // Recolocar si se sale por la derecha
        let newLeft = left;
        const overflowRight = (left + newW) - (viewportW - margin);
        if (overflowRight > 0) {
            newLeft = Math.max(margin, left - overflowRight);
        } else {
            // Mantener dentro por la izquierda
            newLeft = Math.max(margin, Math.min(left, viewportW - margin - newW));
        }
        
        chatWindow.style.left = `${newLeft}px`;
        chatWindow.style.width = `${newW}px`;
        chatWindow.style.height = `${newH}px`;
    };
    
    // Aplicar throttling al resize para mejor rendimiento (16ms ≈ 60fps)
    const throttledResize = throttle(performResize, 16);
    
    const onPointerMove = (e) => {
        throttledResize(e);
    };
    
    const onPointerUp = () => {
        if (!isResizing) return;
        isResizing = false;
        document.removeEventListener('pointermove', onPointerMove);
        document.removeEventListener('pointerup', onPointerUp);
    };
    
    chatResizeHandle.addEventListener('pointerdown', (e) => {
        // Solo botón izquierdo del mouse
        if (e.button !== undefined && e.button !== 0) return;
        
        const rect = chatWindow.getBoundingClientRect();
        
        // Fijar tamaño actual en px para override de clases Tailwind
        chatWindow.style.width = `${rect.width}px`;
        chatWindow.style.height = `${rect.height}px`;
        
        startX = e.clientX;
        startY = e.clientY;
        startW = rect.width;
        startH = rect.height;
        
        isResizing = true;
        document.addEventListener('pointermove', onPointerMove);
        document.addEventListener('pointerup', onPointerUp);
    });
}

/**
 * SECCIÓN 4: INICIALIZACIÓN GLOBAL
 * Ejecuta todas las inicializaciones cuando el DOM está listo
 */
document.addEventListener('DOMContentLoaded', () => {
    initChatToggleButton();
    initModelSelector();
    initResizeHandle();
});
