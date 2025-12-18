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
        transition: opacity var(--design-transition-base), 
                    transform var(--design-transition-fast),
                    background-color var(--design-transition-base);
        font-family: var(--design-font-family);
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
        background: linear-gradient(to right, var(--design-primary), var(--design-secondary));
        color: white;
        font-weight: var(--design-font-weight-semibold);
        padding: var(--design-spacing-md) var(--design-spacing-xl);
        border-radius: var(--design-radius-lg);
        box-shadow: var(--design-shadow-sm);
        font-size: var(--design-font-size-base);
    }

    button:disabled {
        background: var(--design-border-gray-dark);
    }
`;

/**
 * Botón secundario/ghost
 */
export const ghostButton = css`
    button {
        background-color: rgba(255, 255, 255, 0.1);
        color: var(--design-text-light);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: var(--design-radius-full);
        padding: var(--design-spacing-sm) var(--design-spacing-md);
        font-size: var(--design-font-size-base);
        font-weight: var(--design-font-weight-semibold);
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
        color: var(--design-indigo-100);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: var(--design-radius-full);
        padding: var(--design-spacing-sm);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background-color var(--design-transition-base), color var(--design-transition-base);
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
        padding: var(--design-spacing-md);
        border: 1px solid var(--design-border-gray-dark);
        border-radius: var(--design-radius-lg);
        font-size: var(--design-font-size-base);
        line-height: var(--design-line-height-tight);
        box-shadow: var(--design-shadow-xs);
        outline: none;
        transition: border-color var(--design-transition-base), 
                    box-shadow var(--design-transition-base);
        background: var(--design-bg-white);
        color: var(--design-text-primary);
        font-family: var(--design-font-family);
        box-sizing: border-box;
    }

    input:focus,
    select:focus {
        border-color: var(--design-primary-light);
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }

    input:disabled,
    select:disabled {
        background-color: var(--design-bg-gray-100);
        cursor: not-allowed;
        color: var(--design-text-tertiary);
    }
`;

/**
 * Estilos base para cards/tarjetas
 */
export const cardBase = css`
    .card {
        background: var(--design-bg-white);
        border-radius: var(--design-radius-xl);
        box-shadow: var(--design-shadow-sm);
        border: 1px solid var(--design-border-gray);
        overflow: hidden;
    }
`;

/**
 * Estilos para badges/insignias
 */
export const badgeBase = css`
    .badge {
        font-family: var(--design-font-mono);
        padding: 0.125rem var(--design-spacing-sm);
        border-radius: var(--design-radius-sm);
        font-size: var(--design-font-size-sm);
        display: inline-block;
    }

    .badge-primary {
        color: var(--design-primary);
        background-color: var(--design-indigo-50);
        border: 1px solid var(--design-indigo-200);
    }

    .badge-secondary {
        color: var(--design-text-secondary);
        background-color: var(--design-bg-gray-100);
        border: 1px solid var(--design-border-gray);
    }
`;

/**
 * Estilos para checkboxes personalizados
 */
export const checkboxStyles = css`
    input[type="checkbox"] {
        width: 1rem;
        height: 1rem;
        color: var(--design-primary);
        border-radius: var(--design-radius-sm);
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
        background: var(--design-border-gray);
        border-radius: var(--design-radius-md);
        appearance: none;
        cursor: pointer;
    }

    input[type="range"]::-webkit-slider-thumb {
        appearance: none;
        width: 1rem;
        height: 1rem;
        background: var(--design-primary);
        border-radius: 50%;
        cursor: pointer;
    }

    input[type="range"]::-moz-range-thumb {
        width: 1rem;
        height: 1rem;
        background: var(--design-primary);
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
        background: var(--design-bg-gray-50);
    }

    *::-webkit-scrollbar-thumb {
        background: var(--design-border-gray-dark);
        border-radius: var(--design-radius-full);
    }

    *::-webkit-scrollbar-thumb:hover {
        background: var(--design-text-tertiary);
    }
`;
