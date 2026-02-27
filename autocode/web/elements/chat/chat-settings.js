/**
 * chat-settings.js
 * Componente de configuración para el chat
 * Refactorizado: Controles dinámicos para module_kwargs y tools
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { chatSettingsStyles } from './styles/chat-settings.styles.js';
import { themeTokens } from './styles/theme.js';

export class ChatSettings extends LitElement {
    static properties = {
        _settings: { state: true },
        _funcInfo: { state: true },
        chatConfig: { type: Object },
        _enabledTools: { state: true },
        _toolSearchTerm: { state: true },
        _showAdvanced: { state: true }
    };

    static styles = [themeTokens, chatSettingsStyles];

    constructor() {
        super();
        this._settings = {};
        this._funcInfo = null;
        this.chatConfig = null;
        this._enabledTools = new Set();
        this._toolSearchTerm = '';
        this._showAdvanced = false;
    }

    updated(changedProperties) {
        if (changedProperties.has('chatConfig') && this.chatConfig) {
            // Inicializar tools solo cuando llega la configuración por primera vez
            const oldConfig = changedProperties.get('chatConfig');
            if (!oldConfig) {
                this._initTools();
            }
        }
    }

    _initTools() {
        if (this.chatConfig?.available_tools) {
            this._enabledTools = new Set(
                this.chatConfig.available_tools
                    .filter(t => t.enabled_by_default)
                    .map(t => t.name)
            );
        }
    }

    configure(funcInfo) {
        this._funcInfo = funcInfo;
        
        // Inicializar settings
        if (funcInfo && funcInfo.parameters) {
            funcInfo.parameters.forEach(param => {
                if (['message', 'conversation_history', 'lm_kwargs'].includes(param.name)) return;
                
                if (param.default !== undefined && param.default !== null) {
                    this._settings[param.name] = param.default;
                }
            });
        }
        
        this._emitSettingsChange();
        this.requestUpdate();
    }

    getSettings() {
        const settings = { ...this._settings };
        
        // Agregar enabled_tools si el módulo lo soporta
        const moduleType = settings.module_type;
        const moduleConfig = this.chatConfig?.module_kwargs_schemas?.[moduleType];
        
        // Si el módulo soporta tools (o fallback a ReAct hardcoded para compatibilidad antigua)
        if ((moduleConfig?.supports_tools || moduleType === 'ReAct') && this._enabledTools.size > 0) {
            settings.enabled_tools = Array.from(this._enabledTools);
        }
        
        // Construir module_kwargs desde los controles dinámicos
        const moduleKwargs = this._buildModuleKwargs();
        if (Object.keys(moduleKwargs).length > 0) {
            settings.module_kwargs = moduleKwargs;
        }
        
        // Construir lm_kwargs (advanced options)
        const lmKwargs = this._buildLmKwargs();
        if (Object.keys(lmKwargs).length > 0) {
            settings.lm_kwargs = lmKwargs;
        }
        
        return settings;
    }
    
    _buildModuleKwargs() {
        const moduleType = this._settings.module_type;
        if (!moduleType || !this.chatConfig?.module_kwargs_schemas) {
            return {};
        }
        
        const schema = this.chatConfig.module_kwargs_schemas[moduleType];
        if (!schema || !schema.params) return {};
        
        const kwargs = {};
        schema.params.forEach(param => {
            // Excluir 'tools' ya que se maneja con enabled_tools
            if (param.name === 'tools') return;
            
            const settingKey = `module_kwarg_${param.name}`;
            if (this._settings[settingKey] !== undefined) {
                kwargs[param.name] = this._settings[settingKey];
            }
        });
        
        return kwargs;
    }

    _buildLmKwargs() {
        const advancedParams = ['top_p', 'frequency_penalty', 'presence_penalty', 'stop'];
        const kwargs = {};
        
        advancedParams.forEach(param => {
            const settingKey = `lm_kwarg_${param}`;
            if (this._settings[settingKey] !== undefined && this._settings[settingKey] !== '') {
                kwargs[param] = this._settings[settingKey];
            }
        });
        
        return kwargs;
    }

    _getEnablePromptCache() {
        // Por defecto true (activo), el usuario puede desactivarlo
        return this._settings.enable_prompt_cache !== undefined 
            ? this._settings.enable_prompt_cache 
            : true;
    }
    
    // Método interno para actualizar settings (usado en tests)
    _updateSetting(name, value) {
        this._settings = { ...this._settings, [name]: value };
        
        // Si cambió el modelo, intentar actualizar defaults
        if (name === 'model') {
            this._handleModelChange(value);
        }
        
        this._emitSettingsChange();
    }
    
    _handleModelChange(modelId) {
        if (!this.chatConfig?.models) return;
        
        const modelInfo = this.chatConfig.models.find(m => m.id === modelId);
        if (modelInfo) {
            // Aquí podríamos actualizar max_tokens u otros defaults si tuviéramos esa info
            // Por ahora solo forzamos un re-render para mostrar la info de contexto actualizada
            this.requestUpdate();
        }
    }
    
    _toggleTool(toolName) {
        if (this._enabledTools.has(toolName)) {
            this._enabledTools.delete(toolName);
        } else {
            this._enabledTools.add(toolName);
        }
        this._enabledTools = new Set(this._enabledTools); // Trigger reactivity
        this._emitSettingsChange();
    }
    
    _emitSettingsChange() {
        this.dispatchEvent(new CustomEvent('settings-change', {
            detail: this.getSettings(),
            bubbles: true,
            composed: true
        }));
    }

    _openSettings(e) {
        e.stopPropagation();
        const dialog = this.shadowRoot.querySelector('dialog');
        if (dialog) dialog.showModal();
    }

    _closeSettings() {
        const dialog = this.shadowRoot.querySelector('dialog');
        if (dialog) dialog.close();
    }

    _handleDialogClick(e) {
        if (e.target.tagName === 'DIALOG') {
            this._closeSettings();
        }
    }

    render() {
        return html`
            <button class="toggle-btn" @click=${this._openSettings} title="Configuración">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.38a2 2 0 0 0-.73-2.73l-.15-.1a2 2 0 0 1-1-1.72v-.51a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
                    <circle cx="12" cy="12" r="3"/>
                </svg>
            </button>

            <dialog class="settings-dialog" @click=${this._handleDialogClick}>
                <div class="dialog-header">
                    <h3 class="panel-title">
                        <span>🛠️ Configuración</span>
                    </h3>
                    <button class="close-icon-btn" @click=${this._closeSettings} title="Cerrar">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                    </button>
                </div>
                
                <div class="controls">
                    ${this._renderDynamicControls()}
                    ${this._renderAdvancedOptions()}
                    ${this._renderModuleKwargsControls()}
                    ${this._renderToolsSelector()}
                </div>
            </dialog>
        `;
    }

    _renderDynamicControls() {
        if (!this._funcInfo) {
            return html`<p class="loading">Cargando configuración...</p>`;
        }

        return this._funcInfo.parameters.map(param => {
            // Excluir parámetros manejados de forma especial
            if (['message', 'conversation_history', 'module_kwargs', 'enabled_tools', 'lm_kwargs', 'enable_prompt_cache'].includes(param.name)) return '';
            
            return html`
                <div class="control-group">
                    ${param.name !== 'temperature' ? html`
                        <label class="control-label">
                            ${this._formatLabel(param.name)}
                            ${this._renderParamHint(param.name)}
                        </label>
                    ` : ''}
                    ${this._renderControl(param)}
                </div>
            `;
        });
    }

    _renderParamHint(paramName) {
        if (paramName === 'max_tokens') {
            const currentModelId = this._settings.model;
            const modelInfo = this.chatConfig?.models?.find(m => m.id === currentModelId);
            const maxTokens = modelInfo?.top_provider?.max_completion_tokens || modelInfo?.context_length;
            if (maxTokens) {
                return html`<span class="param-hint">(Max: ${maxTokens})</span>`;
            }
        }
        return '';
    }
    
    _renderModuleKwargsControls() {
        const moduleType = this._settings.module_type;
        if (!moduleType || !this.chatConfig?.module_kwargs_schemas) {
            return '';
        }
        
        const schema = this.chatConfig.module_kwargs_schemas[moduleType];
        // schema ahora es { params: [], supports_tools: bool }
        if (!schema || !schema.params || schema.params.length === 0) {
            return '';
        }
        
        // Filtrar parámetros que no deben mostrarse (tools se maneja aparte)
        const visibleParams = schema.params.filter(p => p.name !== 'tools');
        if (visibleParams.length === 0) {
            return '';
        }
        
        return html`
            <div class="section-divider"></div>
            <div class="section-title">Opciones de ${moduleType}</div>
            ${visibleParams.map(param => this._renderModuleKwargControl(param))}
        `;
    }
    
    _renderModuleKwargControl(param) {
        const settingKey = `module_kwarg_${param.name}`;
        const value = this._settings[settingKey] ?? param.default;
        
        return html`
            <div class="control-group">
                <label class="control-label" title="${param.description}">
                    ${this._formatLabel(param.name)}
                </label>
                ${param.type === 'int' ? html`
                    <input 
                        type="number" 
                        .value=${value ?? 0}
                        step="1"
                        min="1"
                        @change=${e => this._updateSetting(settingKey, parseInt(e.target.value))}
                    >
                ` : param.type === 'float' ? html`
                    <input 
                        type="number" 
                        .value=${value ?? 0}
                        step="0.1"
                        @change=${e => this._updateSetting(settingKey, parseFloat(e.target.value))}
                    >
                ` : param.type === 'bool' ? html`
                    <div class="checkbox-wrapper">
                        <input 
                            type="checkbox" 
                            ?checked=${!!value}
                            @change=${e => this._updateSetting(settingKey, e.target.checked)}
                        >
                        <span class="checkbox-label">${param.description}</span>
                    </div>
                ` : html`
                    <input 
                        type="text" 
                        .value=${value ?? ''}
                        @change=${e => this._updateSetting(settingKey, e.target.value)}
                    >
                `}
            </div>
        `;
    }
    
    _renderToolsSelector() {
        const moduleType = this._settings.module_type;
        const schema = this.chatConfig?.module_kwargs_schemas?.[moduleType];
        
        // Mostrar si el módulo soporta tools explicitamente O es ReAct (fallback)
        const supportsTools = schema?.supports_tools || moduleType === 'ReAct';
        
        if (!supportsTools || !this.chatConfig?.available_tools) {
            return '';
        }
        
        const tools = this.chatConfig.available_tools;
        if (tools.length === 0) {
            return '';
        }

        const filteredTools = tools.filter(tool => 
            tool.name.toLowerCase().includes(this._toolSearchTerm.toLowerCase()) ||
            (tool.description && tool.description.toLowerCase().includes(this._toolSearchTerm.toLowerCase()))
        );
        
        return html`
            <div class="section-divider"></div>
            <div class="section-title">
                Tools Disponibles
                <span class="tools-count">(${this._enabledTools.size}/${tools.length})</span>
            </div>

            <div class="search-container">
                <input 
                    type="text" 
                    class="search-input"
                    placeholder="Buscar tools..."
                    .value=${this._toolSearchTerm}
                    @input=${e => this._toolSearchTerm = e.target.value}
                >
            </div>

            <div class="tools-list">
                ${filteredTools.map(tool => html`
                    <div class="tool-item" title="${tool.description}">
                        <label class="tool-checkbox">
                            <input 
                                type="checkbox" 
                                ?checked=${this._enabledTools.has(tool.name)}
                                @change=${() => this._toggleTool(tool.name)}
                            >
                            <span class="tool-name">${tool.name}</span>
                        </label>
                        <span class="tool-description">${this._truncateDescription(tool.description)}</span>
                    </div>
                `)}
                ${filteredTools.length === 0 ? html`<div class="no-results">No se encontraron tools</div>` : ''}
            </div>
        `;
    }
    
    _renderAdvancedOptions() {
        // Verificar parámetros soportados por el modelo seleccionado
        const currentModelId = this._settings.model;
        const modelInfo = this.chatConfig?.models?.find(m => m.id === currentModelId);
        
        // Default supported params if no info available or empty list
        let supportedParams = modelInfo?.supported_parameters;
        if (!supportedParams || supportedParams.length === 0) {
            supportedParams = ['top_p', 'frequency_penalty', 'presence_penalty', 'stop'];
        }

        // Filtrar solo los que queremos mostrar en UI avanzado
        const relevantParams = ['top_p', 'frequency_penalty', 'presence_penalty', 'stop']
            .filter(p => supportedParams.includes(p));

        if (relevantParams.length === 0) return '';

        return html`
            <div class="section-divider"></div>
            <div 
                class="section-title collapsible" 
                @click=${() => this._showAdvanced = !this._showAdvanced}
                style="cursor: pointer; display: flex; align-items: center; justify-content: space-between;"
            >
                <span>Opciones Avanzadas</span>
                <span style="transform: rotate(${this._showAdvanced ? '180deg' : '0deg'}); transition: transform 0.2s;">▼</span>
            </div>
            
            ${this._showAdvanced ? html`
                <div class="advanced-controls">
                    <div class="control-group">
                        <label class="control-label" title="Activa cache de prompts del proveedor (Anthropic/OpenAI) para reducir costos y latencia en llamadas repetidas">
                            💰 Prompt Cache (Proveedor)
                        </label>
                        <div class="checkbox-wrapper">
                            <input 
                                type="checkbox" 
                                ?checked=${this._getEnablePromptCache()}
                                @change=${e => this._updateSetting('enable_prompt_cache', e.target.checked)}
                            >
                            <span class="checkbox-label">Reduce costos cacheando prompts en el servidor del proveedor</span>
                        </div>
                    </div>
                    ${relevantParams.map(param => this._renderAdvancedControl(param))}
                </div>
            ` : ''}
        `;
    }

    _renderAdvancedControl(param) {
        const settingKey = `lm_kwarg_${param}`;
        const value = this._settings[settingKey];

        if (['top_p', 'frequency_penalty', 'presence_penalty'].includes(param)) {
            let min = 0, max = 1, step = 0.01;
            let defaultValue = 1;
            
            if (param === 'top_p') {
                min = 0; max = 1; defaultValue = 1;
            } else {
                // penalty
                min = -2; max = 2; defaultValue = 0;
            }
            
            const displayValue = value !== undefined ? value : defaultValue;

            return html`
                <div class="control-group">
                    <div class="temp-header">
                        <label class="control-label">${this._formatLabel(param)}</label>
                        <span class="temp-value">${displayValue}</span>
                    </div>
                    <input 
                        type="range" 
                        min="${min}" max="${max}" step="${step}"
                        .value=${displayValue}
                        @input=${e => this._updateSetting(settingKey, parseFloat(e.target.value))}
                    >
                    <div class="temp-footer">
                        <span>${min}</span><span>${max}</span>
                    </div>
                </div>
            `;
        }

        return html`
            <div class="control-group">
                <label class="control-label">${this._formatLabel(param)}</label>
                ${param === 'stop' ? html`
                    <input 
                        type="text" 
                        placeholder='["STOP"]'
                        .value=${value ?? ''}
                        @change=${e => this._updateSetting(settingKey, e.target.value)}
                    >
                ` : html`
                    <input 
                        type="number" 
                        .value=${value ?? ''}
                        step="0.01"
                        placeholder="Default"
                        @change=${e => this._updateSetting(settingKey, parseFloat(e.target.value))}
                    >
                `}
            </div>
        `;
    }
    
    _truncateDescription(desc, maxLength = 50) {
        if (!desc || desc.length <= maxLength) return desc;
        return desc.substring(0, maxLength) + '...';
    }

    _renderControl(param) {
        const value = this._settings[param.name];

        // 1. Choices (Select)
        if (param.choices && param.choices.length > 0) {
            // Si es 'model', podemos enriquecer las opciones con nombres de la config
            if (param.name === 'model' && this.chatConfig?.models) {
                return html`
                    <select name="${param.name}" @change=${e => this._updateSetting(param.name, e.target.value)}>
                        ${param.choices.map(choice => {
                            const modelInfo = this.chatConfig.models.find(m => m.id === choice);
                            const label = modelInfo ? `${modelInfo.name}` : choice; // Simplificado
                            return html`
                                <option value="${choice}" ?selected=${choice === value}>
                                    ${label}
                                </option>
                            `;
                        })}
                    </select>
                `;
            }

            return html`
                <select name="${param.name}" @change=${e => this._updateSetting(param.name, e.target.value)}>
                    ${param.choices.map(choice => html`
                        <option value="${choice}" ?selected=${choice === value}>${choice}</option>
                    `)}
                </select>
            `;
        }

        // 2. Temperature (Slider)
        if (param.name === 'temperature') {
            const displayVal = value !== undefined ? value : 0.7;
            return html`
                <div class="temp-header">
                    <label class="control-label">Creatividad (Temperature)</label>
                    <span class="temp-value">${displayVal}</span>
                </div>
                <input 
                    type="range" 
                    name="${param.name}"
                    min="0" max="1" step="0.1" 
                    .value=${displayVal}
                    @input=${e => this._updateSetting(param.name, parseFloat(e.target.value))}
                >
                <div class="temp-footer">
                    <span>Preciso</span><span>Creativo</span>
                </div>
            `;
        }

        // 3. Boolean
        if (param.type === 'bool') {
            return html`
                <div class="checkbox-wrapper">
                    <input 
                        type="checkbox" 
                        name="${param.name}"
                        ?checked=${!!value}
                        @change=${e => this._updateSetting(param.name, e.target.checked)}
                    >
                    <span class="checkbox-label">Activar</span>
                </div>
            `;
        }

        // 4. Number
        if (param.type === 'int' || param.type === 'float') {
            // Special handling for max_tokens to enforce limits
            if (param.name === 'max_tokens') {
                const currentModelId = this._settings.model;
                const modelInfo = this.chatConfig?.models?.find(m => m.id === currentModelId);
                const maxLimit = modelInfo?.top_provider?.max_completion_tokens || modelInfo?.context_length;
                
                return html`
                    <input 
                        type="number" 
                        name="${param.name}"
                        .value=${value || 0}
                        step="1"
                        min="1"
                        max="${maxLimit || ''}"
                        @change=${e => {
                            let val = parseInt(e.target.value);
                            if (maxLimit && val > maxLimit) val = maxLimit;
                            if (val < 1) val = 1;
                            // Update input value if clamped
                            if (val !== parseInt(e.target.value)) e.target.value = val;
                            this._updateSetting(param.name, val);
                        }}
                    >
                `;
            }

            return html`
                <input 
                    type="number" 
                    name="${param.name}"
                    .value=${value || 0}
                    step=${param.type === 'float' ? '0.1' : '1'}
                    @change=${e => {
                        const val = param.type === 'float' ? parseFloat(e.target.value) : parseInt(e.target.value);
                        this._updateSetting(param.name, val);
                    }}
                >
            `;
        }

        // 5. Default Text
        return html`
            <input 
                type="text" 
                name="${param.name}"
                .value=${value || ''}
                @change=${e => this._updateSetting(param.name, e.target.value)}
            >
        `;
    }

    _formatLabel(name) {
        return name
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
}

if (!customElements.get('chat-settings')) {
    customElements.define('chat-settings', ChatSettings);
}
