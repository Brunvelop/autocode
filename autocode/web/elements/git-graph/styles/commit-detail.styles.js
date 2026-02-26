/**
 * commit-detail.styles.js
 * Estilos para el panel de detalle de un commit
 */
import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const commitDetailStyles = css`
    :host {
        display: block;
    }

    .detail-container {
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

    .detail-title {
        font-size: var(--design-font-size-base, 0.875rem);
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-primary, #1f2937);
        margin: 0;
        line-height: var(--design-line-height-normal, 1.5);
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
        min-width: 50px;
    }

    .meta-value {
        color: var(--design-text-primary, #1f2937);
        font-family: var(--design-font-mono, monospace);
        font-size: 11px;
    }

    .meta-value.hash {
        color: var(--design-primary, #4f46e5);
        user-select: all;
    }

    .meta-value.author {
        font-family: var(--design-font-family, system-ui, sans-serif);
    }

    /* ===== FULL MESSAGE ===== */
    .message-section {
        padding: var(--design-spacing-sm, 0.5rem);
        background: var(--design-bg-white, #ffffff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        font-size: var(--design-font-size-sm, 0.75rem);
        color: var(--design-text-primary, #1f2937);
        white-space: pre-wrap;
        font-family: var(--design-font-mono, monospace);
        line-height: var(--design-line-height-relaxed, 1.6);
        max-height: 150px;
        overflow-y: auto;
    }

    /* ===== STATS BAR ===== */
    .stats-bar {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-md, 0.75rem);
        padding: var(--design-spacing-sm, 0.5rem);
        background: var(--design-bg-white, #ffffff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
    }

    .stat-item {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        font-weight: var(--design-font-weight-medium, 500);
    }

    .stat-files {
        color: var(--design-text-secondary, #6b7280);
    }

    .stat-add {
        color: #16a34a;
    }

    .stat-del {
        color: #dc2626;
    }

    /* ===== FILES LIST ===== */
    .files-section {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .files-header {
        font-size: 12px;
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-secondary, #6b7280);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding-bottom: var(--design-spacing-xs, 0.25rem);
    }

    .file-item {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
        border-radius: var(--design-radius-sm, 0.25rem);
        transition: background var(--design-transition-fast, 0.1s);
    }

    .file-item:hover {
        background: var(--design-bg-gray-100, #f3f4f6);
    }

    .file-status-icon {
        font-size: 12px;
        flex-shrink: 0;
        width: 16px;
        text-align: center;
    }

    .file-path {
        flex: 1;
        font-size: 12px;
        font-family: var(--design-font-mono, monospace);
        color: var(--design-text-primary, #1f2937);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .file-stats {
        display: flex;
        gap: 4px;
        font-size: 11px;
        font-family: var(--design-font-mono, monospace);
        flex-shrink: 0;
    }

    .file-stat-add {
        color: #16a34a;
    }

    .file-stat-del {
        color: #dc2626;
    }

    /* ===== LOADING ===== */
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

    /* ===== PARENTS ===== */
    .parents-section {
        display: flex;
        flex-wrap: wrap;
        gap: var(--design-spacing-xs, 0.25rem);
        align-items: center;
    }

    .parent-label {
        font-size: 11px;
        color: var(--design-text-tertiary, #9ca3af);
    }

    .parent-hash {
        font-size: 11px;
        font-family: var(--design-font-mono, monospace);
        color: var(--design-primary, #4f46e5);
        cursor: pointer;
        padding: 1px 4px;
        border-radius: var(--design-radius-sm, 0.25rem);
    }

    .parent-hash:hover {
        background: var(--design-indigo-50, #eef2ff);
        text-decoration: underline;
    }

    /* ===== COMMIT METRICS ===== */
    .metrics-toggle {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-xs, 0.25rem);
        padding: var(--design-spacing-sm, 0.5rem);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        cursor: pointer;
        font-size: 12px;
        color: var(--design-text-secondary, #6b7280);
        transition: background var(--design-transition-fast, 0.1s);
        user-select: none;
    }

    .metrics-toggle:hover {
        background: var(--design-bg-gray-50, #f9fafb);
        color: var(--design-text-primary, #1f2937);
    }

    .metrics-toggle-icon {
        font-size: 10px;
        width: 12px;
    }

    .metrics-toggle-label {
        flex: 1;
        font-weight: var(--design-font-weight-medium, 500);
    }

    .metrics-loading, .metrics-empty {
        font-size: 11px;
        color: var(--design-text-tertiary, #9ca3af);
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
        text-align: center;
    }

    .metrics-content {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-xs, 0.25rem);
    }

    .metrics-summary-bar {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-md, 0.75rem);
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
        background: var(--design-bg-white, #fff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        font-size: 11px;
        font-family: var(--design-font-mono, monospace);
    }

    .ms-item {
        color: var(--design-text-secondary, #6b7280);
    }

    .ms-delta { font-weight: var(--design-font-weight-semibold, 600); }
    .ms-up { color: #dc2626; }
    .ms-down { color: #16a34a; }
    .ms-down-good { color: #16a34a; }
    .ms-up-bad { color: #dc2626; }
    .ms-count { margin-left: auto; color: var(--design-text-tertiary, #9ca3af); }

    .metrics-files {
        display: flex;
        flex-direction: column;
        gap: 1px;
    }

    .mf-row {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-xs, 0.25rem);
        padding: 3px var(--design-spacing-sm, 0.5rem);
        border-radius: var(--design-radius-sm, 0.25rem);
        font-size: 10px;
        font-family: var(--design-font-mono, monospace);
    }

    .mf-row:hover {
        background: var(--design-bg-gray-50, #f9fafb);
    }

    .mf-path {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: var(--design-text-primary, #1f2937);
    }

    .mf-stat {
        color: var(--design-text-tertiary, #9ca3af);
        white-space: nowrap;
        min-width: 55px;
        text-align: right;
    }
`;
