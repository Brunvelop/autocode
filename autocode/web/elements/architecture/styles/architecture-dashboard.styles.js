/**
 * architecture-dashboard.styles.js
 * Estilos para el dashboard de arquitectura de código.
 * Sigue el patrón visual de metrics-dashboard.styles.js.
 */
import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const architectureDashboardStyles = css`
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
        height: 100%;
        box-sizing: border-box;
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
        text-align: center;
        max-width: 400px;
    }

    .retry-btn {
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-md, 0.75rem);
        background: var(--design-primary, #4f46e5);
        color: white;
        border: none;
        border-radius: var(--design-radius-md, 0.5rem);
        cursor: pointer;
        font-size: 12px;
        transition: opacity var(--design-transition-fast, 0.1s);
    }

    .retry-btn:hover {
        opacity: 0.9;
    }

    /* ===== SUMMARY CARDS ===== */
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

    .card-status {
        font-size: 14px;
        position: absolute;
        top: 6px;
        right: 8px;
    }

    /* ===== BREADCRUMB ===== */
    .breadcrumb {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-xs, 0.25rem);
        font-size: var(--design-font-size-sm, 0.75rem);
        color: var(--design-text-secondary, #6b7280);
        padding: var(--design-spacing-xs, 0.25rem) 0;
        flex-wrap: wrap;
    }

    .breadcrumb-segment {
        cursor: pointer;
        color: var(--design-primary, #4f46e5);
        font-weight: var(--design-font-weight-medium, 500);
        padding: 2px var(--design-spacing-xs, 0.25rem);
        border-radius: var(--design-radius-sm, 0.25rem);
        transition: background-color var(--design-transition-fast, 0.1s);
        border: none;
        background: none;
        font-size: inherit;
        font-family: inherit;
    }

    .breadcrumb-segment:hover {
        background-color: var(--design-indigo-50, #eef2ff);
        color: var(--design-primary-dark, #4338ca);
    }

    .breadcrumb-segment.current {
        color: var(--design-text-primary, #1f2937);
        font-weight: var(--design-font-weight-semibold, 600);
        cursor: default;
    }

    .breadcrumb-segment.current:hover {
        background-color: transparent;
    }

    .breadcrumb-separator {
        color: var(--design-text-tertiary, #9ca3af);
        font-size: 10px;
        user-select: none;
    }

    /* ===== VIEW TABS ===== */
    .view-tabs {
        display: flex;
        gap: var(--design-spacing-xs, 0.25rem);
        border-bottom: 1px solid var(--design-border-gray, #e5e7eb);
        padding-bottom: 0;
    }

    .view-tab {
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-md, 0.75rem);
        background: transparent;
        border: 1px solid transparent;
        border-bottom: 2px solid transparent;
        border-radius: var(--design-radius-md, 0.5rem) var(--design-radius-md, 0.5rem) 0 0;
        color: var(--design-text-secondary, #6b7280);
        font-size: 12px;
        font-weight: var(--design-font-weight-medium, 500);
        cursor: pointer;
        transition: all var(--design-transition-fast, 0.1s);
        font-family: inherit;
        display: flex;
        align-items: center;
        gap: var(--design-spacing-xs, 0.25rem);
    }

    .view-tab:hover {
        color: var(--design-text-primary, #1f2937);
        background: var(--design-bg-gray-50, #f9fafb);
    }

    .view-tab.active {
        color: var(--design-primary, #4f46e5);
        border-bottom-color: var(--design-primary, #4f46e5);
        background: var(--design-indigo-50, #eef2ff);
    }

    /* ===== CONTENT AREA ===== */
    .content-area {
        flex: 1;
        min-height: 200px;
        background: var(--design-bg-white, #fff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        position: relative;
    }

    /* Files tab: file-explorer has its own dark bg, let it fill */
    .content-area--files {
        background: transparent;
        border: none;
        border-radius: var(--design-radius-md, 0.5rem);
        overflow: auto;
    }

    .content-area--files file-explorer {
        width: 100%;
        height: 100%;
        border-radius: var(--design-radius-md, 0.5rem);
        overflow: hidden;
    }

    /* Code tab: code-explorer has its own theme, let it fill */
    .content-area--code {
        background: transparent;
        border: none;
        border-radius: var(--design-radius-md, 0.5rem);
        overflow: auto;
    }

    .content-area--code code-explorer {
        width: 100%;
        height: 100%;
        border-radius: var(--design-radius-md, 0.5rem);
        overflow: hidden;
    }

    /* Metrics tab: metrics-dashboard has its own layout, let it fill */
    .content-area--metrics {
        display: block;
        background: transparent;
        border: none;
        overflow-y: auto;
    }

    .content-area--metrics metrics-dashboard {
        width: 100%;
        display: block;
    }

    .content-placeholder {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        color: var(--design-text-tertiary, #9ca3af);
        font-size: var(--design-font-size-sm, 0.75rem);
    }

    .content-placeholder-icon {
        font-size: 2rem;
        opacity: 0.3;
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
