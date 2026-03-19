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

// Step type icons for the execution timeline
const STEP_TYPE_ICONS = {
    thinking: '🤔',
    tool_use: '🛠️',
    text: '💬',
    error: '❌',
};

// Statuses from which a plan can be executed
const EXECUTABLE_STATUSES = new Set(['draft', 'ready', 'failed', 'executing']);

// Statuses that show review section
const REVIEW_STATUSES = new Set(['pending_review']);

// Statuses where manual status change / execute are NOT available
const NON_EDITABLE_STATUSES = new Set([
    'reverted', 'completed',
]);

// Default model for execution
const DEFAULT_MODEL = 'openrouter/z-ai/glm-5';

export class CommitPlanDetail extends LitElement {
    static properties = {
        planId: { type: String },
        _plan: { state: true },          // Full CommitPlan from API
        _loading: { state: true },
        _error: { state: true },
        _isExecuting: { state: true },   // Execution in progress
        _steps: { state: true },         // Array of ExecutionStep objects from SSE
        _executionSummary: { state: true }, // Final result {success, filesChanged, commitHash, ...}
        _selectedModel: { state: true }, // Selected model for execution
        _modelChoices: { state: true },  // Available models from registry
        _selectedBackend: { state: true }, // Selected backend: "opencode", "cline", "dspy"
        _selectedReviewMode: { state: true }, // Review mode: "human" or "auto"
        _elapsedDisplay: { state: true }, // Elapsed time string "1m 23s"
        _lastHeartbeat: { state: true },  // Timestamp of last heartbeat event
        _isApproving: { state: true },    // Approve in progress
        _isReverting: { state: true },    // Revert in progress
        _isAnalyzingReview: { state: true }, // Review analysis in progress (SSE)
    };

    static styles = [themeTokens, commitPlanDetailStyles];

    constructor() {
        super();
        this.planId = null;
        this._plan = null;
        this._loading = false;
        this._error = null;
        this._isExecuting = false;
        this._steps = [];
        this._executionSummary = null;
        this._selectedModel = DEFAULT_MODEL;
        this._modelChoices = [];
        this._selectedBackend = 'opencode';
        this._selectedReviewMode = 'human';
        // Timer & heartbeat
        this._elapsedDisplay = '';
        this._lastHeartbeat = null;
        this._executionStartTime = null;
        this._elapsedInterval = null;
        // Abort controller for cancelling execution
        this._abortController = null;
        // Review state
        this._isApproving = false;
        this._isReverting = false;
        this._isAnalyzingReview = false;
    }

