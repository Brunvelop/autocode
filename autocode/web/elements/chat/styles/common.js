/**
 * common.js
 * Estilos compartidos entre múltiples componentes de chat
 * Patrones reutilizables de botones, cards, inputs, etc.
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

/**
 * Estilos base para botones
 */
export const buttonBase = css`
    button {
        border: none;
        cursor: pointer;
        transition: opacity var(--chat-transition-base), 
                    transform var(--chat-transition-fast),
                    background-color var(--chat-transition-base);
        font-family: var(--chat-font-family);
        outline: none;
    }

    button:hover:not(:disabled) {
        opacity: 0.9;
    }

    button:active:not(:disabled) {
        transform: scale(0.98);
    }

    button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
`;

/**
 * Botón primario con gradiente
 */
export const primaryButton = css`
    button {
        background: linear-gradient(to right, var(--chat-primary), var(--chat-secondary));
        color: white;
        font-weight: var(--chat-font-weight-semibold);
        padding: var(--chat-spacing-md) var(--chat-spacing-xl);
        border-radius: var(--chat-radius-lg);
        box-shadow: var(--chat-shadow-sm);
        font-size: var(--chat-font-size-base);
    }

    button:disabled {
        background: var(--chat-border-gray-dark);
    }
`;

/**
 * Botón secundario/ghost
 */
export const ghostButton = css`
    button {
        background-color: rgba(255, 255, 255, 0.1);
        color: var(--chat-text-light);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: var(--chat-radius-full);
        padding: var(--chat-spacing-sm) var(--chat-spacing-md);
        font-size: var(--chat-font-size-base);
        font-weight: var(--chat-font-weight-semibold);
    }

    button:hover:not(:disabled) {
        background-color: rgba(255, 255, 255, 0.2);
    }
`;

/**
 * Botón de icono circular
 */
export const iconButton = css`
    button {
        background: rgba(255, 255, 255, 0.1);
        color: var(--chat-indigo-100);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: var(--chat-radius-full);
        padding: var(--chat-spacing-sm);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background-color var(--chat-transition-base), color var(--chat-transition-base);
    }

    button:hover:not(:disabled) {
        background-color: rgba(255, 255, 255, 0.2);
        color: white;
    }
`;

/**
 * Estilos base para inputs
 */
export const inputBase = css`
    input[type="text"],
    input[type="number"],
    select {
        width: 100%;
        padding: var(--chat-spacing-md);
        border: 1px solid var(--chat-border-gray-dark);
        border-radius: var(--chat-radius-lg);
        font-size: var(--chat-font-size-base);
        line-height: var(--chat-line-height-tight);
        box-shadow: var(--chat-shadow-xs);
        outline: none;
        transition: border-color var(--chat-transition-base), 
                    box-shadow var(--chat-transition-base);
        background: var(--chat-bg-white);
        color: var(--chat-text-primary);
        font-family: var(--chat-font-family);
        box-sizing: border-box;
    }

    input:focus,
    select:focus {
        border-color: var(--chat-primary-light);
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }

    input:disabled,
    select:disabled {
        background-color: var(--chat-bg-gray-100);
        cursor: not-allowed;
        color: var(--chat-text-tertiary);
    }
`;

/**
 * Estilos base para cards/tarjetas
 */
export const cardBase = css`
    .card {
        background: var(--chat-bg-white);
        border-radius: var(--chat-radius-xl);
        box-shadow: var(--chat-shadow-sm);
        border: 1px solid var(--chat-border-gray);
        overflow: hidden;
    }
`;

/**
 * Estilos para badges/insignias
 */
export const badgeBase = css`
    .badge {
        font-family: var(--chat-font-mono);
        padding: 0.125rem var(--chat-spacing-sm);
        border-radius: var(--chat-radius-sm);
        font-size: var(--chat-font-size-sm);
        display: inline-block;
    }

    .badge-primary {
        color: var(--chat-primary);
        background-color: var(--chat-indigo-50);
        border: 1px solid var(--chat-indigo-200);
    }

    .badge-secondary {
        color: var(--chat-text-secondary);
        background-color: var(--chat-bg-gray-100);
        border: 1px solid var(--chat-border-gray);
    }
`;

/**
 * Estilos para checkboxes personalizados
 */
export const checkboxStyles = css`
    input[type="checkbox"] {
        width: 1rem;
        height: 1rem;
        color: var(--chat-primary);
        border-radius: var(--chat-radius-sm);
        cursor: pointer;
    }
`;

/**
 * Estilos para range sliders
 */
export const rangeSliderStyles = css`
    input[type="range"] {
        width: 100%;
        height: 0.5rem;
        background: var(--chat-border-gray);
        border-radius: var(--chat-radius-md);
        appearance: none;
        cursor: pointer;
    }

    input[type="range"]::-webkit-slider-thumb {
        appearance: none;
        width: 1rem;
        height: 1rem;
        background: var(--chat-primary);
        border-radius: 50%;
        cursor: pointer;
    }

    input[type="range"]::-moz-range-thumb {
        width: 1rem;
        height: 1rem;
        background: var(--chat-primary);
        border-radius: 50%;
        cursor: pointer;
        border: none;
    }
`;

/**
 * Scrollbar personalizado
 */
export const scrollbarStyles = css`
    *::-webkit-scrollbar {
        width: 0.5rem;
    }

    *::-webkit-scrollbar-track {
        background: var(--chat-bg-gray-50);
    }

    *::-webkit-scrollbar-thumb {
        background: var(--chat-border-gray-dark);
        border-radius: var(--chat-radius-full);
    }

    *::-webkit-scrollbar-thumb:hover {
        background: var(--chat-text-tertiary);
    }
`;
