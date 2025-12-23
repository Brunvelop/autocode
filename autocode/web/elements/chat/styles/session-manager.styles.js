/**
 * session-manager.styles.js
 * Estilos específicos para el componente SessionManager
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const sessionManagerStyles = css`
    :host {
        display: block;
    }

    /* Container */
    .session-manager {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
    }

    /* Session Badge (Active) - Más prominente */
    .session-badge {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        padding: var(--design-spacing-sm, 0.5rem) var(--design-spacing-md, 0.75rem);
        border-radius: var(--design-radius-md, 0.5rem);
        background-color: rgba(16, 185, 129, 0.15);
        border: 2px solid rgba(16, 185, 129, 0.5);
        font-size: var(--design-font-size-sm, 0.75rem);
        font-weight: var(--design-font-weight-semibold, 600);
        color: rgb(134, 239, 172);
        max-width: 280px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .session-icon {
        font-size: 1rem;
        flex-shrink: 0;
    }

    .session-dot {
        width: 0.5rem;
        height: 0.5rem;
        border-radius: 50%;
        background-color: rgb(16, 185, 129);
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        flex-shrink: 0;
    }

    .session-description {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }

    /* Session Buttons */
    .new-session-btn,
    .end-session-btn {
        color: var(--design-indigo-100, #e0e7ff);
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: var(--design-radius-full, 9999px);
        padding: var(--design-spacing-sm, 0.375rem) var(--design-spacing-md, 0.75rem);
        font-size: var(--design-font-size-base, 0.875rem);
        font-weight: var(--design-font-weight-semibold, 600);
        transition: all var(--design-transition-base, 0.2s);
        cursor: pointer;
        white-space: nowrap;
    }

    .new-session-btn:hover,
    .end-session-btn:hover {
        background-color: rgba(255, 255, 255, 0.2);
    }

    .new-session-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .end-session-btn {
        background-color: rgba(16, 185, 129, 0.1);
        border-color: rgba(16, 185, 129, 0.3);
        color: rgb(134, 239, 172);
    }

    .end-session-btn:hover {
        background-color: rgba(16, 185, 129, 0.2);
    }

    /* Abort Session Button - Rojo para cancelar */
    .abort-session-btn {
        color: rgb(254, 202, 202);
        background-color: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: var(--design-radius-full, 9999px);
        padding: var(--design-spacing-sm, 0.375rem) var(--design-spacing-md, 0.75rem);
        font-size: var(--design-font-size-base, 0.875rem);
        font-weight: var(--design-font-weight-semibold, 600);
        transition: all var(--design-transition-base, 0.2s);
        cursor: pointer;
        white-space: nowrap;
    }

    .abort-session-btn:hover {
        background-color: rgba(239, 68, 68, 0.2);
        border-color: rgba(239, 68, 68, 0.5);
    }

    /* Error Message */
    .session-error {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        padding: var(--design-spacing-sm, 0.5rem) var(--design-spacing-md, 0.75rem);
        border-radius: var(--design-radius-md, 0.5rem);
        background-color: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.5);
        color: rgb(254, 202, 202);
        font-size: var(--design-font-size-sm, 0.75rem);
        cursor: pointer;
        max-width: 300px;
        animation: fadeIn 0.2s ease-out;
    }

    .session-error:hover {
        background-color: rgba(239, 68, 68, 0.25);
    }

    .error-icon {
        flex-shrink: 0;
    }

    .error-text {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .error-dismiss {
        flex-shrink: 0;
        opacity: 0.7;
        font-size: 0.875rem;
    }

    .error-dismiss:hover {
        opacity: 1;
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(-0.25rem);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
