/**
 * chat-settings.styles.js
 * Estilos específicos para el componente ChatSettings
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

export const chatSettingsStyles = css`
    :host {
        position: relative;
        display: inline-block;
        font-family: var(--design-font-family, system-ui, -apple-system, sans-serif);
    }

    .toggle-btn {
        background: rgba(255, 255, 255, 0.1);
        color: var(--design-indigo-100, #e0e7ff);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: var(--design-radius-full, 9999px);
        padding: var(--design-spacing-sm, 0.375rem);
        cursor: pointer;
        transition: background-color var(--design-transition-base, 0.2s), 
                    color var(--design-transition-base, 0.2s);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .toggle-btn:hover {
        background-color: rgba(255, 255, 255, 0.2);
        color: white;
    }

    .panel {
        position: absolute;
        right: 0;
        top: 100%;
        margin-top: var(--design-spacing-sm, 0.5rem);
        width: 18rem;
        background: var(--design-bg-white, white);
        border-radius: var(--design-radius-lg, 0.75rem);
        box-shadow: var(--design-shadow-xl, 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04));
        border: 1px solid var(--design-border-gray, #e5e7eb);
        padding: var(--design-spacing-lg, 1rem);
        z-index: var(--design-z-dropdown, 50);
        color: var(--design-text-primary, #1f2937);
    }

    .panel-title {
        font-weight: var(--design-font-weight-bold, 700);
        font-size: var(--design-font-size-base, 0.875rem);
        margin-bottom: var(--design-spacing-md, 0.75rem);
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        margin-top: 0;
    }

    .controls {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-lg, 1rem);
        max-height: 60vh;
        overflow-y: auto;
        padding-right: var(--design-spacing-xs, 0.25rem);
    }

    .control-group {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-xs, 0.25rem);
    }

    .control-label {
        font-size: var(--design-font-size-sm, 0.75rem);
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-text-secondary, #6b7280);
    }

    .loading {
        font-size: var(--design-font-size-sm, 0.75rem);
        color: var(--design-text-secondary, #6b7280);
        font-style: italic;
    }

    /* Inputs */
    input[type="text"], 
    input[type="number"], 
    select {
        width: 100%;
        padding: var(--design-spacing-sm, 0.5rem);
        font-size: var(--design-font-size-base, 0.875rem);
        border: 1px solid var(--design-border-gray-dark, #d1d5db);
        border-radius: var(--design-radius-md, 0.5rem);
        background-color: var(--design-bg-gray-50, #f9fafb);
        color: var(--design-text-primary, #1f2937);
        outline: none;
        box-sizing: border-box;
    }

    input[type="text"]:focus, 
    input[type="number"]:focus, 
    select:focus {
        ring: 2px solid var(--design-primary-light, #6366f1);
        border-color: var(--design-primary-light, #6366f1);
    }

    /* Checkbox */
    .checkbox-wrapper {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
    }

    input[type="checkbox"] {
        width: 1rem;
        height: 1rem;
        color: var(--design-primary, #4f46e5);
        border-radius: var(--design-radius-sm, 0.25rem);
    }

    .checkbox-label {
        font-size: var(--design-font-size-base, 0.875rem);
        color: var(--design-text-primary, #374151);
    }

    /* Temperature Slider */
    .temp-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .temp-value {
        font-size: var(--design-font-size-sm, 0.75rem);
        font-family: var(--design-font-mono, monospace);
        color: var(--design-primary, #4f46e5);
    }

    input[type="range"] {
        width: 100%;
        height: 0.5rem;
        background: var(--design-border-gray, #e5e7eb);
        border-radius: var(--design-radius-md, 0.5rem);
        appearance: none;
        cursor: pointer;
    }

    input[type="range"]::-webkit-slider-thumb {
        appearance: none;
        width: 1rem;
        height: 1rem;
        background: var(--design-primary, #4f46e5);
        border-radius: 50%;
        cursor: pointer;
    }

    .temp-footer {
        display: flex;
        justify-content: space-between;
        font-size: var(--design-font-size-xs, 0.625rem);
        color: var(--design-text-tertiary, #9ca3af);
    }
`;
