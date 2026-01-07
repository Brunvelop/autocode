/**
 * code-node.styles.js
 * Estilos para el componente CodeNode (nodo individual del árbol)
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const codeNodeStyles = css`
    :host {
        display: block;
    }

    .node {
        display: flex;
        flex-direction: column;
    }

    .node-row {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-xs, 0.25rem);
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
        border-radius: var(--design-radius-sm, 0.25rem);
        cursor: pointer;
        transition: background var(--design-transition-fast, 0.15s);
        user-select: none;
    }

    .node-row:hover {
        background: var(--design-bg-secondary, #f9fafb);
    }

    .node-row.selected {
        background: var(--design-primary-light, #eef2ff);
    }

    /* Expand/collapse button */
    .expand-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 16px;
        height: 16px;
        padding: 0;
        background: transparent;
        border: none;
        color: var(--design-text-tertiary, #9ca3af);
        cursor: pointer;
        font-size: 10px;
        transition: transform var(--design-transition-fast, 0.15s);
    }

    .expand-btn:hover {
        color: var(--design-text-secondary, #6b7280);
    }

    .expand-btn.expanded {
        transform: rotate(90deg);
    }

    .expand-placeholder {
        width: 16px;
        height: 16px;
    }

    /* Icon */
    .node-icon {
        font-size: 14px;
        flex-shrink: 0;
    }

    /* Name */
    .node-name {
        flex: 1;
        font-size: var(--design-font-size-sm, 0.875rem);
        color: var(--design-text-primary, #1f2937);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Params inline for functions */
    .node-params {
        font-size: var(--design-font-size-xs, 0.75rem);
        color: var(--design-text-tertiary, #9ca3af);
        font-family: var(--design-font-mono, monospace);
    }

    /* Decorators */
    .node-decorators {
        display: flex;
        gap: 2px;
        margin-right: var(--design-spacing-xs, 0.25rem);
    }

    .decorator-badge {
        font-size: 9px;
        padding: 1px 4px;
        background: var(--design-warning-bg, #fef3c7);
        color: var(--design-warning-text, #92400e);
        border-radius: var(--design-radius-sm, 0.25rem);
        font-family: var(--design-font-mono, monospace);
    }

    /* LOC badge */
    .loc-badge {
        font-size: var(--design-font-size-xs, 0.75rem);
        padding: 1px 6px;
        border-radius: var(--design-radius-sm, 0.25rem);
        font-family: var(--design-font-mono, monospace);
        background: var(--design-bg-tertiary, #f3f4f6);
        color: var(--design-text-tertiary, #9ca3af);
    }

    .loc-badge.large {
        background: var(--design-error-bg, #fee2e2);
        color: var(--design-error-text, #991b1b);
    }

    .loc-badge.medium {
        background: var(--design-warning-bg, #fef3c7);
        color: var(--design-warning-text, #92400e);
    }

    /* Children container */
    .node-children {
        margin-left: 16px;
        padding-left: var(--design-spacing-sm, 0.5rem);
        border-left: 1px solid var(--design-border-color, #e5e7eb);
    }

    /* Type-specific colors for icons */
    .icon-directory { color: #f59e0b; }
    .icon-file-python { color: #3776ab; }
    .icon-file-javascript { color: #f7df1e; }
    .icon-file-default { color: #6b7280; }
    .icon-class { color: #8b5cf6; }
    .icon-function { color: #10b981; }
    .icon-method { color: #06b6d4; }
    .icon-import { color: #6366f1; }
    .icon-variable { color: #f97316; }

    /* Async indicator */
    .async-badge {
        font-size: 9px;
        padding: 1px 4px;
        background: var(--design-primary-light, #eef2ff);
        color: var(--design-primary, #4f46e5);
        border-radius: var(--design-radius-sm, 0.25rem);
    }
`;