    connectedCallback() {
        super.connectedCallback();
        this._loadModelChoices();
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this._stopElapsedTimer();
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

                <!-- Description (freeform markdown) -->
                ${this._renderDescription()}

                <!-- Recovery banner for zombie plans -->
                ${this._renderRecoveryBanner(status)}

                <!-- Execution Summary (if available) -->
                ${this._renderExecutionSummary()}

                <!-- Review analyzing banner (during SSE) -->
                ${this._isAnalyzingReview ? html`
                    <div class="review-analyzing">
                        <div class="spinner-sm"></div>
                        <span>Analizando métricas de calidad...</span>
                    </div>
                ` : ''}

                <!-- Reverted banner -->
                ${status === 'reverted' ? html`
                    <div class="reverted-banner">
                        <span class="reverted-icon">↩️</span>
                        <span class="reverted-text">Cambios revertidos — los archivos han sido restaurados al estado anterior</span>
                    </div>
                ` : ''}

                <!-- Review section (pending_review) -->
                ${this._renderReviewSection(status)}

                <!-- Steps timeline (execution trace) -->
                ${this._renderStepsTimeline()}

                <!-- Execution controls -->
                ${this._canExecute(status) ? html`
                    <div class="execute-section">
                        <div class="execute-row">
                            ${this._renderModelSelector()}
                            <select class="backend-select"
                                .value=${this._selectedBackend}
                                ?disabled=${this._isExecuting}
                                @change=${e => this._selectedBackend = e.target.value}
                                title="Backend de ejecución">
                                <option value="opencode" ?selected=${this._selectedBackend === 'opencode'}>⚡ OpenCode</option>
                                <option value="cline" ?selected=${this._selectedBackend === 'cline'}>🤖 Cline</option>
                                <option value="dspy" ?selected=${this._selectedBackend === 'dspy'}>🧪 DSPy (legacy)</option>
                            </select>
                            <select class="review-mode-select"
                                .value=${this._selectedReviewMode}
                                ?disabled=${this._isExecuting}
                                @change=${e => this._selectedReviewMode = e.target.value}
                                title="Modo de review post-ejecución">
                                <option value="human" ?selected=${this._selectedReviewMode === 'human'}>👤 Review manual</option>
                                <option value="auto" ?selected=${this._selectedReviewMode === 'auto'}>🤖 Auto-review</option>
                            </select>
                            <button class="execute-btn"
                                ?disabled=${this._isExecuting}
                                @click=${this._executePlan}>
                                ${this._isExecuting ? html`
                                    <div class="spinner-sm"></div> Ejecutando...
                                ` : '▶️ Ejecutar'}
                            </button>
                            ${this._isExecuting ? html`
                                <button class="cancel-btn" @click=${this._cancelExecution}
                                    title="Cancelar ejecución">⏹ Cancelar</button>
                            ` : ''}
                        </div>
                        ${this._isExecuting ? html`
                            <div class="execute-status-row">
                                ${this._elapsedDisplay ? html`
                                    <span class="elapsed-timer">${this._elapsedDisplay}</span>
                                ` : ''}
                                <span class="activity-indicator">
                                    <span class="activity-dot ${this._isHeartbeatActive() ? 'active' : 'inactive'}"></span>
                                    ${this._isHeartbeatActive() ? 'Activo' : this._lastHeartbeat ? 'Sin respuesta' : 'Conectando...'}
                                </span>
                            </div>
                        ` : ''}
                    </div>
                ` : ''}

                <!-- Actions: status select (editable statuses only) + delete (always) -->
                <div class="actions-section">
                    ${!NON_EDITABLE_STATUSES.has(status) ? html`
                        <select class="status-select ${this._isExecuting ? 'disabled' : ''}"
                            .value=${status}
                            ?disabled=${this._isExecuting}
                            @change=${this._updateStatus}>
                            ${status === 'pending_review' ? html`
                                <option value="pending_review" selected>Pending Review</option>
                            ` : ''}
                            <option value="draft" ?selected=${status === 'draft'}>Draft</option>
                            <option value="ready" ?selected=${status === 'ready'}>Ready</option>
                            <option value="abandoned" ?selected=${status === 'abandoned'}>Abandoned</option>
                        </select>
                    ` : ''}
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
            this._restoreExecutionState(result);
        } catch (error) {
            this._error = error.message || 'Error cargando plan';
            console.error('❌ Error loading commit plan:', error);
        } finally {
            this._loading = false;
        }
    }

    /**
     * Restore execution state from plan.execution data (persisted on server).
     * Called after loading plan to reconstruct UI state after page refresh.
     */
    _restoreExecutionState(plan) {
        // Don't overwrite live execution state
        if (this._isExecuting) return;

        // Restore steps from execution.steps array
        if (plan?.execution?.steps?.length) {
            this._steps = [...plan.execution.steps];
        }

        // Restore execution summary if plan finished or in review
        const summaryStatuses = new Set([
            'completed', 'failed', 'pending_review', 'reverted',
        ]);
        if (summaryStatuses.has(plan?.status) && plan?.execution) {
            const exec = plan.execution;
            this._executionSummary = {
                success: plan.status !== 'failed',
                filesChanged: exec.files_changed || [],
                commitHash: exec.commit_hash || '',
                totalTokens: exec.total_tokens || 0,
                totalCost: exec.total_cost || 0,
                backend: exec.backend || '',
            };
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
     * Load available model choices from get_chat_config (full ModelType catalog).
     */
    async _loadModelChoices() {
        try {
            const result = await AutoFunctionController.executeFunction(
                'get_chat_config',
                {}
            );
            if (result?.models?.length) {
                this._modelChoices = result.models; // [{id, name, context_length, ...}, ...]
                // Ensure selected model is valid
                if (!this._modelChoices.find(m => m.id === this._selectedModel)) {
                    this._selectedModel = this._modelChoices[0].id;
                }
            }
        } catch (error) {
            console.warn('⚠️ Could not load models:', error);
            // Fallback: allow free text input (modelChoices stays [])
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

    /**
     * Render the plan description as freeform text/markdown.
     */
    _renderDescription() {
        const plan = this._plan;
        if (!plan?.description) return '';

        return html`
            <div class="description-section">
                <div class="section-header">📝 Descripción</div>
                <div class="description-content">${plan.description}</div>
            </div>
        `;
    }

    /**
     * Render the model selector for execution.
     * If models are loaded from get_chat_config, shows a rich <select> with
     * name + context length. Falls back to a free-text <input> with datalist.
     */
    _renderModelSelector() {
        if (this._modelChoices.length > 0) {
            return html`
                <select class="model-select"
                    .value=${this._selectedModel}
                    ?disabled=${this._isExecuting}
                    @change=${e => this._selectedModel = e.target.value}>
                    ${this._modelChoices.map(m => html`
                        <option value="${m.id}" ?selected=${m.id === this._selectedModel}>
                            ${m.name}${m.context_length
                                ? ` (${Math.round(m.context_length / 1000)}k ctx)`
                                : ''}
                        </option>
                    `)}
                </select>
            `;
        }

        // Fallback: free-text input with datalist suggestions
        return html`
            <input type="text"
                class="model-input"
                list="model-suggestions"
                .value=${this._selectedModel}
                ?disabled=${this._isExecuting}
                @change=${e => this._selectedModel = e.target.value}
                placeholder="modelo (ej: openrouter/anthropic/claude-sonnet-4-5)">
            <datalist id="model-suggestions">
                <option value="openrouter/anthropic/claude-sonnet-4-5">
                <option value="openrouter/openai/gpt-4o">
                <option value="openrouter/x-ai/grok-3">
            </datalist>
        `;
    }

    /**
     * Render the steps timeline — a chronological list of execution steps.
     * Each step shows an icon by type, content, and optionally tool/path.
     */
    _renderStepsTimeline() {
        if (!this._steps || this._steps.length === 0) return '';

        return html`
            <div class="steps-section">
                <div class="section-header">🔄 Ejecución (${this._steps.length} pasos)</div>
                <div class="steps-timeline">
                    ${this._steps.map(step => this._renderStepItem(step))}
                </div>
            </div>
        `;
    }

    /**
     * Render a single step in the timeline.
     */
    _renderStepItem(step) {
        const icon = STEP_TYPE_ICONS[step.type] || '▪️';
        const hasPath = step.path && step.path.length > 0;
        const hasTool = step.tool && step.tool.length > 0;

        // Build the label: tool name for tool_use, type for others
        const label = hasTool ? step.tool : step.type;

        // Truncate long content for display
        const displayContent = step.content && step.content.length > 200
            ? step.content.substring(0, 200) + '…'
            : step.content || '';

        return html`
            <div class="step-item ${step.type}">
                <span class="step-icon">${icon}</span>
                <div class="step-body">
                    <div class="step-header-row">
                        <span class="step-label">${label}</span>
                        ${hasPath ? html`<span class="step-path">${step.path}</span>` : ''}
                    </div>
                    ${displayContent ? html`
                        <div class="step-content">${displayContent}</div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Format token count for display (e.g., 1500 → "1.5k").
     */
    _formatTokens(tokens) {
        if (!tokens) return '0';
        if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}k`;
        return String(tokens);
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
     * Consumes events from execute_commit_plan and updates steps in real-time.
     * Includes AbortController for cancellation and elapsed timer.
     */
    async _executePlan() {
        if (this._isExecuting) return;

        this._isExecuting = true;
        this._steps = [];
        this._executionSummary = null;
        this._abortController = new AbortController();

        // Start elapsed timer
        this._startElapsedTimer();

        // Optimistically update the badge to "executing"
        this._plan = { ...this._plan, status: 'executing' };

        try {
            const controller = new AutoFunctionController();
            controller.funcName = 'execute_commit_plan';
            await controller.loadFunctionInfo();

            for await (const { event, data } of controller.callStreamAPI(
                'execute_commit_plan',
                { plan_id: this.planId, backend: this._selectedBackend, model: this._selectedModel, review_mode: this._selectedReviewMode },
                null,
                { signal: this._abortController.signal }
            )) {
                this._handleSSEEvent(event, data);
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('⏹ Execution cancelled by user');
                this._executionSummary = {
                    success: false,
                    filesChanged: [],
                    commitHash: '',
                    errorMessage: 'Ejecución cancelada por el usuario',
                };
            } else {
                console.error('❌ Execution error:', error);
                this._executionSummary = {
                    success: false,
                    filesChanged: [],
                    commitHash: '',
                    errorMessage: error.message,
                };
            }
        } finally {
            this._isExecuting = false;
            this._abortController = null;
            this._stopElapsedTimer();
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
     * Cancel the current execution via AbortController.
     */
    _cancelExecution() {
        if (this._abortController) {
            this._abortController.abort();
        }
    }

    /**
     * Handle a single SSE event from the executor stream.
     */
    _handleSSEEvent(event, data) {
        switch (event) {
            case 'plan_start':
                console.log(`🚀 Executing plan: ${data.title} (backend: ${data.backend || '?'}, model: ${data.model})`);
                break;

            case 'step': {
                // Push new step to the timeline
                const step = {
                    type: data.type || '',
                    content: data.content || '',
                    tool: data.tool || '',
                    path: data.path || '',
                    timestamp: data.timestamp || '',
                };
                this._steps = [...this._steps, step];

                // Auto-scroll the steps timeline
                this.updateComplete.then(() => {
                    const timeline = this.shadowRoot?.querySelector('.steps-timeline');
                    if (timeline) timeline.scrollTop = timeline.scrollHeight;
                });
                break;
            }

            case 'plan_complete':
                this._executionSummary = {
                    success: data.success,
                    filesChanged: data.files_changed || [],
                    commitHash: data.commit_hash || '',
                    totalTokens: data.total_tokens || 0,
                    totalCost: data.total_cost || 0,
                    status: data.status || '',
                };
                break;

            case 'heartbeat':
                this._lastHeartbeat = Date.now();
                break;

            case 'review_start':
                console.log(`🔍 Review started: mode=${data.review_mode || data.mode}, files=${data.files_changed?.length}`);
                this._isAnalyzingReview = true;
                break;

            case 'review_complete':
                console.log(`📋 Review complete: verdict=${data.verdict}`);
                this._isAnalyzingReview = false;
                break;

            case 'error':
                console.error('❌ Executor error:', data.message);
                this._isAnalyzingReview = false;
                this._executionSummary = {
                    success: false,
                    filesChanged: [],
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

        const filesCount = s.filesChanged?.length || 0;

        return html`
            <div class="execution-summary ${cssClass}">
                <div class="summary-header">
                    ${s.success ? '✅' : '❌'}
                    ${s.success ? 'Ejecución completada' : 'Ejecución con errores'}
                </div>
                <div class="summary-details">
                    ${filesCount} archivo${filesCount !== 1 ? 's' : ''} modificado${filesCount !== 1 ? 's' : ''}
                    ${s.totalTokens ? html` · <span class="tokens-badge">${this._formatTokens(s.totalTokens)} tokens</span>` : ''}
                    ${s.totalCost ? html` · <span class="cost-badge">$${s.totalCost.toFixed(4)}</span>` : ''}
                    ${s.commitHash ? html` · Commit: <span class="commit-hash">${s.commitHash.substring(0, 7)}</span>` : ''}
                </div>
                ${filesCount > 0 ? html`
                    <div class="summary-files">
                        ${s.filesChanged.map(f => html`<div class="summary-file-item">${f}</div>`)}
                    </div>
                ` : ''}
            </div>
        `;
    }

    // ========================================================================
    // RECOVERY
    // ========================================================================

    /**
     * Render recovery banner for zombie plans (stuck in "executing" without active execution).
     */
    _renderRecoveryBanner(status) {
        // Only show when plan is "executing" but no active execution in this session
        if (status !== 'executing' || this._isExecuting) return '';

        return html`
            <div class="recovery-banner">
                <div class="recovery-text">⚠️ Ejecución anterior interrumpida</div>
                <div class="recovery-actions">
                    <button class="recovery-btn reset" @click=${this._resetToDraft}>↩️ Reset a draft</button>
                    <button class="recovery-btn reexecute" @click=${this._executePlan}>▶️ Re-ejecutar</button>
                </div>
            </div>
        `;
    }

    /**
     * Reset a zombie plan back to draft status (clears execution state).
     */
    async _resetToDraft() {
        try {
            await AutoFunctionController.executeFunction(
                'update_commit_plan',
                { plan_id: this.planId, status: 'draft' }
            );
            this._steps = [];
            this._executionSummary = null;
            await this._loadPlan();
            this.dispatchEvent(new CustomEvent('plan-updated', {
                bubbles: true,
                composed: true,
            }));
        } catch (error) {
            console.error('❌ Error resetting plan to draft:', error);
        }
    }

    // ========================================================================
    // TIMER & HEARTBEAT
    // ========================================================================

    /**
     * Start the elapsed time display timer.
     */
    _startElapsedTimer() {
        this._executionStartTime = Date.now();
        this._elapsedDisplay = '0s';
        this._lastHeartbeat = null;
        this._elapsedInterval = setInterval(() => {
            this._elapsedDisplay = this._formatElapsed(Date.now() - this._executionStartTime);
        }, 1000);
    }

    /**
     * Stop and clean up the elapsed timer.
     */
    _stopElapsedTimer() {
        if (this._elapsedInterval) {
            clearInterval(this._elapsedInterval);
            this._elapsedInterval = null;
        }
        this._executionStartTime = null;
        this._lastHeartbeat = null;
    }

    /**
     * Format milliseconds as human-readable elapsed time (e.g., "1m 23s").
     */
    _formatElapsed(ms) {
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        if (minutes > 0) {
            return `${minutes}m ${seconds}s`;
        }
        return `${seconds}s`;
    }

    /**
     * Check if the heartbeat is considered active (last heartbeat within 15s).
     */
    _isHeartbeatActive() {
        if (!this._lastHeartbeat) return false;
        return (Date.now() - this._lastHeartbeat) < 15000;
    }

    // ========================================================================
    // REVIEW SECTION
    // ========================================================================

    /**
     * Render the full review section (metrics table + quality gates + actions).
     * Visible when status is pending_review.
     */
    _renderReviewSection(status) {
        if (!REVIEW_STATUSES.has(status)) return '';

        const review = this._plan?.execution?.review;
        if (!review) return '';

        return html`
            <div class="review-section">
                <!-- Header: title + verdict -->
                <div class="review-header">
                    <div class="review-title">
                        📊 Review de métricas
                        ${review.verdict ? html`
                            <span class="review-verdict ${review.verdict}">${review.verdict}</span>
                        ` : ''}
                    </div>
                    ${review.summary ? html`
                        <div class="review-summary">${review.summary}</div>
                    ` : ''}
                </div>

                <!-- Quality Gates -->
                ${this._renderQualityGates(review.quality_gates)}

                <!-- Issues & Suggestions -->
                ${(review.issues?.length || review.suggestions?.length) ? html`
                    <div class="review-issues">
                        ${(review.issues || []).map(i => html`
                            <div class="review-issue">${i}</div>
                        `)}
                        ${(review.suggestions || []).map(s => html`
                            <div class="review-suggestion">${s}</div>
                        `)}
                    </div>
                ` : ''}

                <!-- Metrics Table or "no metrics" message -->
                ${review.file_metrics?.length > 0
                    ? this._renderReviewMetricsTable(review.file_metrics)
                    : html`
                        <div class="no-metrics-msg">
                            ℹ️ Sin archivos .py analizados — las métricas solo se calculan para archivos Python
                        </div>
                    `
                }

                <!-- Approve / Revert buttons -->
                <div class="review-actions">
                    <button class="approve-btn"
                        ?disabled=${this._isApproving || this._isReverting}
                        @click=${this._approvePlan}>
                        ${this._isApproving ? html`<div class="spinner-sm"></div>` : ''}
                        ✅ Aprobar y Commit
                    </button>
                    <button class="revert-btn"
                        ?disabled=${this._isApproving || this._isReverting}
                        @click=${this._revertPlan}>
                        ${this._isReverting ? html`<div class="spinner-sm"></div>` : ''}
                        ↩️ Revertir cambios
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Render quality gates as a list of ✅/❌ badges.
     */
    _renderQualityGates(gates) {
        if (!gates || Object.keys(gates).length === 0) return '';

        return html`
            <div class="quality-gates-section">
                ${Object.entries(gates).map(([name, passed]) => html`
                    <span class="quality-gate-item ${passed ? 'passed' : 'failed'}">
                        ${passed ? '✅' : '❌'} ${name.replace(/_/g, ' ')}
                    </span>
                `)}
            </div>
        `;
    }

    // ========================================================================
    // REVIEW METRICS TABLE (commit-detail.js pattern)
    // ========================================================================

    /**
     * Render combined metrics table for review file_metrics.
     * Replicates the pattern from commit-detail.js.
     */
    _renderReviewMetricsTable(fileMetrics) {
        if (!fileMetrics || fileMetrics.length === 0) return '';

        const totals = this._computeReviewTotals(fileMetrics);

        return html`
            <div class="table-section">
                <div class="table-section-header">
                    <span>📈 Archivos analizados</span>
                    <span class="table-py-count">${fileMetrics.length} .py con métricas</span>
                </div>
                <div class="table-scroll-wrapper">
                    <table class="combined-table">
                        <thead>
                            <tr>
                                <th class="th-status"></th>
                                <th class="th-path">Archivo</th>
                                <th class="th-metric">SLOC</th>
                                <th class="th-metric">CC</th>
                                <th class="th-metric">MaxCC</th>
                                <th class="th-metric">MI</th>
                                <th class="th-metric">Fn</th>
                                <th class="th-metric">Cls</th>
                                <th class="th-metric">Nest</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${fileMetrics.map(fm => this._renderReviewTableRow(fm))}
                        </tbody>
                        <tfoot>
                            ${this._renderReviewTotalsRow(totals)}
                        </tfoot>
                    </table>
                </div>
            </div>
        `;
    }

    _renderReviewTableRow(fm) {
        const after = fm.after || {};
        const before = fm.before || {};
        const isNew = Object.keys(before).length === 0;
        const isDeleted = Object.keys(after).length === 0;
        const icon = isNew ? '✅' : isDeleted ? '❌' : '🔄';

        return html`
            <tr class="file-row" title="${fm.path}">
                <td class="td-status">${icon}</td>
                <td class="td-path">${this._breakablePath(fm.path)}</td>
                <!-- SLOC -->
                <td class="td-metric">
                    <span class="metric-val">${after.sloc ?? '—'}</span>
                    ${this._renderDelta(fm.deltas?.delta_sloc, true)}
                </td>
                <!-- CC avg -->
                <td class="td-metric">
                    <span class="metric-val">${after.avg_complexity?.toFixed?.(1) ?? '—'}</span>
                    ${this._renderDelta(fm.deltas?.delta_avg_complexity, true, true)}
                </td>
                <!-- Max CC -->
                <td class="td-metric">
                    <span class="metric-val">${after.max_complexity ?? '—'}</span>
                    ${this._renderDelta(fm.deltas?.delta_max_complexity, true)}
                </td>
                <!-- MI -->
                <td class="td-metric">
                    <span class="metric-val ${this._miClass(after.maintainability_index)}">${after.maintainability_index?.toFixed?.(0) ?? '—'}</span>
                    ${this._renderDelta(fm.deltas?.delta_maintainability_index, false, true, true)}
                </td>
                <!-- Functions -->
                <td class="td-metric">
                    <span class="metric-val">${after.functions_count ?? '—'}</span>
                    ${this._renderDelta(fm.deltas?.delta_functions_count)}
                </td>
                <!-- Classes -->
                <td class="td-metric">
                    <span class="metric-val">${after.classes_count ?? '—'}</span>
                    ${this._renderDelta(fm.deltas?.delta_classes_count)}
                </td>
                <!-- Max Nesting -->
                <td class="td-metric">
                    <span class="metric-val">${after.max_nesting ?? '—'}</span>
                    ${this._renderDelta(fm.deltas?.delta_max_nesting, true)}
                </td>
            </tr>
        `;
    }

    _computeReviewTotals(fileMetrics) {
        let totalSlocAfter = 0, totalSlocBefore = 0;
        let totalFnAfter = 0, totalFnBefore = 0;
        let totalClsAfter = 0, totalClsBefore = 0;
        let sumMiAfter = 0, sumMiBefore = 0;
        let sumCcAfter = 0, sumCcBefore = 0;
        let maxCcAfter = 0, maxCcBefore = 0;
        let maxNestAfter = 0, maxNestBefore = 0;
        let count = 0;

        for (const fm of fileMetrics) {
            const a = fm.after || {};
            const b = fm.before || {};
            totalSlocAfter += a.sloc || 0;
            totalSlocBefore += b.sloc || 0;
            totalFnAfter += a.functions_count || 0;
            totalFnBefore += b.functions_count || 0;
            totalClsAfter += a.classes_count || 0;
            totalClsBefore += b.classes_count || 0;
            sumMiAfter += a.maintainability_index || 0;
            sumMiBefore += b.maintainability_index || 0;
            sumCcAfter += a.avg_complexity || 0;
            sumCcBefore += b.avg_complexity || 0;
            maxCcAfter = Math.max(maxCcAfter, a.max_complexity || 0);
            maxCcBefore = Math.max(maxCcBefore, b.max_complexity || 0);
            maxNestAfter = Math.max(maxNestAfter, a.max_nesting || 0);
            maxNestBefore = Math.max(maxNestBefore, b.max_nesting || 0);
            count++;
        }

        const avgMiAfter = count ? sumMiAfter / count : 0;
        const avgMiBefore = count ? sumMiBefore / count : 0;
        const avgCcAfter = count ? sumCcAfter / count : 0;
        const avgCcBefore = count ? sumCcBefore / count : 0;

        return {
            fileCount: count,
            slocAfter: totalSlocAfter, deltaSloc: totalSlocAfter - totalSlocBefore,
            avgCc: avgCcAfter, deltaCc: avgCcAfter - avgCcBefore,
            maxCcAfter, deltaMaxCc: maxCcAfter - maxCcBefore,
            avgMi: avgMiAfter, deltaMi: avgMiAfter - avgMiBefore,
            fnAfter: totalFnAfter, deltaFn: totalFnAfter - totalFnBefore,
            clsAfter: totalClsAfter, deltaCls: totalClsAfter - totalClsBefore,
            maxNestAfter, deltaMaxNest: maxNestAfter - maxNestBefore,
        };
    }

    _renderReviewTotalsRow(t) {
        return html`
            <tr class="totals-row">
                <td class="td-status">Σ</td>
                <td class="td-path totals-label">
                    ${t.fileCount} archivo${t.fileCount !== 1 ? 's' : ''} .py
                </td>
                <td class="td-metric">
                    <span class="metric-val">${t.slocAfter}</span>
                    ${this._renderDelta(t.deltaSloc, true)}
                </td>
                <td class="td-metric">
                    <span class="metric-val">${t.avgCc.toFixed(1)}</span>
                    ${this._renderDelta(t.deltaCc, true, true)}
                </td>
                <td class="td-metric">
                    <span class="metric-val">${t.maxCcAfter}</span>
                    ${this._renderDelta(t.deltaMaxCc, true)}
                </td>
                <td class="td-metric">
                    <span class="metric-val ${this._miClass(t.avgMi)}">${t.avgMi.toFixed(0)}</span>
                    ${this._renderDelta(t.deltaMi, false, true, true)}
                </td>
                <td class="td-metric">
                    <span class="metric-val">${t.fnAfter}</span>
                    ${this._renderDelta(t.deltaFn)}
                </td>
                <td class="td-metric">
                    <span class="metric-val">${t.clsAfter}</span>
                    ${this._renderDelta(t.deltaCls)}
                </td>
                <td class="td-metric">
                    <span class="metric-val">${t.maxNestAfter}</span>
                    ${this._renderDelta(t.deltaMaxNest, true)}
                </td>
            </tr>
        `;
    }

    // ========================================================================
    // REVIEW RENDER HELPERS (from commit-detail.js)
    // ========================================================================

    _renderDelta(delta, lowerBetter = false, isFloat = false, higherBetter = false) {
        if (delta == null || delta === 0) return html`<span class="delta delta-neutral">—</span>`;
        let cls = 'delta-neutral';
        if (lowerBetter) cls = delta < 0 ? 'delta-positive' : 'delta-negative';
        else if (higherBetter) cls = delta > 0 ? 'delta-positive' : 'delta-negative';
        const sign = delta > 0 ? '+' : '';
        const val = isFloat ? delta.toFixed(1) : delta;
        return html`<span class="delta ${cls}">${sign}${val}</span>`;
    }

    /** Returns MI color class based on value */
    _miClass(mi) {
        if (mi == null) return '';
        if (mi >= 60) return 'mi-good';
        if (mi >= 40) return 'mi-warn';
        return 'mi-bad';
    }

    /**
     * Makes a file path breakable by inserting <wbr> after each '/'.
     */
    _breakablePath(p) {
        if (!p) return '';
        const parts = p.split('/');
        const result = [];
        for (let i = 0; i < parts.length; i++) {
            result.push(html`${i > 0 ? html`/<wbr>` : ''}${parts[i]}`);
        }
        return result;
    }

    // ========================================================================
    // APPROVE / REVERT ACTIONS
    // ========================================================================

    /**
     * Approve the plan: git add + commit → completed.
     * Checks backend success and shows error if operation failed.
     */
    async _approvePlan() {
        if (this._isApproving) return;
        this._isApproving = true;

        try {
            const envelope = await this._callAndCheckSuccess('approve_plan', { plan_id: this.planId });
            if (!envelope.success) {
                alert(`❌ Error al aprobar: ${envelope.message || 'Error desconocido'}`);
                return;
            }
            // Reload plan to get updated status + commit hash
            await this._loadPlan();
            this.dispatchEvent(new CustomEvent('plan-updated', {
                bubbles: true,
                composed: true,
            }));
        } catch (error) {
            console.error('❌ Error approving plan:', error);
            alert(`❌ Error al aprobar: ${error.message}`);
        } finally {
            this._isApproving = false;
        }
    }

    /**
     * Revert the plan: git checkout -- files → reverted.
     * Checks backend success and shows error if operation failed.
     */
    async _revertPlan() {
        if (this._isReverting) return;
        if (!confirm('¿Revertir todos los cambios del plan? Los archivos volverán a su estado anterior.')) return;

        this._isReverting = true;

        try {
            const envelope = await this._callAndCheckSuccess('revert_plan', { plan_id: this.planId });
            if (!envelope.success) {
                alert(`❌ Error al revertir: ${envelope.message || 'Error desconocido'}`);
                return;
            }
            // Reload plan to get updated status
            await this._loadPlan();
            this.dispatchEvent(new CustomEvent('plan-updated', {
                bubbles: true,
                composed: true,
            }));
        } catch (error) {
            console.error('❌ Error reverting plan:', error);
            alert(`❌ Error al revertir: ${error.message}`);
        } finally {
            this._isReverting = false;
        }
    }

    /**
     * Call an API function and return the full envelope {success, result, message}.
     * Unlike executeFunction which only returns result, this gives access to success/message.
     */
    async _callAndCheckSuccess(funcName, params) {
        const controller = new AutoFunctionController();
        controller.funcName = funcName;
        await controller.loadFunctionInfo();
        Object.entries(params).forEach(([key, value]) => {
            controller.setParam(key, value);
        });
        await controller.execute();
        return { success: controller.success, result: controller.result, message: controller.message };
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
