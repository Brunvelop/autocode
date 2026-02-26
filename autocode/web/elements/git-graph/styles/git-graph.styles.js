/**
 * git-graph.styles.js
 * Estilos para el componente principal GitGraph
 */
import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const gitGraphStyles = css`
    :host {
        display: block;
        font-family: var(--design-font-family, system-ui, sans-serif);
        height: 100%;
        overflow: hidden;
    }

    .graph-container {
        display: flex;
        flex-direction: column;
        height: 100%;
        background: var(--design-bg-white, #ffffff);
    }

    /* ===== HEADER ===== */
    .graph-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-lg, 1rem);
        border-bottom: 1px solid var(--design-border-gray, #e5e7eb);
        flex-shrink: 0;
        height: 36px;
        box-sizing: border-box;
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
    }

    .header-title {
        font-size: var(--design-font-size-sm, 0.875rem);
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-primary, #1f2937);
        margin: 0;
    }

    .header-title-icon {
        font-size: 1rem;
    }

    .header-actions {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-xs, 0.25rem);
    }

    .branch-select {
        padding: 2px var(--design-spacing-xs, 0.25rem);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        background: var(--design-bg-white, #ffffff);
        font-size: 11px;
        font-family: var(--design-font-mono, monospace);
        color: var(--design-text-primary, #1f2937);
        cursor: pointer;
        outline: none;
        max-width: 150px;
    }

    .branch-select:focus {
        border-color: var(--design-primary, #4f46e5);
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.15);
    }

    .action-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2px 6px;
        background: transparent;
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        color: var(--design-text-secondary, #6b7280);
        font-size: 12px;
        cursor: pointer;
        transition: all var(--design-transition-fast, 0.1s);
        line-height: 1;
    }

    .action-btn:hover {
        background: var(--design-bg-gray-50, #f9fafb);
        color: var(--design-text-primary, #1f2937);
        border-color: var(--design-primary, #4f46e5);
    }

    .action-btn.active {
        background: var(--design-indigo-50, #eef2ff);
        border-color: var(--design-primary, #4f46e5);
        color: var(--design-primary, #4f46e5);
    }

    /* ===== MAIN CONTENT ===== */
    .graph-body {
        display: flex;
        flex: 1;
        overflow: hidden;
    }

    /* ===== GRAPH PANEL (LEFT) — narrow, collapsible ===== */
    .graph-panel {
        width: 320px;
        flex-shrink: 0;
        overflow-y: auto;
        overflow-x: hidden;
        border-right: 1px solid var(--design-border-gray, #e5e7eb);
        transition: width 0.2s ease, min-width 0.2s ease;
        position: relative;
    }

    .graph-panel.collapsed {
        width: 0;
        min-width: 0;
        overflow: hidden;
        border-right: none;
    }

    .commit-list {
        display: flex;
        flex-direction: column;
    }

    /* ===== COLLAPSE TOGGLE ===== */
    .panel-toggle {
        position: absolute;
        top: 50%;
        right: -14px;
        transform: translateY(-50%);
        z-index: 10;
        width: 14px;
        height: 40px;
        background: var(--design-bg-white, #fff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-left: none;
        border-radius: 0 6px 6px 0;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--design-text-tertiary, #9ca3af);
        font-size: 9px;
        transition: all 0.15s;
        padding: 0;
    }

    .panel-toggle:hover {
        color: var(--design-primary, #4f46e5);
        background: var(--design-indigo-50, #eef2ff);
    }

    /* Toggle when panel is collapsed — shown in the detail area */
    .panel-toggle-collapsed {
        position: absolute;
        top: 50%;
        left: 0;
        transform: translateY(-50%);
        z-index: 10;
        width: 14px;
        height: 40px;
        background: var(--design-bg-white, #fff);
        border: 1px solid var(--design-border-gray, #e5e7eb);
        border-left: none;
        border-radius: 0 6px 6px 0;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--design-text-tertiary, #9ca3af);
        font-size: 9px;
        transition: all 0.15s;
        padding: 0;
    }

    .panel-toggle-collapsed:hover {
        color: var(--design-primary, #4f46e5);
        background: var(--design-indigo-50, #eef2ff);
    }

    /* ===== DETAIL PANEL (RIGHT) — takes remaining space ===== */
    .detail-panel {
        flex: 1;
        min-width: 0;
        overflow-y: auto;
        background: var(--design-bg-gray-50, #f9fafb);
        position: relative;
    }

    .detail-placeholder {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: var(--design-text-tertiary, #9ca3af);
        gap: var(--design-spacing-sm, 0.5rem);
        padding: var(--design-spacing-lg, 1rem);
        text-align: center;
    }

    .detail-placeholder-icon {
        font-size: 2rem;
        opacity: 0.3;
    }

    .detail-placeholder-text {
        font-size: var(--design-font-size-sm, 0.75rem);
    }

    /* ===== LOAD MORE ===== */
    .load-more {
        display: flex;
        justify-content: center;
        padding: var(--design-spacing-xs, 0.25rem);
    }

    .load-more-btn {
        padding: 2px var(--design-spacing-md, 0.75rem);
        background: transparent;
        border: 1px dashed var(--design-border-gray-dark, #d1d5db);
        border-radius: var(--design-radius-md, 0.5rem);
        color: var(--design-text-secondary, #6b7280);
        font-size: 11px;
        cursor: pointer;
        transition: all var(--design-transition-fast, 0.1s);
    }

    .load-more-btn:hover {
        border-color: var(--design-primary, #4f46e5);
        color: var(--design-primary, #4f46e5);
        background: var(--design-indigo-50, #eef2ff);
    }

    /* ===== STATES ===== */
    .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        gap: var(--design-spacing-md, 0.75rem);
        color: var(--design-text-secondary, #6b7280);
        font-size: 12px;
    }

    .spinner {
        width: 24px;
        height: 24px;
        border: 3px solid var(--design-border-gray, #e5e7eb);
        border-top-color: var(--design-primary, #4f46e5);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    .error-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        gap: var(--design-spacing-sm, 0.5rem);
        padding: var(--design-spacing-lg, 1rem);
    }

    .error-box {
        padding: var(--design-spacing-sm, 0.5rem) var(--design-spacing-md, 0.75rem);
        background: var(--design-error-bg, #fef2f2);
        border: 1px solid var(--design-error-border, #fca5a5);
        border-radius: var(--design-radius-md, 0.5rem);
        color: var(--design-error-text, #991b1b);
        font-size: 11px;
        text-align: center;
        max-width: 280px;
    }

    .retry-btn {
        margin-top: var(--design-spacing-xs, 0.25rem);
        padding: 2px var(--design-spacing-md, 0.75rem);
        background: var(--design-error-text, #991b1b);
        color: white;
        border: none;
        border-radius: var(--design-radius-md, 0.5rem);
        cursor: pointer;
        font-size: 11px;
    }

    .retry-btn:hover {
        opacity: 0.9;
    }

    /* ===== RESPONSIVE ===== */
    @media (max-width: 768px) {
        .graph-body {
            flex-direction: column;
        }
        .graph-panel {
            width: 100%;
            max-height: 200px;
            border-right: none;
            border-bottom: 1px solid var(--design-border-gray, #e5e7eb);
        }
        .graph-panel.collapsed {
            max-height: 0;
        }
        .detail-panel {
            flex: 1;
        }
    }
`;
