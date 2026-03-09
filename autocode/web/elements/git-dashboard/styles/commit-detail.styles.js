/**
 * commit-detail.styles.js
 * Estilos para el panel de detalle de un commit.
 * Incluye tabla compacta combinada de archivos + métricas.
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

    /* ===== COMBINED TABLE SECTION ===== */
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

    /* ===== TABLE ===== */
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

    .th-loc {
        text-align: right !important;
        width: 60px;
    }

    .th-metric {
        text-align: right !important;
        width: 48px;
    }

    /* ===== TABLE BODY ===== */
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

    .td-loc {
        text-align: right;
        white-space: nowrap;
        vertical-align: middle;
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

    /* ===== LOC COLORS (code quality semantics: less code = good, more code = bad) ===== */
    .loc-good {
        color: #16a34a;
        font-weight: var(--design-font-weight-medium, 500);
        margin-right: 2px;
    }

    .loc-bad {
        color: #dc2626;
        font-weight: var(--design-font-weight-medium, 500);
        margin-right: 2px;
    }

    .loc-zero {
        color: var(--design-text-tertiary, #9ca3af);
    }

    /* ===== METRIC VALUES ===== */
    .metric-val {
        color: var(--design-text-primary, #1f2937);
        font-weight: var(--design-font-weight-semibold, 600);
        font-size: 11px;
    }

    /* MI color indicators */
    .mi-good { color: #16a34a; }
    .mi-warn { color: #ca8a04; }
    .mi-bad  { color: #dc2626; }

    /* ===== DELTAS ===== */
    .delta {
        font-size: 9px;
        font-weight: var(--design-font-weight-semibold, 600);
        font-family: var(--design-font-mono, monospace);
        margin-left: 2px;
    }

    .delta-positive { color: #16a34a; }
    .delta-negative { color: #dc2626; }
    .delta-neutral  { color: var(--design-text-tertiary, #9ca3af); }

    /* ===== TOTALS ROW ===== */
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
