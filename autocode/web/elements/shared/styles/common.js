/**
 * common.js
 * Utilidades CSS y mixins comunes para todos los componentes
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

/**
 * Badge base: estilo para badges/chips
 */
export const badgeBase = css`
    .badge {
        display: inline-flex;
        align-items: center;
        padding: var(--design-spacing-xs) var(--design-spacing-sm);
        border-radius: var(--design-radius-full);
        font-size: var(--design-font-size-xs);
        font-weight: var(--design-font-weight-medium);
        line-height: var(--design-line-height-tight);
    }
`;

/**
 * Ghost button: botón transparente con hover
 */
export const ghostButton = css`
    .ghost-btn {
        background: transparent;
        border: none;
        padding: var(--design-spacing-xs) var(--design-spacing-sm);
        border-radius: var(--design-radius-md);
        cursor: pointer;
        transition: background-color var(--design-transition-base);
        color: var(--design-text-secondary);
    }
    
    .ghost-btn:hover {
        background-color: var(--design-bg-gray-100);
        color: var(--design-text-primary);
    }
`;

/**
 * Loading spinner animation
 */
export const spinnerStyles = css`
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    .spinner {
        width: 24px;
        height: 24px;
        border: 2px solid var(--dark-border);
        border-top-color: var(--design-primary);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }
`;
