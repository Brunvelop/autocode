/**
 * file-explorer.styles.js
 * Estilos para el componente FileExplorer
 * Usa tokens del sistema de diseño compartido
 */

import { css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { themeTokens } from '../../shared/styles/theme.js';
import { spinnerStyles } from '../../shared/styles/common.js';

export const fileExplorerStyles = css`
    ${themeTokens}
    ${spinnerStyles}
    
    :host {
        display: block;
        width: 100%;
        height: 100%;
    }
    
    .file-explorer-root {
        width: 100%;
        height: 100%;
        overflow: auto;
        background: var(--dark-bg-primary);
        box-sizing: border-box;
        padding: var(--design-spacing-md);
    }
    
    .folder-box {
        display: inline-flex;
        flex-direction: column;
        box-sizing: border-box;
        border-radius: var(--design-radius-md);
        margin: var(--design-spacing-xs);
        vertical-align: top;
        min-width: fit-content;
        box-shadow: var(--design-shadow-md);
        background: var(--dark-bg-tertiary);
        border: 1px solid var(--dark-border);
    }
    
    .folder-header {
        font-weight: var(--design-font-weight-bold);
        padding: var(--design-spacing-xs) var(--design-spacing-md);
        white-space: nowrap;
        border-radius: var(--design-radius-sm) var(--design-radius-sm) 0 0;
        font-size: var(--design-font-size-xs);
        background: var(--dark-bg-secondary);
        color: var(--dark-text-primary);
    }
    
    .folder-content {
        display: flex;
        flex-wrap: wrap;
        align-items: flex-start;
        align-content: flex-start;
        padding: var(--design-spacing-xs);
        gap: var(--design-spacing-xs);
        min-height: 20px;
    }
    
    .file-chip {
        display: inline-flex;
        align-items: center;
        gap: var(--design-spacing-xs);
        padding: 2px 6px;
        border-radius: var(--design-radius-sm);
        font-size: 9px;
        white-space: nowrap;
        cursor: default;
        transition: filter var(--design-transition-base);
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid;
    }
    
    .file-chip:hover {
        filter: brightness(1.2);
    }
    
    /* Loading & Error states */
    .loading-state, .error-state {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: var(--dark-text-secondary);
        flex-direction: column;
        gap: var(--design-spacing-md);
    }
    
    .loading-content {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-md);
    }
    
    .error-content {
        text-align: center;
    }
    
    .error-icon {
        font-size: 32px;
        margin-bottom: var(--design-spacing-md);
    }
    
    .retry-btn {
        margin-top: var(--design-spacing-lg);
        padding: var(--design-spacing-sm) var(--design-spacing-lg);
        background: var(--dark-border);
        border: none;
        border-radius: var(--design-radius-sm);
        color: var(--dark-text-primary);
        cursor: pointer;
        font-size: var(--design-font-size-sm);
        transition: background-color var(--design-transition-base);
    }
    
    .retry-btn:hover {
        background: var(--dark-bg-tertiary);
    }

    /* Root level layout */
    .root-content {
        display: flex;
        flex-wrap: wrap;
        align-items: flex-start;
        align-content: flex-start;
        gap: var(--design-spacing-xs);
    }
`;
