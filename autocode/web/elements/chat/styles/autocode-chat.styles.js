/**
 * autocode-chat.styles.js
 * Estilos específicos para el componente AutocodeChat (orquestador principal)
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const autocodeChatStyles = css`
    :host {
        display: block;
        font-family: var(--design-font-family, system-ui, -apple-system, sans-serif);
    }

    /* Header Actions Container */
    .header-actions {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
    }

    /* Model Badge */
    .model-badge {
        display: none;
        align-items: center;
        gap: var(--design-spacing-xs, 0.25rem);
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
        border-radius: var(--design-radius-full, 9999px);
        background-color: var(--design-indigo-50, #eef2ff);
        border: 1px solid var(--design-indigo-200, #c7d2fe);
        font-size: var(--design-font-size-xs, 0.625rem);
        font-family: var(--design-font-mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace);
        color: var(--design-primary, #4f46e5);
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 150px;
    }

    @media (min-width: 768px) {
        .model-badge {
            display: flex;
        }
    }

    .model-indicator {
        width: 0.375rem;
        height: 0.375rem;
        border-radius: 50%;
        background-color: var(--design-indigo-400, #818cf8);
    }

    /* New Chat Button */
    .new-chat-btn {
        color: var(--design-indigo-100, #e0e7ff);
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: var(--design-radius-full, 9999px);
        padding: var(--design-spacing-sm, 0.375rem) var(--design-spacing-md, 0.75rem);
        font-size: var(--design-font-size-base, 0.875rem);
        font-weight: var(--design-font-weight-semibold, 600);
        transition: background-color var(--design-transition-base, 0.2s);
        cursor: pointer;
    }

    .new-chat-btn:hover {
        background-color: rgba(255, 255, 255, 0.2);
    }

    /* Footer Container */
    .footer-container {
        padding: var(--design-spacing-lg, 1rem);
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-md, 0.75rem);
    }
`;
