/**
 * working-changes-node.styles.js
 * Estilos para el nodo "Working Changes" (presente) en el grafo git.
 * Representa el estado actual del working directory entre los planes (futuro) y commits (pasado).
 */
import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const workingChangesNodeStyles = css`
    :host {
        display: block;
    }

    .wc-row {
        display: flex;
        align-items: center;
        padding: 0 var(--design-spacing-sm, 0.5rem);
        cursor: pointer;
        transition: background var(--design-transition-fast, 0.1s), opacity var(--design-transition-fast, 0.1s);
        border: 1px dashed var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-sm, 0.25rem);
        min-height: 28px;
        height: 28px;
        margin: 1px 2px;
    }

    /* ===== ESTADO CLEAN ===== */
    .wc-row.clean {
        background: transparent;
        border-color: #e5e7eb;
        opacity: 0.6;
    }

    .wc-row.clean:hover {
        opacity: 0.9;
        background: rgba(249, 250, 251, 0.5);
    }

    /* ===== ESTADO DIRTY ===== */
    .wc-row.dirty {
        background: rgba(254, 243, 199, 0.4);
        border-color: #f59e0b;
    }

    .wc-row.dirty:hover {
        background: rgba(254, 243, 199, 0.7);
    }

    /* ===== ESTADO ALL-STAGED (todo staged, listo para commit) ===== */
    .wc-row.all-staged {
        background: rgba(220, 252, 231, 0.4);
        border-color: #22c55e;
    }

    .wc-row.all-staged:hover {
        background: rgba(220, 252, 231, 0.7);
    }

    /* ===== ESTADO SELECTED ===== */
    .wc-row.selected {
        border-style: solid;
        opacity: 1;
    }

    .wc-row.selected.clean {
        border-color: #9ca3af;
        background: rgba(243, 244, 246, 0.5);
    }

    .wc-row.selected.dirty {
        border-color: #d97706;
        background: rgba(254, 243, 199, 0.7);
    }

    .wc-row.selected.all-staged {
        border-color: #16a34a;
        background: rgba(220, 252, 231, 0.7);
    }

    /* ===== ICONO ===== */
    .wc-icon {
        flex-shrink: 0;
        font-size: 12px;
        width: 20px;
        text-align: center;
    }

    /* ===== INFO — single line ===== */
    .wc-info {
        flex: 1;
        min-width: 0;
        display: flex;
        align-items: center;
        gap: 4px;
        padding-left: 4px;
        overflow: hidden;
    }

    .wc-label {
        font-size: 11px;
        color: var(--design-text-secondary, #6b7280);
        font-style: italic;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        flex-shrink: 0;
    }

    .wc-label.dirty {
        color: #92400e;
        font-weight: var(--design-font-weight-medium, 500);
    }

    .wc-label.all-staged {
        color: #166534;
        font-weight: var(--design-font-weight-medium, 500);
    }

    /* ===== BADGES ===== */
    .wc-badges {
        display: flex;
        align-items: center;
        gap: 2px;
        flex-shrink: 0;
    }

    .wc-badge {
        display: inline-flex;
        align-items: center;
        padding: 0 4px;
        border-radius: var(--design-radius-full, 9999px);
        font-size: 8px;
        font-weight: var(--design-font-weight-bold, 700);
        font-family: var(--design-font-mono, monospace);
        white-space: nowrap;
        line-height: 14px;
    }

    .wc-badge.modified {
        background: #fef3c7;
        color: #92400e;
    }

    .wc-badge.added {
        background: #dcfce7;
        color: #166534;
    }

    .wc-badge.deleted {
        background: #fee2e2;
        color: #991b1b;
    }

    .wc-badge.untracked {
        background: var(--design-bg-gray-100, #f3f4f6);
        color: var(--design-text-secondary, #6b7280);
    }

    .wc-badge.staged {
        background: #dbeafe;
        color: #1e40af;
    }

    /* ===== SPINNER (loading) ===== */
    .wc-spinner {
        width: 10px;
        height: 10px;
        border: 1.5px solid var(--design-border-color, #e5e7eb);
        border-top-color: var(--design-primary, #4f46e5);
        border-radius: 50%;
        animation: wc-spin 0.8s linear infinite;
        flex-shrink: 0;
    }

    @keyframes wc-spin {
        to { transform: rotate(360deg); }
    }
`;
