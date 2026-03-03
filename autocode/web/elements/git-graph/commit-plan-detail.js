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
import '../chat/chat-debug-info.js';

// Task type icons
const TASK_ICONS = {
    create: '✅',
    modify: '🔄',
    delete: '❌',
    rename: '📝',
};

// Task execution status icons
const TASK_STATUS_ICONS = {
    pending: '⏳',
    running: '🔄',
    completed: '✅',
    failed: '❌',
    skipped: '⏭️',
};

// Statuses from which a plan can be executed
const EXECUTABLE_STATUSES = new Set(['draft', 'ready', 'failed']);

// Default model for execution
const DEFAULT_MODEL = 'openrouter/z-ai/glm-5';

export class CommitPlanDetail extends LitElement {
    static properties = {
        planId: { type: String },
        _plan: { state: true },          // Full CommitPlan from API
        _loading: { state: true },
        _error: { state: true },
        _isExecuting: { state: true },   // Execution in progress
        _taskStatuses: { state: true },  // Map<taskIndex, {status, messages[], error, summary, files_changed}>
        _executionSummary: { state: true }, // Final result {success, tasksCompleted, tasksFailed, commitHash}
        _selectedModel: { state: true }, // Selected model for execution
        _modelChoices: { state: true },  // Available models from registry
    };

    static styles = [themeTokens, commitPlanDetailStyles];

    constructor() {
        super();
        this.planId = null;
        this._plan = null;
        this._loading = false;
        this._error = null;
        this._isExecuting = false;
        this._taskStatuses = new Map();
        this._executionSummary = null;
        this._selectedModel = DEFAULT_MODEL;
        this._modelChoices = [];
    }

