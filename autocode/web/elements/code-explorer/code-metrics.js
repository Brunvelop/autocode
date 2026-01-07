/**
 * code-metrics.js
 * Componente para mostrar resumen de métricas del código.
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { themeTokens } from './styles/theme.js';
import { codeMetricsStyles } from './styles/code-metrics.styles.js';

export class CodeMetrics extends LitElement {
    static properties = {
        metrics: { type: Object }
    };

    static styles = [themeTokens, codeMetricsStyles];

    constructor() {
        super();
        this.metrics = null;
    }

    render() {
        if (!this.metrics) {
            return html``;
        }

        return html`
            <div class="metrics-container">
                <!-- Archivos -->
                <div class="metric">
                    <span class="metric-icon">📄</span>
                    <span class="metric-value">${this._formatNumber(this.metrics.total_files)}</span>
                    <span class="metric-label">archivos</span>
                </div>

                <!-- LOC -->
                <div class="metric">
                    <span class="metric-icon">📝</span>
                    <span class="metric-value">${this._formatNumber(this.metrics.total_loc)}</span>
                    <span class="metric-label">LOC</span>
                </div>

                <!-- Funciones -->
                <div class="metric">
                    <span class="metric-icon">⚡</span>
                    <span class="metric-value">${this._formatNumber(this.metrics.total_functions)}</span>
                    <span class="metric-label">funciones</span>
                </div>

                <!-- Clases -->
                <div class="metric">
                    <span class="metric-icon">🔷</span>
                    <span class="metric-value">${this._formatNumber(this.metrics.total_classes)}</span>
                    <span class="metric-label">clases</span>
                </div>

                <!-- Lenguajes -->
                ${this._renderLanguages()}
            </div>
        `;
    }

    _renderLanguages() {
        if (!this.metrics.languages || this.metrics.languages.length === 0) {
            return '';
        }

        return html`
            <div class="languages">
                ${this.metrics.languages.map(lang => html`
                    <span class="lang-badge ${lang}">
                        <span class="lang-icon">${lang === 'python' ? '🐍' : '🟨'}</span>
                        ${lang}
                    </span>
                `)}
            </div>
        `;
    }

    _formatNumber(num) {
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'k';
        }
        return num;
    }
}

if (!customElements.get('code-metrics')) {
    customElements.define('code-metrics', CodeMetrics);
}
