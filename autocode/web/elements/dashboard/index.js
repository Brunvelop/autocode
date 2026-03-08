/**
 * index.js
 * CodeDashboard — Panel unificado de exploración de código.
 *
 * Commit 1: Shell mínimo con:
 *   - Registro como custom element
 *   - Carga de datos via get_architecture_snapshot
 *   - Estados: loading, error, success
 *   - Summary cards (6 métricas principales)
 *   - Content area placeholder
 *
 * Usa AutoFunctionController.executeFunction() para llamar al backend.
 */

import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { AutoFunctionController } from '../auto-element-generator.js';

export class CodeDashboard extends LitElement {
    static properties = {
        // Data from API
        _snapshot: { state: true },

        // Navigation state (placeholder for Commit 2)
        _currentNodeId: { state: true },

        // View mode (placeholder for Commit 2)
        _viewMode: { state: true },

        // Loading / error
        _loading: { state: true },
        _error: { state: true },
    };

    // Styles inline (Commit 3 extracts to separate file)
    static styles = css`
        :host {
            display: block;
            height: 100%;
            overflow-y: auto;
            font-family: var(--design-font-family, system-ui, sans-serif);
        }

        /* Design tokens */
        :host {
            --design-primary: #4f46e5;
            --design-text-primary: #1f2937;
            --design-text-secondary: #6b7280;
            --design-text-tertiary: #9ca3af;
            --design-bg-white: #ffffff;
            --design-border-gray: #e5e7eb;
            --design-border-gray-light: #f3f4f6;
            --design-error-bg: #fef2f2;
            --design-error-text: #991b1b;
            --design-error-border: #fca5a5;
            --design-spacing-xs: 0.25rem;
            --design-spacing-sm: 0.5rem;
            --design-spacing-md: 0.75rem;
            --design-spacing-lg: 1rem;
            --design-spacing-xl: 1.25rem;
            --design-spacing-3xl: 2rem;
            --design-radius-md: 0.5rem;
            --design-font-size-sm: 0.75rem;
            --design-font-weight-medium: 500;
            --design-font-weight-semibold: 600;
            --design-font-weight-bold: 700;
            --design-font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            --design-transition-fast: 0.1s;
            --design-indigo-50: #eef2ff;
            --design-indigo-100: #e0e7ff;
        }

        .dashboard {
            padding: var(--design-spacing-lg) var(--design-spacing-xl);
            display: flex;
            flex-direction: column;
            gap: var(--design-spacing-lg);
            height: 100%;
            box-sizing: border-box;
        }

        /* ===== LOADING / ERROR ===== */
        .loading-container, .error-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: var(--design-spacing-3xl);
            gap: var(--design-spacing-md);
            color: var(--design-text-secondary);
        }

        .spinner {
            width: 28px;
            height: 28px;
            border: 3px solid var(--design-border-gray);
            border-top-color: var(--design-primary);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        .error-msg {
            padding: var(--design-spacing-md);
            background: var(--design-error-bg);
            border: 1px solid var(--design-error-border);
            border-radius: var(--design-radius-md);
            color: var(--design-error-text);
            font-size: 12px;
            text-align: center;
            max-width: 400px;
        }

        .retry-btn {
            padding: var(--design-spacing-xs) var(--design-spacing-md);
            background: var(--design-primary);
            color: white;
            border: none;
            border-radius: var(--design-radius-md);
            cursor: pointer;
            font-size: 12px;
            transition: opacity var(--design-transition-fast);
        }

        .retry-btn:hover {
            opacity: 0.9;
        }

        /* ===== SUMMARY CARDS ===== */
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: var(--design-spacing-sm);
        }

        @media (max-width: 700px) {
            .summary-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }

        .summary-card {
            padding: var(--design-spacing-sm) var(--design-spacing-md);
            background: var(--design-bg-white);
            border: 1px solid var(--design-border-gray);
            border-radius: var(--design-radius-md);
            display: flex;
            flex-direction: column;
            gap: 2px;
            position: relative;
        }

        .card-label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--design-text-tertiary);
            font-weight: var(--design-font-weight-medium);
        }

        .card-value {
            font-size: 1.1rem;
            font-weight: var(--design-font-weight-bold);
            color: var(--design-text-primary);
            font-family: var(--design-font-mono);
        }

        .card-status {
            font-size: 14px;
            position: absolute;
            top: 6px;
            right: 8px;
        }

        /* ===== CONTENT AREA (placeholder) ===== */
        .content-area {
            flex: 1;
            min-height: 200px;
            background: var(--design-bg-white);
            border: 1px solid var(--design-border-gray);
            border-radius: var(--design-radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
        }

        .content-placeholder {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: var(--design-spacing-sm);
            color: var(--design-text-tertiary);
            font-size: var(--design-font-size-sm);
        }

        .content-placeholder-icon {
            font-size: 2rem;
            opacity: 0.3;
        }

        /* ===== SNAPSHOT INFO ===== */
        .snapshot-info {
            font-size: 10px;
            color: var(--design-text-tertiary);
            text-align: center;
            padding-top: var(--design-spacing-sm);
            border-top: 1px solid var(--design-border-gray-light);
        }
    `;

