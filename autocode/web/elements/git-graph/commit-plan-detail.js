/**
 * commit-plan-detail.js
 * Panel de detalle de un plan de commit seleccionado.
 * Lazy-loads el plan completo via API. Permite cambiar status y eliminar.
 * Sigue el patrón de commit-detail.js.
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { AutoFunctionController } from '../auto-element-generator.js';
import { themeTokens } from './styles/theme.js';
import { commitPlanDetailStyles } from './styles/commit-plan-detail.styles.js';

// Task type icons
const TASK_ICONS = {
    create: '✅',
    modify: '🔄',
    delete: '❌',
    rename: '📝',
};

export class CommitPlanDetail extends LitElement {
    static properties = {
        planId: { type: String },
        _plan: { state: true },          // Full CommitPlan from API
        _loading: { state: true },
        _error: { state: true },
    };

    static styles = [themeTokens, commitPlanDetailStyles];

    constructor() {
        super();
        this.planId = null;
        this._plan = null;
        this._loading = false;
        this._error = null;
    }

    willUpdate(changed) {
        if (changed.has('planId') && this.planId) {
            this._loadPlan();
        }
    }

    render() {
        if (this._loading) {
            return html`
                <div class="loading-detail">
                    <div class="spinner-sm"></div>
                    <span>Cargando plan...</span>
                </div>
            `;
        }

        if (this._error) {
            return html`
                <div class="plan-detail">
                    <div class="error-msg">❌ ${this._error}</div>
                </div>
            `;
        }

        const plan = this._plan;
        if (!plan) return html``;

        const status = plan.status || 'draft';

        return html`
            <div class="plan-detail">
                <!-- Header -->
                <div class="detail-header">
                    <div class="header-left">
                        <span class="header-icon">📋</span>
                        <h4 class="detail-title">${plan.title}</h4>
                        <span class="status-badge ${status}">${status}</span>
                    </div>
                    <button class="close-btn" @click=${this._handleClose} title="Cerrar">✕</button>
                </div>

                <!-- Meta info -->
                <div class="meta-section">
                    <div class="meta-row">
                        <span class="meta-label">ID</span>
                        <span class="meta-value">${plan.id}</span>
                    </div>
                    <div class="meta-row">
                        <span class="meta-label">Branch</span>
                        <span class="meta-value">${plan.branch}</span>
                    </div>
                    <div class="meta-row">
                        <span class="meta-label">Parent</span>
                        <span class="meta-value">${plan.parent_commit ? plan.parent_commit.substring(0, 7) : '—'}</span>
                    </div>
                    <div class="meta-row">
                        <span class="meta-label">Creado</span>
                        <span class="meta-value">${this._formatDate(plan.created_at)}</span>
                    </div>
                </div>

                <!-- Description -->
                ${plan.description ? html`
                    <div class="description-section">${plan.description}</div>
                ` : ''}

                <!-- Tasks -->
                ${plan.tasks && plan.tasks.length > 0 ? html`
                    <div class="tasks-section">
                        <div class="section-header">📂 Tareas (${plan.tasks.length})</div>
                        ${plan.tasks.map(t => this._renderTask(t))}
                    </div>
                ` : ''}

                <!-- Context -->
                ${this._hasContext(plan.context) ? html`
                    <div class="context-section">
                        <div class="section-header">📚 Contexto</div>
                        ${plan.context.relevant_files?.length ? html`
                            <div class="context-card">
                                <div class="context-label">Archivos relevantes</div>
                                ${plan.context.relevant_files.map(f => html`
                                    <div class="context-file">${f}</div>
                                `)}
                            </div>
                        ` : ''}
                        ${plan.context.relevant_dccs?.length ? html`
                            <div class="context-card">
                                <div class="context-label">DCCs</div>
                                ${plan.context.relevant_dccs.map(d => html`
                                    <div class="context-file">${d}</div>
                                `)}
                            </div>
                        ` : ''}
                        ${plan.context.architectural_notes ? html`
                            <div class="context-card">
                                <div class="context-label">Notas de arquitectura</div>
                                <div class="context-notes">${plan.context.architectural_notes}</div>
                            </div>
                        ` : ''}
                    </div>
                ` : ''}

                <!-- Tags -->
                ${plan.tags && plan.tags.length > 0 ? html`
                    <div class="tags-section">
                        ${plan.tags.map(tag => html`
                            <span class="tag-item">${tag}</span>
                        `)}
                    </div>
                ` : ''}

                <!-- Actions -->
                <div class="actions-section">
                    <select class="status-select" .value=${status} @change=${this._updateStatus}>
                        <option value="draft" ?selected=${status === 'draft'}>Draft</option>
                        <option value="ready" ?selected=${status === 'ready'}>Ready</option>
                        <option value="abandoned" ?selected=${status === 'abandoned'}>Abandoned</option>
                    </select>
                    <button class="delete-btn" @click=${this._delete}>🗑️ Eliminar</button>
                </div>
            </div>
        `;
    }

    // ========================================================================
    // API
    // ========================================================================

    async _loadPlan() {
        if (!this.planId) return;

        this._loading = true;
        this._error = null;
        this._plan = null;

        try {
            const result = await AutoFunctionController.executeFunction(
                'get_commit_plan',
                { plan_id: this.planId }
            );
            this._plan = result;
        } catch (error) {
            this._error = error.message || 'Error cargando plan';
            console.error('❌ Error loading commit plan:', error);
        } finally {
            this._loading = false;
        }
    }

    async _updateStatus(e) {
        const newStatus = e.target.value;
        try {
            await AutoFunctionController.executeFunction(
                'update_commit_plan',
                { plan_id: this.planId, status: newStatus }
            );
            this._plan = { ...this._plan, status: newStatus };
            this.dispatchEvent(new CustomEvent('plan-updated', {
                bubbles: true,
                composed: true,
            }));
        } catch (error) {
            console.error('❌ Error updating plan status:', error);
        }
    }

    async _delete() {
        if (!confirm(`¿Eliminar plan "${this._plan?.title}"?`)) return;

        try {
            await AutoFunctionController.executeFunction(
                'delete_commit_plan',
                { plan_id: this.planId }
            );
            this.dispatchEvent(new CustomEvent('plan-deleted', {
                bubbles: true,
                composed: true,
            }));
        } catch (error) {
            console.error('❌ Error deleting plan:', error);
        }
    }

    // ========================================================================
    // RENDER HELPERS
    // ========================================================================

    _renderTask(task) {
        const icon = TASK_ICONS[task.type] || '📄';
        return html`
            <div class="task-card">
                <div class="task-card-header">
                    <span>${icon}</span>
                    <span class="task-type-badge task-type-${task.type}">${task.type}</span>
                    <span class="task-path" title="${task.path}">${task.path}</span>
                </div>
                <div class="task-body">
                    <div class="task-description">${task.description}</div>
                    ${task.details ? html`
                        <div class="task-details">${task.details}</div>
                    ` : ''}
                    ${task.acceptance_criteria?.length ? html`
                        <ul class="task-criteria">
                            ${task.acceptance_criteria.map(c => html`<li>${c}</li>`)}
                        </ul>
                    ` : ''}
                </div>
            </div>
        `;
    }

    _hasContext(ctx) {
        if (!ctx) return false;
        return (ctx.relevant_files?.length > 0) ||
               (ctx.relevant_dccs?.length > 0) ||
               (ctx.architectural_notes);
    }

    _formatDate(isoDate) {
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
        this.dispatchEvent(new CustomEvent('plan-closed', {
            bubbles: true,
            composed: true,
        }));
    }
}

if (!customElements.get('commit-plan-detail')) {
    customElements.define('commit-plan-detail', CommitPlanDetail);
}
