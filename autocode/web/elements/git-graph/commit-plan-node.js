/**
 * commit-plan-node.js
 * Componente para renderizar una fila de "plan futuro" (ghost node) en el grafo git.
 * Similar a commit-node.js pero con estilo diferenciado: borde punteado, icono 📋,
 * badge de status (DRAFT/READY), fondo semi-transparente.
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { themeTokens } from './styles/theme.js';
import { commitPlanNodeStyles } from './styles/commit-plan-node.styles.js';

export class CommitPlanNode extends LitElement {
    static properties = {
        plan: { type: Object },       // CommitPlanSummary
        selected: { type: Boolean },
    };

    static styles = [themeTokens, commitPlanNodeStyles];

    constructor() {
        super();
        this.plan = null;
        this.selected = false;
    }

    render() {
        if (!this.plan) return html``;

        const status = this.plan.status || 'draft';

        return html`
            <div 
                class="plan-row ${this.selected ? 'selected' : ''}"
                @click=${this._handleClick}
            >
                <div class="plan-icon">📋</div>
                <div class="plan-info">
                    <span class="plan-badge ${status}">${status}</span>
                    <span class="plan-title" title="${this.plan.title}">${this.plan.title}</span>
                    <span class="plan-tasks">${this.plan.tasks_count} tarea${this.plan.tasks_count !== 1 ? 's' : ''}</span>
                </div>
            </div>
        `;
    }

    _handleClick() {
        this.dispatchEvent(new CustomEvent('plan-selected', {
            detail: { plan: this.plan },
            bubbles: true,
            composed: true,
        }));
    }
}

if (!customElements.get('commit-plan-node')) {
    customElements.define('commit-plan-node', CommitPlanNode);
}
