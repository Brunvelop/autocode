/**
 * chat-messages.styles.js
 * Estilos específicos para el componente ChatMessages
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const chatMessagesStyles = css`
    :host {
        display: block;
        flex: 1;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        font-family: var(--chat-font-family, system-ui, -apple-system, sans-serif);
    }

    .container {
        flex: 1;
        overflow-y: auto;
        padding: var(--chat-spacing-lg, 1rem);
        background: linear-gradient(to bottom, var(--chat-bg-gray-50, #f9fafb), var(--chat-bg-white, #ffffff));
        display: flex;
        flex-direction: column;
        gap: var(--chat-spacing-md, 0.75rem);
        min-height: 200px;
    }

    .empty-state {
        text-align: center;
        color: var(--chat-text-secondary, #6b7280);
        font-style: italic;
        margin-top: var(--chat-spacing-3xl, 2rem);
    }

    .message-row {
        display: flex;
        width: 100%;
    }

    .message-row.user {
        justify-content: flex-end;
    }

    .message-row.assistant, .message-row.error {
        justify-content: flex-start;
    }

    .bubble {
        max-width: 85%;
        border-radius: var(--chat-radius-xl, 1rem);
        padding: var(--chat-spacing-md, 0.75rem) var(--chat-spacing-lg, 1rem);
        position: relative;
    }

    .bubble.user {
        background-color: var(--chat-primary, #4f46e5);
        color: white;
        box-shadow: var(--chat-shadow-md, 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06));
        border-bottom-right-radius: var(--chat-radius-sm, 0.25rem);
    }

    .bubble.assistant {
        background-color: var(--chat-bg-white, white);
        color: var(--chat-text-primary, #1f2937);
        box-shadow: var(--chat-shadow-xs, 0 1px 2px 0 rgba(0, 0, 0, 0.05));
        border: 1px solid var(--chat-border-gray, #e5e7eb);
        border-bottom-left-radius: var(--chat-radius-sm, 0.25rem);
    }

    .bubble.error {
        background-color: var(--chat-error-bg, #fef2f2);
        color: var(--chat-error-text, #991b1b);
        border: 1px solid var(--chat-error-border, #fca5a5);
        border-bottom-left-radius: var(--chat-radius-sm, 0.25rem);
    }

    .role-label {
        font-weight: var(--chat-font-weight-bold, 700);
        font-size: var(--chat-font-size-sm, 0.75rem);
        margin-bottom: var(--chat-spacing-xs, 0.25rem);
        opacity: 0.9;
    }

    .message-body {
        font-size: var(--chat-font-size-base, 0.875rem);
        line-height: var(--chat-line-height-normal, 1.5);
        word-break: break-word;
    }

    .text-content {
        white-space: pre-wrap;
    }

    /* Reasoning Details */
    details.reasoning {
        background-color: var(--chat-bg-gray-50, #f9fafb);
        border-radius: var(--chat-radius-md, 0.5rem);
        border: 1px solid var(--chat-border-gray, #e5e7eb);
        overflow: hidden;
        margin-bottom: var(--chat-spacing-sm, 0.5rem);
    }

    details.reasoning summary {
        padding: var(--chat-spacing-sm, 0.5rem) var(--chat-spacing-md, 0.75rem);
        cursor: pointer;
        background-color: var(--chat-bg-gray-100, #f3f4f6);
        font-size: var(--chat-font-size-sm, 0.75rem);
        font-weight: var(--chat-font-weight-semibold, 600);
        color: var(--chat-text-secondary, #4b5563);
        display: flex;
        align-items: center;
        user-select: none;
    }

    details.reasoning summary:hover {
        background-color: var(--chat-border-gray, #e5e7eb);
    }

    details.reasoning .content {
        padding: var(--chat-spacing-md, 0.75rem);
        background-color: var(--chat-bg-white, white);
        color: var(--chat-text-primary, #374151);
        white-space: pre-wrap;
        font-family: var(--chat-font-mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace);
        font-size: var(--chat-font-size-sm, 0.75rem);
        border-top: 1px solid var(--chat-border-gray, #e5e7eb);
    }

    /* Trajectory */
    .trajectory {
        margin-bottom: var(--chat-spacing-md, 0.75rem);
    }

    .trajectory-title {
        font-size: var(--chat-font-size-sm, 0.75rem);
        font-weight: var(--chat-font-weight-semibold, 600);
        color: var(--chat-text-secondary, #6b7280);
        margin-bottom: var(--chat-spacing-xs, 0.25rem);
        display: flex;
        align-items: center;
        gap: var(--chat-spacing-xs, 0.25rem);
    }

    .step {
        font-size: var(--chat-font-size-sm, 0.75rem);
        border-left: 2px solid var(--chat-indigo-200, #c7d2fe);
        padding-left: var(--chat-spacing-md, 0.75rem);
        margin-bottom: var(--chat-spacing-sm, 0.5rem);
        padding-top: var(--chat-spacing-xs, 0.25rem);
        padding-bottom: var(--chat-spacing-xs, 0.25rem);
    }

    .step-thought {
        color: var(--chat-text-secondary, #6b7280);
        font-style: italic;
        margin-bottom: var(--chat-spacing-xs, 0.25rem);
    }

    .tool-call {
        font-family: var(--chat-font-mono, ui-monospace, SFMono-Regular, monospace);
        color: var(--chat-primary, #4f46e5);
        background-color: var(--chat-indigo-50, #eef2ff);
        padding: 0.125rem var(--chat-spacing-sm, 0.5rem);
        border-radius: var(--chat-radius-sm, 0.25rem);
        display: inline-block;
    }

    .observation summary {
        cursor: pointer;
        color: var(--chat-text-tertiary, #9ca3af);
        user-select: none;
        margin-top: var(--chat-spacing-xs, 0.25rem);
    }

    .observation summary:hover {
        color: var(--chat-text-secondary, #4b5563);
    }

    .observation-content {
        margin-top: var(--chat-spacing-xs, 0.25rem);
        padding: var(--chat-spacing-sm, 0.5rem);
        background-color: var(--chat-bg-gray-50, #f9fafb);
        border-radius: var(--chat-radius-sm, 0.25rem);
        border: 1px solid var(--chat-border-gray, #e5e7eb);
        font-family: var(--chat-font-mono, ui-monospace, SFMono-Regular, monospace);
        color: var(--chat-text-secondary, #4b5563);
        white-space: pre-wrap;
        max-height: 8rem;
        overflow-y: auto;
    }
`;
