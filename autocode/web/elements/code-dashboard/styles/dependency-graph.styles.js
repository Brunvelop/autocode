/**
 * dependency-graph.styles.js
 * Estilos para el grafo de dependencias con D3 force.
 */
import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const dependencyGraphStyles = css`
    :host {
        display: block;
        width: 100%;
        height: 100%;
        font-family: var(--design-font-family, system-ui, sans-serif);
    }

    /* ===== WRAPPER (flex column: controls + graph-container) ===== */
    .dg-wrapper {
        display: flex;
        flex-direction: column;
        width: 100%;
        height: 100%;
    }

    /* ===== CONTROLS BAR ===== */
    .dg-controls {
        display: flex;
        align-items: center;
        gap: 10px;
        height: 34px;
        min-height: 34px;
        padding: 0 10px;
        background: rgba(15, 23, 42, 0.95);
        border-bottom: 1px solid rgba(255, 255, 255, 0.07);
        flex-shrink: 0;
        overflow: hidden;
    }

    .dg-control-label {
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 11px;
        color: rgba(255, 255, 255, 0.65);
        white-space: nowrap;
        cursor: default;
        flex-shrink: 0;
    }

    .dg-control-icon {
        font-size: 12px;
        line-height: 1;
        user-select: none;
        flex-shrink: 0;
    }

    .dg-control-select {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 4px;
        color: rgba(255, 255, 255, 0.9);
        font-size: 11px;
        font-family: inherit;
        padding: 1px 4px;
        cursor: pointer;
        outline: none;
        transition: background 0.12s, border-color 0.12s;
        min-width: 80px;
    }

    .dg-control-select:hover {
        background: rgba(255, 255, 255, 0.14);
        border-color: rgba(255, 255, 255, 0.3);
    }

    .dg-control-select:focus {
        border-color: rgba(99, 179, 237, 0.7);
        background: rgba(255, 255, 255, 0.12);
    }

    .dg-control-select option {
        background: #1e293b;
        color: white;
    }

    /* ===== TEXT FILTER ===== */
    .dg-control-search {
        position: relative;
        flex-shrink: 1;
        min-width: 0;
    }

    .dg-filter-input {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 4px;
        color: rgba(255, 255, 255, 0.9);
        font-size: 11px;
        font-family: inherit;
        padding: 2px 22px 2px 6px;
        outline: none;
        width: 120px;
        transition: width 0.2s, background 0.12s, border-color 0.12s;
    }

    .dg-filter-input:focus {
        width: 160px;
        border-color: rgba(99, 179, 237, 0.7);
        background: rgba(255, 255, 255, 0.12);
    }

    .dg-filter-input::placeholder {
        color: rgba(255, 255, 255, 0.3);
    }

    .dg-filter-clear {
        position: absolute;
        right: 4px;
        top: 50%;
        transform: translateY(-50%);
        background: none;
        border: none;
        color: rgba(255, 255, 255, 0.45);
        font-size: 10px;
        cursor: pointer;
        padding: 2px 3px;
        line-height: 1;
        border-radius: 2px;
        transition: color 0.1s;
    }

    .dg-filter-clear:hover {
        color: rgba(255, 255, 255, 0.85);
    }

    /* ===== SEPARATOR ===== */
    .dg-controls-separator {
        width: 1px;
        height: 18px;
        background: rgba(255, 255, 255, 0.12);
        flex-shrink: 0;
    }

    .dg-controls-spacer {
        flex: 1;
    }

    /* ===== QUICK FILTER BUTTONS ===== */
    .dg-filter-btn {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 4px;
        color: rgba(255, 255, 255, 0.6);
        font-size: 10px;
        font-family: inherit;
        padding: 2px 7px;
        cursor: pointer;
        transition: all 0.12s;
        white-space: nowrap;
        flex-shrink: 0;
        line-height: 1.4;
    }

    .dg-filter-btn:hover {
        background: rgba(255, 255, 255, 0.12);
        border-color: rgba(255, 255, 255, 0.25);
        color: rgba(255, 255, 255, 0.85);
    }

    .dg-filter-btn.active {
        background: rgba(99, 179, 237, 0.2);
        border-color: rgba(99, 179, 237, 0.5);
        color: rgb(147, 210, 246);
    }

    .dg-filter-reset {
        color: rgba(251, 191, 36, 0.75);
        border-color: rgba(251, 191, 36, 0.3);
        background: rgba(251, 191, 36, 0.07);
    }

    .dg-filter-reset:hover {
        color: rgba(251, 191, 36, 1);
        border-color: rgba(251, 191, 36, 0.55);
        background: rgba(251, 191, 36, 0.15);
    }

    /* ===== MIN CONNECTIONS INPUT ===== */
    .dg-control-min {
        gap: 4px;
    }

    .dg-min-input {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 4px;
        color: rgba(255, 255, 255, 0.9);
        font-size: 11px;
        font-family: inherit;
        padding: 1px 4px;
        width: 38px;
        text-align: center;
        outline: none;
        cursor: text;
        transition: background 0.12s, border-color 0.12s;
        /* Hide spinner arrows */
        -moz-appearance: textfield;
    }

    .dg-min-input::-webkit-outer-spin-button,
    .dg-min-input::-webkit-inner-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }

    .dg-min-input:focus {
        border-color: rgba(99, 179, 237, 0.7);
        background: rgba(255, 255, 255, 0.12);
    }

    /* ===== GRANULARITY TOGGLE (inside controls bar) ===== */
    .dg-granularity-btn {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 4px;
        color: rgba(255, 255, 255, 0.65);
        font-size: 11px;
        font-family: inherit;
        padding: 3px 9px;
        cursor: pointer;
        transition: all 0.12s;
        white-space: nowrap;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .dg-granularity-btn:hover {
        background: rgba(255, 255, 255, 0.12);
        border-color: rgba(255, 255, 255, 0.3);
        color: rgba(255, 255, 255, 0.9);
    }

    .dg-granularity-btn.active {
        background: rgba(99, 102, 241, 0.25);
        border-color: rgba(99, 102, 241, 0.55);
        color: rgb(167, 171, 247);
    }

    /* ===== GRAPH CONTAINER ===== */
    .graph-container {
        position: relative;
        flex: 1;
        min-height: 0;
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
        opacity: 0.85;
    }

    .graph-node:hover circle {
        opacity: 1 !important;
        stroke-width: 3;
    }

    .graph-node.selected circle {
        stroke: var(--design-primary, #4f46e5);
        stroke-width: 3;
        opacity: 1;
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

    /* ===== LINK HIT AREA ===== */
    .graph-link-hit {
        fill: none;
        stroke: transparent;
        stroke-width: 14;
        cursor: crosshair;
    }

    /* ===== NODE TOOLTIP ===== */
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

    /* ===== LINK TOOLTIP ===== */
    .link-tooltip {
        position: absolute;
        pointer-events: none;
        background: var(--design-bg-white, #fff);
        border: 1px solid #e0e7ff;
        border-radius: var(--design-radius-md, 0.5rem);
        padding: 7px 10px;
        box-shadow: var(--design-shadow-lg, 0 10px 15px -3px rgba(0, 0, 0, 0.1));
        font-size: 11px;
        z-index: var(--design-z-tooltip, 110);
        opacity: 0;
        transition: opacity 0.15s;
        max-width: 260px;
        min-width: 140px;
    }

    .link-tooltip.visible {
        opacity: 1;
    }

    .link-tooltip-arrow {
        color: #6366f1;
        font-weight: 700;
        margin: 0 3px;
    }

    .link-tooltip-imports {
        margin-top: 5px;
        padding-top: 5px;
        border-top: 1px solid #e5e7eb;
        display: flex;
        flex-direction: column;
        gap: 2px;
        max-height: 120px;
        overflow-y: auto;
    }

    .link-tooltip-import-row {
        font-family: var(--design-font-mono, monospace);
        font-size: 10px;
        color: var(--design-text-secondary, #4b5563);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .link-tooltip-empty {
        margin-top: 5px;
        font-size: 10px;
        color: var(--design-text-tertiary, #9ca3af);
        font-style: italic;
    }

    /* ===== SHARED TOOLTIP PARTS ===== */
    .tooltip-header {
        font-weight: var(--design-font-weight-bold, 700);
        color: var(--design-text-primary, #1f2937);
        margin-bottom: 4px;
        font-size: 12px;
        display: flex;
        align-items: center;
        gap: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 250px;
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
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 3px;
    }

    .tooltip-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    /* Section divider inside tooltip */
    .tooltip-section {
        font-size: 9px;
        color: var(--design-text-tertiary, #9ca3af);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 6px;
        padding-top: 5px;
        border-top: 1px solid var(--design-border-gray-light, #f3f4f6);
        margin-bottom: 3px;
        grid-column: 1 / -1;
    }

    /* ===== LEGEND (injected via DOM, inside graph-container) ===== */
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
        display: inline-block;
    }

    .legend-line {
        width: 20px;
        height: 2px;
        flex-shrink: 0;
        display: inline-block;
    }

    .legend-line.dashed {
        background: repeating-linear-gradient(
            to right,
            #dc2626 0,
            #dc2626 4px,
            transparent 4px,
            transparent 7px
        );
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
