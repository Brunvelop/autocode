/**
 * floating-chat.js
 * Clase principal del componente de chat flotante
 * 
 * ESTRUCTURA:
 * - Constructor y configuración
 * - Inicialización y setup de componentes
 * - Gestión de estado (drag, contexto, mensajes)
 * - Comunicación con API
 * - Modal de configuración
 */

class FloatingChat {
    // ============================================
    // SECCIÓN 1: CONSTRUCTOR Y CONFIGURACIÓN
    // ============================================
    
    constructor() {
        // Referencias DOM
        this.conversationHistory = [];
        this.chatPanel = document.getElementById('chatPanel');
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messageInput = document.getElementById('messageInput');
        this.chatWindow = document.getElementById('chatWindow');
        this.chatDragHandle = document.getElementById('chatDragHandle');
        
        // Timers
        this.debounceTimer = null;
        
        // Configuración
        this.config = this.loadConfig();
        
        // Inicializar
        this.init();
    }

    /**
     * Carga la configuración desde localStorage con valores por defecto
     * @returns {Object} Configuración del chat
     */
    loadConfig() {
        const defaultConfig = {
            model: 'openrouter/openai/gpt-4o',
            temperature: 0.7,
            max_tokens: 16000,
            module_type: 'ReAct',
            module_kwargs: {}
        };
        
        try {
            const saved = localStorage.getItem('autocode_chat_config');
            return saved ? { ...defaultConfig, ...JSON.parse(saved) } : defaultConfig;
        } catch (e) {
            console.error('Error loading config:', e);
            return defaultConfig;
        }
    }

    /**
     * Guarda la configuración en localStorage
     * @param {Object} config - Configuración a guardar
     */
    saveConfig(config) {
        try {
            localStorage.setItem('autocode_chat_config', JSON.stringify(config));
            this.config = config;
            
            // Notificar a chat-components sobre el cambio
            window.dispatchEvent(new CustomEvent('chatConfigUpdated', { 
                detail: { model: config.model } 
            }));
        } catch (e) {
            console.error('Error saving config:', e);
        }
    }

    // ============================================
    // SECCIÓN 2: INICIALIZACIÓN
    // ============================================

    /**
     * Inicializa todos los componentes del chat
     */
    init() {
        this.setupDrag();
        this.setupConfigModal();
        this.setupFormListeners();
        this.setupHeaderButtons();
    }
    
