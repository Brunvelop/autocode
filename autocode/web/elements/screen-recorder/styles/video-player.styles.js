/**
 * video-player.styles.js
 * Estilos para el modal de preview y reproducción del video grabado
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const videoPlayerStyles = css`
    :host {
        display: block;
    }

    /* Overlay oscuro de fondo */
    .overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(4px);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: fadeIn 0.2s ease-out;
        padding: 20px;
        box-sizing: border-box;
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }

    /* Contenedor del player */
    .player-container {
        background: var(--design-bg-gray-900);
        border-radius: var(--design-radius-xl);
        box-shadow: var(--design-shadow-2xl);
        max-width: 90vw;
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        animation: slideUp 0.3s ease-out;
        overflow: hidden;
    }

    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Header */
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        background: rgba(17, 24, 39, 0.5);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .title {
        color: white;
        font-size: var(--design-font-size-lg);
        font-weight: var(--design-font-weight-semibold);
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .close-btn {
        width: 32px;
        height: 32px;
        border-radius: var(--design-radius-md);
        border: none;
        background: rgba(255, 255, 255, 0.1);
        color: white;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background var(--design-transition-base);
    }

    .close-btn:hover {
        background: rgba(255, 255, 255, 0.2);
    }

    /* Video */
    .video-wrapper {
        position: relative;
        background: black;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 300px;
    }

    video {
        width: 100%;
        max-height: calc(90vh - 200px);
        display: block;
    }

    /* Acciones */
    .actions {
        display: flex;
        gap: 12px;
        padding: 20px;
        background: rgba(17, 24, 39, 0.5);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    .action-btn {
        flex: 1;
        padding: 12px 20px;
        border-radius: var(--design-radius-lg);
        border: none;
        font-size: var(--design-font-size-base);
        font-weight: var(--design-font-weight-medium);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        transition: all var(--design-transition-base);
    }

    .action-btn.primary {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
    }

    .action-btn.primary:hover {
        transform: translateY(-2px);
        box-shadow: var(--design-shadow-lg);
    }

    .action-btn.secondary {
        background: rgba(255, 255, 255, 0.1);
        color: white;
    }

    .action-btn.secondary:hover {
        background: rgba(255, 255, 255, 0.15);
    }

    .action-btn:active {
        transform: translateY(0);
    }

    /* Info del video */
    .video-info {
        padding: 12px 20px;
        background: rgba(17, 24, 39, 0.3);
        display: flex;
        gap: 20px;
        font-size: var(--design-font-size-sm);
        color: rgba(255, 255, 255, 0.7);
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    }

    .video-info span {
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .player-container {
            max-width: 95vw;
            max-height: 95vh;
        }

        .actions {
            flex-direction: column;
        }

        .action-btn {
            width: 100%;
        }
    }
`;
