/**
 * architecture-graph.styles.js
 * Estilos para el grafo de dependencias de arquitectura con D3 force.
 * Sigue el patrón visual de architecture-treemap.styles.js.
 */
import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const architectureGraphStyles = css`
    :host {
        display: block;
        width: 100%;
        height: 100%;
        font-family: var(--design-font-family, system-ui, sans-serif);
    }

    /* ===== CONTAINER ===== */
    .graph-container {
        position: relative;
        width: 100%;
        height: 100%;
        overflow: hidden;
    }

    /* ===== SVG ===== */
    .graph-svg {
        display: block;
        width: 100%;
        height: 100%;
    }

    /* ===== NODES ===== */
    .graph-node {
        cursor: pointer;
    }

    .graph-node circle {
        transition: opacity var(--design-transition-fast, 0.1s),
                    stroke-width var(--design-transition-fast, 0.1s);
        stroke: var(--design-bg-white, #ffffff);
        stroke-width: 2;
    }

    .graph-node:hover circle {
        opacity: 1 !important;
        stroke-width: 3;
    }

    .graph-node.selected circle {
        stroke: var(--design-primary, #4f46e5);
        stroke-width: 3;
    }

    .graph-node.dimmed {
        opacity: 0.2;
    }

    /* ===== NODE LABELS ===== */
    .graph-node-label {
        font-size: 9px;
        fill: var(--design-text-secondary, #6b7280);
        text-anchor: middle;
        pointer-events: none;
        user-select: none;
    }

    /* ===== LINKS ===== */
    .graph-link {
        fill: none;
        stroke: var(--design-border-gray-dark, #d1d5db);
        stroke-width: 1.5;
        stroke-opacity: 0.6;
        transition: stroke-opacity var(--design-transition-fast, 0.1s),
                    stroke var(--design-transition-fast, 0.1s);
    }

    .graph-link.circular {
        stroke: #dc2626;
        stroke-dasharray: 6 3;
        stroke-opacity: 0.8;
        stroke-width: 2;
    }

    .graph-link.highlight-out {
        stroke: #f97316;
        stroke-opacity: 1;
        stroke-width: 2.5;
    }

    .graph-link.highlight-in {
        stroke: #3b82f6;
        stroke-opacity: 1;
        stroke-width: 2.5;
    }

    .graph-link.dimmed {
        stroke-opacity: 0.08;
    }

    /* ===== TOOLTIP ===== */
    .graph-tooltip {
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

    .graph-tooltip.visible {
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

    .tooltip-section-label {
        font-size: 9px;
        color: var(--design-text-tertiary, #9ca3af);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 4px;
        padding-top: 4px;
        border-top: 1px solid var(--design-border-gray-light, #f3f4f6);
        grid-column: 1 / -1;
    }

    /* ===== GRANULARITY TOGGLE ===== */
    .granularity-toggle {
        position: absolute;
        top: 8px;
        right: 8px;
        z-index: 10;
        padding: 4px 10px;
        background: var(--design-bg-white, #fff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        font-size: 11px;
        font-family: inherit;
        color: var(--design-text-secondary, #6b7280);
        cursor: pointer;
        transition: all var(--design-transition-fast, 0.1s);
        box-shadow: var(--design-shadow-xs, 0 1px 2px rgba(0, 0, 0, 0.05));
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .granularity-toggle:hover {
        background: var(--design-bg-gray-50, #f9fafb);
        border-color: var(--design-border-gray-dark, #d1d5db);
        color: var(--design-text-primary, #1f2937);
    }

    .granularity-toggle.active {
        background: var(--design-indigo-50, #eef2ff);
        border-color: var(--design-primary, #4f46e5);
        color: var(--design-primary, #4f46e5);
    }

    /* ===== LEGEND ===== */
    .graph-legend {
        position: absolute;
        bottom: 8px;
        left: 8px;
        z-index: 10;
        padding: 6px 10px;
        background: var(--design-bg-white, #fff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        font-size: 9px;
        color: var(--design-text-secondary, #6b7280);
        box-shadow: var(--design-shadow-xs, 0 1px 2px rgba(0, 0, 0, 0.05));
        display: flex;
        flex-direction: column;
        gap: 4px;
        max-width: 180px;
    }

    .legend-title {
        font-weight: var(--design-font-weight-semibold, 600);
        font-size: 10px;
        color: var(--design-text-primary, #1f2937);
        margin-bottom: 2px;
    }

    .legend-row {
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .legend-color {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        flex-shrink: 0;
        border: 1px solid rgba(0, 0, 0, 0.1);
    }

    .legend-line {
        width: 20px;
        height: 2px;
        flex-shrink: 0;
    }

    .legend-line.dashed {
        background: repeating-linear-gradient(
            to right,
            #dc2626 0,
            #dc2626 4px,
            transparent 4px,
            transparent 7px
        );
        height: 2px;
    }

    .legend-line.solid {
        background: var(--design-border-gray-dark, #d1d5db);
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
`;
