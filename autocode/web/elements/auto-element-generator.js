/**
 * auto-element-generator.js
 * Generador automático de Custom Elements para funciones del registry
 * 
 * ARQUITECTURA:
 * - AutoFunctionController: Clase base con toda la lógica (estado, validación, API) pero sin UI.
 * - AutoFunctionElement: Implementación con UI tipo "Tarjeta" (Shadow DOM).
 * - AutoElementGenerator: Fábrica que crea elementos dinámicos basados en AutoFunctionElement.
 */

import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

/**
 * CONTROLADOR BASE (LÓGICA PURA)
 * Maneja el estado, la validación y la comunicación con la API.
 * Desacoplado de la presentación visual.
 */
export class AutoFunctionController extends LitElement {
    static properties = {
        // Configuración
        funcName: { type: String, attribute: 'func-name' },
        funcInfo: { type: Object, state: true },
        
        // Estado
        params: { type: Object, state: true }, // Valores actuales de los parámetros
        result: { type: Object, state: true },
        // Respuesta completa del backend (envelope)
        envelope: { type: Object, state: true },
        // Metadata conveniente (derivada del envelope)
        success: { type: Boolean, state: true },
        message: { type: String, state: true },
        errors: { type: Object, state: true },
        
        // UI Status
        _status: { type: String, state: true },
        _statusMessage: { type: String, state: true },
        _errorMessage: { type: String, state: true },
        _isExecuting: { type: Boolean, state: true }
    };

    constructor() {
        super();
        this.funcName = '';
        this.funcInfo = null;
        this.params = {}; // { paramName: value }
        this.result = null;
        this.envelope = null;
        this.success = undefined;
        this.message = '';
        this.errors = {};
        
        this._status = 'default';
        this._statusMessage = 'Listo';
        this._errorMessage = '';
        this._isExecuting = false;
    }

    async connectedCallback() {
        super.connectedCallback();
        
        // 1. Si tengo nombre pero no info, cargarla del registry
        if (this.funcName && !this.funcInfo) {
            try {
                await this.loadFunctionInfo();
            } catch (error) {
                this._errorMessage = error.message;
                this._setStatus('error', 'Error cargando función');
            }
        }

        // 2. Inicializar params con defaults si funcInfo ya está cargado
        if (this.funcInfo && Object.keys(this.params).length === 0) {
            this._initParamsWithDefaults();
        }
        
        this.dispatchEvent(new CustomEvent('function-connected', {
            detail: { funcName: this.funcName, funcInfo: this.funcInfo },
            bubbles: true,
            composed: true
        }));
    }

    async loadFunctionInfo() {
        const response = await fetch('/functions/details');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        
        if (!data.functions[this.funcName]) {
            throw new Error(`Function "${this.funcName}" not found in registry`);
        }
        
        this.funcInfo = data.functions[this.funcName];
    }

    // Si funcInfo cambia, reinicializar defaults
    updated(changedProperties) {
        if (changedProperties.has('funcInfo') && this.funcInfo) {
            this._initParamsWithDefaults();
        }
    }

    _initParamsWithDefaults() {
        const newParams = { ...this.params };
        this.funcInfo?.parameters?.forEach(p => {
            if (newParams[p.name] === undefined && p.default !== null) {
                newParams[p.name] = p.default;
            }
        });
        this.params = newParams;
    }

    // ========================================================================
    // LOGIC API (STATE MANAGEMENT)
    // ========================================================================

    /**
     * Establece el valor de un parámetro y actualiza el estado.
     */
    setParam(name, value) {
        // Actualización inmutable para disparar reactividad de Lit
        this.params = {
            ...this.params,
            [name]: value
        };

        // Limpiar error asociado si existe
        if (this.errors[name]) {
            const newErrors = { ...this.errors };
            delete newErrors[name];
            this.errors = newErrors;
        }

        this.dispatchEvent(new CustomEvent('params-changed', {
            detail: { params: this.params },
            bubbles: true,
            composed: true
        }));
    }

    getParam(name) {
        return this.params[name];
    }

