/**
 * treemap-view.styles.js
 * Estilos para el componente de treemap zoomable de arquitectura.
 * Sigue el patrón visual de metrics-chart.styles.js.
 */
import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const treemapViewStyles = css`
    :host {
        display: block;
        width: 100%;
        height: 100%;
        font-family: var(--design-font-family, system-ui, sans-serif);
    }

    /* ===== CONTAINER ===== */
    .treemap-container {
        position: relative;
        width: 100%;
        height: 100%;
        overflow: hidden;
    }

    /* ===== SVG ===== */
    .treemap-svg {
        display: block;
        width: 100%;
        height: 100%;
    }

    /* ===== CELLS ===== */
    .treemap-cell {
        cursor: pointer;
    }

    .treemap-cell rect {
        transition: opacity var(--design-transition-fast, 0.1s);
        stroke: var(--design-bg-white, #ffffff);
        stroke-width: 1.5;
    }

    .treemap-cell:hover rect {
        opacity: 1 !important;
        stroke-width: 2;
    }

    /* ===== LABELS ===== */
    .treemap-label {
        pointer-events: none;
        user-select: none;
    }

    .treemap-label-name {
        font-size: 11px;
        font-weight: var(--design-font-weight-semibold, 600);
        fill: white;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
    }

    .treemap-label-sloc {
        font-size: 9px;
        font-weight: var(--design-font-weight-normal, 400);
        fill: rgba(255, 255, 255, 0.8);
        font-family: var(--design-font-mono, monospace);
    }

    /* ===== TOOLTIP ===== */
    .treemap-tooltip {
        position: absolute;
        pointer-events: none;
        background: var(--design-bg-white, #fff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        padding: var(--design-spacing-sm, 0.5rem) var(--design-spacing-md, 0.75rem);
        box-shadow: var(--design-shadow-lg, 0 10px 15px -3px rgba(0, 0, 0, 0.1));
        font-size: 11px;
        z-index: var(--design-z-tooltip, 110);
        white-space: nowrap;
        opacity: 0;
        transition: opacity 0.15s;
        max-width: 280px;
    }

    .treemap-tooltip.visible {
        opacity: 1;
    }

    .tooltip-header {
        font-weight: var(--design-font-weight-bold, 700);
        color: var(--design-text-primary, #1f2937);
        margin-bottom: 4px;
        font-size: 12px;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .tooltip-path {
        font-size: 10px;
        color: var(--design-text-tertiary, #9ca3af);
        font-family: var(--design-font-mono, monospace);
        margin-bottom: 6px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 250px;
    }

    .tooltip-grid {
        display: grid;
        grid-template-columns: auto auto;
        gap: 2px 12px;
    }

    .tooltip-label {
        color: var(--design-text-secondary, #6b7280);
        font-size: 10px;
    }

    .tooltip-value {
        font-family: var(--design-font-mono, monospace);
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-primary, #1f2937);
        font-size: 10px;
        text-align: right;
    }

    .tooltip-mi-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 2px;
        vertical-align: middle;
    }

    /* ===== EMPTY STATE ===== */
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        min-height: 120px;
        color: var(--design-text-tertiary, #9ca3af);
        gap: var(--design-spacing-sm, 0.5rem);
    }

    .empty-state-icon {
        font-size: 2rem;
        opacity: 0.3;
    }

    .empty-state-text {
        font-size: var(--design-font-size-sm, 0.75rem);
        text-align: center;
    }

    /* ===== SINGLE NODE ===== */
    .single-node {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        min-height: 120px;
        gap: var(--design-spacing-sm, 0.5rem);
        border-radius: var(--design-radius-md, 0.5rem);
        color: white;
        padding: var(--design-spacing-lg, 1rem);
    }

    .single-node-name {
        font-size: 1rem;
        font-weight: var(--design-font-weight-bold, 700);
    }

    .single-node-metrics {
        font-size: var(--design-font-size-sm, 0.75rem);
        opacity: 0.85;
        font-family: var(--design-font-mono, monospace);
    }

    /* ===== DIRECTORY BADGE ===== */
    .dir-badge {
        font-size: 9px;
        fill: rgba(255, 255, 255, 0.7);
        font-family: var(--design-font-mono, monospace);
    }
`;
