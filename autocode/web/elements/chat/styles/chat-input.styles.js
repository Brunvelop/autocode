/**
 * chat-input.styles.js
 * Estilos específicos para el componente ChatInput
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const chatInputStyles = css`
    :host {
        display: block;
        width: 100%;
        font-family: var(--chat-font-family, system-ui, -apple-system, sans-serif);
    }

    .container {
        display: flex;
        gap: var(--chat-spacing-sm, 0.5rem);
        width: 100%;
    }

    input {
        flex: 1;
        padding: var(--chat-spacing-md, 0.75rem);
        border: 1px solid var(--chat-border-gray-dark, #d1d5db);
        border-radius: var(--chat-radius-lg, 0.75rem);
        font-size: var(--chat-font-size-base, 0.875rem);
        line-height: var(--chat-line-height-tight, 1.25rem);
        box-shadow: var(--chat-shadow-xs, 0 1px 2px 0 rgba(0, 0, 0, 0.05));
        outline: none;
        transition: border-color var(--chat-transition-base, 0.2s), 
                    box-shadow var(--chat-transition-base, 0.2s);
        background: var(--chat-bg-white, white);
        color: var(--chat-text-primary, #1f2937);
    }

    input:focus {
        border-color: var(--chat-primary-light, #6366f1);
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }

    input:disabled {
        background-color: var(--chat-bg-gray-100, #f3f4f6);
        cursor: not-allowed;
        color: var(--chat-text-tertiary, #9ca3af);
    }

    button {
        background: linear-gradient(to right, var(--chat-primary, #4f46e5), var(--chat-secondary, #7c3aed));
        color: white;
        font-weight: var(--chat-font-weight-semibold, 600);
        padding: var(--chat-spacing-md, 0.75rem) var(--chat-spacing-xl, 1.25rem);
        border-radius: var(--chat-radius-lg, 0.75rem);
        border: none;
        box-shadow: var(--chat-shadow-sm, 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06));
        cursor: pointer;
        transition: opacity var(--chat-transition-base, 0.2s), 
                    transform var(--chat-transition-fast, 0.1s);
        font-size: var(--chat-font-size-base, 0.875rem);
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
        background: var(--chat-border-gray-dark, #d1d5db);
    }
`;