    getParams() {
        return this.params;
    }

    getResult() {
        return this.result;
    }

    /**
     * Devuelve el envelope completo del backend.
     * Útil para consumidores que necesiten metadata (reasoning/trajectory/history, etc.).
     */
    getEnvelope() {
        return this.envelope;
    }

    /**
     * Devuelve el payload real (alias de result).
     */
    getPayload() {
        return this.result;
    }

    isSuccess() {
        return this.success === true;
    }

    // ========================================================================
    // EXECUTION LOGIC
    // ========================================================================

    async execute() {
        // 1. Validar estado (params vs funcInfo)
        if (!this.validate()) {
            this._errorMessage = 'Por favor, completa todos los campos requeridos y corrige los errores.';
            this._setStatus('error', 'Error de validación');
            return;
        }

        // 2. Pre-execution hook
        const preEvent = new CustomEvent('before-execute', {
            detail: { funcName: this.funcName, params: this.params },
            bubbles: true,
            composed: true,
            cancelable: true
        });

        if (!this.dispatchEvent(preEvent)) {
            console.log('Ejecución cancelada por before-execute handler');
            return;
        }

        // 3. Setup execution state
        this._isExecuting = true;
        this._setStatus('loading', 'Ejecutando...');
        this._errorMessage = '';
        
        try {
            // 4. Call API
            const data = await this.callAPI(this.params);

            // Guardar envelope completo
            this.envelope = data;

            // Derivar metadata + payload estandarizado
            const hasEnvelopeShape = (data && typeof data === 'object' && Object.prototype.hasOwnProperty.call(data, 'result'));
            this.result = hasEnvelopeShape ? data.result : data;

            if (data && typeof data === 'object') {
                this.success = data.success;
                this.message = data.message;
            } else {
                this.success = undefined;
                this.message = '';
            }

            // Si el backend devuelve success=false, lo tratamos como ejecución fallida
            // (pero NO lanzamos excepción: queda a criterio del consumidor)
            if (this.success === false) {
                this._errorMessage = this.message || 'Error en ejecución';
                this._setStatus('error', 'Error en ejecución');
            } else {
                this._errorMessage = '';
                this._setStatus('success', 'Ejecutado correctamente');
            }

            const payload = this.result;

            this.dispatchEvent(new CustomEvent('after-execute', {
                detail: { funcName: this.funcName, params: this.params, result: payload, envelope: this.envelope },
                bubbles: true,
                composed: true
            }));

            return payload;
        } catch (error) {
            this.result = { _isError: true, _message: `Error: ${error.message}` };
            this.envelope = this.result;
            this.success = false;
            this.message = this.result._message;
            this._setStatus('error', 'Error en ejecución');

            this.dispatchEvent(new CustomEvent('execute-error', {
                detail: { funcName: this.funcName, params: this.params, error },
                bubbles: true,
                composed: true
            }));

            throw error;
        } finally {
            this._isExecuting = false;
        }
    }

    /**
     * Valida los parámetros actuales contra la definición (funcInfo).
     * NO depende del DOM.
     */
    validate() {
        let isValid = true;
        const newErrors = {};

        this.funcInfo?.parameters?.forEach(param => {
            const value = this.params[param.name];
            let error = null;

            // Required check
            if (param.required) {
                if (value === undefined || value === null || (typeof value === 'string' && value.trim() === '')) {
                    // Checkbox/Boolean required usually ignored unless specified true needed
                    if (param.type !== 'bool') {
                        error = 'Campo requerido';
                    }
                }
            }

            // Type check (basic)
            if (!error && value !== undefined && value !== null && value !== '') {
                if (param.type === 'int') {
                    if (!Number.isInteger(Number(value))) error = 'Debe ser un número entero';
                } else if (param.type === 'float') {
                    if (isNaN(parseFloat(value))) error = 'Debe ser un número decimal';
                } else if (this._isComplexType(param.type)) {
                    // Si es string (desde textarea), intentar parsear
                    if (typeof value === 'string') {
                        try {
                            JSON.parse(value);
                        } catch (e) {
                            error = 'JSON inválido';
                        }
                    }
                }
            }

            if (error) {
                isValid = false;
                newErrors[param.name] = error;
            }
        });

        this.errors = newErrors;
        return isValid;
    }