    /**
     * Configura los listeners del formulario de chat
     */
    setupFormListeners() {
        const chatForm = document.getElementById('chatForm');
        const messageInput = document.getElementById('messageInput');
        
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSubmit(e);
            });
        }
        
        if (messageInput) {
            messageInput.addEventListener('input', () => {
                this.debouncedUpdateContext();
            });
        }
    }
    
    /**
     * Configura los botones del header (cerrar, nueva conversación, config)
     */
    setupHeaderButtons() {
        const chatCloseBtn = document.getElementById('chatCloseBtn');
        const chatPanel = document.getElementById('chatPanel');
        const newChatBtn = document.getElementById('newChatBtn');
        const configBtn = document.getElementById('configBtn');
        
        // Cerrar chat
        if (chatCloseBtn && chatPanel) {
            chatCloseBtn.addEventListener('click', () => {
                chatPanel.classList.add('hidden');
            });
        }
        
        // Nueva conversación
        if (newChatBtn) {
            newChatBtn.addEventListener('click', () => {
                this.resetConversation();
            });
        }
        
        // Configuración
        if (configBtn) {
            configBtn.addEventListener('click', () => {
                this.openConfigModal();
            });
        }
    }

    // ============================================
    // SECCIÓN 3: DRAG & DROP FUNCTIONALITY
    // ============================================

    /**
     * Configura la funcionalidad de arrastrar la ventana de chat
     */
    setupDrag() {
        if (!this.chatWindow || !this.chatDragHandle) return;
        
        let isDragging = false;
        let offsetX = 0, offsetY = 0;

        const onPointerMove = (e) => {
            if (!isDragging) return;
            
            const w = this.chatWindow.offsetWidth;
            const h = this.chatWindow.offsetHeight;
            let x = e.clientX - offsetX;
            let y = e.clientY - offsetY;
            
            // Límites de ventana
            const maxX = Math.max(0, window.innerWidth - w);
            const maxY = Math.max(0, window.innerHeight - h);
            
            x = Math.min(Math.max(0, x), maxX);
            y = Math.min(Math.max(0, y), maxY);
            
            this.chatWindow.style.left = `${x}px`;
            this.chatWindow.style.top = `${y}px`;
        };

        const onPointerUp = () => {
            if (!isDragging) return;
            isDragging = false;
            this.chatDragHandle.classList.remove('cursor-grabbing');
            document.removeEventListener('pointermove', onPointerMove);
            document.removeEventListener('pointerup', onPointerUp);
        };

        this.chatDragHandle.addEventListener('pointerdown', (e) => {
            if (e.button !== undefined && e.button !== 0) return;
            
            isDragging = true;
            this.chatDragHandle.classList.add('cursor-grabbing');

            const rect = this.chatWindow.getBoundingClientRect();
            this.chatWindow.style.left = `${rect.left}px`;
            this.chatWindow.style.top = `${rect.top}px`;
            this.chatWindow.style.right = 'auto';
            this.chatWindow.style.bottom = 'auto';

            offsetX = e.clientX - rect.left;
            offsetY = e.clientY - rect.top;

            document.addEventListener('pointermove', onPointerMove);
            document.addEventListener('pointerup', onPointerUp);
        });
    }

    // ============================================
    // SECCIÓN 4: GESTIÓN DE CONTEXTO
    // ============================================

    /**
     * Actualiza el uso de contexto con debouncing
     */
    debouncedUpdateContext() {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => this.updateContextUsage(), 300);
    }

    /**
     * Calcula y actualiza la barra de uso de contexto
     */
    async updateContextUsage() {
        const currentMessage = this.messageInput.value.trim();
        const model = this.config.model;
        
        // Construir lista de mensajes
        const messages = [...this.conversationHistory];
        if (currentMessage) {
            messages.push({ role: 'user', content: currentMessage });
        }
        
        // Si no hay mensajes, resetear barra
        if (messages.length === 0) {
            if (window.chatHelpers?.resetContextBar) {
                window.chatHelpers.resetContextBar();
            }
            return;
        }
        
        try {
            const response = await fetch('/calculate_context_usage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model, messages })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            const result = data.result || {};
            const current = result.current || 0;
            const max = result.max || 0;
            const percentage = result.percentage || 0;
            
            // Actualizar barra
            if (window.chatHelpers?.updateContextBar) {
                window.chatHelpers.updateContextBar(current, max, percentage);
            }
        } catch (error) {
            console.error('Error calculating context usage:', error);
            // No mostrar error al usuario, solo loguearlo
        }
    }

    // ============================================
    // SECCIÓN 5: COMUNICACIÓN CON API
    // ============================================

    /**
     * Maneja el envío del formulario
     * @param {Event} event - Evento de submit
     */
    async handleSubmit(event) {
        event.preventDefault();
        
        const message = this.messageInput.value.trim();
        if (!message) return;

        // Agregar mensaje del usuario
        if (window.chatHelpers?.addMessage) {
            window.chatHelpers.addMessage('user', message);
        }
        
        this.messageInput.value = '';
        
        if (window.chatHelpers?.setLoading) {
            window.chatHelpers.setLoading(true);
        }

        try {
            const response = await this.sendMessage(message);
            
            if (response.error) {
                if (window.chatHelpers?.addMessage) {
                    window.chatHelpers.addMessage('error', response.error);
                }
            } else {
                if (window.chatHelpers?.addMessage) {
                    window.chatHelpers.addMessage('assistant', response.response, response.dspy_output);
                }
                this.conversationHistory = response.conversation_history || [];
                await this.updateContextUsage();
            }
        } catch (error) {
            console.error('Error en handleSubmit:', error);
            if (window.chatHelpers?.addMessage) {
                window.chatHelpers.addMessage('error', `Error: ${error.message}`);
            }
        } finally {
            if (window.chatHelpers?.setLoading) {
                window.chatHelpers.setLoading(false);
            }
        }
    }

    /**
     * Envía un mensaje al servidor
     * @param {string} message - Mensaje a enviar
     * @returns {Promise<Object>} Respuesta del servidor
     */
    async sendMessage(message) {
        const payload = {
            message: message,
            conversation_history: this.conversationHistory,
            model: this.config.model,
            max_tokens: this.config.max_tokens,
            temperature: this.config.temperature,
            module_type: this.config.module_type,
            module_kwargs: this.config.module_kwargs
        };
        
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data.result || data;
        } catch (error) {
            // Re-lanzar para que handleSubmit lo capture
            throw error;
        }
    }

    // ============================================
    // SECCIÓN 6: UTILIDADES
    // ============================================

    /**
     * Reinicia la conversación y limpia el UI
     */
    resetConversation() {
        this.conversationHistory = [];
        
        if (window.chatHelpers?.clearMessages) {
            window.chatHelpers.clearMessages();
        }
        
        if (window.chatHelpers?.resetContextBar) {
            window.chatHelpers.resetContextBar();
        }
        
        if (this.messageInput) {
            this.messageInput.value = '';
            this.messageInput.focus();
        }
    }

    // ============================================
    // SECCIÓN 7: MODAL DE CONFIGURACIÓN
    // ============================================

    /**
     * Abre el modal de configuración
     */
    openConfigModal() {
        this.loadConfigToModal();
        const configModal = document.getElementById('configModal');
        if (configModal) configModal.classList.remove('hidden');
    }

    /**
     * Carga la configuración actual en el modal
     */
    loadConfigToModal() {
        const modelSelect = document.getElementById('configModel');
        const tempSlider = document.getElementById('configTemperature');
        const tempValue = document.getElementById('tempValue');
        const maxTokens = document.getElementById('configMaxTokens');
        const moduleType = document.getElementById('configModuleType');
        const moduleKwargs = document.getElementById('configModuleKwargs');
        const gpt5Warning = document.getElementById('gpt5Warning');
        
        if (modelSelect) modelSelect.value = this.config.model;
        if (tempSlider) tempSlider.value = this.config.temperature;
        if (tempValue) tempValue.textContent = this.config.temperature;
        if (maxTokens) maxTokens.value = this.config.max_tokens;
        if (moduleType) moduleType.value = this.config.module_type;
        if (moduleKwargs) {
            moduleKwargs.value = Object.keys(this.config.module_kwargs).length > 0 
                ? JSON.stringify(this.config.module_kwargs, null, 2) 
                : '';
        }
        
        // Mostrar warning si es GPT-5
        if (gpt5Warning) {
            gpt5Warning.classList.toggle('hidden', !this.config.model.includes('gpt-5'));
        }
    }

    /**
     * Configura todos los listeners del modal de configuración
     */
    setupConfigModal() {
        const modal = document.getElementById('configModal');
        const closeBtn = document.getElementById('configCloseBtn');
        const saveBtn = document.getElementById('configSaveBtn');
        const resetBtn = document.getElementById('configResetBtn');
        const tempSlider = document.getElementById('configTemperature');
        const tempValue = document.getElementById('tempValue');
        const modelSelect = document.getElementById('configModel');
        const moduleTypeSelect = document.getElementById('configModuleType');
        const moduleKwargsHelp = document.getElementById('moduleKwargsHelp');
        const gpt5Warning = document.getElementById('gpt5Warning');
        
        // Actualizar display de temperatura
        if (tempSlider && tempValue) {
            tempSlider.addEventListener('input', () => {
                tempValue.textContent = tempSlider.value;
            });
        }
        
        // Mostrar warning para GPT-5
        if (modelSelect && gpt5Warning) {
            modelSelect.addEventListener('change', () => {
                const isGPT5 = modelSelect.value.includes('gpt-5');
                gpt5Warning.classList.toggle('hidden', !isGPT5);
            });
        }
        
        // Help de module_kwargs
        if (moduleKwargsHelp) {
            moduleKwargsHelp.addEventListener('click', (e) => {
                e.preventDefault();
                alert('Module Kwargs ejemplos:\n\n' +
                      '- ReAct: {"max_iters": 5}\n' +
                      '- Predict: {"n": 3}\n' +
                      '- MultiChainComparison: {"num_comparisons": 3}\n\n' +
                      'Dejar vacío para usar defaults.');
            });
        }
        
        // Descripción de module_type
        const moduleDescriptions = {
            'Predict': 'Predictor básico sin modificaciones',
            'ChainOfThought': 'Incluye razonamiento paso a paso',
            'ProgramOfThought': 'Genera código para resolver',
            'ReAct': 'Permite usar herramientas y razonar sobre qué usar',
            'MultiChainComparison': 'Compara múltiples outputs y elige el mejor'
        };
        
        if (moduleTypeSelect) {
            moduleTypeSelect.addEventListener('change', () => {
                const desc = document.getElementById('moduleTypeDescription');
                if (desc) desc.textContent = moduleDescriptions[moduleTypeSelect.value] || '';
            });
        }
        
        // Cerrar modal
        if (closeBtn && modal) {
            closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
        }
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) modal.classList.add('hidden');
            });
        }
        
        // Guardar configuración
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this.handleConfigSave();
            });
        }
        
        // Restaurar por defecto
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.handleConfigReset();
            });
        }
    }

    /**
     * Maneja el guardado de configuración
     */
    handleConfigSave() {
        const modal = document.getElementById('configModal');
        const moduleKwargsText = document.getElementById('configModuleKwargs')?.value.trim();
        let moduleKwargs = {};
        
        if (moduleKwargsText) {
            try {
                moduleKwargs = JSON.parse(moduleKwargsText);
            } catch (e) {
                alert('Error en Module Kwargs JSON: ' + e.message);
                return;
            }
        }
        
        const newConfig = {
            model: document.getElementById('configModel')?.value || this.config.model,
            temperature: parseFloat(document.getElementById('configTemperature')?.value) || 0.7,
            max_tokens: parseInt(document.getElementById('configMaxTokens')?.value) || 16000,
            module_type: document.getElementById('configModuleType')?.value || 'ReAct',
            module_kwargs: moduleKwargs
        };
        
        // Validar GPT-5
        if (newConfig.model.includes('gpt-5')) {
            if (newConfig.temperature !== 1.0 || newConfig.max_tokens < 16000) {
                alert('⚠️ GPT-5 requiere temperature=1.0 y max_tokens≥16000');
                return;
            }
        }
        
        this.saveConfig(newConfig);
        if (modal) modal.classList.add('hidden');
        alert('✅ Configuración guardada');
    }

    /**
     * Maneja el reseteo de configuración
     */
    handleConfigReset() {
        if (confirm('¿Restaurar configuración por defecto?')) {
            const defaultConfig = {
                model: 'openrouter/openai/gpt-4o',
                temperature: 0.7,
                max_tokens: 16000,
                module_type: 'ReAct',
                module_kwargs: {}
            };
            this.saveConfig(defaultConfig);
            this.loadConfigToModal();
            alert('✅ Configuración restaurada');
        }
    }
}

// Inicializar chat cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.floatingChat = new FloatingChat();
});
