/**
 * git-status.js
 * Componente para mostrar el estado actual del repositorio git.
 * Muestra archivos modificados, añadidos, eliminados, etc. con badges.
 * Para archivos .py/.js, muestra métricas de código via files-metrics-table.
 */

import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { AutoFunctionController } from '../auto-element-generator.js';
import { themeTokens } from './styles/theme.js';
import './files-metrics-table.js';

// Mapeo de status a iconos y colores
const STATUS_CONFIG = {
    added: { icon: '✅', color: '#22c55e', label: 'Añadido' },
    modified: { icon: '🔄', color: '#f59e0b', label: 'Modificado' },
    deleted: { icon: '❌', color: '#ef4444', label: 'Eliminado' },
    renamed: { icon: '📝', color: '#8b5cf6', label: 'Renombrado' },
    untracked: { icon: '❓', color: '#6b7280', label: 'Sin trackear' },
    staged: { icon: '📦', color: '#3b82f6', label: 'Staged' }
};

export class GitStatus extends LitElement {
    static properties = {
        status: { type: Object },
        loading: { type: Boolean },
        error: { type: String },
        _metrics: { state: true },
        _metricsLoading: { state: true },
    };

    static styles = [themeTokens, css`
        :host {
            display: block;
        }

        .status-container {
            display: flex;
            flex-direction: column;
            gap: var(--design-spacing-sm, 0.5rem);
        }

        /* Branch header */
        .branch-header {
            display: flex;
            align-items: center;
            gap: var(--design-spacing-sm, 0.5rem);
            padding: var(--design-spacing-sm, 0.5rem);
            background: var(--design-bg-secondary, #f9fafb);
            border-radius: var(--design-radius-md, 0.5rem);
        }

        .branch-icon {
            font-size: 1.25rem;
        }

        .branch-name {
            font-family: var(--design-font-mono, monospace);
            font-weight: var(--design-font-weight-semibold, 600);
            color: var(--design-text-primary, #1f2937);
        }

        .clean-badge {
            margin-left: auto;
            padding: 2px 8px;
            background: #22c55e20;
            color: #22c55e;
            border-radius: var(--design-radius-full, 9999px);
            font-size: var(--design-font-size-xs, 0.75rem);
        }

        /* Summary badges */
        .summary-row {
            display: flex;
            flex-wrap: wrap;
            gap: var(--design-spacing-xs, 0.25rem);
            padding: var(--design-spacing-xs, 0.25rem) 0;
        }

        .summary-badge {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 2px 8px;
            border-radius: var(--design-radius-full, 9999px);
            font-size: var(--design-font-size-xs, 0.75rem);
            font-weight: var(--design-font-weight-medium, 500);
        }

        /* Empty state */
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: var(--design-spacing-sm, 0.5rem);
            padding: var(--design-spacing-xl, 1.5rem);
            color: var(--design-text-secondary, #6b7280);
        }

        .empty-icon {
            font-size: 2rem;
        }

        /* Loading */
        .loading-state {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: var(--design-spacing-sm, 0.5rem);
            padding: var(--design-spacing-lg, 1rem);
            color: var(--design-text-secondary, #6b7280);
        }

        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid var(--design-border-color, #e5e7eb);
            border-top-color: var(--design-primary, #4f46e5);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Error state */
        .error-state {
            padding: var(--design-spacing-md, 0.75rem);
            background: var(--design-error-bg, #fee2e2);
            border: 1px solid var(--design-error-border, #fca5a5);
            border-radius: var(--design-radius-md, 0.5rem);
            color: var(--design-error-text, #991b1b);
            font-size: var(--design-font-size-sm, 0.875rem);
        }
    `];

    constructor() {
        super();
        this.status = null;
        this.loading = false;
        this.error = null;
        this._metrics = null;
        this._metricsLoading = false;
    }

    willUpdate(changed) {
        if (changed.has('status') && this.status && !this.status.is_clean) {
            this._metrics = null;
            this._loadWorkingMetrics();
        }
    }