    async callAPI(params) {
        const method = this.funcInfo.http_methods[0];
        let url = `/${this.funcName}`;
        let options = {
            method: method.toUpperCase(),
            headers: { 'Content-Type': 'application/json' }
        };

        // Procesar params para envío
        const processedParams = {};
        Object.entries(params).forEach(([key, val]) => {
            // Parsear JSON strings si es necesario (para complex types que vengan de textareas)
            const paramDef = this.funcInfo.parameters.find(p => p.name === key);
            if (paramDef && this._isComplexType(paramDef.type) && typeof val === 'string') {
                try {
                    processedParams[key] = JSON.parse(val);
                } catch {
                    processedParams[key] = val; // Fallback
                }
            } else if (paramDef && paramDef.type === 'int') {
                processedParams[key] = parseInt(val);
            } else if (paramDef && paramDef.type === 'float') {
                processedParams[key] = parseFloat(val);
            } else {
                processedParams[key] = val;
            }
        });

        if (method.toUpperCase() === 'GET') {
            const queryParams = new URLSearchParams();
            for (const [key, val] of Object.entries(processedParams)) {
                if (typeof val === 'object' && val !== null) {
                    queryParams.append(key, JSON.stringify(val));
                } else {
                    queryParams.append(key, val);
                }
            }
            const queryString = queryParams.toString();
            if (queryString) url += `?${queryString}`;
        } else {
            options.body = JSON.stringify(processedParams);
        }

        const response = await fetch(url, options);
        if (!response.ok) {
            let errorMsg = `HTTP ${response.status}`;
            try {
                const errorData = await response.json();
                errorMsg = errorData.detail 
                    ? (typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail)) 
                    : JSON.stringify(errorData);
            } catch {
                errorMsg = response.statusText || errorMsg;
            }
            throw new Error(errorMsg);
        }

        const data = await response.json();
        return data;
    }

    /**
     * Helper estático para ejecutar funciones sin crear elementos en el DOM.
     * Útil para llamadas inter-funciones (ej: chat llamando a calculate_context_usage).
     * 
     * @param {string} funcName - Nombre de la función registrada
     * @param {object} params - Parámetros para la función
     * @returns {Promise<any>} - Resultado de la ejecución
     * @throws {Error} - Si la función no existe o falla la ejecución
     * 
     * @example
     * const result = await AutoFunctionController.executeFunction(
     *     'calculate_context_usage',
     *     { model: 'gpt-4', messages: [...] }
     * );
     */
    static async executeFunction(funcName, params) {
        const controller = new AutoFunctionController();
        controller.funcName = funcName;
        
        try {
            // Cargar metadata de la función
            await controller.loadFunctionInfo();
            
            // Establecer parámetros
            Object.entries(params).forEach(([key, value]) => {
                controller.setParam(key, value);
            });
            
            // Ejecutar y retornar resultado
            const result = await controller.execute();
            return result;
        } catch (error) {
            console.error(`❌ Error executing function "${funcName}":`, error);
            throw error;
        }
    }

    // Helpers internos
    _isComplexType(type) {
        if (!type) return false;
        return /\b(dict|list)\b|json/i.test(type);
    }
    
    _setStatus(type, message) {
        this._status = type;
        this._statusMessage = message;
    }

    // Default render: nada visual, solo slot
    render() {
        return html`<slot></slot>`;
    }
}


/**
 * UI GENÉRICA (TARJETA)
 * Implementación visual estándar de AutoFunctionController.
 * Usa Shadow DOM.
 * NO DISEÑADA PARA SER EXTENDIDA.
 */
