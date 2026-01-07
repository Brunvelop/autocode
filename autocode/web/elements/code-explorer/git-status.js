/**
 * git-status.js
 * Componente para mostrar el estado actual del repositorio git.
 * Muestra archivos modificados, añadidos, eliminados, etc. con badges.
 */

import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { themeTokens } from './styles/theme.js';

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
        error: { type: String }
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

        /* Files list */
        .files-list {
            display: flex;
            flex-direction: column;
            gap: 2px;
            max-height: 400px;
            overflow-y: auto;
        }

        .file-item {
            display: flex;
            align-items: center;
            gap: var(--design-spacing-sm, 0.5rem);
            padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
            border-radius: var(--design-radius-sm, 0.25rem);
            cursor: pointer;
            transition: background var(--design-transition-fast, 0.15s);
        }

        .file-item:hover {
            background: var(--design-bg-secondary, #f9fafb);
        }

        .file-status-icon {
            font-size: 12px;
            flex-shrink: 0;
        }

        .file-path {
            flex: 1;
            font-size: var(--design-font-size-sm, 0.875rem);
            font-family: var(--design-font-mono, monospace);
            color: var(--design-text-primary, #1f2937);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .file-stats {
            display: flex;
            gap: 4px;
            font-size: var(--design-font-size-xs, 0.75rem);
            font-family: var(--design-font-mono, monospace);
        }

        .stat-add {
            color: #22c55e;
        }

        .stat-del {
            color: #ef4444;
        }

        .staged-indicator {
            font-size: 10px;
            padding: 1px 4px;
            background: #3b82f620;
            color: #3b82f6;
            border-radius: var(--design-radius-sm, 0.25rem);
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

        /* Group headers */
        .group-header {
            display: flex;
            align-items: center;
            gap: var(--design-spacing-xs, 0.25rem);
            padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
            font-size: var(--design-font-size-xs, 0.75rem);
            font-weight: var(--design-font-weight-semibold, 600);
            color: var(--design-text-secondary, #6b7280);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid var(--design-border-color, #e5e7eb);
            margin-top: var(--design-spacing-sm, 0.5rem);
        }

        .group-header:first-child {
            margin-top: 0;
        }
    `];

    constructor() {
        super();
        this.status = null;
        this.loading = false;
        this.error = null;
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

        // Agrupar archivos por estado
        const staged = files.filter(f => f.staged);
        const unstaged = files.filter(f => !f.staged && f.status !== 'untracked');
        const untracked = files.filter(f => f.status === 'untracked');

        return html`
            <div class="files-list">
                ${staged.length > 0 ? html`
                    <div class="group-header">
                        📦 Staged (${staged.length})
                    </div>
                    ${staged.map(f => this._renderFileItem(f))}
                ` : ''}

                ${unstaged.length > 0 ? html`
                    <div class="group-header">
                        📝 Cambios sin stage (${unstaged.length})
                    </div>
                    ${unstaged.map(f => this._renderFileItem(f))}
                ` : ''}

                ${untracked.length > 0 ? html`
                    <div class="group-header">
                        ❓ Sin trackear (${untracked.length})
                    </div>
                    ${untracked.map(f => this._renderFileItem(f))}
                ` : ''}
            </div>
        `;
    }

    _renderFileItem(file) {
        const config = STATUS_CONFIG[file.status] || STATUS_CONFIG.modified;
        const hasStats = file.additions > 0 || file.deletions > 0;

        return html`
            <div 
                class="file-item"
                @click=${() => this._handleFileClick(file)}
                title="${file.path}"
            >
                <span class="file-status-icon">${config.icon}</span>
                <span class="file-path">${file.path}</span>
                
                ${hasStats ? html`
                    <span class="file-stats">
                        ${file.additions > 0 ? html`
                            <span class="stat-add">+${file.additions}</span>
                        ` : ''}
                        ${file.deletions > 0 ? html`
                            <span class="stat-del">-${file.deletions}</span>
                        ` : ''}
                    </span>
                ` : ''}

                ${file.staged ? html`
                    <span class="staged-indicator">staged</span>
                ` : ''}
            </div>
        `;
    }

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
