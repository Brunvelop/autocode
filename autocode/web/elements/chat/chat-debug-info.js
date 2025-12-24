/**
 * chat-debug-info.js
 * Componente para visualizar metadatos técnicos de la respuesta del chat
 * Refactorizado: Interface con pestañas y visualización rica de trajectoria
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { chatDebugInfoStyles } from './styles/chat-debug-info.styles.js';
import { themeTokens } from './styles/theme.js';

export class ChatDebugInfo extends LitElement {
    static properties = {
        data: { type: Object },
        _activeTab: { state: true }
    };

    static styles = [themeTokens, chatDebugInfoStyles];

    constructor() {
        super();
        this.data = null;
        this._activeTab = 'overview';
    }

    render() {
        if (!this.data) {
            return html``;
        }

        const info = this._parseData(this.data);
        const hasTrajectory = info.trajectory && info.trajectory.length > 0;
        const hasHistory = info.history && info.history.length > 0;

        return html`
            <details>
                <summary>
                    <span class="summary-content">
                        <span>🐞 Info Técnica</span>
                        <span class="separator">|</span>
                        
                        ${info.model ? html`
                            <span class="model-badge" title="${info.model}">
                                ${info.model.split('/').pop()}
                            </span>
                        ` : ''}

                        ${info.total_tokens ? html`
                            <span class="tokens-badge">
                                ${info.total_tokens} tokens
                            </span>
                        ` : ''}

                        ${info.success !== undefined ? html`
                            <span class="status-badge" style="color: ${info.success ? 'green' : 'red'}">
                                ${info.success ? '✔' : '✘'}
                            </span>
                        ` : ''}
                    </span>
                    <svg class="chevron" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                </summary>

                <div class="content">
                    <!-- Tabs Navigation -->
                    <div class="tabs">
                        <button 
                            class="tab-btn ${this._activeTab === 'overview' ? 'active' : ''}" 
                            @click=${() => this._activeTab = 'overview'}
                        >
                            Resumen
                        </button>
                        
                        ${hasTrajectory ? html`
                            <button 
                                class="tab-btn ${this._activeTab === 'trajectory' ? 'active' : ''}" 
                                @click=${() => this._activeTab = 'trajectory'}
                            >
                                Trajectoria (${info.trajectory.length})
                            </button>
                        ` : ''}

                        ${hasHistory ? html`
                            <button 
                                class="tab-btn ${this._activeTab === 'history' ? 'active' : ''}" 
                                @click=${() => this._activeTab = 'history'}
                            >
                                Historial (${info.history.length})
                            </button>
                        ` : ''}

                        <button 
                            class="tab-btn ${this._activeTab === 'raw' ? 'active' : ''}" 
                            @click=${() => this._activeTab = 'raw'}
                        >
                            JSON
                        </button>
                    </div>

                    <!-- Tab Content -->
                    <div class="tab-content">
                        ${this._renderActiveTab(info)}
                    </div>
                </div>
            </details>
        `;
    }

    _renderActiveTab(info) {
        switch (this._activeTab) {
            case 'overview': return this._renderOverview(info);
            case 'trajectory': return this._renderTrajectory(info.trajectory);
            case 'history': return this._renderHistory(info.history);
            case 'raw': return this._renderJsonViewer();
            default: return this._renderOverview(info);
        }
    }

    _renderOverview(info) {
        return html`
            <div class="overview-section">
                <!-- Metrics -->
                ${this._renderMetricsGrid(info)}

                <!-- Reasoning -->
                ${info.reasoning ? html`
                    <div class="reasoning-box">
                        <div class="reasoning-label">
                            <span>🧠</span> Proceso de Pensamiento
                        </div>
                        <div class="reasoning-text">${info.reasoning}</div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    _renderTrajectory(trajectory) {
        return html`
            <div class="trajectory-list">
                ${trajectory.map((step, index) => html`
                    <div class="trajectory-step">
                        <div class="step-header">
                            <span class="step-tool">${step.tool_name || step.tool || 'Unknown Tool'}</span>
                            <span class="label">Paso ${index + 1}</span>
                        </div>
                        <div class="step-body">
                            ${step.thought ? html`
                                <div class="step-thought">💭 ${step.thought}</div>
                            ` : ''}
                            
                            <div class="step-input">
                                <div class="label">Input</div>
                                <code>${typeof step.tool_args === 'string' ? step.tool_args : JSON.stringify(step.tool_args)}</code>
                            </div>

                            ${step.observation || step.result ? html`
                                <div class="step-output">
                                    <div class="label">Observation</div>
                                    <details>
                                        <summary>Ver resultado</summary>
                                        <pre style="font-size: 0.65rem; max-height: 200px; overflow: auto;">${
                                            typeof (step.observation || step.result) === 'string' 
                                                ? (step.observation || step.result) 
                                                : JSON.stringify(step.observation || step.result, null, 2)
                                        }</pre>
                                    </details>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `)}
            </div>
        `;
    }

    _renderHistory(history) {
        return html`
            <div class="history-list">
                ${history.map(msg => html`
                    <div class="history-item ${msg.role}">
                        <div class="history-role">${msg.role}</div>
                        <div class="history-content">${msg.content}</div>
                    </div>
                `)}
            </div>
        `;
    }

    _renderMetricsGrid(info) {
        if (!info.total_tokens && !info.model) return '';

        return html`
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Prompt</div>
                    <div class="metric-value">${info.prompt_tokens}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Completion</div>
                    <div class="metric-value">${info.completion_tokens}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total</div>
                    <div class="metric-value total">${info.total_tokens}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Model</div>
                    <div class="metric-value model" title="${info.model}">
                        ${info.model ? info.model.split('/').pop() : '-'}
                    </div>
                </div>
            </div>
        `;
    }

    _renderJsonViewer() {
        return html`
            <div class="json-section">
                <div class="json-content">${JSON.stringify(this.data, null, 2)}</div>
            </div>
        `;
    }

    _parseData(data) {
        // Estructura base
        let info = {
            model: null,
            prompt_tokens: 0,
            completion_tokens: 0,
            total_tokens: 0,
            reasoning: null,
            trajectory: [],
            history: [],
            success: undefined
        };

        // 1. Extraer Reasoning
        if (data.reasoning) info.reasoning = data.reasoning;
        else if (data.result && data.result.reasoning) info.reasoning = data.result.reasoning;

        // 2. Extraer Trajectory
        if (data.trajectory && Array.isArray(data.trajectory)) info.trajectory = data.trajectory;
        else if (data.result && data.result.trajectory) info.trajectory = data.result.trajectory;

        // 3. Extraer History
        if (data.history && Array.isArray(data.history)) info.history = data.history;
        else if (data.result && data.result.history) info.history = data.result.history;

        // 4. Extraer Success
        if (data.success !== undefined) info.success = data.success;

        // 5. Extraer Metrics (Model & Tokens)
        // Intentar sacar de la raíz
        if (data.model) info.model = data.model;
        if (data.usage) {
            info.prompt_tokens = data.usage.prompt_tokens || 0;
            info.completion_tokens = data.usage.completion_tokens || 0;
            info.total_tokens = data.usage.total_tokens || 0;
        }

        // Si no hay métricas, buscar en el historial (donde DSPy suele ponerlo)
        if (!info.total_tokens && info.history && info.history.length > 0) {
            // A veces el último paso del historial tiene info de uso si es un assistant message
            // Pero en DSPy structures a veces está en un campo aparte o en el último 'turn'
            // Por ahora nos quedamos con la lógica básica anterior
        }
        
        // Buscar en trajectory si hay info de modelo
        // (A veces no está explícito en la respuesta top-level)

        return info;
    }
}

if (!customElements.get('chat-debug-info')) {
    customElements.define('chat-debug-info', ChatDebugInfo);
}
