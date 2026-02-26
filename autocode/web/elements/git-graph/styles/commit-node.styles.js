/**
 * commit-node.styles.js
 * Estilos compactos para cada fila de commit en el grafo
 */
import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const commitNodeStyles = css`
    :host {
        display: block;
    }

    .commit-row {
        display: flex;
        align-items: center;
        padding: 0 var(--design-spacing-sm, 0.5rem);
        cursor: pointer;
        transition: background var(--design-transition-fast, 0.1s);
        border-bottom: 1px solid transparent;
        min-height: 28px;
        height: 28px;
    }

    .commit-row:hover {
        background: var(--design-bg-gray-50, #f9fafb);
    }

    .commit-row.selected {
        background: var(--design-indigo-50, #eef2ff);
        border-bottom-color: var(--design-indigo-200, #c7d2fe);
    }

    /* ===== GRAPH LANE (SVG area) ===== */
    .graph-lane {
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .graph-lane svg {
        display: block;
    }

    /* ===== COMMIT INFO — single line ===== */
    .commit-info {
        flex: 1;
        min-width: 0;
        display: flex;
        align-items: center;
        gap: 4px;
        padding-left: 4px;
        overflow: hidden;
    }

    /* Badges inline */
    .branch-badge {
        display: inline-flex;
        align-items: center;
        gap: 2px;
        padding: 0 4px;
        border-radius: var(--design-radius-full, 9999px);
        font-size: 9px;
        font-weight: var(--design-font-weight-semibold, 600);
        font-family: var(--design-font-mono, monospace);
        white-space: nowrap;
        line-height: 16px;
        flex-shrink: 0;
    }

    .branch-badge.current {
        background: var(--design-indigo-100, #e0e7ff);
        color: var(--design-indigo-700, #4338ca);
    }

    .branch-badge.other {
        background: var(--design-bg-gray-100, #f3f4f6);
        color: var(--design-text-secondary, #6b7280);
    }

    .tag-badge {
        display: inline-flex;
        align-items: center;
        gap: 2px;
        padding: 0 4px;
        border-radius: var(--design-radius-full, 9999px);
        font-size: 9px;
        font-weight: var(--design-font-weight-semibold, 600);
        font-family: var(--design-font-mono, monospace);
        background: #fef3c7;
        color: #92400e;
        white-space: nowrap;
        line-height: 16px;
        flex-shrink: 0;
    }

    .commit-hash {
        font-family: var(--design-font-mono, monospace);
        font-size: 10px;
        color: var(--design-text-secondary, #6b7280);
        font-weight: var(--design-font-weight-medium, 500);
        flex-shrink: 0;
    }

    .commit-message {
        font-size: 11px;
        color: var(--design-text-primary, #1f2937);
        font-weight: var(--design-font-weight-medium, 500);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        flex: 1;
        min-width: 0;
    }

    .commit-date {
        font-size: 10px;
        color: var(--design-text-tertiary, #9ca3af);
        white-space: nowrap;
        flex-shrink: 0;
    }

    .merge-indicator {
        font-size: 8px;
        padding: 0 3px;
        border-radius: var(--design-radius-sm, 0.25rem);
        background: #dbeafe;
        color: #1e40af;
        font-weight: var(--design-font-weight-medium, 500);
        line-height: 14px;
        flex-shrink: 0;
    }
`;