    constructor() {
        super();
        this._snapshot = null;
        this._currentNodeId = '.';
        this._viewMode = 'treemap';
        this._loading = false;
        this._error = null;
    }

    connectedCallback() {
        super.connectedCallback();
        this.refresh();
    }

    // ========================================================================
    // DATA LOADING
    // ========================================================================

    async refresh() {
        this._loading = true;
        this._error = null;
        try {
            const result = await AutoFunctionController.executeFunction(
                'get_architecture_snapshot',
                {}
            );
            this._snapshot = result;
            this._currentNodeId = result?.root_id || '.';
        } catch (e) {
            this._error = e.message || 'Error cargando arquitectura';
        } finally {
            this._loading = false;
        }
    }

    // ========================================================================
    // RENDER
    // ========================================================================

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
                    <button class="retry-btn" @click=${() => this.refresh()}>Reintentar</button>
                </div>
            `;
        }

        if (!this._snapshot) return html``;

        const snap = this._snapshot;

        return html`
            <div class="dashboard">
                ${this._renderSummary(snap)}
                ${this._renderContentArea()}
                ${this._renderSnapshotInfo(snap)}
            </div>
        `;
    }

    // ========================================================================
    // SUMMARY CARDS
    // ========================================================================

    _renderSummary(snap) {
        return html`
            <div class="summary-grid">
                ${this._card('Archivos', snap.total_files)}
                ${this._card('SLOC', this._fmt(snap.total_sloc))}
                ${this._card('MI Media', snap.avg_mi?.toFixed(1),
                    snap.avg_mi >= 60 ? '✅' : snap.avg_mi >= 40 ? '⚠️' : '🔴')}
                ${this._card('CC Media', snap.avg_complexity?.toFixed(2),
                    snap.avg_complexity < 5 ? '✅' : snap.avg_complexity < 10 ? '⚠️' : '🔴')}
                ${this._card('Funciones', snap.total_functions)}
                ${this._card('Clases', snap.total_classes)}
            </div>
        `;
    }

    _card(label, value, status) {
        return html`
            <div class="summary-card">
                ${status ? html`<span class="card-status">${status}</span>` : ''}
                <span class="card-label">${label}</span>
                <span class="card-value">${value}</span>
            </div>
        `;
    }

    // ========================================================================
    // CONTENT AREA (placeholder for Commit 2)
    // ========================================================================

    _renderContentArea() {
        return html`
            <div class="content-area">
                <div class="content-placeholder">
                    <span class="content-placeholder-icon">📊</span>
                    <span>Content area — tabs coming in Commit 2</span>
                </div>
            </div>
        `;
    }

    // ========================================================================
    // SNAPSHOT INFO
    // ========================================================================

    _renderSnapshotInfo(snap) {
        return html`
            <div class="snapshot-info">
                📊 Commit ${snap.commit_short} · ${snap.branch} · ${this._formatDate(snap.timestamp)}
            </div>
        `;
    }

    // ========================================================================
    // HELPERS
    // ========================================================================

    _fmt(n) {
        if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
        return n;
    }

    _formatDate(iso) {
        if (!iso) return '';
        try {
            return new Date(iso).toLocaleString('es-ES', {
                dateStyle: 'short',
                timeStyle: 'short',
            });
        } catch {
            return iso;
        }
    }
}

// Register the custom element
if (!customElements.get('code-dashboard')) {
    customElements.define('code-dashboard', CodeDashboard);
}