export class AutoFunctionElement extends AutoFunctionController {
    static styles = css`
        :host { display: block; font-family: system-ui, sans-serif; }
        .container { 
            display: flex; flex-direction: column; gap: 1rem; padding: 1rem; 
            border: 1px solid #e5e7eb; border-radius: 0.5rem; background: #ffffff; 
            box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
        }
        .header { display: flex; flex-direction: column; gap: 0.5rem; }
        .header-row { display: flex; justify-content: space-between; align-items: center; }
        .title { font-size: 1.25rem; font-weight: 600; margin: 0; color: #1f2937; }
        .description { font-size: 0.875rem; color: #6b7280; font-style: italic; margin: 0; }
        
        .error-banner { 
            padding: 0.75rem; background: #fee2e2; border: 1px solid #fca5a5; 
            border-radius: 0.5rem; color: #991b1b; font-size: 0.875rem;
        }
        
        /* Inputs */
        .params { display: flex; flex-direction: column; gap: 0.75rem; }
        .param-group { display: flex; flex-direction: column; gap: 0.25rem; }
        .param-label { font-size: 0.875rem; font-weight: 600; color: #374151; }
        .param-required { color: #ef4444; }
        .param-desc { font-size: 0.75rem; color: #6b7280; margin: 0; }
        .field-error { font-size: 0.75rem; color: #ef4444; }

        input, select, textarea { 
            padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 0.5rem; 
            font-size: 0.875rem; width: 100%; box-sizing: border-box;
            background: #fff; color: #1f2937;
        }
        input:focus, select:focus, textarea:focus {
            outline: none; border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }
        input.error, select.error, textarea.error { border-color: #ef4444; background: #fef2f2; }
        
        .checkbox-wrapper { display: flex; align-items: center; gap: 0.5rem; }
        input[type="checkbox"] { width: 1rem; height: 1rem; accent-color: #6366f1; }

        /* Button */
        .execute-btn {
            padding: 0.5rem 1rem; background: linear-gradient(to right, #4f46e5, #7c3aed); 
            color: white; border: none; border-radius: 0.5rem; font-weight: 500; cursor: pointer;
            transition: opacity 0.2s;
        }
        .execute-btn:hover:not(:disabled) { opacity: 0.9; }
        .execute-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        
        /* Result */
        .result { 
            padding: 0.75rem; border-radius: 0.5rem; font-family: monospace; 
            font-size: 0.875rem; white-space: pre-wrap; word-break: break-word;
        }
        .result-success { background: #dcfce7; border: 1px solid #86efac; color: #166534; }
        .result-error { background: #fee2e2; border: 1px solid #fca5a5; color: #991b1b; }

        /* Status */
        .status { display: flex; align-items: center; gap: 0.5rem; font-size: 0.75rem; color: #6b7280; }
        .status-indicator { width: 0.5rem; height: 0.5rem; border-radius: 50%; background: #d1d5db; }
        .status-indicator.success { background: #22c55e; }
        .status-indicator.error { background: #ef4444; }
        .status-indicator.loading { background: #eab308; }
    `;

    render() {
        if (!this.funcInfo) {
            return html`<div class="container">Cargando...</div>`;
        }

        return html`
            <div class="container">
                <div class="header">
                    <div class="header-row">
                        <h3 class="title">🔧 ${this.funcInfo.name}</h3>
                    </div>
                    ${this.funcInfo.description ? html`<p class="description">${this.funcInfo.description}</p>` : ''}
                </div>

                ${this._errorMessage ? html`<div class="error-banner">${this._errorMessage}</div>` : ''}

                ${this.funcInfo.parameters?.length ? html`
                    <div class="params">
                        ${this.funcInfo.parameters.map(p => this.renderParam(p))}
                    </div>
                ` : ''}

                <button class="execute-btn" ?disabled=${this._isExecuting} @click=${this.execute}>
                    ${this._isExecuting ? 'Ejecutando...' : `Ejecutar ⚡`}
                </button>

                ${this.result !== null ? this.renderResult() : ''}

                <div class="status">
                    <div class="status-indicator ${this._status}"></div>
                    <span>${this._statusMessage}</span>
                </div>
            </div>
        `;
    }

