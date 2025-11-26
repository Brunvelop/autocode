/**
 * chat-settings.js
 * Componente de configuración para el chat
 * Permite ajustar modelo, temperatura y otros parámetros de forma dinámica
 * basándose en la definición de la función del backend.
 */

class ChatSettings extends HTMLElement {
    constructor() {
        super();
        this._settings = {};
        this._funcInfo = null;
    }

    connectedCallback() {
        this.render();
        this._setupEvents();
    }

    /**
     * Configura el componente con la información de la función
     * @param {Object} funcInfo Metadata de la función (incluyendo parámetros)
     */
    configure(funcInfo) {
        this._funcInfo = funcInfo;
        
        // Inicializar settings con valores por defecto
        if (funcInfo && funcInfo.parameters) {
            funcInfo.parameters.forEach(param => {
                // Ignorar parámetros que no son de configuración
                if (['message', 'conversation_history'].includes(param.name)) return;
                
                // Usar default si existe
                if (param.default !== undefined && param.default !== null) {
                    this._settings[param.name] = param.default;
                }
            });
        }
        
        // Re-renderizar con los nuevos controles
        this.render();
        this._setupEvents();
        
        // Emitir cambio inicial para sincronizar
        this.dispatchEvent(new CustomEvent('settings-change', {
            detail: { ...this._settings },
            bubbles: true
        }));
    }

    render() {
        // Estructura base
        this.innerHTML = `
            <div class="relative">
                <!-- Toggle Button -->
                <button 
                    data-ref="toggleBtn"
                    class="text-indigo-100 bg-white/10 hover:bg-white/20 border border-white/20 rounded-full p-1.5 transition-colors"
                    title="Configuración"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.38a2 2 0 0 0-.73-2.73l-.15-.1a2 2 0 0 1-1-1.72v-.51a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
                        <circle cx="12" cy="12" r="3"/>
                    </svg>
                </button>

                <!-- Panel Flotante -->
                <div 
                    data-ref="panel"
                    class="hidden absolute right-0 top-full mt-2 w-72 bg-white rounded-xl shadow-xl border border-gray-200 p-4 z-50 text-gray-800"
                >
                    <h3 class="font-bold text-sm mb-3 flex items-center gap-2">
                        <span>🛠️ Configuración</span>
                    </h3>
                    
                    <div data-ref="controlsContainer" class="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
                        <!-- Controls will be injected here -->
                        ${!this._funcInfo ? '<p class="text-xs text-gray-500 italic">Cargando configuración...</p>' : ''}
                    </div>
                </div>
            </div>
        `;

        if (this._funcInfo) {
            this._renderDynamicControls();
        }
    }

    _renderDynamicControls() {
        const container = this.querySelector('[data-ref="controlsContainer"]');
        if (!container) return;

        container.innerHTML = '';

        this._funcInfo.parameters.forEach(param => {
            // Ignorar parámetros reservados
            if (['message', 'conversation_history'].includes(param.name)) return;

            const wrapper = document.createElement('div');
            wrapper.className = "space-y-1";

            // Etiqueta
            const label = document.createElement('label');
            label.className = "text-xs font-semibold text-gray-500 block";
            label.textContent = this._formatLabel(param.name);
            wrapper.appendChild(label);

            // Control
            let control;

            // Caso 1: Choices (Select)
            if (param.choices && param.choices.length > 0) {
                control = document.createElement('select');
                control.className = "w-full text-sm p-2 border border-gray-300 rounded-lg bg-gray-50 focus:ring-2 focus:ring-indigo-500 outline-none";
                
                param.choices.forEach(choice => {
                    const option = document.createElement('option');
                    option.value = choice;
                    option.textContent = choice;
                    if (choice === this._settings[param.name]) {
                        option.selected = true;
                    }
                    control.appendChild(option);
                });
            }
            // Caso 2: Temperatura (Slider especial)
            else if (param.name === 'temperature') {
                control = this._createTemperatureControl(param);
                wrapper.innerHTML = ''; // Limpiar wrapper para usar layout custom
                wrapper.appendChild(control);
                control = null; // Ya añadido
            }
            // Caso 3: Boolean
            else if (param.type === 'bool') {
                control = document.createElement('div');
                control.className = "flex items-center gap-2";
                
                const checkbox = document.createElement('input');
                checkbox.type = "checkbox";
                checkbox.name = param.name; // Asignar nombre para tests
                checkbox.className = "w-4 h-4 text-indigo-600 bg-gray-100 border-gray-300 rounded focus:ring-indigo-500";
                checkbox.checked = !!this._settings[param.name];
                
                const span = document.createElement('span');
                span.className = "text-sm text-gray-700";
                span.textContent = "Activar";
                
                control.appendChild(checkbox);
                control.appendChild(span);
                
                // Mapear change event del checkbox al wrapper
                checkbox.addEventListener('change', (e) => {
                    this._updateSetting(param.name, e.target.checked);
                });
                
                // No asignamos control a la variable global porque ya manejamos eventos aquí
                wrapper.appendChild(control);
                return container.appendChild(wrapper);
            }
            // Caso 4: Number (Int/Float)
            else if (param.type === 'int' || param.type === 'float') {
                control = document.createElement('input');
                control.type = "number";
                control.className = "w-full text-sm p-2 border border-gray-300 rounded-lg bg-gray-50 focus:ring-2 focus:ring-indigo-500 outline-none";
                control.value = this._settings[param.name] || 0;
                
                if (param.type === 'int') control.step = "1";
                if (param.type === 'float') control.step = "0.1";
            }
            // Caso 5: Default (Text)
            else {
                control = document.createElement('input');
                control.type = "text";
                control.className = "w-full text-sm p-2 border border-gray-300 rounded-lg bg-gray-50 focus:ring-2 focus:ring-indigo-500 outline-none";
                control.value = this._settings[param.name] || '';
            }

            if (control) {
                control.name = param.name;
                control.addEventListener('change', (e) => {
                    let val = e.target.value;
                    if (param.type === 'int') val = parseInt(val);
                    if (param.type === 'float') val = parseFloat(val);
                    this._updateSetting(param.name, val);
                });
                wrapper.appendChild(control);
            }

            container.appendChild(wrapper);
        });
    }

