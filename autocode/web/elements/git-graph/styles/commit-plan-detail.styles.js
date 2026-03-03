/**
 * commit-plan-detail.styles.js
 * Estilos para el panel de detalle de un plan de commit.
 * Sigue el patrón de commit-detail.styles.js con variaciones para planes.
 */
import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const commitPlanDetailStyles = css`
    :host {
        display: block;
    }

    .plan-detail {
        padding: var(--design-spacing-lg, 1rem);
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-md, 0.75rem);
    }

    /* ===== HEADER ===== */
    .detail-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: var(--design-spacing-sm, 0.5rem);
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        flex: 1;
        min-width: 0;
    }

    .header-icon {
        font-size: 16px;
        flex-shrink: 0;
    }

    .detail-title {
        font-size: var(--design-font-size-base, 0.875rem);
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-primary, #1f2937);
        margin: 0;
        line-height: var(--design-line-height-normal, 1.5);
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 1px 8px;
        border-radius: var(--design-radius-full, 9999px);
        font-size: 10px;
        font-weight: var(--design-font-weight-bold, 700);
        text-transform: uppercase;
        letter-spacing: 0.04em;
        flex-shrink: 0;
    }

    .status-badge.draft {
        background: #fef3c7;
        color: #92400e;
    }

    .status-badge.ready {
        background: #dcfce7;
        color: #166534;
    }

    .status-badge.abandoned {
        background: var(--design-bg-gray-100, #f3f4f6);
        color: var(--design-text-tertiary, #9ca3af);
    }

    .close-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        background: transparent;
        border: none;
        border-radius: var(--design-radius-sm, 0.25rem);
        color: var(--design-text-tertiary, #9ca3af);
        cursor: pointer;
        font-size: 14px;
        flex-shrink: 0;
    }

    .close-btn:hover {
        background: var(--design-bg-gray-100, #f3f4f6);
        color: var(--design-text-primary, #1f2937);
    }

    /* ===== META INFO ===== */
    .meta-section {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-xs, 0.25rem);
        padding: var(--design-spacing-sm, 0.5rem);
        background: var(--design-bg-white, #ffffff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
    }

    .meta-row {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        font-size: 12px;
    }

    .meta-label {
        color: var(--design-text-tertiary, #9ca3af);
        font-weight: var(--design-font-weight-medium, 500);
        min-width: 55px;
    }

    .meta-value {
        color: var(--design-text-primary, #1f2937);
        font-family: var(--design-font-mono, monospace);
        font-size: 11px;
    }

    /* ===== DESCRIPTION ===== */
    .description-section {
        padding: var(--design-spacing-sm, 0.5rem);
        background: var(--design-bg-white, #ffffff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        font-size: var(--design-font-size-sm, 0.75rem);
        color: var(--design-text-primary, #1f2937);
        line-height: var(--design-line-height-relaxed, 1.6);
    }

    /* ===== TASKS ===== */
    .section-header {
        font-size: 12px;
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-secondary, #6b7280);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding-bottom: var(--design-spacing-xs, 0.25rem);
    }

    .tasks-section {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-xs, 0.25rem);
    }

    .task-card {
        background: var(--design-bg-white, #ffffff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        overflow: hidden;
    }

    .task-card-header {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-xs, 0.25rem);
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
        background: var(--design-bg-gray-50, #f9fafb);
        border-bottom: 1px solid var(--design-border-gray, #e5e7eb);
    }

    .task-type-badge {
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        padding: 1px 5px;
        border-radius: var(--design-radius-sm, 0.25rem);
        font-weight: var(--design-font-weight-semibold, 600);
    }

    .task-type-create {
        background: #dcfce7;
        color: #166534;
    }

    .task-type-modify {
        background: #dbeafe;
        color: #1e40af;
    }

    .task-type-delete {
        background: #fef2f2;
        color: #991b1b;
    }

    .task-type-rename {
        background: #fef3c7;
        color: #92400e;
    }

    .task-path {
        flex: 1;
        font-size: 11px;
        font-family: var(--design-font-mono, monospace);
        color: var(--design-text-primary, #1f2937);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-weight: var(--design-font-weight-medium, 500);
    }

    .task-body {
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
        font-size: 11px;
        color: var(--design-text-primary, #1f2937);
    }

    .task-description {
        font-weight: var(--design-font-weight-medium, 500);
        margin-bottom: 2px;
    }

    .task-details {
        color: var(--design-text-secondary, #6b7280);
        font-size: 10px;
        line-height: 1.4;
    }

    .task-criteria {
        margin-top: 4px;
        padding-left: 12px;
    }

    .task-criteria li {
        font-size: 10px;
        color: var(--design-text-secondary, #6b7280);
        line-height: 1.5;
    }

    /* ===== CONTEXT ===== */
    .context-section {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-xs, 0.25rem);
    }

    .context-card {
        padding: var(--design-spacing-sm, 0.5rem);
        background: var(--design-bg-white, #ffffff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        font-size: 11px;
    }

    .context-label {
        font-size: 10px;
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-tertiary, #9ca3af);
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 3px;
    }

    .context-file {
        font-family: var(--design-font-mono, monospace);
        font-size: 10px;
        color: var(--design-primary, #4f46e5);
        padding: 1px 0;
    }

    .context-notes {
        font-size: 11px;
        color: var(--design-text-primary, #1f2937);
        line-height: 1.5;
        white-space: pre-wrap;
    }

    /* ===== TAGS ===== */
    .tags-section {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
    }

    .tag-item {
        font-size: 9px;
        padding: 1px 6px;
        border-radius: var(--design-radius-full, 9999px);
        background: var(--design-indigo-50, #eef2ff);
        color: var(--design-primary, #4f46e5);
        font-weight: var(--design-font-weight-medium, 500);
    }

    /* ===== FOOTER / ACTIONS ===== */
    .actions-section {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        padding-top: var(--design-spacing-xs, 0.25rem);
        border-top: 1px solid var(--design-border-gray, #e5e7eb);
    }

    .status-select {
        padding: 2px var(--design-spacing-xs, 0.25rem);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        background: var(--design-bg-white, #ffffff);
        font-size: 11px;
        color: var(--design-text-primary, #1f2937);
        cursor: pointer;
        outline: none;
    }

    .status-select:focus {
        border-color: var(--design-primary, #4f46e5);
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.15);
    }

    .delete-btn {
        margin-left: auto;
        display: flex;
        align-items: center;
        gap: 3px;
        padding: 2px 8px;
        background: transparent;
        border: 1px solid var(--design-error-border, #fca5a5);
        border-radius: var(--design-radius-md, 0.5rem);
        color: var(--design-error-text, #991b1b);
        font-size: 11px;
        cursor: pointer;
        transition: all var(--design-transition-fast, 0.1s);
    }

    .delete-btn:hover {
        background: var(--design-error-bg, #fef2f2);
    }

    /* ===== LOADING / ERROR ===== */
    .loading-detail {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: var(--design-spacing-xl, 1.25rem);
        color: var(--design-text-tertiary, #9ca3af);
        gap: var(--design-spacing-sm, 0.5rem);
        font-size: var(--design-font-size-sm, 0.75rem);
    }

    .spinner-sm {
        width: 16px;
        height: 16px;
        border: 2px solid var(--design-border-gray, #e5e7eb);
        border-top-color: var(--design-primary, #4f46e5);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    .error-msg {
        padding: var(--design-spacing-sm, 0.5rem);
        background: var(--design-error-bg, #fef2f2);
        border: 1px solid var(--design-error-border, #fca5a5);
        border-radius: var(--design-radius-md, 0.5rem);
        color: var(--design-error-text, #991b1b);
        font-size: 12px;
    }

    /* ===== EXECUTE SECTION ===== */
    .execute-section {
        padding-top: var(--design-spacing-xs, 0.25rem);
    }

    .execute-row {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
    }

    .model-select {
        flex: 1;
        min-width: 0;
        padding: 4px 6px;
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        background: var(--design-bg-white, #ffffff);
        font-size: 10px;
        font-family: var(--design-font-mono, monospace);
        color: var(--design-text-primary, #1f2937);
        cursor: pointer;
        outline: none;
    }

    .model-select:focus {
        border-color: var(--design-primary, #4f46e5);
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.15);
    }

    .model-select:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .execute-btn {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 4px 12px;
        background: linear-gradient(to right, #4f46e5, #7c3aed);
        color: white;
        border: none;
        border-radius: var(--design-radius-md, 0.5rem);
        font-size: 11px;
        font-weight: var(--design-font-weight-semibold, 600);
        cursor: pointer;
        transition: all var(--design-transition-fast, 0.1s);
        white-space: nowrap;
        flex-shrink: 0;
    }

    .execute-btn:hover:not(:disabled) {
        opacity: 0.9;
        box-shadow: 0 2px 8px rgba(79, 70, 229, 0.3);
    }

    .execute-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    /* ===== TASK EXECUTION STATES ===== */
    .task-card.running {
        border-left: 3px solid #f59e0b;
    }

    .task-card.completed {
        border-left: 3px solid #10b981;
    }

    .task-card.failed {
        border-left: 3px solid #ef4444;
    }

    .task-status-icon {
        margin-left: auto;
        font-size: 14px;
        flex-shrink: 0;
    }

    /* Task log (status messages from ReAct) */
    .task-log {
        max-height: 120px;
        overflow-y: auto;
        padding: 4px 8px;
        background: #1f2937;
        border-radius: var(--design-radius-sm, 0.25rem);
        margin-top: 4px;
    }

    .task-log .log-line {
        font-family: var(--design-font-mono, monospace);
        font-size: 10px;
        color: #d1d5db;
        line-height: 1.5;
    }

    /* Task error */
    .task-error {
        padding: 4px 8px;
        background: #fef2f2;
        border: 1px solid #fca5a5;
        border-radius: var(--design-radius-sm, 0.25rem);
        color: #991b1b;
        font-size: 10px;
        margin-top: 4px;
    }

    /* Task summary */
    .task-summary {
        padding: 4px 8px;
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: var(--design-radius-sm, 0.25rem);
        color: #166534;
        font-size: 10px;
        margin-top: 4px;
        line-height: 1.4;
    }

    /* Task cost badge (inline in header) */
    .task-cost-badge {
        display: inline-flex;
        align-items: center;
        padding: 1px 6px;
        border-radius: var(--design-radius-full, 9999px);
        background: var(--design-indigo-50, #eef2ff);
        color: var(--design-primary, #4f46e5);
        font-size: 9px;
        font-family: var(--design-font-mono, monospace);
        font-weight: var(--design-font-weight-medium, 500);
        white-space: nowrap;
        flex-shrink: 0;
    }

    /* Task files changed */
    .task-files {
        padding: 4px 8px;
        margin-top: 4px;
        font-size: 10px;
    }

    .task-files-label {
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-tertiary, #9ca3af);
        margin-bottom: 2px;
    }

    .task-file-item {
        font-family: var(--design-font-mono, monospace);
        color: var(--design-primary, #4f46e5);
        font-size: 10px;
    }

    /* ===== EXECUTION SUMMARY BANNER ===== */
    .execution-summary {
        padding: 8px 12px;
        border-radius: var(--design-radius-md, 0.5rem);
        font-size: 12px;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .execution-summary.success {
        background: #dcfce7;
        border: 1px solid #86efac;
        color: #166534;
    }

    .execution-summary.failed {
        background: #fef2f2;
        border: 1px solid #fca5a5;
        color: #991b1b;
    }

    .execution-summary .summary-header {
        font-weight: var(--design-font-weight-semibold, 600);
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .execution-summary .summary-details {
        font-size: 11px;
        opacity: 0.85;
    }

    .commit-hash {
        font-family: var(--design-font-mono, monospace);
        font-weight: var(--design-font-weight-bold, 700);
    }

    /* ===== STATUS BADGE EXTENDED ===== */
    .status-badge.executing {
        background: #fef3c7;
        color: #92400e;
        animation: pulse 1.5s infinite;
    }

    .status-badge.completed {
        background: #dcfce7;
        color: #166534;
    }

    .status-badge.failed {
        background: #fef2f2;
        color: #991b1b;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* Task debug wrapper (chat-debug-info component) */
    .task-debug-wrapper {
        margin-top: 4px;
        padding: 0 4px;
    }

    .task-debug-wrapper chat-debug-info {
        --debug-font-size: 10px;
    }

    /* Cost / token badges in execution summary */
    .tokens-badge,
    .cost-badge {
        font-family: var(--design-font-mono, monospace);
        font-weight: var(--design-font-weight-bold, 700);
    }

    .cost-badge {
        color: inherit;
    }

    /* Actions during execution */
    .actions-section .disabled {
        opacity: 0.4;
        pointer-events: none;
    }
`;
