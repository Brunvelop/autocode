/**
 * chat-window.styles.js
 * Estilos específicos para el componente ChatWindow
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const chatWindowStyles = css`
    :host {
        display: contents;
        font-family: var(--chat-font-family, system-ui, -apple-system, sans-serif);
    }

    .toggle-btn {
        position: fixed;
        top: var(--chat-spacing-lg, 1rem);
        left: var(--chat-spacing-lg, 1rem);
        z-index: var(--chat-z-tooltip, 110);
        background: var(--chat-bg-white, white);
        color: var(--chat-primary, #4f46e5);
        border-radius: var(--chat-radius-full, 9999px);
        padding: var(--chat-spacing-lg, 1rem);
        box-shadow: var(--chat-shadow-lg, 0 10px 15px -3px rgb(0 0 0 / 0.1));
        border: none;
        cursor: pointer;
        transition: transform var(--chat-transition-slow, 0.3s), 
                    box-shadow var(--chat-transition-slow, 0.3s);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .toggle-btn:hover {
        transform: scale(1.05);
        box-shadow: var(--chat-shadow-xl, 0 20px 25px -5px rgb(0 0 0 / 0.1));
    }

    .panel {
        position: fixed;
        inset: 0;
        z-index: var(--chat-z-modal, 100);
        background: transparent;
        pointer-events: none;
        opacity: 1;
        transition: opacity var(--chat-transition-base, 0.2s);
    }

    .panel.hidden {
        display: none;
        opacity: 0;
        pointer-events: none;
    }

    .window {
        position: fixed;
        top: 5rem;
        right: var(--chat-spacing-2xl, 1.5rem);
        width: min(92vw, 560px);
        height: 70vh;
        min-width: 320px;
        min-height: 300px;
        background: var(--chat-bg-white, white);
        border-radius: var(--chat-radius-xl, 1rem);
        box-shadow: var(--chat-shadow-2xl, 0 25px 50px -12px rgb(0 0 0 / 0.25));
        overflow: hidden;
        display: flex;
        flex-direction: column;
        pointer-events: auto;
        border: 1px solid var(--chat-border-gray, #e5e7eb);
    }

    .header {
        background: linear-gradient(to right, var(--chat-primary, #4f46e5), var(--chat-secondary, #7c3aed));
        padding: var(--chat-spacing-lg, 1rem);
        display: flex;
        align-items: center;
        justify-content: space-between;
        user-select: none;
        flex-shrink: 0;
        gap: var(--chat-spacing-md, 0.75rem);
    }

    /* Zona draggable: Solo icono y título */
    .drag-handle {
        flex: 1;
        display: flex;
        align-items: center;
        gap: var(--chat-spacing-md, 0.75rem);
        cursor: move;
        min-width: 0; /* Permite que el texto se trunque si es necesario */
    }

    .drag-handle:active {
        cursor: grabbing;
    }

    .header-title {
        color: white;
        font-weight: var(--chat-font-weight-bold, bold);
        font-size: var(--chat-font-size-xl, 1.25rem);
        margin: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Zona interactiva: Botones sin drag */
    .header-actions {
        display: flex;
        align-items: center;
        gap: var(--chat-spacing-sm, 0.5rem);
        flex-shrink: 0; /* Nunca se comprimen los botones */
    }

    .close-btn {
        color: white;
        background: transparent;
        border: none;
        border-radius: var(--chat-radius-full, 9999px);
        padding: var(--chat-spacing-sm, 0.5rem);
        cursor: pointer;
        transition: background var(--chat-transition-base, 0.2s);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .close-btn:hover {
        background: rgba(255, 255, 255, 0.2);
    }

    .content {
        flex: 1;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        position: relative;
    }

    .footer {
        background: var(--chat-bg-white, white);
        border-top: 1px solid var(--chat-border-gray, #e5e7eb);
        flex-shrink: 0;
    }

    .resize-handle {
        position: absolute;
        bottom: var(--chat-spacing-xs, 0.25rem);
        right: var(--chat-spacing-xs, 0.25rem);
        width: var(--chat-spacing-2xl, 1.5rem);
        height: var(--chat-spacing-2xl, 1.5rem);
        cursor: se-resize;
        color: rgba(99, 102, 241, 0.5);
        user-select: none;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10;
    }

    .resize-handle:hover {
        color: rgba(99, 102, 241, 0.8);
    }

    /* Estilos para contenido slotted */
    ::slotted([slot="content"]) {
        flex: 1;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }

    /* Styles for header-actions slot */
    ::slotted([slot="header-actions"]) {
        display: flex;
        align-items: center;
    }
`;