    connectedCallback() {
        super.connectedCallback();
        this._loadModelChoices();
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

                <!-- Execution Summary (if available) -->
                ${this._renderExecutionSummary()}

                <!-- Tasks -->
                ${plan.tasks && plan.tasks.length > 0 ? html`
                    <div class="tasks-section">
                        <div class="section-header">📂 Tareas (${plan.tasks.length})</div>
                        ${plan.tasks.map((t, i) => this._renderTask(t, i))}
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

                <!-- Execution controls -->
                ${this._canExecute(status) ? html`
                    <div class="execute-section">
                        <div class="execute-row">
                            ${this._modelChoices.length > 0 ? html`
                                <select class="model-select"
                                    .value=${this._selectedModel}
                                    ?disabled=${this._isExecuting}
                                    @change=${e => this._selectedModel = e.target.value}>
                                    ${this._modelChoices.map(m => html`
                                        <option value="${m}" ?selected=${m === this._selectedModel}>
                                            ${m.split('/').pop()}
                                        </option>
                                    `)}
                                </select>
                            ` : ''}
                            <button class="execute-btn"
                                ?disabled=${this._isExecuting}
                                @click=${this._executePlan}>
                                ${this._isExecuting ? html`
                                    <div class="spinner-sm"></div> Ejecutando...
                                ` : '▶️ Ejecutar'}
                            </button>
                        </div>
                    </div>
                ` : ''}

                <!-- Actions -->
                <div class="actions-section">
                    <select class="status-select ${this._isExecuting ? 'disabled' : ''}"
                        .value=${status}
                        ?disabled=${this._isExecuting}
                        @change=${this._updateStatus}>
                        <option value="draft" ?selected=${status === 'draft'}>Draft</option>
                        <option value="ready" ?selected=${status === 'ready'}>Ready</option>
                        <option value="abandoned" ?selected=${status === 'abandoned'}>Abandoned</option>
                    </select>
                    <button class="delete-btn ${this._isExecuting ? 'disabled' : ''}"
                        ?disabled=${this._isExecuting}
                        @click=${this._delete}>🗑️ Eliminar</button>
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

    /**
     * Load available model choices from the execute_commit_plan function schema.
     */
    async _loadModelChoices() {
        try {
            const response = await fetch('/functions/details');
            if (!response.ok) return;
            const data = await response.json();
            const funcInfo = data.functions?.execute_commit_plan;
            if (funcInfo?.parameters) {
                const modelParam = funcInfo.parameters.find(p => p.name === 'model');
                if (modelParam?.choices?.length) {
                    this._modelChoices = modelParam.choices;
                    // Ensure selected model is valid
                    if (!this._modelChoices.includes(this._selectedModel)) {
                        this._selectedModel = modelParam.default || this._modelChoices[0];
                    }
                }
            }
        } catch (error) {
            console.warn('⚠️ Could not load model choices:', error);
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

    _renderTask(task, index) {
        const icon = TASK_ICONS[task.type] || '📄';
        const taskStatus = this._taskStatuses.get(index);
        const execStatus = taskStatus?.status || '';
        const statusIcon = TASK_STATUS_ICONS[execStatus] || '';
        const hasCost = taskStatus?.total_tokens > 0 || taskStatus?.total_cost > 0;
        const hasDebugData = taskStatus?.trajectory?.length > 0 || taskStatus?.history?.length > 0;

        return html`
            <div class="task-card ${execStatus}">
                <div class="task-card-header">
                    <span>${icon}</span>
                    <span class="task-type-badge task-type-${task.type}">${task.type}</span>
                    <span class="task-path" title="${task.path}">${task.path}</span>
                    ${hasCost ? html`
                        <span class="task-cost-badge" title="Tokens: ${taskStatus.total_tokens}">
                            ${this._formatTokens(taskStatus.total_tokens)}
                            ${taskStatus.total_cost > 0 ? html` · $${taskStatus.total_cost.toFixed(4)}` : ''}
                        </span>
                    ` : ''}
                    ${statusIcon ? html`<span class="task-status-icon">${statusIcon}</span>` : ''}
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
                ${taskStatus?.error ? html`
                    <div class="task-error">❌ ${taskStatus.error}</div>
                ` : ''}
                ${taskStatus?.summary ? html`
                    <div class="task-summary">✅ ${taskStatus.summary}</div>
                ` : ''}
                ${taskStatus?.files_changed?.length ? html`
                    <div class="task-files">
                        <div class="task-files-label">Archivos modificados:</div>
                        ${taskStatus.files_changed.map(f => html`
                            <div class="task-file-item">${f}</div>
                        `)}
                    </div>
                ` : ''}
                ${taskStatus?.messages?.length ? html`
                    <div class="task-log" id="task-log-${index}">
                        ${taskStatus.messages.map(m => html`
                            <div class="log-line">${m}</div>
                        `)}
                    </div>
                ` : ''}
                ${hasDebugData ? html`
                    <div class="task-debug-wrapper">
                        <chat-debug-info .data=${this._buildDebugData(taskStatus)}></chat-debug-info>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Build a data object compatible with chat-debug-info from task status.
     */
    _buildDebugData(taskStatus) {
        return {
            success: taskStatus.status === 'completed',
            trajectory: taskStatus.trajectory || [],
            history: taskStatus.history || [],
            _statusLog: (taskStatus.messages || []).map(m => ({
                message: m,
                timestamp: Date.now(),
            })),
        };
    }

    /**
     * Format token count for display (e.g., 1500 → "1.5k").
     */
    _formatTokens(tokens) {
        if (!tokens) return '0';
        if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}k`;
        return String(tokens);
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
    // EXECUTION
    // ========================================================================

    /**
     * Whether the plan can be executed from its current status.
     */
    _canExecute(status) {
        return EXECUTABLE_STATUSES.has(status) || this._isExecuting;
    }

    /**
     * Execute the plan via SSE streaming endpoint.
     * Consumes events from execute_commit_plan and updates task statuses in real-time.
     */
    async _executePlan() {
        if (this._isExecuting) return;

        this._isExecuting = true;
        this._taskStatuses = new Map();
        this._executionSummary = null;

        // Optimistically update the badge to "executing"
        this._plan = { ...this._plan, status: 'executing' };

        try {
            const controller = new AutoFunctionController();
            controller.funcName = 'execute_commit_plan';
            await controller.loadFunctionInfo();

            for await (const { event, data } of controller.callStreamAPI(
                'execute_commit_plan',
                { plan_id: this.planId, model: this._selectedModel, auto_commit: true }
            )) {
                this._handleSSEEvent(event, data);
            }
        } catch (error) {
            console.error('❌ Execution error:', error);
            this._executionSummary = {
                success: false,
                tasksCompleted: 0,
                tasksFailed: 0,
                commitHash: '',
                errorMessage: error.message,
            };
        } finally {
            this._isExecuting = false;
            // Refresh plan data from server to get final status
            await this._loadPlan();
            // Notify parent to refresh graph (new commit may have been created)
            this.dispatchEvent(new CustomEvent('plan-updated', {
                bubbles: true,
                composed: true,
            }));
        }
    }

    /**
     * Handle a single SSE event from the executor stream.
     */
    _handleSSEEvent(event, data) {
        switch (event) {
            case 'plan_start':
                console.log(`🚀 Executing plan: ${data.title} (${data.total_tasks} tasks, model: ${data.model})`);
                break;

            case 'task_start':
                this._taskStatuses.set(data.task_index, {
                    status: 'running',
                    messages: [],
                    error: '',
                    summary: '',
                    files_changed: [],
                });
                // Force Lit reactivity
                this._taskStatuses = new Map(this._taskStatuses);
                break;

            case 'status': {
                const ts = this._taskStatuses.get(data.task_index);
                if (ts) {
                    ts.messages.push(data.message);
                    this._taskStatuses = new Map(this._taskStatuses);
                    // Auto-scroll the task log to show latest message
                    this.updateComplete.then(() => {
                        const logEl = this.shadowRoot?.getElementById(`task-log-${data.task_index}`);
                        if (logEl) logEl.scrollTop = logEl.scrollHeight;
                    });
                }
                break;
            }

            case 'task_debug': {
                const ts = this._taskStatuses.get(data.task_index);
                if (ts) {
                    ts.trajectory = data.trajectory || [];
                    ts.history = data.history || [];
                    ts.prompt_tokens = data.prompt_tokens || 0;
                    ts.completion_tokens = data.completion_tokens || 0;
                    ts.total_tokens = data.total_tokens || 0;
                    ts.total_cost = data.total_cost || 0;
                }
                this._taskStatuses = new Map(this._taskStatuses);
                break;
            }

            case 'task_complete': {
                const ts = this._taskStatuses.get(data.task_index);
                if (ts) {
                    ts.status = 'completed';
                    ts.summary = data.summary || '';
                    ts.files_changed = data.files_changed || [];
                    ts.total_tokens = data.total_tokens || ts.total_tokens || 0;
                    ts.total_cost = data.total_cost || ts.total_cost || 0;
                }
                this._taskStatuses = new Map(this._taskStatuses);
                break;
            }

            case 'task_error': {
                const ts = this._taskStatuses.get(data.task_index);
                if (ts) {
                    ts.status = 'failed';
                    ts.error = data.error || 'Unknown error';
                }
                this._taskStatuses = new Map(this._taskStatuses);
                break;
            }

            case 'plan_complete':
                this._executionSummary = {
                    success: data.success,
                    tasksCompleted: data.tasks_completed,
                    tasksFailed: data.tasks_failed,
                    commitHash: data.commit_hash || '',
                    totalTokens: data.total_tokens || 0,
                    totalCost: data.total_cost || 0,
                };
                break;

            case 'error':
                console.error('❌ Executor error:', data.message);
                this._executionSummary = {
                    success: false,
                    tasksCompleted: 0,
                    tasksFailed: 0,
                    commitHash: '',
                    errorMessage: data.message,
                };
                break;

            default:
                console.log(`ℹ️ Unknown SSE event: ${event}`, data);
        }
    }

    /**
     * Render the execution summary banner (shown after execution completes).
     */
    _renderExecutionSummary() {
        if (!this._executionSummary) return '';

        const s = this._executionSummary;
        const cssClass = s.success ? 'success' : 'failed';

        if (s.errorMessage) {
            return html`
                <div class="execution-summary failed">
                    <div class="summary-header">❌ Error de ejecución</div>
                    <div class="summary-details">${s.errorMessage}</div>
                </div>
            `;
        }

        return html`
            <div class="execution-summary ${cssClass}">
                <div class="summary-header">
                    ${s.success ? '✅' : '❌'}
                    ${s.success ? 'Ejecución completada' : 'Ejecución con errores'}
                </div>
                <div class="summary-details">
                    ${s.tasksCompleted} tarea${s.tasksCompleted !== 1 ? 's' : ''} completada${s.tasksCompleted !== 1 ? 's' : ''}
                    ${s.tasksFailed > 0 ? html` · ${s.tasksFailed} fallida${s.tasksFailed !== 1 ? 's' : ''}` : ''}
                    ${s.totalTokens ? html` · <span class="tokens-badge">${this._formatTokens(s.totalTokens)} tokens</span>` : ''}
                    ${s.totalCost ? html` · <span class="cost-badge">$${s.totalCost.toFixed(4)}</span>` : ''}
                    ${s.commitHash ? html` · Commit: <span class="commit-hash">${s.commitHash.substring(0, 7)}</span>` : ''}
                </div>
            </div>
        `;
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
