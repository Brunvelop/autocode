/**
 * auto-element-generator.js
 * Generador automático de Custom Elements para funciones del registry
 * 
 * CARACTERÍSTICAS:
 * - Auto-detección de funciones via /functions/details
 * - Creación dinámica de Web Components (e.g., <auto-multiply>)
 * - Encapsulación completa de lógica funcional básica
 * - UI mínima con Tailwind CSS
 * - Slots para personalización completa de UI
 * - Atributos observados para configuración
 * - Eventos para hooks externos
 * - Métodos públicos para extensión programática
 * 
 * EXTENSIBILIDAD:
 * - Slots: header, toolbar, params-ui, execute-button, result-ui, status, footer
 * - Atributos: auto-execute, show-result, show-params, readonly
 * - Eventos: function-connected, before-execute, after-execute, execute-error, params-changed
 * - Métodos: execute(), getResult(), setParam(), getParam(), getParams(), validate()
 */

export class AutoElementGenerator {
    constructor() {
        this.functions = {};
        this.registeredElements = new Set();
    }

    /**
     * Inicializar: cargar funciones y generar elementos
     */
    async init() {
        try {
            await this.loadFunctions();
            this.generateAllElements();
            console.log(`✅ ${this.registeredElements.size} custom elements generados:`, 
                       Array.from(this.registeredElements));
        } catch (error) {
            console.error('❌ Error inicializando auto-element-generator:', error);
            throw error;
        }
    }

    /**
     * Cargar funciones desde /functions/details
     */
    async loadFunctions() {
        const response = await fetch('/functions/details');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        this.functions = data.functions;
        console.log(`📦 Cargadas ${Object.keys(this.functions).length} funciones`);
    }

    /**
     * Generar custom elements para todas las funciones
     */
    generateAllElements() {
        for (const [funcName, funcInfo] of Object.entries(this.functions)) {
            this.generateElement(funcName, funcInfo);
        }
    }

    /**
     * Generar un custom element para una función específica
     */
    generateElement(funcName, funcInfo) {
        const elementName = `auto-${funcName}`;
        
        // Evitar registros duplicados
        if (customElements.get(elementName)) {
            console.warn(`⚠️ Custom element ${elementName} ya está registrado`);
            return;
        }

        // Crear clase dinámica que extiende AutoFunctionElement
        const ElementClass = this.createElementClass(funcName, funcInfo);
        
        // Registrar el custom element
        customElements.define(elementName, ElementClass);
        this.registeredElements.add(elementName);
        
        console.log(`✨ Registrado: <${elementName}>`);
    }