    _createTemperatureControl(param) {
        const wrapper = document.createElement('div');
        wrapper.className = "space-y-1";
        
        const header = document.createElement('div');
        header.className = "flex justify-between";
        
        const label = document.createElement('label');
        label.className = "text-xs font-semibold text-gray-500";
        label.textContent = "Creatividad (Temperature)";
        
        const valueDisplay = document.createElement('span');
        valueDisplay.className = "text-xs font-mono text-indigo-600";
        valueDisplay.textContent = this._settings[param.name] || 0.7;
        
        header.appendChild(label);
        header.appendChild(valueDisplay);
        
        const input = document.createElement('input');
        input.type = "range";
        input.name = param.name; // IMPORTANTE: Asignar nombre para tests y referencias
        input.min = "0";
        input.max = "1"; // Asumimos rango estandar 0-1, aunque podría ser mayor
        input.step = "0.1";
        input.value = this._settings[param.name] || 0.7;
        input.className = "w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600";
        
        const footer = document.createElement('div');
        footer.className = "flex justify-between text-[10px] text-gray-400";
        footer.innerHTML = "<span>Preciso</span><span>Creativo</span>";
        
        input.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            valueDisplay.textContent = val;
            this._updateSetting(param.name, val);
        });
        
        wrapper.appendChild(header);
        wrapper.appendChild(input);
        wrapper.appendChild(footer);
        
        return wrapper;
    }

    _formatLabel(name) {
        // Convertir snake_case a Title Case amigable
        return name
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    _updateSetting(name, value) {
        this._settings[name] = value;
        this.dispatchEvent(new CustomEvent('settings-change', {
            detail: { ...this._settings },
            bubbles: true
        }));
    }

    _setupEvents() {
        const toggleBtn = this.querySelector('[data-ref="toggleBtn"]');
        const panel = this.querySelector('[data-ref="panel"]');
        
        if (!toggleBtn || !panel) return;

        // Limpiar listeners anteriores (si render se llama múltiples veces)
        // Nota: replaceWith clonado es una forma rápida de limpiar listeners, 
        // pero aquí simplemente reasignamos porque render() recrea el DOM.
        
        toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            panel.classList.toggle('hidden');
        });

        // Evitar conflicto con Drag & Drop
        ['pointerdown', 'mousedown', 'click'].forEach(evt => {
            panel.addEventListener(evt, (e) => e.stopPropagation());
        });

        // Close on outside click
        // Usamos una referencia a la función para poder removerla si desconectamos?
        // En este caso simple, document listener se acumula si no limpiamos.
        // TODO: Implementar disconnectedCallback para limpieza si fuera un componente SPA complejo.
        document.addEventListener('click', (e) => {
            if (!this.contains(e.target)) {
                panel.classList.add('hidden');
            }
        });
    }

    getSettings() {
        return { ...this._settings };
    }
}

if (!customElements.get('chat-settings')) {
    customElements.define('chat-settings', ChatSettings);
}

export { ChatSettings };
