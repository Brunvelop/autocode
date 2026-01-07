/**
 * code-explorer.styles.js
 * Estilos para el componente principal CodeExplorer
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const codeExplorerStyles = css`
    :host {
        display: block;
        font-family: var(--design-font-family, system-ui, sans-serif);
    }

    .explorer-container {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-md, 0.75rem);
        padding: var(--design-spacing-md, 0.75rem);
        border: 1px solid var(--design-border-color, #e5e7eb);
        border-radius: var(--design-radius-lg, 0.75rem);
        background: var(--design-bg-primary, #ffffff);
        max-height: 600px;
        overflow: hidden;
    }

    .explorer-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: var(--design-spacing-sm, 0.5rem);
        border-bottom: 1px solid var(--design-border-color, #e5e7eb);
    }

    .explorer-title {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        font-size: var(--design-font-size-lg, 1.125rem);
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-primary, #1f2937);
        margin: 0;
    }

    .explorer-title-icon {
        font-size: 1.25rem;
    }

    .explorer-actions {
        display: flex;
        gap: var(--design-spacing-xs, 0.25rem);
    }

    .action-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
        background: transparent;
        border: 1px solid var(--design-border-color, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        color: var(--design-text-secondary, #6b7280);
        font-size: var(--design-font-size-sm, 0.875rem);
        cursor: pointer;
        transition: all var(--design-transition-fast, 0.15s);
    }

    .action-btn:hover {
        background: var(--design-bg-secondary, #f9fafb);
        color: var(--design-text-primary, #1f2937);
        border-color: var(--design-primary, #4f46e5);
    }

    .explorer-content {
        flex: 1;
        overflow-y: auto;
        overflow-x: hidden;
    }

    /* Loading state */
    .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: var(--design-spacing-md, 0.75rem);
        padding: var(--design-spacing-xl, 1.5rem);
        color: var(--design-text-secondary, #6b7280);
    }

    .spinner {
        width: 24px;
        height: 24px;
        border: 2px solid var(--design-border-color, #e5e7eb);
        border-top-color: var(--design-primary, #4f46e5);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    /* Error state */
    .error-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        padding: var(--design-spacing-lg, 1rem);
        background: var(--design-error-bg, #fee2e2);
        border: 1px solid var(--design-error-border, #fca5a5);
        border-radius: var(--design-radius-md, 0.5rem);
        color: var(--design-error-text, #991b1b);
    }

    .error-icon {
        font-size: 1.5rem;
    }

    .error-message {
        font-size: var(--design-font-size-sm, 0.875rem);
        text-align: center;
    }

    .retry-btn {
        margin-top: var(--design-spacing-sm, 0.5rem);
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-md, 0.75rem);
        background: var(--design-error-text, #991b1b);
        color: white;
        border: none;
        border-radius: var(--design-radius-md, 0.5rem);
        cursor: pointer;
        font-size: var(--design-font-size-sm, 0.875rem);
    }

    .retry-btn:hover {
        opacity: 0.9;
    }

    /* Empty state */
    .empty-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        padding: var(--design-spacing-xl, 1.5rem);
        color: var(--design-text-secondary, #6b7280);
    }

    .empty-icon {
        font-size: 2rem;
        opacity: 0.5;
    }

    /* View Toggle */
    .view-toggle {
        display: flex;
        gap: 2px;
        padding: var(--design-spacing-xs, 0.25rem);
        background: var(--design-bg-secondary, #f9fafb);
        border-radius: var(--design-radius-md, 0.5rem);
    }

    .toggle-btn {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: var(--design-spacing-xs, 0.25rem);
        padding: var(--design-spacing-sm, 0.5rem) var(--design-spacing-md, 0.75rem);
        background: transparent;
        border: none;
        border-radius: var(--design-radius-sm, 0.25rem);
        color: var(--design-text-secondary, #6b7280);
        font-size: var(--design-font-size-sm, 0.875rem);
        font-weight: var(--design-font-weight-medium, 500);
        cursor: pointer;
        transition: all var(--design-transition-fast, 0.15s);
    }

    .toggle-btn:hover {
        color: var(--design-text-primary, #1f2937);
        background: var(--design-bg-primary, #ffffff);
    }

    .toggle-btn.active {
        background: var(--design-bg-primary, #ffffff);
        color: var(--design-primary, #4f46e5);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
`;
