/**
 * commit-detail.js
 * Panel de detalle de un commit seleccionado.
 * Lazy-loads the commit detail (files changed, stats) via API.
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { AutoFunctionController } from '../auto-element-generator.js';
import { themeTokens } from './styles/theme.js';
import { commitDetailStyles } from './styles/commit-detail.styles.js';

// Status icons for file changes
const STATUS_ICONS = {
    added: '✅',
    modified: '🔄',
    deleted: '❌',
    renamed: '📝',
    copied: '📋',
    type_changed: '🔀',
};

export class CommitDetail extends LitElement {
    static properties = {
        commitHash: { type: String, attribute: 'commit-hash' },
        commitSummary: { type: Object },  // Basic info passed from parent (for instant display)
        _detail: { state: true },          // Full detail loaded from API
        _loading: { state: true },
        _error: { state: true },
        // Commit metrics — always visible
        _metrics: { state: true },
        _metricsLoading: { state: true },
        _metricsCollapsed: { state: true },
    };

    static styles = [themeTokens, commitDetailStyles];

    constructor() {
        super();
        this.commitHash = null;
        this.commitSummary = null;
        this._detail = null;
        this._loading = false;
        this._error = null;
        // Metrics — expanded by default
        this._metrics = null;
        this._metricsLoading = false;
        this._metricsCollapsed = false;
    }

    willUpdate(changed) {
        if (changed.has('commitHash') && this.commitHash) {
            this._loadDetail();
            // Auto-load metrics alongside detail
            this._metrics = null;
            this._loadMetrics();
        }
    }

    render() {
        if (this._loading) {
            return html`
                <div class="loading-detail">
                    <div class="spinner-sm"></div>
                    <span>Cargando detalle...</span>
                </div>
            `;
        }

        if (this._error) {
            return html`
                <div class="detail-container">
                    <div class="error-msg">❌ ${this._error}</div>
                </div>
            `;
        }

        const detail = this._detail;
        if (!detail) return html``;

        return html`
            <div class="detail-container">
                <!-- Header -->
                <div class="detail-header">
                    <h4 class="detail-title">${detail.message_full?.split('\n')[0] || 'Commit'}</h4>
                    <button class="close-btn" @click=${this._handleClose} title="Cerrar">✕</button>
                </div>

                <!-- Meta info -->
                <div class="meta-section">
                    <div class="meta-row">
                        <span class="meta-label">Hash</span>
                        <span class="meta-value hash">${detail.hash}</span>
                    </div>
                    <div class="meta-row">
                        <span class="meta-label">Autor</span>
                        <span class="meta-value author">${detail.author} &lt;${detail.author_email}&gt;</span>
                    </div>
                    <div class="meta-row">
                        <span class="meta-label">Fecha</span>
                        <span class="meta-value">${this._formatFullDate(detail.date)}</span>
                    </div>
                </div>

                <!-- Parents -->
                ${detail.parents && detail.parents.length > 0 ? html`
                    <div class="parents-section">
                        <span class="parent-label">
                            ${detail.parents.length > 1 ? 'Padres:' : 'Padre:'}
                        </span>
                        ${detail.parents.map(p => html`
                            <span class="parent-hash" 
                                @click=${() => this._navigateToCommit(p)}
                                title="Ver commit ${p.substring(0, 7)}"
                            >${p.substring(0, 7)}</span>
                        `)}
                    </div>
                ` : ''}

                <!-- Full message (if multiline) -->
                ${this._isMultilineMessage(detail.message_full) ? html`
                    <div class="message-section">${detail.message_full}</div>
                ` : ''}

                <!-- Stats bar -->
                ${detail.stats ? html`
                    <div class="stats-bar">
                        <span class="stat-item stat-files">
                            📄 ${detail.stats.files_changed || 0} archivos
                        </span>
                        <span class="stat-item stat-add">
                            +${detail.stats.total_additions || 0}
                        </span>
                        <span class="stat-item stat-del">
                            −${detail.stats.total_deletions || 0}
                        </span>
                    </div>
                ` : ''}

                <!-- Files list -->
                ${detail.files && detail.files.length > 0 ? html`
                    <div class="files-section">
                        <div class="files-header">Archivos cambiados</div>
                        ${detail.files.map(f => this._renderFileItem(f))}
                    </div>
                ` : ''}

                <!-- Code Metrics (expandable) -->
                ${this._renderMetricsSection()}
            </div>
        `;
    }

    // ========================================================================
    // API
    // ========================================================================

    async _loadDetail() {
        if (!this.commitHash) return;

        this._loading = true;
        this._error = null;
        this._detail = null;

        try {
            const result = await AutoFunctionController.executeFunction(
                'get_commit_detail',
                { commit_hash: this.commitHash }
            );

            this._detail = result;
        } catch (error) {
            this._error = error.message || 'Error cargando detalle del commit';
            console.error('❌ Error loading commit detail:', error);
        } finally {
            this._loading = false;
        }
    }

    // ========================================================================
    // RENDER HELPERS
    // ========================================================================

    _renderFileItem(file) {
        const icon = STATUS_ICONS[file.status] || '📄';
        const hasStats = file.additions > 0 || file.deletions > 0;

        return html`
            <div class="file-item" title="${file.path}">
                <span class="file-status-icon">${icon}</span>
                <span class="file-path">${file.path}</span>
                ${hasStats ? html`
                    <span class="file-stats">
                        ${file.additions > 0 ? html`
                            <span class="file-stat-add">+${file.additions}</span>
                        ` : ''}
                        ${file.deletions > 0 ? html`
                            <span class="file-stat-del">-${file.deletions}</span>
                        ` : ''}
                    </span>
                ` : ''}
            </div>
        `;
    }

    _isMultilineMessage(msg) {
        if (!msg) return false;
        const lines = msg.split('\n').filter(l => l.trim());
        return lines.length > 1;
    }

    _formatFullDate(isoDate) {
        if (!isoDate) return '';
        try {
            return new Date(isoDate).toLocaleString('es-ES', {
                weekday: 'short',
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            });
        } catch {
            return isoDate;
        }
    }

    // ========================================================================
    // COMMIT METRICS (always visible, detailed)
    // ========================================================================

    _renderMetricsSection() {
        const isCollapsed = this._metricsCollapsed;
        return html`
            <div class="metrics-header-bar" @click=${this._toggleMetrics}>
                <span class="metrics-toggle-icon">${isCollapsed ? '▸' : '▾'}</span>
                <span class="metrics-header-label">📊 Métricas de código</span>
                ${this._metricsLoading ? html`<div class="spinner-sm"></div>` : ''}
                ${!this._metricsLoading && this._metrics?.files?.length ? html`
                    <span class="metrics-header-count">${this._metrics.files.length} .py</span>
                ` : ''}
            </div>
            ${!isCollapsed ? this._renderMetricsContent() : ''}
        `;
    }

    _renderMetricsContent() {
        if (this._metricsLoading) {
            return html`<div class="metrics-loading">
                <div class="spinner-sm"></div>
                <span>Analizando métricas...</span>
            </div>`;
        }
        if (!this._metrics || !this._metrics.files || this._metrics.files.length === 0) {
            return html`<div class="metrics-empty">Sin archivos .py en este commit</div>`;
        }

        const m = this._metrics;
        const s = m.summary || {};

        // Aggregate totals from file data for detailed summary
        const totalBefore = { sloc: 0, funcs: 0, classes: 0, maxCC: 0 };
        const totalAfter = { sloc: 0, funcs: 0, classes: 0, maxCC: 0 };
        let totalMiBefore = 0, totalMiAfter = 0, miCount = 0;

        for (const f of m.files) {
            if (f.before) {
                totalBefore.sloc += f.before.sloc || 0;
                totalBefore.funcs += f.before.functions_count || 0;
                totalBefore.classes += f.before.classes_count || 0;
                totalBefore.maxCC = Math.max(totalBefore.maxCC, f.before.max_complexity || 0);
                totalMiBefore += f.before.maintainability_index || 0;
            }
            if (f.after) {
                totalAfter.sloc += f.after.sloc || 0;
                totalAfter.funcs += f.after.functions_count || 0;
                totalAfter.classes += f.after.classes_count || 0;
                totalAfter.maxCC = Math.max(totalAfter.maxCC, f.after.max_complexity || 0);
                totalMiAfter += f.after.maintainability_index || 0;
            }
            if (f.after || f.before) miCount++;
        }

        const avgMiBefore = miCount ? totalMiBefore / miCount : 0;
        const avgMiAfter = miCount ? totalMiAfter / miCount : 0;
        const deltaMi = avgMiAfter - avgMiBefore;
        const deltaFuncs = totalAfter.funcs - totalBefore.funcs;
        const deltaClasses = totalAfter.classes - totalBefore.classes;

        return html`
            <div class="metrics-content">
                <!-- Summary cards -->
                <div class="metrics-summary-grid">
                    ${this._metricCard('SLOC', s.delta_sloc, totalAfter.sloc, true)}
                    ${this._metricCard('CC Media', s.delta_avg_complexity, null, true, true)}
                    ${this._metricCard('MI Media', deltaMi, avgMiAfter?.toFixed(1), false, true, true)}
                    ${this._metricCard('Funciones', deltaFuncs, totalAfter.funcs)}
                    ${this._metricCard('Clases', deltaClasses, totalAfter.classes)}
                    ${this._metricCard('Max CC', totalAfter.maxCC - totalBefore.maxCC, totalAfter.maxCC, true)}
                </div>

                <!-- Per-file detailed cards -->
                <div class="metrics-files-detailed">
                    ${m.files.map(f => this._renderFileMetrics(f))}
                </div>
            </div>
        `;
    }

    _metricCard(label, delta, value, lowerBetter = false, isFloat = false, higherBetter = false) {
        let deltaClass = 'delta-neutral';
        if (delta != null && delta !== 0) {
            if (lowerBetter) deltaClass = delta < 0 ? 'delta-positive' : 'delta-negative';
            else if (higherBetter) deltaClass = delta > 0 ? 'delta-positive' : 'delta-negative';
        }
        const sign = delta > 0 ? '+' : '';
        const deltaStr = delta != null && delta !== 0
            ? (isFloat ? `${sign}${delta.toFixed(2)}` : `${sign}${delta}`)
            : '—';

        return html`
            <div class="mc-card">
                <span class="mc-label">${label}</span>
                ${value != null ? html`<span class="mc-value">${value}</span>` : ''}
                <span class="mc-delta ${deltaClass}">${deltaStr}</span>
            </div>
        `;
    }

    _renderFileMetrics(f) {
        const statusIcons = { added: '✅', modified: '🔄', deleted: '❌' };
        const icon = statusIcons[f.status] || '📄';
        const after = f.after || {};
        const before = f.before || {};

        // MI status indicator
        const mi = after.maintainability_index ?? 0;
        const miIcon = mi >= 60 ? '✅' : mi >= 40 ? '⚠️' : '🔴';

        return html`
            <div class="mf-card">
                <div class="mf-card-header">
                    <span class="mf-status-icon">${icon}</span>
                    <span class="mf-card-path" title="${f.path}">${this._shortPath(f.path)}</span>
                    <span class="mf-status-badge mf-status-${f.status}">${f.status}</span>
                </div>

                ${f.status === 'deleted' ? html`
                    <div class="mf-deleted-info">Archivo eliminado (${before.sloc || 0} SLOC)</div>
                ` : html`
                    <!-- Metrics grid -->
                    <div class="mf-metrics-grid">
                        <div class="mf-metric">
                            <span class="mf-metric-label">SLOC</span>
                            <span class="mf-metric-value">${after.sloc || 0}</span>
                            ${this._renderDelta(f.delta_sloc, true)}
                        </div>
                        <div class="mf-metric">
                            <span class="mf-metric-label">Funciones</span>
                            <span class="mf-metric-value">${after.functions_count || 0}</span>
                            ${this._renderDelta((after.functions_count || 0) - (before.functions_count || 0))}
                        </div>
                        <div class="mf-metric">
                            <span class="mf-metric-label">Clases</span>
                            <span class="mf-metric-value">${after.classes_count || 0}</span>
                            ${this._renderDelta((after.classes_count || 0) - (before.classes_count || 0))}
                        </div>
                        <div class="mf-metric">
                            <span class="mf-metric-label">CC Media</span>
                            <span class="mf-metric-value">${after.avg_complexity?.toFixed(1) || '0'}</span>
                            ${this._renderDelta(f.delta_complexity, true, true)}
                        </div>
                        <div class="mf-metric">
                            <span class="mf-metric-label">Max CC</span>
                            <span class="mf-metric-value">${after.max_complexity || 0}</span>
                            ${this._renderDelta((after.max_complexity || 0) - (before.max_complexity || 0), true)}
                        </div>
                        <div class="mf-metric">
                            <span class="mf-metric-label">Max Nest</span>
                            <span class="mf-metric-value">${after.max_nesting || 0}</span>
                            ${this._renderDelta((after.max_nesting || 0) - (before.max_nesting || 0), true)}
                        </div>
                        <div class="mf-metric mf-metric-wide">
                            <span class="mf-metric-label">MI ${miIcon}</span>
                            <span class="mf-metric-value">${mi.toFixed(1)}</span>
                            ${this._renderDelta(f.delta_mi, false, true, true)}
                        </div>
                    </div>

                    <!-- Top complex functions (if any) -->
                    ${after.functions && after.functions.length > 0 ? html`
                        <div class="mf-functions">
                            <div class="mf-functions-title">Funciones (por CC)</div>
                            ${[...after.functions]
                                .sort((a, b) => b.complexity - a.complexity)
                                .slice(0, 5)
                                .map(fn => html`
                                    <div class="mf-func-row">
                                        <span class="mf-func-name" title="${fn.name}">${fn.name}</span>
                                        <span class="mf-func-cc">CC ${fn.complexity}</span>
                                        <span class="rank-badge rank-${fn.rank}">${fn.rank}</span>
                                        <span class="mf-func-nest">↕${fn.nesting_depth}</span>
                                    </div>
                                `)}
                        </div>
                    ` : ''}
                `}
            </div>
        `;
    }

    _renderDelta(delta, lowerBetter = false, isFloat = false, higherBetter = false) {
        if (delta == null || delta === 0) return html`<span class="mc-delta delta-neutral">—</span>`;
        let cls = 'delta-neutral';
        if (lowerBetter) cls = delta < 0 ? 'delta-positive' : 'delta-negative';
        else if (higherBetter) cls = delta > 0 ? 'delta-positive' : 'delta-negative';
        const sign = delta > 0 ? '+' : '';
        const val = isFloat ? delta.toFixed(1) : delta;
        return html`<span class="mc-delta ${cls}">${sign}${val}</span>`;
    }

    _toggleMetrics() {
        this._metricsCollapsed = !this._metricsCollapsed;
    }

    async _loadMetrics() {
        if (!this.commitHash) return;
        this._metricsLoading = true;
        try {
            const result = await AutoFunctionController.executeFunction(
                'get_commit_metrics',
                { commit_hash: this.commitHash }
            );
            this._metrics = result;
        } catch (e) {
            console.error('❌ Error loading commit metrics:', e);
            this._metrics = { files: [], summary: {} };
        } finally {
            this._metricsLoading = false;
        }
    }

    _shortPath(p) {
        if (!p) return '';
        const parts = p.split('/');
        return parts.length > 2 ? '…/' + parts.slice(-2).join('/') : p;
    }

    // ========================================================================
    // EVENTS
    // ========================================================================

    _handleClose() {
        this.dispatchEvent(new CustomEvent('detail-closed', {
            bubbles: true,
            composed: true,
        }));
    }

    _navigateToCommit(hash) {
        this.dispatchEvent(new CustomEvent('navigate-commit', {
            detail: { hash },
            bubbles: true,
            composed: true,
        }));
    }
}

if (!customElements.get('commit-detail')) {
    customElements.define('commit-detail', CommitDetail);
}
