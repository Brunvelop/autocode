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
        // Commit metrics
        _metrics: { state: true },
        _metricsLoading: { state: true },
        _metricsExpanded: { state: true },
    };

    static styles = [themeTokens, commitDetailStyles];

    constructor() {
        super();
        this.commitHash = null;
        this.commitSummary = null;
        this._detail = null;
        this._loading = false;
        this._error = null;
        // Metrics
        this._metrics = null;
        this._metricsLoading = false;
        this._metricsExpanded = false;
    }

    willUpdate(changed) {
        if (changed.has('commitHash') && this.commitHash) {
            this._loadDetail();
            this._metrics = null;
            this._metricsExpanded = false;
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
    // COMMIT METRICS
    // ========================================================================

    _renderMetricsSection() {
        return html`
            <div class="metrics-toggle" @click=${this._toggleMetrics}>
                <span class="metrics-toggle-icon">${this._metricsExpanded ? '▾' : '▸'}</span>
                <span class="metrics-toggle-label">📊 Métricas de código</span>
                ${this._metricsLoading ? html`<div class="spinner-sm"></div>` : ''}
            </div>
            ${this._metricsExpanded ? this._renderMetricsContent() : ''}
        `;
    }

    _renderMetricsContent() {
        if (this._metricsLoading) {
            return html`<div class="metrics-loading">Analizando...</div>`;
        }
        if (!this._metrics || !this._metrics.files || this._metrics.files.length === 0) {
            return html`<div class="metrics-empty">Sin archivos .py en este commit</div>`;
        }

        const m = this._metrics;
        const s = m.summary || {};

        return html`
            <div class="metrics-content">
                <!-- Summary -->
                <div class="metrics-summary-bar">
                    <span class="ms-item">
                        SLOC <span class="ms-delta ${s.delta_sloc > 0 ? 'ms-up' : s.delta_sloc < 0 ? 'ms-down' : ''}">
                            ${s.delta_sloc > 0 ? '+' : ''}${s.delta_sloc || 0}
                        </span>
                    </span>
                    <span class="ms-item">
                        CC <span class="ms-delta ${s.delta_avg_complexity > 0 ? 'ms-up' : s.delta_avg_complexity < 0 ? 'ms-down' : ''}">
                            ${s.delta_avg_complexity > 0 ? '+' : ''}${s.delta_avg_complexity?.toFixed(2) || '0'}
                        </span>
                    </span>
                    <span class="ms-item ms-count">${s.files_analyzed || 0} .py</span>
                </div>

                <!-- Per-file table -->
                <div class="metrics-files">
                    ${m.files.map(f => html`
                        <div class="mf-row">
                            <span class="mf-path" title="${f.path}">${this._shortPath(f.path)}</span>
                            <span class="mf-stat">
                                SLOC <span class="${f.delta_sloc > 0 ? 'ms-up' : f.delta_sloc < 0 ? 'ms-down' : ''}">${f.delta_sloc > 0 ? '+' : ''}${f.delta_sloc}</span>
                            </span>
                            <span class="mf-stat">
                                CC <span class="${f.delta_complexity > 0 ? 'ms-up' : f.delta_complexity < 0 ? 'ms-down' : ''}">${f.delta_complexity > 0 ? '+' : ''}${f.delta_complexity?.toFixed(1)}</span>
                            </span>
                            <span class="mf-stat">
                                MI <span class="${f.delta_mi > 0 ? 'ms-down-good' : f.delta_mi < 0 ? 'ms-up-bad' : ''}">${f.delta_mi > 0 ? '+' : ''}${f.delta_mi?.toFixed(1)}</span>
                            </span>
                        </div>
                    `)}
                </div>
            </div>
        `;
    }

    async _toggleMetrics() {
        this._metricsExpanded = !this._metricsExpanded;
        if (this._metricsExpanded && !this._metrics && !this._metricsLoading) {
            await this._loadMetrics();
        }
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
