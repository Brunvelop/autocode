/**
 * chat-debug-info.js
 * Componente para visualizar metadatos técnicos de la respuesta del chat
 * Refactorizado: Lógica pura separada de estilos
 * Muestra métricas de tokens, modelo utilizado y JSON crudo de la respuesta.
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { chatDebugInfoStyles } from './styles/chat-debug-info.styles.js';
import { themeTokens } from './styles/theme.js';

export class ChatDebugInfo extends LitElement {
    static properties = {
        data: { type: Object }
    };

    static styles = [themeTokens, chatDebugInfoStyles];

    constructor() {
        super();
        this.data = null;
    }

    render() {
        if (!this.data) {
            return html``;
        }

        const metrics = this._extractMetrics(this.data);
        const hasMetrics = metrics.model || metrics.total_tokens;

        return html`
            <details>
                <summary>
                    <span class="summary-content">
                        <span>🐞 Info Técnica</span>
                        ${hasMetrics ? html`
                            <span class="separator">|</span>
                            <span class="model-badge">
                                ${metrics.model ? metrics.model.split('/').pop() : 'Unknown Model'}
                            </span>
                            ${metrics.total_tokens ? html`
                                <span class="tokens-badge">
                                    ${metrics.total_tokens} tokens
                                </span>
                            ` : ''}
                        ` : ''}
                    </span>
                    <svg class="chevron" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                </summary>

                <div class="content">
                    ${this._renderMetricsGrid(metrics)}
                    ${this._renderJsonViewer()}
                </div>
            </details>
        `;
    }

    _renderMetricsGrid(metrics) {
        if (!metrics.total_tokens && !metrics.model) return '';

        return html`
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Prompt</div>
                    <div class="metric-value">${metrics.prompt_tokens}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Completion</div>
                    <div class="metric-value">${metrics.completion_tokens}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total</div>
                    <div class="metric-value total">${metrics.total_tokens}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Model</div>
                    <div class="metric-value model" title="${metrics.model}">
                        ${metrics.model ? metrics.model.split('/').pop() : '-'}
                    </div>
                </div>
            </div>
        `;
    }

    _renderJsonViewer() {
        return html`
            <div class="json-section">
                <div class="json-label">Raw Response</div>
                <pre class="json-content">${JSON.stringify(this.data, null, 2)}</pre>
            </div>
        `;
    }

    _extractMetrics(data) {
        let metrics = {
            model: null,
            prompt_tokens: 0,
            completion_tokens: 0,
            total_tokens: 0,
            cost: null
        };

        // 1. Intentar sacar de la raíz (algunos backends lo ponen directo)
        if (data.model) metrics.model = data.model;
        if (data.usage) {
            metrics.prompt_tokens = data.usage.prompt_tokens || 0;
            metrics.completion_tokens = data.usage.completion_tokens || 0;
            metrics.total_tokens = data.usage.total_tokens || 0;
        }

        // 2. Intentar sacar del último paso del historial (DSPy suele ponerlo ahí)
        if (data.history && Array.isArray(data.history) && data.history.length > 0) {
            const lastStep = data.history[data.history.length - 1];
            
            // Modelo
            if (lastStep.model) metrics.model = lastStep.model;
            
            // Usage (a veces está en response.usage o directo en usage)
            let usage = lastStep.usage;
            if (!usage && lastStep.response && lastStep.response.usage) {
                usage = lastStep.response.usage;
            }

            if (usage) {
                metrics.prompt_tokens = usage.prompt_tokens || metrics.prompt_tokens;
                metrics.completion_tokens = usage.completion_tokens || metrics.completion_tokens;
                metrics.total_tokens = usage.total_tokens || metrics.total_tokens;
            }
        }

        return metrics;
    }
}

if (!customElements.get('chat-debug-info')) {
    customElements.define('chat-debug-info', ChatDebugInfo);
}
