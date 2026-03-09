/**
 * treemap-view.styles.js
 * Estilos para el treemap zoomable anidado.
 */
import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const treemapViewStyles = css`
    :host {
        display: block;
        width: 100%;
        height: 100%;
        font-family: var(--design-font-family, system-ui, sans-serif);
    }

    /* ===== WRAPPER (flex column: header + treemap) ===== */
    .treemap-wrapper {
        display: flex;
        flex-direction: column;
        width: 100%;
        height: 100%;
    }

    /* ===== HEADER BAR — HTML element, always visible ===== */
    .tm-header-bar {
        display: flex;
        align-items: center;
        gap: 8px;
        height: 30px;
        min-height: 30px;
        padding: 0 12px;
        background: rgba(30, 41, 59, 0.9);
        color: white;
        font-size: 12px;
        font-weight: 600;
        flex-shrink: 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        overflow: hidden;
    }

    /* ===== BREADCRUMB SEGMENTS ===== */
    .tm-header-segment {
        background: none;
        border: none;
        color: rgba(255, 255, 255, 0.75);
        font-size: 12px;
        font-weight: 500;
        font-family: inherit;
        padding: 2px 5px;
        border-radius: 3px;
        cursor: pointer;
        transition: background 0.12s, color 0.12s;
        white-space: nowrap;
        flex-shrink: 0;
        line-height: 1.4;
    }

    .tm-header-segment:hover:not(:disabled) {
        background: rgba(255, 255, 255, 0.15);
        color: white;
    }

    .tm-header-segment.current {
        color: white;
        font-weight: 700;
        cursor: default;
        padding: 2px 5px;
    }

    .tm-header-segment:disabled {
        cursor: default;
    }

    .tm-header-separator {
        color: rgba(255, 255, 255, 0.4);
        font-size: 11px;
        user-select: none;
        flex-shrink: 0;
        padding: 0 1px;
    }

    /* ===== CONTROLS BAR — metric selectors ===== */
    .tm-controls {
        display: flex;
        align-items: center;
        gap: 16px;
        height: 28px;
        min-height: 28px;
        padding: 0 12px;
        background: rgba(15, 23, 42, 0.95);
        border-bottom: 1px solid rgba(255,255,255,0.07);
        flex-shrink: 0;
    }

    .tm-control-label {
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 11px;
        color: rgba(255, 255, 255, 0.65);
        white-space: nowrap;
        cursor: default;
    }

    .tm-control-icon {
        font-size: 12px;
        line-height: 1;
        user-select: none;
    }

    .tm-control-select {
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

    .tm-control-select:hover {
        background: rgba(255, 255, 255, 0.14);
        border-color: rgba(255, 255, 255, 0.3);
    }

    .tm-control-select:focus {
        border-color: rgba(99, 179, 237, 0.7);
        background: rgba(255, 255, 255, 0.12);
    }

    .tm-control-select option {
        background: #1e293b;
        color: white;
    }

    /* ===== CONTAINER (holds SVG + tooltip) ===== */
    .treemap-container {
        position: relative;
        flex: 1;
        min-height: 0;
        overflow: hidden;
    }

    /* ===== SVG ===== */
    .treemap-svg {
        display: block;
        width: 100%;
        height: 100%;
    }

    /* ===== DIRECTORY NODES ===== */
    .tm-dir {
        stroke: rgba(255, 255, 255, 0.15);
        stroke-width: 1;
        transition: opacity 0.12s;
    }

    .tm-node:hover > .tm-dir {
        opacity: 0.9;
        stroke: rgba(255, 255, 255, 0.4);
        stroke-width: 1.5;
    }

    /* ===== LEAF NODES (files) ===== */
    .tm-leaf {
        stroke: rgba(255, 255, 255, 0.25);
        stroke-width: 0.75;
        transition: opacity 0.12s;
    }

    .tm-node:hover > .tm-leaf {
        stroke: white;
        stroke-width: 1.5;
        opacity: 1 !important;
    }

    /* ===== DIRECTORY LABELS ===== */
    .tm-dir-label {
        font-size: 11px;
        font-weight: 600;
        fill: rgba(255, 255, 255, 0.92);
        pointer-events: none;
        user-select: none;
    }

    /* ===== LEAF LABELS ===== */
    .tm-leaf-name {
        font-size: 10px;
        font-weight: 600;
        fill: white;
        pointer-events: none;
        user-select: none;
    }

    .tm-leaf-sloc {
        font-size: 9px;
        font-weight: 400;
        fill: rgba(255, 255, 255, 0.75);
        font-family: var(--design-font-mono, monospace);
        pointer-events: none;
        user-select: none;
    }

    /* ===== TOOLTIP ===== */
    .treemap-tooltip {
        position: absolute;
        pointer-events: none;
        background: var(--design-bg-white, #fff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        padding: var(--design-spacing-sm, 0.5rem) var(--design-spacing-md, 0.75rem);
        box-shadow: var(--design-shadow-lg, 0 10px 15px -3px rgba(0,0,0,0.1));
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
`;
