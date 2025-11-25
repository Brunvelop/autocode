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
 * Carga los modelos disponibles desde el API
 * @returns {Promise<Array<string>>} Lista de modelos disponibles
 */
async function loadAvailableModels() {
    try {
        const response = await fetch('/functions/details');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Extraer choices del parámetro 'model' de la función 'chat'
        const chatFunction = data.functions?.chat;
        if (!chatFunction) {
            console.warn('Chat function not found in API response');
            return null;
        }
        
        const modelParam = chatFunction.parameters?.find(p => p.name === 'model');
        if (!modelParam || !modelParam.choices) {
            console.warn('Model parameter or choices not found');
            return null;
        }
        
        return modelParam.choices;
    } catch (error) {
        console.error('Error loading models:', error);
        return null;
    }
}

/**
 * Popular un selector con las opciones de modelos
 * @param {HTMLSelectElement} selectElement - Elemento select a popular
 * @param {Array<string>} models - Lista de modelos
 * @param {string} selectedValue - Valor a seleccionar (opcional)
 */
function populateModelSelect(selectElement, models, selectedValue = null) {
    if (!selectElement || !models || models.length === 0) return;
    
    // Limpiar opciones existentes
    selectElement.innerHTML = '';
    
    // Crear opciones dinámicamente
    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        
        // Extraer nombre amigable del modelo
        // Formato: "openrouter/provider/model-name" -> "Model Name (Provider)"
        const parts = model.split('/');
        if (parts.length === 3) {
            const provider = parts[1];
            const modelName = parts[2]
                .split('-')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
            option.textContent = `${modelName} (${provider.charAt(0).toUpperCase() + provider.slice(1)})`;
        } else {
            option.textContent = model;
        }
        
        selectElement.appendChild(option);
    });
    
    // Seleccionar valor si se proporciona
    if (selectedValue && models.includes(selectedValue)) {
        selectElement.value = selectedValue;
    }
}

/**
 * Inicializa el selector de modelo y sincroniza con la configuración
 * Escucha cambios tanto del usuario como de la configuración guardada
 */
async function initModelSelector() {
    const modelSelect = document.getElementById('modelSelect');
    
    if (!modelSelect) return;
    
    // Cargar modelos disponibles desde el API
    const models = await loadAvailableModels();
    
    // Si no se pudieron cargar, usar fallback hardcodeado
    const fallbackModels = [
        'openrouter/openai/gpt-4o',
        'openrouter/x-ai/grok-4',
        'openrouter/anthropic/claude-sonnet-4.5',
        'openrouter/openai/gpt-5',
        'openrouter/openai/gpt-5-codex'
    ];
    
    const availableModels = models || fallbackModels;
    
    // Popular el selector
    populateModelSelect(modelSelect, availableModels);
    
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
    
    // Exponer función para uso en otros módulos
    window.chatComponents = window.chatComponents || {};
    window.chatComponents.loadAvailableModels = loadAvailableModels;
    window.chatComponents.populateModelSelect = populateModelSelect;
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
