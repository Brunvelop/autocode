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
    };

    static styles = [themeTokens, commitDetailStyles];

    constructor() {
        super();
        this.commitHash = null;
        this.commitSummary = null;
        this._detail = null;
        this._loading = false;
        this._error = null;
    }

    willUpdate(changed) {
        if (changed.has('commitHash') && this.commitHash) {
            this._loadDetail();
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
