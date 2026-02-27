/**
 * commit-plan-node.styles.js
 * Estilos para ghost nodes de planes de commit en el grafo.
 * Diferenciados de commit-node: borde punteado, fondo semi-transparente.
 */
import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const commitPlanNodeStyles = css`
    :host {
        display: block;
    }

    .plan-row {
        display: flex;
        align-items: center;
        padding: 0 var(--design-spacing-sm, 0.5rem);
        cursor: pointer;
        transition: background var(--design-transition-fast, 0.1s);
        border: 1px dashed var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-sm, 0.25rem);
        min-height: 28px;
        height: 28px;
        margin: 1px 2px;
        background: rgba(238, 242, 255, 0.5);
    }

    .plan-row:hover {
        background: rgba(238, 242, 255, 0.85);
        border-color: var(--design-primary, #4f46e5);
    }

    .plan-row.selected {
        background: var(--design-indigo-50, #eef2ff);
        border-color: var(--design-primary, #4f46e5);
        border-style: solid;
    }

    /* ===== PLAN ICON ===== */
    .plan-icon {
        flex-shrink: 0;
        font-size: 12px;
        width: 20px;
        text-align: center;
    }

    /* ===== PLAN INFO — single line ===== */
    .plan-info {
        flex: 1;
        min-width: 0;
        display: flex;
        align-items: center;
        gap: 4px;
        padding-left: 4px;
        overflow: hidden;
    }

    /* Status badges */
    .plan-badge {
        display: inline-flex;
        align-items: center;
        padding: 0 5px;
        border-radius: var(--design-radius-full, 9999px);
        font-size: 8px;
        font-weight: var(--design-font-weight-bold, 700);
        text-transform: uppercase;
        letter-spacing: 0.04em;
        white-space: nowrap;
        line-height: 15px;
        flex-shrink: 0;
    }

    .plan-badge.draft {
        background: #fef3c7;
        color: #92400e;
    }

    .plan-badge.ready {
        background: #dcfce7;
        color: #166534;
    }

    .plan-badge.abandoned {
        background: var(--design-bg-gray-100, #f3f4f6);
        color: var(--design-text-tertiary, #9ca3af);
    }

    .plan-title {
        font-size: 11px;
        color: var(--design-text-primary, #1f2937);
        font-weight: var(--design-font-weight-medium, 500);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        flex: 1;
        min-width: 0;
        font-style: italic;
    }

    .plan-tasks {
        font-size: 10px;
        color: var(--design-text-tertiary, #9ca3af);
        white-space: nowrap;
        flex-shrink: 0;
        font-family: var(--design-font-mono, monospace);
    }
`;
