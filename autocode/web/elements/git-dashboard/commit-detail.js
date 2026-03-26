/**
 * commit-detail.js
 * Panel de detalle de un commit seleccionado.
 * Lazy-loads the commit detail (files changed, stats) via API.
 * Shows a combined table merging file changes with code metrics.
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { RefractClient } from '/elements/client.js';
import { themeTokens } from './styles/theme.js';
import { commitDetailStyles } from './styles/commit-detail.styles.js';
import './files-metrics-table.js';

export class CommitDetail extends LitElement {
    static properties = {
        commitHash: { type: String, attribute: 'commit-hash' },
        commitSummary: { type: Object },
        _detail: { state: true },
        _loading: { state: true },
        _error: { state: true },
        _metrics: { state: true },
        _metricsLoading: { state: true },
    };

    static styles = [themeTokens, commitDetailStyles];

    constructor() {
        super();

        // HTTP client
        this._client = new RefractClient();

        this.commitHash = null;
        this.commitSummary = null;
        this._detail = null;
        this._loading = false;
        this._error = null;
        this._metrics = null;
        this._metricsLoading = false;
    }

    willUpdate(changed) {
        if (changed.has('commitHash') && this.commitHash) {
            this._loadDetail();
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

                <!-- Combined files + metrics table -->
                <files-metrics-table
                    .files=${this._mergeFilesWithMetrics()}
                    .metricsLoading=${this._metricsLoading}
                ></files-metrics-table>
            </div>
        `;
    }

    // ========================================================================
    // API
    // ========================================================================

    /**
     * Call API and unwrap envelope → payload.
     * Mirrors the behavior of AutoFunctionController.executeFunction().
     */
    async _call(funcName, params) {
        const data = await this._client.call(funcName, params);
        return (data && typeof data === 'object' && Object.prototype.hasOwnProperty.call(data, 'result'))
            ? data.result : data;
    }

    async _loadDetail() {
        if (!this.commitHash) return;
        this._loading = true;
        this._error = null;
        this._detail = null;

        try {
            const result = await this._call(
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

    async _loadMetrics() {
        if (!this.commitHash) return;
        this._metricsLoading = true;
        try {
            const result = await this._call(
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

    // ========================================================================
    // DATA HELPERS
    // ========================================================================

    /**
     * Merge detail.files (all changed files) with metrics.files (.py metrics)
     * Returns array of { path, status, additions, deletions, metrics: {before, after, delta_*} | null }
     */
    _mergeFilesWithMetrics() {
        const detailFiles = this._detail?.files || [];
        const metricsFiles = this._metrics?.files || [];

        // Build lookup by path from metrics
        const metricsMap = new Map();
        for (const mf of metricsFiles) {
            metricsMap.set(mf.path, mf);
        }

        return detailFiles.map(f => ({
            path: f.path,
            status: f.status,
            additions: f.additions || 0,
            deletions: f.deletions || 0,
            metrics: metricsMap.get(f.path) || null,
        }));
    }

    // ========================================================================
    // RENDER HELPERS
    // ========================================================================

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