    renderParam(param) {
        const hasError = this.errors[param.name];
        const errorClass = hasError ? 'error' : '';
        const currentValue = this.params[param.name] ?? '';

        let inputHtml;
        
        if (param.choices?.length > 0) {
            inputHtml = html`
                <select name="${param.name}" class="${errorClass}" ?required=${param.required}
                    @change=${e => this.setParam(param.name, e.target.value)}>
                    ${param.choices.map(c => html`<option value="${c}" ?selected=${c === currentValue}>${c}</option>`)}
                </select>
            `;
        } else if (this._isComplexType(param.type)) {
            const displayValue = typeof currentValue === 'object' ? JSON.stringify(currentValue, null, 2) : currentValue;
            inputHtml = html`
                <textarea name="${param.name}" class="${errorClass}" rows="3" .value=${displayValue}
                    ?required=${param.required}
                    @change=${e => this.setParam(param.name, e.target.value)}></textarea>
            `;
        } else if (param.type === 'bool') {
            inputHtml = html`
                <div class="checkbox-wrapper">
                    <input type="checkbox" name="${param.name}" ?checked=${!!currentValue}
                        @change=${e => this.setParam(param.name, e.target.checked)}>
                    <span>Activar</span>
                </div>
            `;
        } else {
            const isNumber = param.type === 'int' || param.type === 'float';
            inputHtml = html`
                <input type="${isNumber ? 'number' : 'text'}" name="${param.name}" class="${errorClass}" 
                    .value=${String(currentValue)} ?required=${param.required}
                    step="${param.type === 'float' ? 'any' : param.type === 'int' ? '1' : ''}"
                    @change=${e => this.setParam(param.name, e.target.value)}>
            `;
        }

        return html`
            <div class="param-group">
                <label class="param-label">
                    ${param.name} ${param.required ? html`<span class="param-required">*</span>` : ''}
                </label>
                <p class="param-desc">${param.description} (${param.type})</p>
                ${inputHtml}
                ${hasError ? html`<span class="field-error">${this.errors[param.name]}</span>` : ''}
            </div>
        `;
    }

    renderResult() {
        const isError = this.result?._isError;
        const content = typeof this.result === 'object' && !isError
            ? JSON.stringify(this.result, null, 2)
            : this.result?._message || this.result;

        return html`
            <div class="result ${isError ? 'result-error' : 'result-success'}">
                ${content}
            </div>
        `;
    }
}

// Registrar clases base
if (!customElements.get('auto-function-controller')) {
    customElements.define('auto-function-controller', AutoFunctionController);
}
if (!customElements.get('auto-function-element')) {
    customElements.define('auto-function-element', AutoFunctionElement);
}

/**
 * GENERADOR DINÁMICO
 */
export class AutoElementGenerator {
    constructor() {
        this.functions = {};
        this.registeredElements = new Set();
    }

    async init() {
        try {
            await this.loadFunctions();
            this.generateAllElements();
            console.log(`✅ ${this.registeredElements.size} custom elements generados`);
        } catch (error) {
            console.error('❌ Error inicializando auto-element-generator:', error);
            throw error;
        }
    }

    async loadFunctions() {
        const response = await fetch('/functions/details');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        this.functions = data.functions;
    }

    generateAllElements() {
        for (const [funcName, funcInfo] of Object.entries(this.functions)) {
            this.generateElement(funcName, funcInfo);
        }
    }

    generateElement(funcName, funcInfo) {
        const elementName = `auto-${funcName}`;
        if (customElements.get(elementName)) return;

        // IMPORTANTE: Ahora extendemos de AutoFunctionElement (que extiende del Controller)
        const ElementClass = class extends AutoFunctionElement {
            constructor() {
                super();
                this.funcName = funcName;
                this.funcInfo = funcInfo;
            }
        };

        customElements.define(elementName, ElementClass);
        this.registeredElements.add(elementName);
    }
}

// Inicialización
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', async () => {
        window.autoElementGenerator = new AutoElementGenerator();
        await window.autoElementGenerator.init();
    });
} else {
    window.autoElementGenerator = new AutoElementGenerator();
    window.autoElementGenerator.init();
}
