/**
 * theme.js
 * Sistema de tokens de diseño para los componentes de chat
 * Define variables CSS reutilizables para mantener consistencia visual
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

/**
 * Tokens de diseño base
 * Estos pueden ser reutilizados en todos los componentes del chat
 */
export const themeTokens = css`
    :host {
        /* Colores */
        --chat-primary: #4f46e5;
        --chat-primary-light: #6366f1;
        --chat-primary-dark: #4338ca;
        --chat-secondary: #7c3aed;
        
        --chat-text-primary: #1f2937;
        --chat-text-secondary: #6b7280;
        --chat-text-tertiary: #9ca3af;
        --chat-text-light: #f3f4f6;
        
        --chat-bg-white: #ffffff;
        --chat-bg-gray-50: #f9fafb;
        --chat-bg-gray-100: #f3f4f6;
        --chat-bg-gray-900: #111827;
        
        --chat-border-gray: #e5e7eb;
        --chat-border-gray-light: #f3f4f6;
        --chat-border-gray-dark: #d1d5db;
        
        --chat-error-bg: #fef2f2;
        --chat-error-text: #991b1b;
        --chat-error-border: #fca5a5;
        
        --chat-success: #22c55e;
        --chat-warning: #eab308;
        --chat-danger: #ef4444;
        
        /* Indigo/Purple system */
        --chat-indigo-50: #eef2ff;
        --chat-indigo-100: #e0e7ff;
        --chat-indigo-200: #c7d2fe;
        --chat-indigo-600: #4f46e5;
        --chat-indigo-700: #4338ca;
        
        /* Espaciado */
        --chat-spacing-xs: 0.25rem;
        --chat-spacing-sm: 0.5rem;
        --chat-spacing-md: 0.75rem;
        --chat-spacing-lg: 1rem;
        --chat-spacing-xl: 1.25rem;
        --chat-spacing-2xl: 1.5rem;
        --chat-spacing-3xl: 2rem;
        
        /* Border radius */
        --chat-radius-sm: 0.25rem;
        --chat-radius-md: 0.5rem;
        --chat-radius-lg: 0.75rem;
        --chat-radius-xl: 1rem;
        --chat-radius-full: 9999px;
        
        /* Sombras */
        --chat-shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --chat-shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        --chat-shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --chat-shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        --chat-shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
        --chat-shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);
        
        /* Tipografía */
        --chat-font-family: system-ui, -apple-system, sans-serif;
        --chat-font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        
        --chat-font-size-xs: 0.625rem;
        --chat-font-size-sm: 0.75rem;
        --chat-font-size-base: 0.875rem;
        --chat-font-size-lg: 1rem;
        --chat-font-size-xl: 1.25rem;
        
        --chat-font-weight-normal: 400;
        --chat-font-weight-medium: 500;
        --chat-font-weight-semibold: 600;
        --chat-font-weight-bold: 700;
        
        --chat-line-height-tight: 1.25;
        --chat-line-height-normal: 1.5;
        --chat-line-height-relaxed: 1.6;
        
        /* Transiciones */
        --chat-transition-fast: 0.1s;
        --chat-transition-base: 0.2s;
        --chat-transition-slow: 0.3s;
        
        /* Z-index */
        --chat-z-dropdown: 50;
        --chat-z-modal: 100;
        --chat-z-tooltip: 110;
    }
`;