    /**
     * Crear clase de custom element para una función
     */
    createElementClass(funcName, funcInfo) {
        const generator = this;
        
        return class extends HTMLElement {
            static get observedAttributes() {
                return [
                    'auto-execute',    // true/false (ejecuta al cargar)
                    'show-result',     // true/false (muestra resultado)
                    'show-params',     // true/false (muestra formulario)
                    'readonly'         // true/false (modo solo lectura)
                ];
            }

            constructor() {
                super();
                this.funcName = funcName;
                this.funcInfo = funcInfo;
                this.result = null;
                this.errors = {};
                
                // Config desde atributos
                this._autoExecute = false;
                this._showResult = true;
                this._showParams = true;
                this._readonly = false;
            }

            connectedCallback() {
                this.loadAttributeDefaults();
                this.render();
                this.setupEventListeners();
                
                if (this._autoExecute) {
                    this.executeWithDefaults();
                }
                
                // Dispatch evento de conexión
                this.dispatchEvent(new CustomEvent('function-connected', {
                    detail: { funcName, funcInfo },
                    bubbles: true,
                    composed: true
                }));
            }

            attributeChangedCallback(name, oldValue, newValue) {
                if (oldValue === newValue) return;
                
                switch (name) {
                    case 'auto-execute':
                        this._autoExecute = newValue === 'true';
                        break;
                    case 'show-result':
                        this._showResult = newValue !== 'false';
                        this.updateResultVisibility();
                        break;
                    case 'show-params':
                        this._showParams = newValue !== 'false';
                        this.updateParamsVisibility();
                        break;
                    case 'readonly':
                        this._readonly = newValue === 'true';
                        this.updateReadonly();
                        break;
                }
            }

            loadAttributeDefaults() {
                this._autoExecute = this.getAttribute('auto-execute') === 'true';
                this._showResult = this.getAttribute('show-result') !== 'false';
                this._showParams = this.getAttribute('show-params') !== 'false';
                this._readonly = this.getAttribute('readonly') === 'true';
            }

            render() {
                const html = this.getHTML();
                this.innerHTML = html;
            }

            getHTML() {
                const paramsHTML = this.funcInfo.parameters
                    .map(param => this.createParamHTML(param))
                    .join('');

                return `
                    <div class="flex flex-col gap-4 p-4 border border-gray-200 rounded-lg bg-white shadow-sm" data-part="container">
                        
                        <!-- Slot para header customizable -->
                        <slot name="header">
                            <div class="flex justify-between items-center gap-4">
                                <slot name="title">
                                    <h3 class="text-xl font-semibold text-gray-800 m-0" data-part="title">
                                        🔧 ${this.funcInfo.name}
                                    </h3>
                                </slot>
                                
                                <!-- Slot para toolbar (botones extra) -->
                                <div class="flex gap-2 items-center">
                                    <slot name="toolbar"></slot>
                                </div>
                            </div>
                            
                            ${this.funcInfo.description ? `
                                <p class="text-sm text-gray-600 italic m-0">
                                    ${this.funcInfo.description}
                                </p>
                            ` : ''}
                            
                            <div class="flex gap-2 flex-wrap">
                                ${this.funcInfo.http_methods.map(method => 
                                    `<span class="px-2 py-0.5 rounded-full text-xs font-bold ${method === 'GET' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}">${method}</span>`
                                ).join('')}
                            </div>
                        </slot>
                        
                        <!-- Mensaje de error general -->
                        <div data-ref="error" class="hidden p-3 bg-red-100 border border-red-300 rounded-lg text-red-800 text-sm" data-part="error-message">
                        </div>
                        
                        <!-- Slot para UI custom de parámetros -->
                        <slot name="params-ui">
                            <div class="${!this._showParams ? 'hidden' : ''} flex flex-col gap-3" data-ref="defaultParams">
                                ${paramsHTML}
                            </div>
                        </slot>
                        
                        <!-- Slot para botón custom -->
                        <slot name="execute-button">
                            <button 
                                data-ref="executeBtn"
                                class="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                                data-part="execute-button">
                                Ejecutar ${this.funcInfo.name} ⚡
                            </button>
                        </slot>
                        
                        <!-- Slot para resultado custom -->
                        <slot name="result-ui">
                            <div data-ref="resultContainer" class="${!this._showResult ? 'hidden' : ''} hidden p-3 rounded-lg font-mono text-sm whitespace-pre-wrap break-words" data-part="result-container">
                            </div>
                        </slot>
                        
                        <!-- Slot para status customizable -->
                        <slot name="status">
                            <div class="flex gap-2 items-center text-xs text-gray-600" data-part="status">
                                <div data-ref="indicator" class="w-2 h-2 rounded-full bg-gray-300" data-part="status-indicator"></div>
                                <span data-ref="statusText">Listo</span>
                            </div>
                        </slot>
                        
                        <!-- Slot para footer -->
                        <slot name="footer"></slot>
                    </div>
                `;
            }

            createParamHTML(param) {
                const requiredMark = param.required ? '<span class="text-red-500">*</span>' : '';
                const defaultValue = param.default !== null ? param.default : '';
                
                if (param.choices && Array.isArray(param.choices) && param.choices.length > 0) {
                    const options = param.choices.map(choice => 
                        `<option value="${choice}" ${choice === defaultValue ? 'selected' : ''}>${choice}</option>`
                    ).join('');
                    
                    return `
                        <div class="flex flex-col gap-1" data-param="${param.name}">
                            <label class="text-sm font-semibold text-gray-700">
                                ${param.name} ${requiredMark}
                            </label>
                            <p class="text-xs text-gray-500 m-0">
                                ${param.description} (${param.type})
                            </p>
                            <select 
                                name="${param.name}" 
                                ${param.required ? 'required' : ''}
                                class="p-2 border border-gray-300 rounded-lg text-sm bg-white text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 disabled:bg-gray-100 disabled:cursor-not-allowed">
                                ${options}
                            </select>
                        </div>
                    `;
                } else {
                    const inputType = param.type === 'int' || param.type === 'float' ? 'number' : 'text';
                    const step = param.type === 'float' ? 'step="0.01"' : '';
                    return `
                        <div class="flex flex-col gap-1" data-param="${param.name}">
                            <label class="text-sm font-semibold text-gray-700">
                                ${param.name} ${requiredMark}
                            </label>
                            <p class="text-xs text-gray-500 m-0">
                                ${param.description} (${param.type})
                            </p>
                            <input 
                                type="${inputType}" 
                                name="${param.name}" 
                                value="${defaultValue}"
                                ${step}
                                ${param.required ? 'required' : ''}
                                placeholder="${param.description}"
                                class="p-2 border border-gray-300 rounded-lg text-sm bg-white text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 disabled:bg-gray-100 disabled:cursor-not-allowed"
                            />
                        </div>
                    `;
                }
            }

            setupEventListeners() {
                const executeBtn = this.querySelector('[data-ref="executeBtn"]');
                if (executeBtn) {
                    executeBtn.addEventListener('click', () => this.execute());
                }
                
                // Escuchar cambios en parámetros
                const inputs = this.querySelectorAll('input, select');
                inputs.forEach(input => {
                    input.addEventListener('change', () => {
                        this.dispatchEvent(new CustomEvent('params-changed', {
                            detail: { params: this.getParams() },
                            bubbles: true,
                            composed: true
                        }));
                    });
                });
                
                // Escuchar clicks en slots para execute-button
                const executeSlot = this.querySelector('slot[name="execute-button"]');
                if (executeSlot) {
                    executeSlot.addEventListener('click', (e) => {
                        if (e.target.matches('button')) {
                            this.execute();
                        }
                    });
                }
            }

            async execute() {
                // Validar antes de ejecutar
                if (!this.validate()) {
                    this.showError('Por favor, completa todos los campos requeridos');
                    return;
                }
                
                const params = this.getParams();
                
                // Dispatch evento pre-ejecución (permite cancelar)
                const preEvent = new CustomEvent('before-execute', {
                    detail: { funcName: this.funcName, params },
                    bubbles: true,
                    composed: true,
                    cancelable: true
                });
                
                if (!this.dispatchEvent(preEvent)) {
                    console.log('Ejecución cancelada por before-execute handler');
                    return;
                }
                
                const executeBtn = this.querySelector('[data-ref="executeBtn"]');
                if (executeBtn) {
                    executeBtn.disabled = true;
                    executeBtn.textContent = 'Ejecutando...';
                }
                
                this.setStatus('loading', 'Ejecutando...');
                this.hideError();
                
                try {
                    const result = await this.callAPI(params);
                    this.result = result;
                    this.showResult(result, false);
                    this.setStatus('success', 'Ejecutado correctamente');
                    
                    // Dispatch evento post-ejecución
                    this.dispatchEvent(new CustomEvent('after-execute', {
                        detail: { funcName: this.funcName, params, result },
                        bubbles: true,
                        composed: true
                    }));
                } catch (error) {
                    this.showResult(`Error: ${error.message}`, true);
                    this.setStatus('error', 'Error en ejecución');
                    
                    this.dispatchEvent(new CustomEvent('execute-error', {
                        detail: { funcName: this.funcName, params, error },
                        bubbles: true,
                        composed: true
                    }));
                } finally {
                    if (executeBtn) {
                        executeBtn.disabled = false;
                        executeBtn.textContent = `Ejecutar ${this.funcInfo.name} ⚡`;
                    }
                }
            }

            async executeWithDefaults() {
                await this.execute();
            }

            validate() {
                const inputs = this.querySelectorAll('input[required], select[required]');
                let isValid = true;
                this.errors = {};
                
                inputs.forEach(input => {
                    if (!input.value || input.value.trim() === '') {
                        isValid = false;
                        this.errors[input.name] = 'Campo requerido';
                        input.classList.add('border-red-500', 'bg-red-50');
                    } else {
                        input.classList.remove('border-red-500', 'bg-red-50');
                        input.classList.add('border-gray-300');
                    }
                });
                
                return isValid;
            }

            getParams() {
                const params = {};
                const inputs = this.querySelectorAll('input, select');
                
                inputs.forEach(input => {
                    const value = input.value;
                    if (value !== '') {
                        const param = this.funcInfo.parameters.find(p => p.name === input.name);
                        if (param) {
                            params[input.name] = param.type === 'int' ? parseInt(value) :
                                                param.type === 'float' ? parseFloat(value) : value;
                        }
                    }
                });
                
                return params;
            }

            async callAPI(params) {
                const method = this.funcInfo.http_methods[0];
                let url = `/${this.funcName}`;
                let options = { 
                    method: method.toUpperCase(), 
                    headers: { 'Content-Type': 'application/json' } 
                };
                
                if (method.toUpperCase() === 'GET') {
                    const queryString = new URLSearchParams(params).toString();
                    if (queryString) url += `?${queryString}`;
                } else {
                    options.body = JSON.stringify(params);
                }
                
                const response = await fetch(url, options);
                if (!response.ok) {
                    let errorMsg = `HTTP ${response.status}`;
                    try {
                        const errorData = await response.json();
                        errorMsg = errorData.detail || errorMsg;
                    } catch {
                        errorMsg = response.statusText || errorMsg;
                    }
                    throw new Error(errorMsg);
                }
                
                const data = await response.json();
                return data.result !== undefined ? data.result : data;
            }

            showResult(content, isError = false) {
                const resultContainer = this.querySelector('[data-ref="resultContainer"]');
                if (!resultContainer) return;
                
                resultContainer.textContent = typeof content === 'object' 
                    ? JSON.stringify(content, null, 2) 
                    : content;
                    
                // Remover clases previas
                resultContainer.classList.remove('bg-green-100', 'border-green-300', 'text-green-800', 'bg-red-100', 'border-red-300', 'text-red-800', 'hidden');
                
                // Añadir clases según tipo
                if (isError) {
                    resultContainer.classList.add('bg-red-100', 'border', 'border-red-300', 'text-red-800');
                } else {
                    resultContainer.classList.add('bg-green-100', 'border', 'border-green-300', 'text-green-800');
                }
            }

            setStatus(type, message) {
                const indicator = this.querySelector('[data-ref="indicator"]');
                const statusText = this.querySelector('[data-ref="statusText"]');
                
                if (!indicator || !statusText) return;
                
                // Remover clases previas
                indicator.classList.remove('bg-gray-300', 'bg-green-500', 'bg-red-500', 'bg-yellow-500');
                
                // Agregar clase según tipo
                switch(type) {
                    case 'success':
                        indicator.classList.add('bg-green-500');
                        break;
                    case 'error':
                        indicator.classList.add('bg-red-500');
                        break;
                    case 'loading':
                        indicator.classList.add('bg-yellow-500');
                        break;
                    default:
                        indicator.classList.add('bg-gray-300');
                }
                
                statusText.textContent = message;
            }

            showError(message) {
                const error = this.querySelector('[data-ref="error"]');
                if (!error) return;
                error.textContent = message;
                error.classList.remove('hidden');
            }

            hideError() {
                const error = this.querySelector('[data-ref="error"]');
                if (!error) return;
                error.classList.add('hidden');
            }

            updateResultVisibility() {
                const resultContainer = this.querySelector('[data-ref="resultContainer"]');
                if (resultContainer) {
                    if (this._showResult) {
                        resultContainer.classList.remove('hidden');
                    } else {
                        resultContainer.classList.add('hidden');
                    }
                }
            }

            updateParamsVisibility() {
                const defaultParams = this.querySelector('[data-ref="defaultParams"]');
                if (defaultParams) {
                    if (this._showParams) {
                        defaultParams.classList.remove('hidden');
                    } else {
                        defaultParams.classList.add('hidden');
                    }
                }
            }

            updateReadonly() {
                const inputs = this.querySelectorAll('input, select');
                const executeBtn = this.querySelector('[data-ref="executeBtn"]');
                
                inputs.forEach(input => {
                    input.disabled = this._readonly;
                });
                
                if (executeBtn) {
                    executeBtn.disabled = this._readonly;
                }
                
                if (this._readonly) {
                    this.setStatus('default', 'Modo solo lectura');
                }
            }

            // API pública para uso externo
            getResult() {
                return this.result;
            }

            setParam(paramName, value) {
                const input = this.querySelector(`[name="${paramName}"]`);
                if (input) {
                    input.value = value;
                    // Trigger change event para notificar
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }

            getParam(paramName) {
                const input = this.querySelector(`[name="${paramName}"]`);
                return input ? input.value : null;
            }
        };
    }
}

// Auto-inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', async () => {
        window.autoElementGenerator = new AutoElementGenerator();
        await window.autoElementGenerator.init();
    });
} else {
    window.autoElementGenerator = new AutoElementGenerator();
    window.autoElementGenerator.init();
}
