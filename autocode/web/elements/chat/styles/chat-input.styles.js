/**
 * chat-input.styles.js
 * Estilos específicos para el componente ChatInput
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const chatInputStyles = css`
    :host {
        display: block;
        width: 100%;
        font-family: var(--design-font-family, system-ui, -apple-system, sans-serif);
    }

    .container {
        display: flex;
        gap: var(--design-spacing-sm, 0.5rem);
        width: 100%;
    }

    input {
        flex: 1;
        padding: var(--design-spacing-md, 0.75rem);
        border: 1px solid var(--design-border-gray-dark, #d1d5db);
        border-radius: var(--design-radius-lg, 0.75rem);
        font-size: var(--design-font-size-base, 0.875rem);
        line-height: var(--design-line-height-tight, 1.25rem);
        box-shadow: var(--design-shadow-xs, 0 1px 2px 0 rgba(0, 0, 0, 0.05));
        outline: none;
        transition: border-color var(--design-transition-base, 0.2s), 
                    box-shadow var(--design-transition-base, 0.2s);
        background: var(--design-bg-white, white);
        color: var(--design-text-primary, #1f2937);
    }

    input:focus {
        border-color: var(--design-primary-light, #6366f1);
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }

    input:disabled {
        background-color: var(--design-bg-gray-100, #f3f4f6);
        cursor: not-allowed;
        color: var(--design-text-tertiary, #9ca3af);
    }

    button {
        background: linear-gradient(to right, var(--design-primary, #4f46e5), var(--design-secondary, #7c3aed));
        color: white;
        font-weight: var(--design-font-weight-semibold, 600);
        padding: var(--design-spacing-md, 0.75rem) var(--design-spacing-xl, 1.25rem);
        border-radius: var(--design-radius-lg, 0.75rem);
        border: none;
        box-shadow: var(--design-shadow-sm, 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06));
        cursor: pointer;
        transition: opacity var(--design-transition-base, 0.2s), 
                    transform var(--design-transition-fast, 0.1s);
        font-size: var(--design-font-size-base, 0.875rem);
        white-space: nowrap;
    }

    button:hover:not(:disabled) {
        opacity: 0.9;
    }

    button:active:not(:disabled) {
        transform: scale(0.98);
    }

    button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        background: var(--design-border-gray-dark, #d1d5db);
    }
`;
