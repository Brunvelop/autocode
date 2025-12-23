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

    .settings-dialog {
        position: fixed; /* Explicitly fixed for older browsers, though dialog is usually top-layer */
        border: none;
        border-radius: var(--design-radius-lg, 0.75rem);
        padding: 0;
        width: min(90vw, 420px);
        max-height: 85vh;
        background: var(--design-bg-white, white);
        box-shadow: var(--design-shadow-2xl, 0 25px 50px -12px rgba(0, 0, 0, 0.25));
        color: var(--design-text-primary, #1f2937);
        outline: none;
    }

    .settings-dialog[open] {
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }

    .settings-dialog::backdrop {
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(2px);
    }

    .dialog-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: var(--design-spacing-md, 0.75rem) var(--design-spacing-lg, 1rem);
        border-bottom: 1px solid var(--design-border-gray, #e5e7eb);
        background: var(--design-bg-white, white);
        position: sticky;
        top: 0;
        z-index: 10;
    }

    .panel-title {
        font-weight: var(--design-font-weight-bold, 700);
        font-size: var(--design-font-size-base, 0.875rem);
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        margin: 0;
    }

    .close-icon-btn {
        background: transparent;
        border: none;
        color: var(--design-text-tertiary, #9ca3af);
        cursor: pointer;
        padding: var(--design-spacing-xs, 0.25rem);
        border-radius: var(--design-radius-full, 9999px);
        transition: all 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .close-icon-btn:hover {
        background: var(--design-bg-gray-100, #f3f4f6);
        color: var(--design-text-primary, #1f2937);
    }

    .controls {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-lg, 1rem);
        padding: var(--design-spacing-lg, 1rem);
        flex: 1;
        min-height: 0;
        overflow-y: auto;
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

    /* Section Divider */
    .section-divider {
        height: 1px;
        background: var(--design-border-gray, #e5e7eb);
        margin: var(--design-spacing-sm, 0.5rem) 0;
    }

    .section-title {
        font-size: var(--design-font-size-sm, 0.75rem);
        font-weight: var(--design-font-weight-semibold, 600);
        color: var(--design-primary, #4f46e5);
        margin-bottom: var(--design-spacing-sm, 0.5rem);
        display: flex;
        align-items: center;
        gap: var(--design-spacing-xs, 0.25rem);
    }

    .tools-count {
        font-weight: var(--design-font-weight-normal, 400);
        color: var(--design-text-tertiary, #9ca3af);
    }

    /* Search Input */
    .search-container {
        margin-bottom: var(--design-spacing-sm, 0.5rem);
    }

    .search-input {
        width: 100%;
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
        font-size: var(--design-font-size-sm, 0.75rem);
        border: 1px solid var(--design-border-gray, #d1d5db);
        border-radius: var(--design-radius-md, 0.5rem);
        outline: none;
        transition: border-color 0.2s, box-shadow 0.2s;
        box-sizing: border-box; /* Ensure padding doesn't overflow width */
    }

    .search-input:focus {
        border-color: var(--design-primary, #4f46e5);
        box-shadow: 0 0 0 2px var(--design-primary-light-translucent, rgba(99, 102, 241, 0.2));
    }

    .no-results {
        padding: var(--design-spacing-md, 0.75rem);
        text-align: center;
        color: var(--design-text-tertiary, #9ca3af);
        font-size: var(--design-font-size-sm, 0.75rem);
        font-style: italic;
    }

    /* Tools List */
    .tools-list {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-xs, 0.25rem);
        /* Removed fixed height to avoid nested scrolling */
        padding-right: var(--design-spacing-xs, 0.25rem);
    }

    .tool-item {
        display: flex;
        flex-direction: column;
        padding: var(--design-spacing-xs, 0.25rem) var(--design-spacing-sm, 0.5rem);
        border-radius: var(--design-radius-sm, 0.25rem);
        background: var(--design-bg-gray-50, #f9fafb);
        border: 1px solid transparent;
        transition: border-color var(--design-transition-base, 0.2s);
    }

    .tool-item:hover {
        border-color: var(--design-border-gray-dark, #d1d5db);
    }

    .tool-checkbox {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-sm, 0.5rem);
        cursor: pointer;
    }

    .tool-checkbox input[type="checkbox"] {
        flex-shrink: 0;
    }

    .tool-name {
        font-size: var(--design-font-size-sm, 0.75rem);
        font-weight: var(--design-font-weight-medium, 500);
        color: var(--design-text-primary, #1f2937);
        font-family: var(--design-font-mono, monospace);
    }

    .tool-description {
        font-size: var(--design-font-size-xs, 0.625rem);
        color: var(--design-text-tertiary, #9ca3af);
        margin-left: calc(1rem + var(--design-spacing-sm, 0.5rem));
        line-height: 1.3;
    }

    /* Scrollbar styling */
    .controls::-webkit-scrollbar,
    .tools-list::-webkit-scrollbar {
        width: 4px;
    }

    .controls::-webkit-scrollbar-track,
    .tools-list::-webkit-scrollbar-track {
        background: var(--design-bg-gray-100, #f3f4f6);
        border-radius: 2px;
    }

    .controls::-webkit-scrollbar-thumb,
    .tools-list::-webkit-scrollbar-thumb {
        background: var(--design-border-gray-dark, #d1d5db);
        border-radius: 2px;
    }

    .controls::-webkit-scrollbar-thumb:hover,
    .tools-list::-webkit-scrollbar-thumb:hover {
        background: var(--design-text-tertiary, #9ca3af);
    }

    /* Param Hint */
    .param-hint {
        font-weight: normal;
        font-size: var(--design-font-size-xs, 0.625rem);
        color: var(--design-text-tertiary, #9ca3af);
        margin-left: var(--design-spacing-xs, 0.25rem);
    }

    /* Collapsible Section */
    .collapsible {
        user-select: none;
        transition: color 0.2s;
    }

    .collapsible:hover {
        color: var(--design-primary-dark, #4338ca);
    }

    .advanced-controls {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-sm, 0.5rem);
        padding: var(--design-spacing-sm, 0.5rem);
        background: var(--design-bg-gray-50, #f9fafb);
        border-radius: var(--design-radius-md, 0.5rem);
        margin-top: var(--design-spacing-xs, 0.25rem);
    }
`;
