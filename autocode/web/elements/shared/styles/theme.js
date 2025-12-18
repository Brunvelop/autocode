/**
 * theme.js
 * Sistema de tokens de diseño globales para todos los componentes
 * Define variables CSS reutilizables para mantener consistencia visual
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

/**
 * Tokens de diseño base
 * Estos pueden ser reutilizados en todos los componentes de la aplicación
 */
export const themeTokens = css`
    :host {
        /* Colores */
        --design-primary: #4f46e5;
        --design-primary-light: #6366f1;
        --design-primary-dark: #4338ca;
        --design-secondary: #7c3aed;
        
        --design-text-primary: #1f2937;
        --design-text-secondary: #6b7280;
        --design-text-tertiary: #9ca3af;
        --design-text-light: #f3f4f6;
        
        --design-bg-white: #ffffff;
        --design-bg-gray-50: #f9fafb;
        --design-bg-gray-100: #f3f4f6;
        --design-bg-gray-900: #111827;
        
        --design-border-gray: #e5e7eb;
        --design-border-gray-light: #f3f4f6;
        --design-border-gray-dark: #d1d5db;
        
        --design-error-bg: #fef2f2;
        --design-error-text: #991b1b;
        --design-error-border: #fca5a5;
        
        --design-success: #22c55e;
        --design-warning: #eab308;
        --design-danger: #ef4444;
        
        /* Indigo/Purple system */
        --design-indigo-50: #eef2ff;
        --design-indigo-100: #e0e7ff;
        --design-indigo-200: #c7d2fe;
        --design-indigo-600: #4f46e5;
        --design-indigo-700: #4338ca;
        
        /* Dark mode colors (para file-explorer y componentes oscuros) */
        --dark-bg-primary: #020617;    /* Slate 950 */
        --dark-bg-secondary: #0f172a;  /* Slate 900 */
        --dark-bg-tertiary: #1e293b;   /* Slate 800 */
        --dark-border: #334155;         /* Slate 700 */
        --dark-text-primary: #e2e8f0;  /* Slate 200 */
        --dark-text-secondary: #94a3b8; /* Slate 400 */
        
        /* Espaciado */
        --design-spacing-xs: 0.25rem;
        --design-spacing-sm: 0.5rem;
        --design-spacing-md: 0.75rem;
        --design-spacing-lg: 1rem;
        --design-spacing-xl: 1.25rem;
        --design-spacing-2xl: 1.5rem;
        --design-spacing-3xl: 2rem;
        
        /* Border radius */
        --design-radius-sm: 0.25rem;
        --design-radius-md: 0.5rem;
        --design-radius-lg: 0.75rem;
        --design-radius-xl: 1rem;
        --design-radius-full: 9999px;
        
        /* Sombras */
        --design-shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --design-shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        --design-shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --design-shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        --design-shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
        --design-shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);
        
        /* Tipografía */
        --design-font-family: system-ui, -apple-system, sans-serif;
        --design-font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        
        --design-font-size-xs: 0.625rem;
        --design-font-size-sm: 0.75rem;
        --design-font-size-base: 0.875rem;
        --design-font-size-lg: 1rem;
        --design-font-size-xl: 1.25rem;
        
        --design-font-weight-normal: 400;
        --design-font-weight-medium: 500;
        --design-font-weight-semibold: 600;
        --design-font-weight-bold: 700;
        
        --design-line-height-tight: 1.25;
        --design-line-height-normal: 1.5;
        --design-line-height-relaxed: 1.6;
        
        /* Transiciones */
        --design-transition-fast: 0.1s;
        --design-transition-base: 0.2s;
        --design-transition-slow: 0.3s;
        
        /* Z-index */
        --design-z-dropdown: 50;
        --design-z-modal: 100;
        --design-z-tooltip: 110;
    }
`;
