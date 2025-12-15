/**
 * chat-settings.js
 * Componente de configuración para el chat
 * Refactorizado: Lógica pura separada de estilos
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { chatSettingsStyles } from './styles/chat-settings.styles.js';
import { themeTokens } from './styles/theme.js';

export class ChatSettings extends LitElement {
    static properties = {
        _settings: { state: true },
        _funcInfo: { state: true },
        _isOpen: { state: true }
    };

    static styles = [themeTokens, chatSettingsStyles];

    constructor() {
        super();
        this._settings = {};
        this._funcInfo = null;
        this._isOpen = false;
        
        // Bind para event listeners globales
        this._handleOutsideClick = this._handleOutsideClick.bind(this);
    }

    connectedCallback() {
        super.connectedCallback();
        document.addEventListener('click', this._handleOutsideClick);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        document.removeEventListener('click', this._handleOutsideClick);
    }

    configure(funcInfo) {
        this._funcInfo = funcInfo;
        
        // Inicializar settings
        if (funcInfo && funcInfo.parameters) {
            funcInfo.parameters.forEach(param => {
                if (['message', 'conversation_history'].includes(param.name)) return;
                
                if (param.default !== undefined && param.default !== null) {
                    this._settings[param.name] = param.default;
                }
            });
        }
        
        this.dispatchEvent(new CustomEvent('settings-change', {
            detail: { ...this._settings },
            bubbles: true,
            composed: true
        }));
        
        this.requestUpdate();
    }

    getSettings() {
        return { ...this._settings };
    }
    
    // Método interno para actualizar settings (usado en tests)
    _updateSetting(name, value) {
        this._settings = { ...this._settings, [name]: value };
        this.dispatchEvent(new CustomEvent('settings-change', {
            detail: { ...this._settings },
            bubbles: true,
            composed: true
        }));
    }

    _handleOutsideClick(e) {
        if (this._isOpen && !this.contains(e.target)) {
            this._isOpen = false;
        }
    }

    _togglePanel(e) {
        e.stopPropagation();
        this._isOpen = !this._isOpen;
    }

    render() {
        return html`
            <button class="toggle-btn" @click=${this._togglePanel} title="Configuración">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.38a2 2 0 0 0-.73-2.73l-.15-.1a2 2 0 0 1-1-1.72v-.51a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
                    <circle cx="12" cy="12" r="3"/>
                </svg>
            </button>

            ${this._isOpen ? html`
                <div class="panel" @click=${e => e.stopPropagation()}>
                    <h3 class="panel-title">
                        <span>🛠️ Configuración</span>
                    </h3>
                    
                    <div class="controls">
                        ${this._renderDynamicControls()}
                    </div>
                </div>
            ` : ''}
        `;
    }

    _renderDynamicControls() {
        if (!this._funcInfo) {
            return html`<p class="loading">Cargando configuración...</p>`;
        }

        return this._funcInfo.parameters.map(param => {
            if (['message', 'conversation_history'].includes(param.name)) return '';
            
            return html`
                <div class="control-group">
                    ${param.name !== 'temperature' ? html`
                        <label class="control-label">${this._formatLabel(param.name)}</label>
                    ` : ''}
                    ${this._renderControl(param)}
                </div>
            `;
        });
    }

    _renderControl(param) {
        const value = this._settings[param.name];

        // 1. Choices (Select)
        if (param.choices && param.choices.length > 0) {
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
            return html`
                <div class="temp-header">
                    <label class="control-label">Creatividad (Temperature)</label>
                    <span class="temp-value">${value || 0.7}</span>
                </div>
                <input 
                    type="range" 
                    name="${param.name}"
                    min="0" max="1" step="0.1" 
                    .value=${value || 0.7}
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
