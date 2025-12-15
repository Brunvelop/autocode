/**
 * context-bar.styles.js
 * Estilos específicos para el componente ContextBar
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const contextBarStyles = css`
    :host {
        display: block;
        width: 100%;
        font-family: var(--chat-font-family, system-ui, -apple-system, sans-serif);
    }

    .container {
        width: 100%;
    }

    .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: var(--chat-font-size-sm, 0.75rem);
        color: var(--chat-text-secondary, #4b5563);
        margin-bottom: var(--chat-spacing-xs, 0.25rem);
    }

    .stats {
        font-family: var(--chat-font-mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace);
    }

    .track {
        width: 100%;
        background-color: var(--chat-border-gray, #e5e7eb);
        border-radius: var(--chat-radius-full, 9999px);
        height: 0.5rem;
        overflow: hidden;
    }

    .bar {
        height: 100%;
        transition: width var(--chat-transition-slow, 0.3s) ease, 
                    background-color var(--chat-transition-slow, 0.3s) ease;
        border-radius: var(--chat-radius-full, 9999px);
    }

    .bar.green {
        background-color: var(--chat-success, #22c55e);
    }

    .bar.yellow {
        background-color: var(--chat-warning, #eab308);
    }

    .bar.red {
        background-color: var(--chat-danger, #ef4444);
    }
`;
