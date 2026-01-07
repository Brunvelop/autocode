/**
 * code-metrics.styles.js
 * Estilos para el componente CodeMetrics (resumen de métricas)
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const codeMetricsStyles = css`
    :host {
        display: block;
    }

    .metrics-container {
        display: flex;
        flex-wrap: wrap;
        gap: var(--design-spacing-md, 0.75rem);
        padding: var(--design-spacing-sm, 0.5rem);
        background: var(--design-bg-secondary, #f9fafb);
        border-radius: var(--design-radius-md, 0.5rem);
    }

    .metric {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-xs, 0.25rem);
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
        background: var(--design-bg-primary, #ffffff);
        border-radius: var(--design-radius-sm, 0.25rem);
        border: 1px solid var(--design-border-color, #e5e7eb);
    }

    .metric-icon {
        font-size: 14px;
    }

    .metric-value {
        font-size: var(--design-font-size-sm, 0.875rem);
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-primary, #1f2937);
        font-family: var(--design-font-mono, monospace);
    }

    .metric-label {
        font-size: var(--design-font-size-xs, 0.75rem);
        color: var(--design-text-secondary, #6b7280);
    }

    /* Language badges */
    .languages {
        display: flex;
        gap: var(--design-spacing-xs, 0.25rem);
    }

    .lang-badge {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 2px 8px;
        border-radius: var(--design-radius-full, 9999px);
        font-size: var(--design-font-size-xs, 0.75rem);
        font-weight: var(--design-font-weight-medium, 500);
    }

    .lang-badge.python {
        background: #3776ab20;
        color: #3776ab;
    }

    .lang-badge.javascript {
        background: #f7df1e20;
        color: #b7a10e;
    }

    .lang-icon {
        font-size: 12px;
    }
`;
