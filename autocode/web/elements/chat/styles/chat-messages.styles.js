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
        font-family: var(--design-font-family, system-ui, -apple-system, sans-serif);
    }

    .container {
        flex: 1;
        overflow-y: auto;
        padding: var(--design-spacing-lg, 1rem);
        background: linear-gradient(to bottom, var(--design-bg-gray-50, #f9fafb), var(--design-bg-white, #ffffff));
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-md, 0.75rem);
        min-height: 200px;
    }

    .empty-state {
        text-align: center;
        color: var(--design-text-secondary, #6b7280);
        font-style: italic;
        margin-top: var(--design-spacing-3xl, 2rem);
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
        border-radius: var(--design-radius-xl, 1rem);
        padding: var(--design-spacing-md, 0.75rem) var(--design-spacing-lg, 1rem);
        position: relative;
    }

    .bubble.user {
        background-color: var(--design-primary, #4f46e5);
        color: white;
        box-shadow: var(--design-shadow-md, 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06));
        border-bottom-right-radius: var(--design-radius-sm, 0.25rem);
    }

    .bubble.assistant {
        background-color: var(--design-bg-white, white);
        color: var(--design-text-primary, #1f2937);
        box-shadow: var(--design-shadow-xs, 0 1px 2px 0 rgba(0, 0, 0, 0.05));
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-bottom-left-radius: var(--design-radius-sm, 0.25rem);
    }

    .bubble.error {
        background-color: var(--design-error-bg, #fef2f2);
        color: var(--design-error-text, #991b1b);
        border: 1px solid var(--design-error-border, #fca5a5);
        border-bottom-left-radius: var(--design-radius-sm, 0.25rem);
    }

    .role-label {
        font-weight: var(--design-font-weight-bold, 700);
        font-size: var(--design-font-size-sm, 0.75rem);
        margin-bottom: var(--design-spacing-xs, 0.25rem);
        opacity: 0.9;
    }

    .message-body {
        font-size: var(--design-font-size-base, 0.875rem);
        line-height: var(--design-line-height-normal, 1.5);
        word-break: break-word;
    }

    .text-content {
        white-space: pre-wrap;
    }

    /* Streaming cursor */
    .cursor {
        animation: blink 0.8s step-end infinite;
        color: var(--design-primary, #6366f1);
    }

    @keyframes blink {
        50% { opacity: 0; }
    }

    /* Streaming bubble indicator */
    .bubble.streaming {
        border-left: 3px solid var(--design-primary, #6366f1);
    }

    /* Waiting dots (antes de que lleguen tokens) */
    .streaming-waiting {
        display: flex;
        gap: 4px;
        align-items: center;
        padding: 0.25rem 0;
    }

    /* Process log: pasos en tiempo real */
    .process-log {
        display: flex;
        flex-direction: column;
        gap: 2px;
        background: var(--design-bg-gray-50, #f9fafb);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        padding: 0.5rem 0.75rem;
        margin-bottom: 0.5rem;
        font-size: 0.72rem;
        font-family: var(--design-font-mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace);
    }

    .process-step {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 1px 0;
        line-height: 1.4;
    }

    .process-step.done {
        color: var(--design-text-tertiary, #9ca3af);
    }

    .process-step.active {
        color: var(--design-text-secondary, #4b5563);
        font-weight: 500;
    }

    .step-text {
        flex: 1;
    }

    /* Dots compartidos: streaming-waiting y step-pulse */
    .dot {
        display: inline-block;
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: var(--design-primary, #6366f1);
        animation: dot-bounce 1.2s infinite ease-in-out;
    }

    .dot:nth-child(1) { animation-delay: 0s; }
    .dot:nth-child(2) { animation-delay: 0.2s; }
    .dot:nth-child(3) { animation-delay: 0.4s; }

    @keyframes dot-bounce {
        0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
        40% { opacity: 1; transform: scale(1.1); }
    }

    .step-pulse {
        display: inline-flex;
        gap: 3px;
        align-items: center;
        flex-shrink: 0;
    }

    .step-pulse .dot {
        width: 4px;
        height: 4px;
        background: var(--design-primary, #6366f1);
    }

    /* Reasoning Details */
    details.reasoning {
        background-color: var(--design-bg-gray-50, #f9fafb);
        border-radius: var(--design-radius-md, 0.5rem);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        overflow: hidden;
        margin-bottom: var(--design-spacing-sm, 0.5rem);
    }

    details.reasoning summary {
        padding: var(--design-spacing-sm, 0.5rem) var(--design-spacing-md, 0.75rem);
        cursor: pointer;
        background-color: var(--design-bg-gray-100, #f3f4f6);
        font-size: var(--design-font-size-sm, 0.75rem);
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-secondary, #4b5563);
        display: flex;
        align-items: center;
        user-select: none;
    }

    details.reasoning summary:hover {
        background-color: var(--design-border-gray, #e5e7eb);
    }

    details.reasoning .content {
        padding: var(--design-spacing-md, 0.75rem);
        background-color: var(--design-bg-white, white);
        color: var(--design-text-primary, #374151);
        white-space: pre-wrap;
        font-family: var(--design-font-mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace);
        font-size: var(--design-font-size-sm, 0.75rem);
        border-top: 1px solid var(--design-border-gray, #e5e7eb);
    }

    /* Trajectory */
    .trajectory {
        margin-bottom: var(--design-spacing-md, 0.75rem);
    }

    .trajectory-title {
        font-size: var(--design-font-size-sm, 0.75rem);
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-secondary, #6b7280);
        margin-bottom: var(--design-spacing-xs, 0.25rem);
        display: flex;
        align-items: center;
        gap: var(--design-spacing-xs, 0.25rem);
    }

    .step {
        font-size: var(--design-font-size-sm, 0.75rem);
        border-left: 2px solid var(--design-indigo-200, #c7d2fe);
        padding-left: var(--design-spacing-md, 0.75rem);
        margin-bottom: var(--design-spacing-sm, 0.5rem);
        padding-top: var(--design-spacing-xs, 0.25rem);
        padding-bottom: var(--design-spacing-xs, 0.25rem);
    }

    .step-thought {
        color: var(--design-text-secondary, #6b7280);
        font-style: italic;
        margin-bottom: var(--design-spacing-xs, 0.25rem);
    }

    .tool-call {
        font-family: var(--design-font-mono, ui-monospace, SFMono-Regular, monospace);
        color: var(--design-primary, #4f46e5);
        background-color: var(--design-indigo-50, #eef2ff);
        padding: 0.125rem var(--design-spacing-sm, 0.5rem);
        border-radius: var(--design-radius-sm, 0.25rem);
        display: inline-block;
    }

    .observation summary {
        cursor: pointer;
        color: var(--design-text-tertiary, #9ca3af);
        user-select: none;
        margin-top: var(--design-spacing-xs, 0.25rem);
    }

    .observation summary:hover {
        color: var(--design-text-secondary, #4b5563);
    }

    .observation-content {
        margin-top: var(--design-spacing-xs, 0.25rem);
        padding: var(--design-spacing-sm, 0.5rem);
        background-color: var(--design-bg-gray-50, #f9fafb);
        border-radius: var(--design-radius-sm, 0.25rem);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        font-family: var(--design-font-mono, ui-monospace, SFMono-Regular, monospace);
        color: var(--design-text-secondary, #4b5563);
        white-space: pre-wrap;
        max-height: 8rem;
        overflow-y: auto;
    }
`;
