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

                        ${info.total_cost ? html`
                            <span class="cost-badge">
                                $${info.total_cost.toFixed(4)}
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
                            <span>🧠</span> Razonamiento Final
                        </div>
                        <div class="reasoning-text">${info.reasoning}</div>
                        <div class="reasoning-hint">
                            💡 Los pensamientos de cada paso están en la pestaña "Trajectoria"
                        </div>
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
                <div class="history-header">
                    📡 Llamadas al LM (${history.length} total)
                </div>
                ${history.map((call, index) => html`
                    <div class="history-item lm-call">
                        <div class="history-call-header">
                            <span class="call-number">Llamada ${index + 1}</span>
                            ${call.model ? html`<span class="call-model">${call.model.split('/').pop()}</span>` : ''}
                            ${this._getCallTokens(call) ? html`<span class="call-tokens">${this._getCallTokens(call)} tokens</span>` : ''}
                            ${this._getCallCost(call) ? html`<span class="call-cost">$${this._getCallCost(call).toFixed(4)}</span>` : ''}
                        </div>
                        <details class="call-details">
                            <summary>Ver prompt/respuesta</summary>
                            <div class="call-content">
                                ${this._renderCallMessages(call)}
                                ${this._renderCallOutputs(call)}
                            </div>
                        </details>
                    </div>
                `)}
            </div>
        `;
    }

    _getCallCost(call) {
        return call.cost 
            || call.response_cost 
            || call._hidden_params?.response_cost
            || call.response?._hidden_params?.response_cost
            || null;
    }

    _getCallTokens(call) {
        const usage = call.usage || call.response?.usage || call.outputs?.[0]?.usage;
        if (!usage) return null;
        return usage.total_tokens || ((usage.prompt_tokens || 0) + (usage.completion_tokens || 0));
    }

    _renderCallMessages(call) {
        // DSPy puede tener los mensajes en diferentes campos
        const messages = call.messages || call.prompt || call.inputs;
        if (!messages) return '';

        if (Array.isArray(messages)) {
            return html`
                <div class="call-section">
                    <div class="call-section-label">Prompt (${messages.length} msgs)</div>
                    ${messages.map(msg => html`
                        <div class="prompt-msg ${msg.role || 'unknown'}">
                            <strong>${msg.role || 'msg'}:</strong> 
                            ${typeof msg.content === 'string' 
                                ? (msg.content.length > 300 ? msg.content.substring(0, 300) + '...' : msg.content)
                                : JSON.stringify(msg.content).substring(0, 300)}
                        </div>
                    `)}
                </div>
            `;
        }
        
        return html`
            <div class="call-section">
                <div class="call-section-label">Prompt</div>
                <pre class="prompt-text">${typeof messages === 'string' ? messages : JSON.stringify(messages, null, 2)}</pre>
            </div>
        `;
    }

    _renderCallOutputs(call) {
        // DSPy puede tener las respuestas en diferentes campos
        const outputs = call.outputs || call.response?.choices || call.completions;
        if (!outputs) return '';

        return html`
            <div class="call-section">
                <div class="call-section-label">Respuesta</div>
                ${Array.isArray(outputs) ? outputs.map((out, i) => html`
                    <div class="output-item">
                        ${outputs.length > 1 ? html`<span class="output-num">#${i + 1}</span>` : ''}
                        <pre class="output-text">${
                            typeof out === 'string' 
                                ? out 
                                : (out.message?.content || out.text || JSON.stringify(out, null, 2))
                        }</pre>
                    </div>
                `) : html`
                    <pre class="output-text">${typeof outputs === 'string' ? outputs : JSON.stringify(outputs, null, 2)}</pre>
                `}
            </div>
        `;
    }

    _renderMetricsGrid(info) {
        if (!info.total_tokens && !info.model && !info.total_cost) return '';

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
                    <div class="metric-label">Cost</div>
                    <div class="metric-value cost">
                        ${info.total_cost ? `$${info.total_cost.toFixed(4)}` : '-'}
                    </div>
                </div>
                <div class="metric-card full-width">
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
            total_cost: 0,
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
        // Intentar sacar de la raíz primero
        if (data.model) info.model = data.model;
        if (data.usage) {
            info.prompt_tokens = data.usage.prompt_tokens || 0;
            info.completion_tokens = data.usage.completion_tokens || 0;
            info.total_tokens = data.usage.total_tokens || 0;
        }

        // Si no hay métricas en la raíz, extraerlas del historial de DSPy
        // El history de DSPy contiene las llamadas al LM con usage info
        if (info.history && info.history.length > 0) {
            // Sumar tokens y costos de todas las llamadas al LM
            let totalPrompt = 0;
            let totalCompletion = 0;
            let totalCost = 0;
            let lastModel = null;

            for (const call of info.history) {
                // DSPy history puede tener diferentes estructuras
                const usage = call.usage || call.response?.usage || call.outputs?.[0]?.usage;
                if (usage) {
                    totalPrompt += usage.prompt_tokens || usage.input_tokens || 0;
                    totalCompletion += usage.completion_tokens || usage.output_tokens || 0;
                }
                
                // Extraer costo de la llamada (LiteLLM puede ponerlo en varios lugares)
                const cost = call.cost 
                    || call.response_cost 
                    || call._hidden_params?.response_cost
                    || call.response?._hidden_params?.response_cost
                    || 0;
                totalCost += cost;
                
                // Extraer modelo de la llamada
                if (call.model) lastModel = call.model;
                else if (call.response?.model) lastModel = call.response.model;
            }

            if (!info.total_tokens && (totalPrompt || totalCompletion)) {
                info.prompt_tokens = totalPrompt;
                info.completion_tokens = totalCompletion;
                info.total_tokens = totalPrompt + totalCompletion;
            }

            if (totalCost > 0) {
                info.total_cost = totalCost;
            }

            if (!info.model && lastModel) {
                info.model = lastModel;
            }
        }

        return info;
    }
}

if (!customElements.get('chat-debug-info')) {
    customElements.define('chat-debug-info', ChatDebugInfo);
}
