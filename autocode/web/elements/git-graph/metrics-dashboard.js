/**
 * metrics-dashboard.js
 * Dashboard de métricas de código del proyecto.
 *
 * Muestra snapshot actual con tarjetas resumen, distribución de complejidad,
 * top funciones complejas, peores MI, acoplamiento y comparación con snapshot previo.
 *
 * Usa AutoFunctionController.executeFunction() para llamar a generate_code_metrics.
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { AutoFunctionController } from '../auto-element-generator.js';
import { themeTokens } from './styles/theme.js';
import { metricsDashboardStyles } from './styles/metrics-dashboard.styles.js';

// Sub-component: metrics chart (evolution over commits)
import './metrics-chart.js';

const RANKS = ['A', 'B', 'C', 'D', 'E', 'F'];

export class MetricsDashboard extends LitElement {
    static properties = {
        _data: { state: true },       // MetricsComparison from API
        _loading: { state: true },
        _error: { state: true },
    };

    static styles = [themeTokens, metricsDashboardStyles];

    constructor() {
        super();
        this._data = null;
        this._loading = false;
        this._error = null;
    }

    connectedCallback() {
        super.connectedCallback();
        this.refresh();
    }

    async refresh() {
        this._loading = true;
        this._error = null;
        try {
            const result = await AutoFunctionController.executeFunction('generate_code_metrics', {});
            this._data = result;
        } catch (e) {
            this._error = e.message || 'Error generando métricas';
        } finally {
            this._loading = false;
        }
    }

    render() {
        if (this._loading) {
            return html`
                <div class="loading-container">
                    <div class="spinner"></div>
                    <span>Analizando código...</span>
                </div>
            `;
        }
        if (this._error) {
            return html`
                <div class="error-container">
                    <div class="error-msg">❌ ${this._error}</div>
                    <button class="retry-btn" @click=${this.refresh}>Reintentar</button>
                </div>
            `;
        }
        if (!this._data) return html``;

        const snap = this._data.after;
        const before = this._data.before;
        if (!snap) return html`<div class="error-container"><span>Sin datos</span></div>`;

        return html`
            <div class="dashboard">
                ${this._renderSummary(snap, before)}
                <!-- Metrics evolution chart (over commits) -->
                <metrics-chart></metrics-chart>
                ${this._renderDistribution(snap)}
                <div class="two-col">
                    ${this._renderTopComplex(snap)}
                    ${this._renderWorstMI(snap)}
                </div>
                ${this._renderCoupling(snap)}
                ${this._renderSnapshotInfo(snap)}
            </div>
        `;
    }

    // ===== SUMMARY CARDS =====

    _renderSummary(snap, before) {
        const d = this._data;
        return html`
            <div class="summary-grid">
                ${this._card('SLOC', this._fmt(snap.total_sloc), d.delta_sloc, null, true)}
                ${this._card('Archivos', snap.total_files, null)}
                ${this._card('Funciones', snap.total_functions, d.delta_functions)}
                ${this._card('Clases', snap.total_classes, d.delta_classes)}
                ${this._card('CC Media', snap.avg_complexity?.toFixed(2), d.delta_avg_complexity,
                    snap.avg_complexity < 5 ? '✅' : snap.avg_complexity < 10 ? '⚠️' : '🔴')}
                ${this._card('MI Media', snap.avg_mi?.toFixed(1), d.delta_avg_mi,
                    snap.avg_mi >= 60 ? '✅' : snap.avg_mi >= 40 ? '⚠️' : '🔴', false, true)}
            </div>
        `;
    }

    _card(label, value, delta, status, lowerBetter = false, higherBetter = false) {
        let deltaHtml = '';
        if (delta != null && delta !== 0) {
            const sign = delta > 0 ? '+' : '';
            const num = typeof delta === 'number' ? (Number.isInteger(delta) ? delta : delta.toFixed(2)) : delta;
            let cls = 'delta-neutral';
            if (lowerBetter) cls = delta < 0 ? 'delta-positive' : 'delta-negative';
            else if (higherBetter) cls = delta > 0 ? 'delta-positive' : 'delta-negative';
            deltaHtml = html`<span class="card-delta ${cls}">${sign}${num}</span>`;
        }
        return html`
            <div class="summary-card">
                ${status ? html`<span class="card-status">${status}</span>` : ''}
                <span class="card-label">${label}</span>
                <span class="card-value">${value}</span>
                ${deltaHtml}
            </div>
        `;
    }

    // ===== COMPLEXITY DISTRIBUTION =====

    _renderDistribution(snap) {
        const dist = snap.complexity_distribution || {};
        const maxVal = Math.max(1, ...RANKS.map(r => dist[r] || 0));
        return html`
            <div class="section">
                <div class="section-title">🧩 Distribución de Complejidad</div>
                <div class="dist-bars">
                    ${RANKS.map(rank => {
                        const count = dist[rank] || 0;
                        const pct = (count / maxVal) * 100;
                        return html`
                            <div class="dist-bar-group">
                                <span class="dist-count">${count}</span>
                                <div class="dist-bar rank-${rank}" style="height: ${Math.max(pct, 3)}%"></div>
                                <span class="dist-label">${rank}</span>
                            </div>
                        `;
                    })}
                </div>
            </div>
        `;
    }

    // ===== TOP COMPLEX FUNCTIONS =====

    _renderTopComplex(snap) {
        const allFuncs = (snap.files || []).flatMap(f => f.functions || []);
        const top = allFuncs.sort((a, b) => b.complexity - a.complexity).slice(0, 10);
        if (top.length === 0) return '';
        return html`
            <div class="section">
                <div class="section-title">🔥 Top Funciones Complejas</div>
                <table class="metrics-table">
                    <thead><tr>
                        <th>Función</th><th>Archivo</th><th>CC</th><th>Rank</th><th>Nesting</th>
                    </tr></thead>
                    <tbody>
                        ${top.map(f => html`
                            <tr>
                                <td class="mono">${f.name}</td>
                                <td class="path" title="${f.file}">${this._shortPath(f.file)}</td>
                                <td class="mono">${f.complexity}</td>
                                <td><span class="rank-badge rank-${f.rank}">${f.rank}</span></td>
                                <td class="mono">${f.nesting_depth}</td>
                            </tr>
                        `)}
                    </tbody>
                </table>
            </div>
        `;
    }

    // ===== WORST MAINTAINABILITY =====

    _renderWorstMI(snap) {
        const files = [...(snap.files || [])].sort((a, b) => a.maintainability_index - b.maintainability_index).slice(0, 10);
        if (files.length === 0) return '';
        return html`
            <div class="section">
                <div class="section-title">📐 Peor Mantenibilidad</div>
                <table class="metrics-table">
                    <thead><tr>
                        <th>Archivo</th><th>MI</th><th>SLOC</th><th>Max CC</th><th></th>
                    </tr></thead>
                    <tbody>
                        ${files.map(f => html`
                            <tr>
                                <td class="path" title="${f.path}">${this._shortPath(f.path)}</td>
                                <td class="mono">${f.maintainability_index?.toFixed(1)}</td>
                                <td class="mono">${f.sloc}</td>
                                <td class="mono">${f.max_complexity}</td>
                                <td class="status-icon">${f.maintainability_index >= 60 ? '✅' : f.maintainability_index >= 40 ? '⚠️' : '🔴'}</td>
                            </tr>
                        `)}
                    </tbody>
                </table>
            </div>
        `;
    }

    // ===== COUPLING =====

    _renderCoupling(snap) {
        const coupling = snap.coupling || [];
        const circulars = snap.circular_deps || [];
        if (coupling.length === 0) return '';

        return html`
            <div class="section">
                <div class="section-title">🏗️ Acoplamiento</div>
                ${circulars.length > 0 ? html`
                    ${circulars.map(c => html`
                        <div class="circular-warning">⚠️ Circular: ${c[0]} ↔ ${c[1]}</div>
                    `)}
                ` : html`<div class="no-issues">✅ Sin dependencias circulares</div>`}
                <table class="metrics-table">
                    <thead><tr>
                        <th>Paquete</th><th>Ce</th><th>Ca</th><th>Inest.</th>
                    </tr></thead>
                    <tbody>
                        ${coupling.map(c => html`
                            <tr>
                                <td class="mono">${c.name}</td>
                                <td class="mono">${c.ce}</td>
                                <td class="mono">${c.ca}</td>
                                <td class="mono">${c.instability?.toFixed(2)}</td>
                            </tr>
                        `)}
                    </tbody>
                </table>
            </div>
        `;
    }

    // ===== SNAPSHOT INFO =====

    _renderSnapshotInfo(snap) {
        return html`
            <div class="snapshot-info">
                📊 Commit ${snap.commit_short} · ${snap.branch} · ${this._formatDate(snap.timestamp)}
            </div>
        `;
    }

    // ===== HELPERS =====

    _fmt(n) {
        if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
        return n;
    }

    _shortPath(p) {
        if (!p) return '';
        const parts = p.split('/');
        return parts.length > 2 ? '…/' + parts.slice(-2).join('/') : p;
    }

    _formatDate(iso) {
        if (!iso) return '';
        try { return new Date(iso).toLocaleString('es-ES', { dateStyle: 'short', timeStyle: 'short' }); }
        catch { return iso; }
    }
}

if (!customElements.get('metrics-dashboard')) {
    customElements.define('metrics-dashboard', MetricsDashboard);
}
