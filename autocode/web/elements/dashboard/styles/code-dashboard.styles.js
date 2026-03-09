/**
 * code-dashboard.styles.js
 * Estilos del componente <code-dashboard>.
 * Los design tokens (--design-*) vienen de theme.js (shared/styles/theme.js).
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const codeDashboardStyles = css`
    :host {
        display: block;
        height: 100%;
        overflow-y: auto;
        font-family: var(--design-font-family, system-ui, sans-serif);
    }

    .dashboard {
        padding: var(--design-spacing-lg) var(--design-spacing-xl);
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-lg);
        height: 100%;
        box-sizing: border-box;
    }

    /* ===== LOADING / ERROR ===== */
    .loading-container, .error-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: var(--design-spacing-3xl);
        gap: var(--design-spacing-md);
        color: var(--design-text-secondary);
    }

    .spinner {
        width: 28px;
        height: 28px;
        border: 3px solid var(--design-border-gray);
        border-top-color: var(--design-primary);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    .error-msg {
        padding: var(--design-spacing-md);
        background: var(--design-error-bg);
        border: 1px solid var(--design-error-border);
        border-radius: var(--design-radius-md);
        color: var(--design-error-text);
        font-size: 12px;
        text-align: center;
        max-width: 400px;
    }

    .retry-btn {
        padding: var(--design-spacing-xs) var(--design-spacing-md);
        background: var(--design-primary);
        color: white;
        border: none;
        border-radius: var(--design-radius-md);
        cursor: pointer;
        font-size: 12px;
        transition: opacity var(--design-transition-fast);
    }

    .retry-btn:hover {
        opacity: 0.9;
    }

    /* ===== SUMMARY CARDS ===== */
    .summary-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: var(--design-spacing-sm);
    }

    @media (max-width: 700px) {
        .summary-grid {
            grid-template-columns: repeat(3, 1fr);
        }
    }

    .summary-card {
        padding: var(--design-spacing-sm) var(--design-spacing-md);
        background: var(--design-bg-white);
        border: 1px solid var(--design-border-gray);
        border-radius: var(--design-radius-md);
        display: flex;
        flex-direction: column;
        gap: 2px;
        position: relative;
    }

    .card-label {
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--design-text-tertiary);
        font-weight: var(--design-font-weight-medium);
    }

    .card-value {
        font-size: 1.1rem;
        font-weight: var(--design-font-weight-bold);
        color: var(--design-text-primary);
        font-family: var(--design-font-mono);
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
        gap: var(--design-spacing-xs);
        font-size: var(--design-font-size-sm);
        color: var(--design-text-secondary);
        padding: var(--design-spacing-xs) 0;
        flex-wrap: wrap;
    }

    .breadcrumb-segment {
        cursor: pointer;
        color: var(--design-primary);
        font-weight: var(--design-font-weight-medium);
        padding: 2px var(--design-spacing-xs);
        border-radius: var(--design-radius-sm);
        transition: background-color var(--design-transition-fast);
        border: none;
        background: none;
        font-size: inherit;
        font-family: inherit;
    }

    .breadcrumb-segment:hover {
        background-color: var(--design-indigo-50);
        color: var(--design-primary-dark);
    }

    .breadcrumb-segment.current {
        color: var(--design-text-primary);
        font-weight: var(--design-font-weight-semibold);
        cursor: default;
    }

    .breadcrumb-segment.current:hover {
        background-color: transparent;
    }

    .breadcrumb-separator {
        color: var(--design-text-tertiary);
        font-size: 10px;
        user-select: none;
    }

    /* ===== VIEW TABS ===== */
    .view-tabs {
        display: flex;
        gap: var(--design-spacing-xs);
        border-bottom: 1px solid var(--design-border-gray);
        padding-bottom: 0;
    }

    .view-tab {
        padding: var(--design-spacing-xs) var(--design-spacing-md);
        background: transparent;
        border: 1px solid transparent;
        border-bottom: 2px solid transparent;
        border-radius: var(--design-radius-md) var(--design-radius-md) 0 0;
        color: var(--design-text-secondary);
        font-size: 12px;
        font-weight: var(--design-font-weight-medium);
        cursor: pointer;
        transition: all var(--design-transition-fast);
        font-family: inherit;
        display: flex;
        align-items: center;
        gap: var(--design-spacing-xs);
    }

    .view-tab:hover {
        color: var(--design-text-primary);
        background: var(--design-bg-gray-50);
    }

    .view-tab.active {
        color: var(--design-primary);
        border-bottom-color: var(--design-primary);
        background: var(--design-indigo-50);
    }

    /* ===== CONTENT AREA ===== */
    .content-area {
        flex: 1;
        min-height: 200px;
        background: var(--design-bg-white);
        border: 1px solid var(--design-border-gray);
        border-radius: var(--design-radius-md);
        display: flex;
        align-items: stretch;
        overflow: hidden;
        position: relative;
    }

    .content-placeholder {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--design-spacing-sm);
        color: var(--design-text-tertiary);
        font-size: var(--design-font-size-sm);
    }

    .content-placeholder-icon {
        font-size: 2rem;
        opacity: 0.3;
    }

    /* ===== SNAPSHOT INFO ===== */
    .snapshot-info {
        font-size: 10px;
        color: var(--design-text-tertiary);
        text-align: center;
        padding-top: var(--design-spacing-sm);
        border-top: 1px solid var(--design-border-gray-light);
    }
`;