    render() {
        if (this.loading) {
            return html`
                <div class="loading-state">
                    <div class="spinner"></div>
                    <span>Cargando estado git...</span>
                </div>
            `;
        }

        if (this.error) {
            return html`
                <div class="error-state">
                    ❌ ${this.error}
                </div>
            `;
        }

        if (!this.status) {
            return html`
                <div class="empty-state">
                    <span class="empty-icon">📭</span>
                    <span>Sin datos de git status</span>
                </div>
            `;
        }

        return html`
            <div class="status-container">
                ${this._renderBranchHeader()}
                ${this._renderSummary()}
                ${this._renderFilesList()}
            </div>
        `;
    }

    _renderBranchHeader() {
        const { branch, is_clean } = this.status;

        return html`
            <div class="branch-header">
                <span class="branch-icon">🌿</span>
                <span class="branch-name">${branch}</span>
                ${is_clean ? html`
                    <span class="clean-badge">✨ Limpio</span>
                ` : ''}
            </div>
        `;
    }

    _renderSummary() {
        const { total_added, total_modified, total_deleted, total_untracked, total_staged, is_clean } = this.status;

        if (is_clean) {
            return '';
        }

        const badges = [];

        if (total_staged > 0) {
            badges.push({ count: total_staged, status: 'staged' });
        }
        if (total_added > 0) {
            badges.push({ count: total_added, status: 'added' });
        }
        if (total_modified > 0) {
            badges.push({ count: total_modified, status: 'modified' });
        }
        if (total_deleted > 0) {
            badges.push({ count: total_deleted, status: 'deleted' });
        }
        if (total_untracked > 0) {
            badges.push({ count: total_untracked, status: 'untracked' });
        }

        return html`
            <div class="summary-row">
                ${badges.map(b => {
                    const config = STATUS_CONFIG[b.status];
                    return html`
                        <span 
                            class="summary-badge"
                            style="background: ${config.color}20; color: ${config.color};"
                        >
                            ${config.icon} ${b.count} ${config.label}
                        </span>
                    `;
                })}
            </div>
        `;
    }

    _renderFilesList() {
        const { files, is_clean } = this.status;

        if (is_clean || !files || files.length === 0) {
            return html`
                <div class="empty-state">
                    <span class="empty-icon">✨</span>
                    <span>Working directory limpio</span>
                </div>
            `;
        }

        return html`
            <files-metrics-table
                .files=${this._mergeFilesWithMetrics()}
                .metricsLoading=${this._metricsLoading}
            ></files-metrics-table>
        `;
    }

    // ========================================================================
    // API
    // ========================================================================

    async _loadWorkingMetrics() {
        this._metricsLoading = true;
        try {
            const result = await AutoFunctionController.executeFunction(
                'get_working_changes_metrics',
                {}
            );
            this._metrics = result;
        } catch (e) {
            console.error('❌ Error loading working metrics:', e);
            this._metrics = { files: [], summary: {} };
        } finally {
            this._metricsLoading = false;
        }
    }

    // ========================================================================
    // DATA HELPERS
    // ========================================================================

    /**
     * Merge status.files (all changed files) with metrics.files (.py/.js metrics)
     * Returns array of { path, status, additions, deletions, staged, metrics: {...} | null }
     */
    _mergeFilesWithMetrics() {
        const statusFiles = this.status?.files || [];
        const metricsFiles = this._metrics?.files || [];

        // Build lookup by path from metrics
        const metricsMap = new Map();
        for (const mf of metricsFiles) {
            metricsMap.set(mf.path, mf);
        }

        return statusFiles.map(f => ({
            path: f.path,
            status: f.status,
            additions: f.additions || 0,
            deletions: f.deletions || 0,
            staged: f.staged || false,
            metrics: metricsMap.get(f.path) || null,
        }));
    }

    // ========================================================================
    // EVENTS
    // ========================================================================

    _handleFileClick(file) {
        this.dispatchEvent(new CustomEvent('file-selected', {
            detail: { file },
            bubbles: true,
            composed: true
        }));
    }
}

if (!customElements.get('git-status')) {
    customElements.define('git-status', GitStatus);
}
