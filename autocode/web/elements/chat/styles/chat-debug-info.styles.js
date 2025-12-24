/**
 * chat-debug-info.styles.js
 * Estilos específicos para el componente ChatDebugInfo
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const chatDebugInfoStyles = css`
    :host {
        display: block;
        font-family: var(--design-font-family, system-ui, -apple-system, sans-serif);
    }

    details {
        background-color: rgba(249, 250, 251, 0.5);
        border-radius: var(--design-radius-md, 0.5rem);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        overflow: hidden;
        margin-top: var(--design-spacing-lg, 1rem);
        font-size: var(--design-font-size-sm, 0.75rem);
    }

    summary {
        padding: var(--design-spacing-sm, 0.5rem) var(--design-spacing-md, 0.75rem);
        cursor: pointer;
        transition: background-color var(--design-transition-base, 0.2s);
        display: flex;
        align-items: center;
        user-select: none;
        color: var(--design-text-secondary, #6b7280);
        gap: var(--design-spacing-sm, 0.5rem);
    }

    summary:hover {
        background-color: var(--design-bg-gray-100, #f3f4f6);
    }

    .summary-content {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
    }

    .separator {
        color: var(--design-border-gray-dark, #d1d5db);
    }

    .model-badge {
        font-family: var(--design-font-mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace);
        color: var(--design-primary, #4f46e5);
        background-color: var(--design-indigo-50, #eef2ff);
        padding: 0.125rem var(--design-spacing-sm, 0.375rem);
        border-radius: var(--design-radius-sm, 0.25rem);
        border: 1px solid var(--design-indigo-200, #c7d2fe);
    }

    .tokens-badge {
        font-family: var(--design-font-mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace);
        color: var(--design-text-secondary, #4b5563);
        background-color: var(--design-bg-gray-100, #f3f4f6);
        padding: 0.125rem var(--design-spacing-sm, 0.375rem);
        border-radius: var(--design-radius-sm, 0.25rem);
        border: 1px solid var(--design-border-gray, #e5e7eb);
    }

    .cost-badge {
        font-family: var(--design-font-mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace);
        color: var(--design-emerald-700, #047857);
        background-color: var(--design-emerald-50, #ecfdf5);
        padding: 0.125rem var(--design-spacing-sm, 0.375rem);
        border-radius: var(--design-radius-sm, 0.25rem);
        border: 1px solid var(--design-emerald-200, #a7f3d0);
    }

    .chevron {
        width: 1rem;
        height: 1rem;
        margin-left: auto;
        transform: rotate(0deg);
        transition: transform var(--design-transition-base, 0.2s);
        color: var(--design-text-tertiary, #9ca3af);
    }

    details[open] .chevron {
        transform: rotate(180deg);
    }

    .content {
        border-top: 1px solid var(--design-border-gray, #e5e7eb);
        display: flex;
        flex-direction: column;
    }

    /* Tabs Navigation */
    .tabs {
        display: flex;
        border-bottom: 1px solid var(--design-border-gray, #e5e7eb);
        background-color: var(--design-bg-gray-50, #f9fafb);
        overflow-x: auto;
    }

    .tab-btn {
        appearance: none;
        background: none;
        border: none;
        padding: var(--design-spacing-sm, 0.5rem) var(--design-spacing-md, 0.75rem);
        font-size: var(--design-font-size-xs, 0.7rem);
        font-weight: 500;
        color: var(--design-text-secondary, #6b7280);
        cursor: pointer;
        border-bottom: 2px solid transparent;
        transition: all 0.2s;
        white-space: nowrap;
    }

    .tab-btn:hover {
        color: var(--design-text-primary, #374151);
        background-color: var(--design-bg-gray-100, #f3f4f6);
    }

    .tab-btn.active {
        color: var(--design-primary, #4f46e5);
        border-bottom-color: var(--design-primary, #4f46e5);
        background-color: white;
    }

    .tab-content {
        padding: var(--design-spacing-md, 0.75rem);
        max-height: 400px;
        overflow-y: auto;
    }

    /* Overview Section */
    .overview-section {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-md, 0.75rem);
    }

    .reasoning-box {
        background-color: var(--design-bg-white, #ffffff);
        border: 1px solid var(--design-indigo-100, #e0e7ff);
        border-radius: var(--design-radius-sm, 0.25rem);
        padding: var(--design-spacing-md, 0.75rem);
    }
    
    .reasoning-label {
        color: var(--design-primary, #4f46e5);
        font-weight: 600;
        margin-bottom: var(--design-spacing-xs, 0.25rem);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .reasoning-text {
        color: var(--design-text-primary, #374151);
        line-height: 1.5;
        white-space: pre-wrap;
    }

    .reasoning-hint {
        margin-top: var(--design-spacing-sm, 0.5rem);
        padding-top: var(--design-spacing-sm, 0.5rem);
        border-top: 1px dashed var(--design-border-gray, #e5e7eb);
        font-size: var(--design-font-size-xs, 0.65rem);
        color: var(--design-text-tertiary, #9ca3af);
        font-style: italic;
    }

    /* Metrics Grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: var(--design-spacing-sm, 0.5rem);
    }

    @media (min-width: 640px) {
        .metrics-grid {
            grid-template-columns: repeat(4, 1fr);
        }
    }

    .metric-card {
        background-color: var(--design-bg-white, white);
        padding: var(--design-spacing-sm, 0.5rem);
        border-radius: var(--design-radius-sm, 0.25rem);
        border: 1px solid var(--design-bg-gray-100, #f3f4f6);
    }

    .metric-label {
        font-size: var(--design-font-size-xs, 0.625rem);
        color: var(--design-text-tertiary, #9ca3af);
        text-transform: uppercase;
    }

    .metric-value {
        font-family: var(--design-font-mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace);
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-primary, #374151);
    }

    .metric-value.total {
        font-weight: var(--design-font-weight-bold, 700);
        color: var(--design-primary, #4f46e5);
    }

    .metric-value.model {
        color: var(--design-text-secondary, #4b5563);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .metric-value.cost {
        color: var(--design-emerald-700, #047857);
    }

    .metric-card.full-width {
        grid-column: 1 / -1;
    }

    /* Trajectory Section */
    .trajectory-list {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-md, 0.75rem);
        position: relative;
    }

    .trajectory-step {
        background-color: white;
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-sm, 0.25rem);
        overflow: hidden;
    }

    .step-header {
        background-color: var(--design-bg-gray-50, #f9fafb);
        padding: var(--design-spacing-sm, 0.5rem);
        border-bottom: 1px solid var(--design-border-gray, #e5e7eb);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .step-tool {
        font-family: var(--design-font-mono, monospace);
        color: var(--design-primary, #4f46e5);
        font-weight: 600;
    }

    .step-body {
        padding: var(--design-spacing-sm, 0.5rem);
        font-size: var(--design-font-size-xs, 0.7rem);
    }

    .step-thought {
        font-style: italic;
        color: var(--design-text-secondary, #6b7280);
        margin-bottom: var(--design-spacing-sm, 0.5rem);
        padding-bottom: var(--design-spacing-sm, 0.5rem);
        border-bottom: 1px dashed var(--design-border-gray, #e5e7eb);
    }

    .step-input, .step-output {
        margin-top: 0.25rem;
    }

    .label {
        font-weight: 600;
        color: var(--design-text-tertiary, #9ca3af);
        font-size: 0.6rem;
        text-transform: uppercase;
    }

    /* History Section */
    .history-list {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-sm, 0.5rem);
    }

    .history-item {
        padding: var(--design-spacing-sm, 0.5rem);
        border-radius: var(--design-radius-sm, 0.25rem);
        background-color: white;
        border: 1px solid var(--design-border-gray, #e5e7eb);
    }

    .history-item.user {
        border-left: 3px solid var(--design-indigo-400, #818cf8);
    }

    .history-item.assistant {
        border-left: 3px solid var(--design-emerald-400, #34d399);
    }

    .history-role {
        font-weight: 600;
        font-size: 0.65rem;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
        color: var(--design-text-tertiary, #9ca3af);
    }

    .history-content {
        white-space: pre-wrap;
        color: var(--design-text-secondary, #4b5563);
    }

    /* JSON Viewer */
    .json-section {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-xs, 0.25rem);
    }

    .json-content {
        background-color: var(--design-bg-gray-900, #111827);
        color: var(--design-text-light, #f3f4f6);
        padding: var(--design-spacing-md, 0.75rem);
        border-radius: var(--design-radius-md, 0.5rem);
        overflow-x: auto;
        font-family: var(--design-font-mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace);
        font-size: var(--design-font-size-xs, 0.625rem);
        line-height: var(--design-line-height-relaxed, 1.6);
        white-space: pre;
    }

    /* History LM Calls Section */
    .history-header {
        font-weight: 600;
        color: var(--design-text-secondary, #6b7280);
        padding-bottom: var(--design-spacing-sm, 0.5rem);
        border-bottom: 1px solid var(--design-border-gray, #e5e7eb);
        margin-bottom: var(--design-spacing-sm, 0.5rem);
    }

    .history-item.lm-call {
        border-left: 3px solid var(--design-amber-400, #fbbf24);
    }

    .history-call-header {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        flex-wrap: wrap;
    }

    .call-number {
        font-weight: 600;
        color: var(--design-text-primary, #374151);
    }

    .call-model {
        font-family: var(--design-font-mono, monospace);
        font-size: 0.65rem;
        color: var(--design-primary, #4f46e5);
        background-color: var(--design-indigo-50, #eef2ff);
        padding: 0.125rem 0.375rem;
        border-radius: var(--design-radius-sm, 0.25rem);
    }

    .call-tokens {
        font-family: var(--design-font-mono, monospace);
        font-size: 0.65rem;
        color: var(--design-text-tertiary, #9ca3af);
    }

    .call-cost {
        font-family: var(--design-font-mono, monospace);
        font-size: 0.65rem;
        color: var(--design-emerald-700, #047857);
        background-color: var(--design-emerald-50, #ecfdf5);
        padding: 0.125rem 0.375rem;
        border-radius: var(--design-radius-sm, 0.25rem);
    }

    .call-details {
        margin-top: var(--design-spacing-sm, 0.5rem);
    }

    .call-details summary {
        padding: var(--design-spacing-xs, 0.25rem) 0;
        font-size: 0.65rem;
        color: var(--design-primary, #4f46e5);
        cursor: pointer;
    }

    .call-content {
        margin-top: var(--design-spacing-sm, 0.5rem);
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-sm, 0.5rem);
    }

    .call-section {
        background-color: var(--design-bg-gray-50, #f9fafb);
        border-radius: var(--design-radius-sm, 0.25rem);
        padding: var(--design-spacing-sm, 0.5rem);
    }

    .call-section-label {
        font-weight: 600;
        font-size: 0.6rem;
        text-transform: uppercase;
        color: var(--design-text-tertiary, #9ca3af);
        margin-bottom: var(--design-spacing-xs, 0.25rem);
    }

    .prompt-msg {
        padding: var(--design-spacing-xs, 0.25rem);
        margin-bottom: var(--design-spacing-xs, 0.25rem);
        border-radius: var(--design-radius-sm, 0.25rem);
        font-size: 0.65rem;
        line-height: 1.4;
    }

    .prompt-msg.system {
        background-color: var(--design-amber-50, #fffbeb);
        border-left: 2px solid var(--design-amber-400, #fbbf24);
    }

    .prompt-msg.user {
        background-color: var(--design-indigo-50, #eef2ff);
        border-left: 2px solid var(--design-indigo-400, #818cf8);
    }

    .prompt-msg.assistant {
        background-color: var(--design-emerald-50, #ecfdf5);
        border-left: 2px solid var(--design-emerald-400, #34d399);
    }

    .prompt-text, .output-text {
        font-family: var(--design-font-mono, monospace);
        font-size: 0.6rem;
        white-space: pre-wrap;
        word-break: break-word;
        max-height: 150px;
        overflow-y: auto;
        margin: 0;
    }

    .output-item {
        position: relative;
    }

    .output-num {
        position: absolute;
        top: 0.25rem;
        right: 0.25rem;
        font-size: 0.55rem;
        color: var(--design-text-tertiary, #9ca3af);
        background-color: white;
        padding: 0.125rem 0.25rem;
        border-radius: var(--design-radius-sm, 0.25rem);
    }
`;
