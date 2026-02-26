/**
 * git-graph.styles.js
 * Estilos para el componente principal GitGraph
 */
import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const gitGraphStyles = css`
    :host {
        display: block;
        font-family: var(--design-font-family, system-ui, sans-serif);
        height: 100%;
        overflow: hidden;
    }

    .graph-container {
        display: flex;
        flex-direction: column;
        height: 100%;
        background: var(--design-bg-white, #ffffff);
    }

    /* ===== HEADER ===== */
    .graph-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: var(--design-spacing-sm, 0.5rem) var(--design-spacing-lg, 1rem);
        border-bottom: 1px solid var(--design-border-gray, #e5e7eb);
        flex-shrink: 0;
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
    }

    .header-title {
        font-size: var(--design-font-size-lg, 1rem);
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-primary, #1f2937);
        margin: 0;
    }

    .header-title-icon {
        font-size: 1.25rem;
    }

    .header-actions {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
    }

    .branch-select {
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        background: var(--design-bg-white, #ffffff);
        font-size: var(--design-font-size-sm, 0.75rem);
        font-family: var(--design-font-mono, monospace);
        color: var(--design-text-primary, #1f2937);
        cursor: pointer;
        outline: none;
    }

    .branch-select:focus {
        border-color: var(--design-primary, #4f46e5);
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.15);
    }

    .action-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
        background: transparent;
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        color: var(--design-text-secondary, #6b7280);
        font-size: var(--design-font-size-sm, 0.875rem);
        cursor: pointer;
        transition: all var(--design-transition-fast, 0.1s);
    }

    .action-btn:hover {
        background: var(--design-bg-gray-50, #f9fafb);
        color: var(--design-text-primary, #1f2937);
        border-color: var(--design-primary, #4f46e5);
    }

    /* ===== MAIN CONTENT ===== */
    .graph-body {
        display: flex;
        flex: 1;
        overflow: hidden;
    }

    /* ===== GRAPH PANEL (LEFT) ===== */
    .graph-panel {
        flex: 1;
        overflow-y: auto;
        overflow-x: hidden;
        min-width: 0;
    }

    .commit-list {
        display: flex;
        flex-direction: column;
    }

    /* ===== DETAIL PANEL (RIGHT) ===== */
    .detail-panel {
        width: 380px;
        flex-shrink: 0;
        border-left: 1px solid var(--design-border-gray, #e5e7eb);
        overflow-y: auto;
        background: var(--design-bg-gray-50, #f9fafb);
    }

    .detail-placeholder {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: var(--design-text-tertiary, #9ca3af);
        gap: var(--design-spacing-sm, 0.5rem);
        padding: var(--design-spacing-lg, 1rem);
        text-align: center;
    }

    .detail-placeholder-icon {
        font-size: 2.5rem;
        opacity: 0.4;
    }

    .detail-placeholder-text {
        font-size: var(--design-font-size-sm, 0.75rem);
    }

    /* ===== LOAD MORE ===== */
    .load-more {
        display: flex;
        justify-content: center;
        padding: var(--design-spacing-md, 0.75rem);
    }

    .load-more-btn {
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-lg, 1rem);
        background: transparent;
        border: 1px dashed var(--design-border-gray-dark, #d1d5db);
        border-radius: var(--design-radius-md, 0.5rem);
        color: var(--design-text-secondary, #6b7280);
        font-size: var(--design-font-size-sm, 0.75rem);
        cursor: pointer;
        transition: all var(--design-transition-fast, 0.1s);
    }

    .load-more-btn:hover {
        border-color: var(--design-primary, #4f46e5);
        color: var(--design-primary, #4f46e5);
        background: var(--design-indigo-50, #eef2ff);
    }

    /* ===== STATES ===== */
    .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
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

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    .error-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        gap: var(--design-spacing-sm, 0.5rem);
        padding: var(--design-spacing-lg, 1rem);
    }

    .error-box {
        padding: var(--design-spacing-md, 0.75rem) var(--design-spacing-lg, 1rem);
        background: var(--design-error-bg, #fef2f2);
        border: 1px solid var(--design-error-border, #fca5a5);
        border-radius: var(--design-radius-md, 0.5rem);
        color: var(--design-error-text, #991b1b);
        font-size: var(--design-font-size-sm, 0.75rem);
        text-align: center;
        max-width: 400px;
    }

    .retry-btn {
        margin-top: var(--design-spacing-sm, 0.5rem);
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-md, 0.75rem);
        background: var(--design-error-text, #991b1b);
        color: white;
        border: none;
        border-radius: var(--design-radius-md, 0.5rem);
        cursor: pointer;
        font-size: var(--design-font-size-sm, 0.75rem);
    }

    .retry-btn:hover {
        opacity: 0.9;
    }

    /* ===== RESPONSIVE ===== */
    @media (max-width: 768px) {
        .graph-body {
            flex-direction: column;
        }
        .detail-panel {
            width: 100%;
            max-height: 50%;
            border-left: none;
            border-top: 1px solid var(--design-border-gray, #e5e7eb);
        }
    }
`;
