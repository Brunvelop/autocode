/**
 * working-changes-node.js
 * Componente para renderizar el nodo "Working Changes" (presente) en el grafo git.
 * Se sitúa entre los planes futuros (commit-plan-node) y los commits pasados (commit-node).
 *
 * Estados:
 * - loading: spinner mientras carga el status
 * - clean: working directory limpio (○ gris, casi invisible)
 * - dirty: hay cambios sin stage (◐ naranja, badges de contadores)
 * - all-staged: todos los cambios están staged (◑ verde, listo para commit)
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { themeTokens } from './styles/theme.js';
import { workingChangesNodeStyles } from './styles/working-changes-node.styles.js';

export class WorkingChangesNode extends LitElement {
    static properties = {
        status: { type: Object },    // GitStatusResult del backend
        loading: { type: Boolean },
        selected: { type: Boolean },
    };

    static styles = [themeTokens, workingChangesNodeStyles];

    constructor() {
        super();
        this.status = null;
        this.loading = false;
        this.selected = false;
    }

    render() {
        if (this.loading) {
            return html`
                <div class="wc-row dirty ${this.selected ? 'selected' : ''}" @click=${this._handleClick}>
                    <div class="wc-spinner"></div>
                    <div class="wc-info">
                        <span class="wc-label">Cargando cambios...</span>
                    </div>
                </div>
            `;
        }

        if (!this.status) {
            return html`
                <div class="wc-row clean ${this.selected ? 'selected' : ''}" @click=${this._handleClick}>
                    <div class="wc-icon">○</div>
                    <div class="wc-info">
                        <span class="wc-label">Working changes</span>
                    </div>
                </div>
            `;
        }

        const { is_clean, total_modified, total_added, total_deleted, total_untracked, total_staged, files } = this.status;

        // Determinar estado
        const totalChanges = (total_modified || 0) + (total_added || 0) + (total_deleted || 0) + (total_untracked || 0);
        const hasUnstagedChanges = totalChanges > 0;
        const hasStagedChanges = (total_staged || 0) > 0;
        const allStaged = hasStagedChanges && !hasUnstagedChanges;

        if (is_clean) {
            return html`
                <div class="wc-row clean ${this.selected ? 'selected' : ''}" @click=${this._handleClick}>
                    <div class="wc-icon">○</div>
                    <div class="wc-info">
                        <span class="wc-label">✨ Limpio</span>
                    </div>
                </div>
            `;
        }

        if (allStaged) {
            return html`
                <div class="wc-row all-staged ${this.selected ? 'selected' : ''}" @click=${this._handleClick}>
                    <div class="wc-icon">◑</div>
                    <div class="wc-info">
                        <span class="wc-label all-staged">Listo para commit</span>
                        <div class="wc-badges">
                            <span class="wc-badge staged">${total_staged}S</span>
                        </div>
                    </div>
                </div>
            `;
        }

        // Estado dirty: hay cambios sin stage (con o sin staged)
        return html`
            <div class="wc-row dirty ${this.selected ? 'selected' : ''}" @click=${this._handleClick}>
                <div class="wc-icon">◐</div>
                <div class="wc-info">
                    <span class="wc-label dirty">${totalChanges + (total_staged || 0)} cambios</span>
                    <div class="wc-badges">
                        ${total_modified > 0 ? html`<span class="wc-badge modified">${total_modified}M</span>` : ''}
                        ${total_added > 0 ? html`<span class="wc-badge added">${total_added}A</span>` : ''}
                        ${total_deleted > 0 ? html`<span class="wc-badge deleted">${total_deleted}D</span>` : ''}
                        ${total_untracked > 0 ? html`<span class="wc-badge untracked">${total_untracked}?</span>` : ''}
                        ${total_staged > 0 ? html`<span class="wc-badge staged">${total_staged}S</span>` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    _handleClick() {
        this.dispatchEvent(new CustomEvent('working-changes-selected', {
            bubbles: true,
            composed: true,
        }));
    }
}

if (!customElements.get('working-changes-node')) {
    customElements.define('working-changes-node', WorkingChangesNode);
}
