/**
 * metrics-chart.styles.js
 * Estilos para el componente de gráfica temporal de métricas.
 */
import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const metricsChartStyles = css`
    :host {
        display: block;
        font-family: var(--design-font-family, system-ui, sans-serif);
    }

    .chart-container {
        background: var(--design-bg-white, #fff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        overflow: hidden;
    }

    /* ===== HEADER ===== */
    .chart-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: var(--design-spacing-sm, 0.5rem) var(--design-spacing-md, 0.75rem);
        border-bottom: 1px solid var(--design-border-gray-light, #f3f4f6);
    }

    .chart-title {
        font-size: var(--design-font-size-sm, 0.75rem);
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-secondary, #6b7280);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: flex;
        align-items: center;
        gap: var(--design-spacing-xs, 0.25rem);
    }

    .chart-info {
        font-size: 10px;
        color: var(--design-text-tertiary, #9ca3af);
    }

    /* ===== METRIC TOGGLES ===== */
    .toggles-container {
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-md, 0.75rem);
        border-bottom: 1px solid var(--design-border-gray-light, #f3f4f6);
    }

    .toggle-group {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        align-items: center;
    }

    .toggle-group-label {
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--design-text-tertiary, #9ca3af);
        font-weight: var(--design-font-weight-semibold, 600);
        margin-right: 4px;
        min-width: 55px;
    }

    .metric-toggle {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        padding: 2px 6px;
        border-radius: var(--design-radius-sm, 0.25rem);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        background: transparent;
        cursor: pointer;
        font-size: 10px;
        font-family: var(--design-font-family, system-ui, sans-serif);
        color: var(--design-text-secondary, #6b7280);
        transition: all var(--design-transition-fast, 0.1s);
        line-height: 1.2;
    }

    .metric-toggle:hover {
        border-color: var(--design-text-tertiary, #9ca3af);
    }

    .metric-toggle.active {
        color: white;
        border-color: transparent;
    }

    .metric-toggle .color-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    /* ===== CHART AREA ===== */
    .chart-area {
        position: relative;
        padding: var(--design-spacing-sm, 0.5rem);
        min-height: 200px;
    }

    .chart-svg {
        display: block;
        width: 100%;
    }

    /* D3 axis styles inside Shadow DOM */
    .chart-svg .axis text {
        font-size: 10px;
        font-family: var(--design-font-mono, monospace);
        fill: var(--design-text-tertiary, #9ca3af);
    }

    .chart-svg .axis line,
    .chart-svg .axis path {
        stroke: var(--design-border-gray-light, #f3f4f6);
    }

    .chart-svg .grid line {
        stroke: var(--design-border-gray-light, #f3f4f6);
        stroke-dasharray: 2,3;
    }

    .chart-svg .grid path {
        stroke: none;
    }

    .chart-svg .metric-line {
        fill: none;
        stroke-width: 2;
        stroke-linejoin: round;
        stroke-linecap: round;
    }

    .chart-svg .metric-dot {
        stroke: white;
        stroke-width: 1.5;
    }

    .chart-svg .metric-area {
        opacity: 0.08;
    }

    /* ===== TOOLTIP ===== */
    .chart-tooltip {
        position: absolute;
        pointer-events: none;
        background: var(--design-bg-white, #fff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
        box-shadow: var(--design-shadow-md, 0 4px 6px rgba(0,0,0,0.1));
        font-size: 11px;
        z-index: 20;
        white-space: nowrap;
        opacity: 0;
        transition: opacity 0.15s;
    }

    .chart-tooltip.visible {
        opacity: 1;
    }

    .tooltip-header {
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-primary, #1f2937);
        margin-bottom: 2px;
        font-family: var(--design-font-mono, monospace);
        font-size: 10px;
    }

    .tooltip-row {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 1px 0;
    }

    .tooltip-color {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    .tooltip-label {
        color: var(--design-text-secondary, #6b7280);
    }

    .tooltip-value {
        font-family: var(--design-font-mono, monospace);
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-primary, #1f2937);
        margin-left: auto;
        padding-left: 8px;
    }

    /* ===== HOVER LINE ===== */
    .chart-svg .hover-line {
        stroke: var(--design-border-gray-dark, #d1d5db);
        stroke-width: 1;
        stroke-dasharray: 3,3;
        opacity: 0;
    }

    /* ===== EMPTY STATE ===== */
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: var(--design-spacing-2xl, 1.5rem);
        color: var(--design-text-tertiary, #9ca3af);
        gap: var(--design-spacing-sm, 0.5rem);
        min-height: 180px;
    }

    .empty-state-icon {
        font-size: 1.5rem;
        opacity: 0.4;
    }

    .empty-state-text {
        font-size: 12px;
        text-align: center;
    }

    /* ===== LOADING ===== */
    .loading-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: var(--design-spacing-2xl, 1.5rem);
        color: var(--design-text-secondary, #6b7280);
        gap: var(--design-spacing-sm, 0.5rem);
        min-height: 180px;
    }

    .spinner-sm {
        width: 20px;
        height: 20px;
        border: 2px solid var(--design-border-gray, #e5e7eb);
        border-top-color: var(--design-primary, #4f46e5);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    /* ===== TOGGLE GROUPS SPACING ===== */
    .toggle-groups {
        display: flex;
        flex-direction: column;
        gap: 3px;
    }
`;
