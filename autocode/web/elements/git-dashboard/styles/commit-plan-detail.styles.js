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
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-xs, 0.25rem);
    }

    .description-content {
        padding: var(--design-spacing-sm, 0.5rem);
        background: var(--design-bg-white, #ffffff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        font-size: var(--design-font-size-sm, 0.75rem);
        color: var(--design-text-primary, #1f2937);
        line-height: var(--design-line-height-relaxed, 1.6);
        white-space: pre-wrap;
        word-break: break-word;
    }

    /* ===== SECTION HEADER (shared) ===== */
    .section-header {
        font-size: 12px;
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-secondary, #6b7280);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding-bottom: var(--design-spacing-xs, 0.25rem);
    }

    /* ===== STEPS TIMELINE ===== */
    .steps-section {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-xs, 0.25rem);
    }

    .steps-timeline {
        max-height: 300px;
        overflow-y: auto;
        padding: var(--design-spacing-sm, 0.5rem);
        background: var(--design-bg-white, #ffffff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .step-item {
        display: flex;
        gap: 8px;
        padding: 3px 0;
        font-size: 11px;
        border-bottom: 1px solid var(--design-bg-gray-50, #f9fafb);
    }

    .step-item:last-child {
        border-bottom: none;
    }

    .step-icon {
        flex-shrink: 0;
        width: 18px;
        text-align: center;
        font-size: 12px;
    }

    .step-body {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 1px;
    }

    .step-header-row {
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .step-label {
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-secondary, #6b7280);
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        flex-shrink: 0;
    }

    .step-path {
        font-family: var(--design-font-mono, monospace);
        font-size: 10px;
        color: var(--design-primary, #4f46e5);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .step-content {
        font-family: var(--design-font-mono, monospace);
        font-size: 10px;
        color: var(--design-text-primary, #1f2937);
        line-height: 1.4;
        word-break: break-word;
        opacity: 0.85;
    }

    /* Step type variants */
    .step-item.thinking {
        background: #fefce8;
    }

    .step-item.error {
        background: #fef2f2;
    }

    .step-item.error .step-content {
        color: #991b1b;
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

    /* ===== REVIEW MODE SELECT ===== */
    .review-mode-select {
        padding: 4px 6px;
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        background: var(--design-bg-white, #ffffff);
        font-size: 10px;
        color: var(--design-text-primary, #1f2937);
        cursor: pointer;
        outline: none;
        flex-shrink: 0;
    }

    .review-mode-select:focus {
        border-color: var(--design-primary, #4f46e5);
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.15);
    }

    .review-mode-select:disabled {
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

    .execution-summary .summary-files {
        margin-top: 4px;
        padding-top: 4px;
        border-top: 1px solid rgba(0, 0, 0, 0.1);
    }

    .summary-file-item {
        font-family: var(--design-font-mono, monospace);
        font-size: 10px;
        color: inherit;
        opacity: 0.8;
        padding: 1px 0;
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

    .status-badge.pending_review {
        background: #fff7ed;
        color: #9a3412;
        animation: pulse 1.5s infinite;
    }

    .status-badge.reverted {
        background: #fef2f2;
        color: #991b1b;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
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

    /* ===== CANCEL BUTTON ===== */
    .cancel-btn {
        display: flex;
        align-items: center;
        gap: 3px;
        padding: 4px 10px;
        background: transparent;
        border: 1px solid var(--design-error-border, #fca5a5);
        border-radius: var(--design-radius-md, 0.5rem);
        color: var(--design-error-text, #991b1b);
        font-size: 11px;
        cursor: pointer;
        transition: all var(--design-transition-fast, 0.1s);
        white-space: nowrap;
        flex-shrink: 0;
    }

    .cancel-btn:hover {
        background: var(--design-error-bg, #fef2f2);
    }

    /* ===== EXECUTION STATUS ROW (timer + heartbeat) ===== */
    .execute-status-row {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        margin-top: 4px;
        font-size: 11px;
    }

    .elapsed-timer {
        font-family: var(--design-font-mono, monospace);
        font-size: 11px;
        color: var(--design-text-secondary, #6b7280);
        font-weight: var(--design-font-weight-medium, 500);
    }

    .activity-indicator {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 10px;
        color: var(--design-text-tertiary, #9ca3af);
    }

    .activity-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    .activity-dot.active {
        background: #22c55e;
        box-shadow: 0 0 4px rgba(34, 197, 94, 0.5);
    }

    .activity-dot.inactive {
        background: #ef4444;
        box-shadow: 0 0 4px rgba(239, 68, 68, 0.3);
    }

    /* ===== RECOVERY BANNER ===== */
    .recovery-banner {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--design-spacing-sm, 0.5rem);
        padding: 8px 12px;
        background: #fffbeb;
        border: 1px solid #fbbf24;
        border-radius: var(--design-radius-md, 0.5rem);
        font-size: 12px;
    }

    .recovery-text {
        color: #92400e;
        font-weight: var(--design-font-weight-medium, 500);
    }

    .recovery-actions {
        display: flex;
        align-items: center;
        gap: 6px;
        flex-shrink: 0;
    }

    .recovery-btn {
        display: flex;
        align-items: center;
        gap: 3px;
        padding: 3px 8px;
        border-radius: var(--design-radius-sm, 0.25rem);
        font-size: 10px;
        font-weight: var(--design-font-weight-semibold, 600);
        cursor: pointer;
        transition: all var(--design-transition-fast, 0.1s);
        white-space: nowrap;
        border: 1px solid;
    }

    .recovery-btn.reset {
        background: var(--design-bg-white, #ffffff);
        border-color: var(--design-border-gray, #e5e7eb);
        color: var(--design-text-secondary, #6b7280);
    }

    .recovery-btn.reset:hover {
        background: var(--design-bg-gray-50, #f9fafb);
        border-color: var(--design-text-tertiary, #9ca3af);
    }

    .recovery-btn.reexecute {
        background: linear-gradient(to right, #4f46e5, #7c3aed);
        border-color: transparent;
        color: white;
    }

    .recovery-btn.reexecute:hover {
        opacity: 0.9;
    }

    /* ===== REVIEW SECTION ===== */
    .review-section {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-sm, 0.5rem);
        padding: var(--design-spacing-sm, 0.5rem);
        background: var(--design-bg-white, #ffffff);
        border: 1px solid #fdba74;
        border-radius: var(--design-radius-md, 0.5rem);
    }

    .review-header {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .review-title {
        font-size: 12px;
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-secondary, #6b7280);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .review-verdict {
        display: inline-flex;
        align-items: center;
        padding: 1px 8px;
        border-radius: var(--design-radius-full, 9999px);
        font-size: 10px;
        font-weight: var(--design-font-weight-bold, 700);
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .review-verdict.approved {
        background: #dcfce7;
        color: #166534;
    }

    .review-verdict.rejected {
        background: #fef2f2;
        color: #991b1b;
    }

    .review-verdict.needs_changes {
        background: #fff7ed;
        color: #9a3412;
    }

    .review-summary {
        font-size: 11px;
        color: var(--design-text-secondary, #6b7280);
        line-height: 1.4;
    }

    /* ===== QUALITY GATES ===== */
    .quality-gates-section {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        padding: 6px 0;
    }

    .quality-gate-item {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        padding: 2px 8px;
        border-radius: var(--design-radius-sm, 0.25rem);
        font-size: 10px;
        font-weight: var(--design-font-weight-medium, 500);
        border: 1px solid;
    }

    .quality-gate-item.passed {
        background: #f0fdf4;
        border-color: #86efac;
        color: #166534;
    }

    .quality-gate-item.failed {
        background: #fef2f2;
        border-color: #fca5a5;
        color: #991b1b;
    }

    /* ===== REVIEW ISSUES & SUGGESTIONS ===== */
    .review-issues {
        display: flex;
        flex-direction: column;
        gap: 2px;
        font-size: 10px;
    }

    .review-issue {
        color: #991b1b;
        line-height: 1.4;
    }

    .review-suggestion {
        color: #92400e;
        line-height: 1.4;
    }

    /* ===== REVIEW ACTIONS (approve/revert buttons) ===== */
    .review-actions {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        padding-top: var(--design-spacing-xs, 0.25rem);
        border-top: 1px solid var(--design-border-gray, #e5e7eb);
    }

    .approve-btn {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 5px 14px;
        background: linear-gradient(to right, #16a34a, #15803d);
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

    .approve-btn:hover:not(:disabled) {
        opacity: 0.9;
        box-shadow: 0 2px 8px rgba(22, 163, 74, 0.3);
    }

    .approve-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .revert-btn {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 5px 14px;
        background: transparent;
        border: 1px solid var(--design-error-border, #fca5a5);
        border-radius: var(--design-radius-md, 0.5rem);
        color: var(--design-error-text, #991b1b);
        font-size: 11px;
        font-weight: var(--design-font-weight-semibold, 600);
        cursor: pointer;
        transition: all var(--design-transition-fast, 0.1s);
        white-space: nowrap;
        flex-shrink: 0;
    }

    .revert-btn:hover:not(:disabled) {
        background: var(--design-error-bg, #fef2f2);
    }

    .revert-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    /* ===== REVERTED BANNER ===== */
    .reverted-banner {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        padding: 8px 12px;
        background: var(--design-bg-gray-100, #f3f4f6);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        font-size: 12px;
        color: var(--design-text-secondary, #6b7280);
    }

    .reverted-banner .reverted-icon {
        font-size: 16px;
    }

    .reverted-banner .reverted-text {
        font-weight: var(--design-font-weight-medium, 500);
    }

    /* ===== REVIEW ANALYZING BANNER ===== */
    .review-analyzing {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        padding: 8px 12px;
        background: #fff7ed;
        border: 1px solid #fdba74;
        border-radius: var(--design-radius-md, 0.5rem);
        font-size: 12px;
        color: #9a3412;
    }

    /* ===== NO METRICS MESSAGE ===== */
    .no-metrics-msg {
        padding: 8px 12px;
        background: var(--design-bg-gray-50, #f9fafb);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        font-size: 11px;
        color: var(--design-text-tertiary, #9ca3af);
        text-align: center;
    }

    /* ===== COMBINED METRICS TABLE (from commit-detail pattern) ===== */
    .table-section {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-xs, 0.25rem);
    }

    .table-section-header {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        font-size: 12px;
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-secondary, #6b7280);
        padding-bottom: 2px;
    }

    .table-py-count {
        font-size: 10px;
        color: var(--design-text-tertiary, #9ca3af);
        font-family: var(--design-font-mono, monospace);
        font-weight: var(--design-font-weight-normal, 400);
        margin-left: auto;
    }

    .table-scroll-wrapper {
        overflow-x: auto;
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        background: var(--design-bg-white, #ffffff);
    }

    .combined-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 11px;
        font-family: var(--design-font-mono, monospace);
    }

    .combined-table thead {
        background: var(--design-bg-gray-50, #f9fafb);
        border-bottom: 1px solid var(--design-border-gray, #e5e7eb);
    }

    .combined-table th {
        padding: 4px 6px;
        font-size: 9px;
        font-weight: var(--design-font-weight-semibold, 600);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--design-text-tertiary, #9ca3af);
        text-align: left;
        white-space: nowrap;
        border-bottom: 1px solid var(--design-border-gray, #e5e7eb);
    }

    .th-status {
        width: 22px;
        text-align: center !important;
    }

    .th-path {
        min-width: 100px;
    }

    .th-metric {
        text-align: right !important;
        width: 48px;
    }

    .combined-table tbody tr {
        border-bottom: 1px solid var(--design-border-gray, #e5e7eb);
        transition: background var(--design-transition-fast, 0.1s);
    }

    .combined-table tbody tr:last-child {
        border-bottom: none;
    }

    .combined-table tbody tr:hover {
        background: var(--design-bg-gray-50, #f9fafb);
    }

    .combined-table td {
        padding: 4px 6px;
        vertical-align: top;
    }

    .td-status {
        text-align: center;
        font-size: 11px;
        width: 22px;
        vertical-align: middle;
    }

    .td-path {
        color: var(--design-text-primary, #1f2937);
        word-break: break-word;
        overflow-wrap: break-word;
        max-width: 200px;
        line-height: 1.3;
        font-size: 10.5px;
    }

    .td-metric {
        text-align: right;
        white-space: nowrap;
        vertical-align: middle;
    }

    .td-na {
        text-align: center !important;
        color: var(--design-text-tertiary, #9ca3af);
    }

    .metric-val {
        color: var(--design-text-primary, #1f2937);
        font-weight: var(--design-font-weight-semibold, 600);
        font-size: 11px;
    }

    .mi-good { color: #16a34a; }
    .mi-warn { color: #ca8a04; }
    .mi-bad  { color: #dc2626; }

    .delta {
        font-size: 9px;
        font-weight: var(--design-font-weight-semibold, 600);
        font-family: var(--design-font-mono, monospace);
        margin-left: 2px;
    }

    .delta-positive { color: #16a34a; }
    .delta-negative { color: #dc2626; }
    .delta-neutral  { color: var(--design-text-tertiary, #9ca3af); }

    .combined-table tfoot {
        border-top: 2px solid var(--design-border-gray, #e5e7eb);
    }

    .totals-row {
        background: var(--design-bg-gray-50, #f9fafb);
    }

    .totals-row td {
        padding: 5px 6px;
        font-weight: var(--design-font-weight-semibold, 600);
    }

    .totals-row .td-status {
        font-size: 12px;
        color: var(--design-text-secondary, #6b7280);
    }

    .totals-label {
        font-family: var(--design-font-family, system-ui, sans-serif);
        font-size: 11px;
        color: var(--design-text-secondary, #6b7280);
    }

    .totals-py {
        font-size: 10px;
        color: var(--design-text-tertiary, #9ca3af);
        font-weight: var(--design-font-weight-normal, 400);
    }
`;
