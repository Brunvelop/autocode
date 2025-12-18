/**
 * recorder-controls.styles.js
 * Estilos para el botón flotante FAB y controles de grabación
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const recorderControlsStyles = css`
    :host {
        display: block;
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 1000;
        font-family: var(--design-font-family);
    }

    /* Botón FAB principal */
    .fab {
        width: 56px;
        height: 56px;
        border-radius: var(--design-radius-full);
        border: none;
        cursor: pointer;
        font-size: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: var(--design-shadow-lg);
        transition: all var(--design-transition-base);
        background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
    }

    .fab:hover {
        transform: scale(1.05);
        box-shadow: var(--design-shadow-xl);
    }

    .fab:active {
        transform: scale(0.95);
    }

    /* Estado grabando */
    .fab.recording {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        animation: pulse 2s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% {
            box-shadow: var(--design-shadow-lg);
        }
        50% {
            box-shadow: 0 0 0 8px rgba(239, 68, 68, 0.3);
        }
    }

    /* Indicador de grabación */
    .recording-indicator {
        position: absolute;
        bottom: 70px;
        right: 0;
        background: rgba(17, 24, 39, 0.95);
        backdrop-filter: blur(10px);
        padding: 8px 16px;
        border-radius: var(--design-radius-lg);
        display: flex;
        align-items: center;
        gap: 8px;
        color: white;
        font-size: var(--design-font-size-sm);
        font-weight: var(--design-font-weight-medium);
        box-shadow: var(--design-shadow-md);
        animation: slideIn 0.3s ease-out;
    }

    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Dot pulsante */
    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #ef4444;
        animation: pulseDot 1.5s ease-in-out infinite;
    }

    @keyframes pulseDot {
        0%, 100% {
            opacity: 1;
            transform: scale(1);
        }
        50% {
            opacity: 0.5;
            transform: scale(1.2);
        }
    }

    /* Estado no soportado */
    .fab.unsupported {
        background: #6b7280;
        cursor: not-allowed;
        opacity: 0.6;
    }

    .fab.unsupported:hover {
        transform: none;
    }

    /* Tooltip */
    .fab[title]::after {
        content: attr(title);
        position: absolute;
        bottom: 100%;
        right: 0;
        margin-bottom: 8px;
        padding: 6px 12px;
        background: rgba(17, 24, 39, 0.95);
        color: white;
        font-size: var(--design-font-size-xs);
        border-radius: var(--design-radius-md);
        white-space: nowrap;
        opacity: 0;
        pointer-events: none;
        transition: opacity var(--design-transition-base);
    }

    .fab:hover::after {
        opacity: 1;
    }
`;
