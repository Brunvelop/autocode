/**
 * metrics-dashboard.styles.js
 * Estilos para el dashboard de métricas de código — aprovecha layout amplio
 */
import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const metricsDashboardStyles = css`
    :host {
        display: block;
        height: 100%;
        overflow-y: auto;
        font-family: var(--design-font-family, system-ui, sans-serif);
    }

    .dashboard {
        padding: var(--design-spacing-lg, 1rem) var(--design-spacing-xl, 1.25rem);
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-lg, 1rem);
    }

    /* ===== LOADING / ERROR ===== */
    .loading-container, .error-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: var(--design-spacing-3xl, 2rem);
        gap: var(--design-spacing-md, 0.75rem);
        color: var(--design-text-secondary, #6b7280);
    }

    .spinner {
        width: 28px;
        height: 28px;
        border: 3px solid var(--design-border-gray, #e5e7eb);
        border-top-color: var(--design-primary, #4f46e5);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    .error-msg {
        padding: var(--design-spacing-md, 0.75rem);
        background: var(--design-error-bg, #fef2f2);
        border: 1px solid var(--design-error-border, #fca5a5);
        border-radius: var(--design-radius-md, 0.5rem);
        color: var(--design-error-text, #991b1b);
        font-size: 12px;
    }

    .retry-btn {
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-md, 0.75rem);
        background: var(--design-primary, #4f46e5);
        color: white;
        border: none;
        border-radius: var(--design-radius-md, 0.5rem);
        cursor: pointer;
        font-size: 12px;
    }

    /* ===== SUMMARY CARDS — wider grid ===== */
    .summary-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: var(--design-spacing-sm, 0.5rem);
    }

    @media (max-width: 700px) {
        .summary-grid {
            grid-template-columns: repeat(3, 1fr);
        }
    }

    .summary-card {
        padding: var(--design-spacing-sm, 0.5rem) var(--design-spacing-md, 0.75rem);
        background: var(--design-bg-white, #fff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        display: flex;
        flex-direction: column;
        gap: 2px;
        position: relative;
    }

    .card-label {
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--design-text-tertiary, #9ca3af);
        font-weight: var(--design-font-weight-medium, 500);
    }

    .card-value {
        font-size: 1.1rem;
        font-weight: var(--design-font-weight-bold, 700);
        color: var(--design-text-primary, #1f2937);
        font-family: var(--design-font-mono, monospace);
    }

    .card-delta {
        font-size: 11px;
        font-family: var(--design-font-mono, monospace);
        font-weight: var(--design-font-weight-medium, 500);
    }

    .delta-positive { color: #16a34a; }
    .delta-negative { color: #dc2626; }
    .delta-neutral { color: var(--design-text-tertiary, #9ca3af); }

    .card-status {
        font-size: 14px;
        position: absolute;
        top: 6px;
        right: 8px;
    }

    /* ===== SECTION ===== */
    .section {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-sm, 0.5rem);
    }

    .section-title {
        font-size: var(--design-font-size-sm, 0.75rem);
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-secondary, #6b7280);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: flex;
        align-items: center;
        gap: var(--design-spacing-xs, 0.25rem);
    }

    /* ===== TWO-COLUMN LAYOUT for tables ===== */
    .two-col {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: var(--design-spacing-lg, 1rem);
        align-items: start;
    }

    @media (max-width: 600px) {
        .two-col {
            grid-template-columns: 1fr;
        }
    }

    /* ===== COMPLEXITY DISTRIBUTION ===== */
    .dist-bars {
        display: flex;
        gap: var(--design-spacing-sm, 0.5rem);
        align-items: flex-end;
        height: 90px;
        padding: var(--design-spacing-sm, 0.5rem) var(--design-spacing-md, 0.75rem);
        background: var(--design-bg-white, #fff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
    }

    .dist-bar-group {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        height: 100%;
        justify-content: flex-end;
    }

    .dist-bar {
        width: 100%;
        max-width: 50px;
        border-radius: 3px 3px 0 0;
        min-height: 2px;
        transition: height 0.3s;
    }

    .dist-bar.rank-A { background: #22c55e; }
    .dist-bar.rank-B { background: #84cc16; }
    .dist-bar.rank-C { background: #eab308; }
    .dist-bar.rank-D { background: #f97316; }
    .dist-bar.rank-E { background: #ef4444; }
    .dist-bar.rank-F { background: #991b1b; }

    .dist-label {
        font-size: 11px;
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-secondary, #6b7280);
    }

    .dist-count {
        font-size: 10px;
        color: var(--design-text-tertiary, #9ca3af);
        font-family: var(--design-font-mono, monospace);
    }

    /* ===== TABLES ===== */
    .metrics-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
        background: var(--design-bg-white, #fff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        overflow: hidden;
    }

    .metrics-table th {
        background: var(--design-bg-gray-50, #f9fafb);
        padding: 6px var(--design-spacing-sm, 0.5rem);
        text-align: left;
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-secondary, #6b7280);
        border-bottom: 1px solid var(--design-border-gray, #e5e7eb);
        font-size: 11px;
    }

    .metrics-table td {
        padding: 5px var(--design-spacing-sm, 0.5rem);
        border-bottom: 1px solid var(--design-border-gray-light, #f3f4f6);
        color: var(--design-text-primary, #1f2937);
    }

    .metrics-table tr:last-child td {
        border-bottom: none;
    }

    .metrics-table tr:hover td {
        background: var(--design-bg-gray-50, #f9fafb);
    }

    .metrics-table .mono {
        font-family: var(--design-font-mono, monospace);
    }

    .metrics-table .path {
        max-width: 250px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-family: var(--design-font-mono, monospace);
        font-size: 11px;
    }

    .rank-badge {
        display: inline-block;
        width: 20px;
        height: 20px;
        line-height: 20px;
        text-align: center;
        border-radius: var(--design-radius-sm, 0.25rem);
        font-size: 11px;
        font-weight: var(--design-font-weight-bold, 700);
        color: white;
    }

    .rank-A { background: #22c55e; }
    .rank-B { background: #84cc16; }
    .rank-C { background: #eab308; color: #1f2937; }
    .rank-D { background: #f97316; }
    .rank-E { background: #ef4444; }
    .rank-F { background: #991b1b; }

    .status-icon { font-size: 13px; }

    /* ===== COUPLING ===== */
    .circular-warning {
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
        background: #fef2f2;
        border: 1px solid #fca5a5;
        border-radius: var(--design-radius-sm, 0.25rem);
        font-size: 11px;
        color: #991b1b;
    }

    .no-issues {
        font-size: 11px;
        color: var(--design-text-tertiary, #9ca3af);
        padding: var(--design-spacing-xs, 0.25rem);
    }

    /* ===== SNAPSHOT INFO ===== */
    .snapshot-info {
        font-size: 10px;
        color: var(--design-text-tertiary, #9ca3af);
        text-align: center;
        padding-top: var(--design-spacing-sm, 0.5rem);
        border-top: 1px solid var(--design-border-gray-light, #f3f4f6);
    }
`;
