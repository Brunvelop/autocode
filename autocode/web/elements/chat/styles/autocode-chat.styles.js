/**
 * autocode-chat.styles.js
 * Estilos específicos para el componente AutocodeChat (orquestador principal)
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const autocodeChatStyles = css`
    :host {
        display: block;
        font-family: var(--chat-font-family, system-ui, -apple-system, sans-serif);
    }

    /* Header Actions Container */
    .header-actions {
        display: flex;
        align-items: center;
        gap: var(--chat-spacing-sm, 0.5rem);
    }

    /* Model Badge */
    .model-badge {
        display: none;
        align-items: center;
        gap: var(--chat-spacing-xs, 0.25rem);
        padding: var(--chat-spacing-xs, 0.25rem) var(--chat-spacing-sm, 0.5rem);
        border-radius: var(--chat-radius-full, 9999px);
        background-color: var(--chat-indigo-50, #eef2ff);
        border: 1px solid var(--chat-indigo-200, #c7d2fe);
        font-size: var(--chat-font-size-xs, 0.625rem);
        font-family: var(--chat-font-mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace);
        color: var(--chat-primary, #4f46e5);
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
        background-color: var(--chat-indigo-400, #818cf8);
    }

    /* New Chat Button */
    .new-chat-btn {
        color: var(--chat-indigo-100, #e0e7ff);
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: var(--chat-radius-full, 9999px);
        padding: var(--chat-spacing-sm, 0.375rem) var(--chat-spacing-md, 0.75rem);
        font-size: var(--chat-font-size-base, 0.875rem);
        font-weight: var(--chat-font-weight-semibold, 600);
        transition: background-color var(--chat-transition-base, 0.2s);
        cursor: pointer;
    }

    .new-chat-btn:hover {
        background-color: rgba(255, 255, 255, 0.2);
    }

    /* Footer Container */
    .footer-container {
        padding: var(--chat-spacing-lg, 1rem);
        display: flex;
        flex-direction: column;
        gap: var(--chat-spacing-md, 0.75rem);
    }
`;
