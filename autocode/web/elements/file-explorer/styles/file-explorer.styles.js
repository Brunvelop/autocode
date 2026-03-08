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
        font-family: var(--design-font-family, system-ui, sans-serif);
    }

    /* ===== ROOT SCROLL AREA ===== */
    .file-explorer-root {
        width: 100%;
        height: 100%;
        overflow: auto;
        background: var(--design-bg-gray-50);
        box-sizing: border-box;
        padding: var(--design-spacing-md);
    }

    /* ===== FOLDER BOX — caja sobre caja, full width ===== */
    .folder-box {
        display: flex;
        flex-direction: column;
        width: 100%;
        box-sizing: border-box;
        border-radius: var(--design-radius-md);
        border: 1px solid var(--design-border-gray);
        background: var(--design-bg-white);
        box-shadow: var(--design-shadow-xs);
        overflow: hidden;
    }

    /* ===== FOLDER HEADER ===== */
    .folder-header {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-xs);
        font-weight: var(--design-font-weight-semibold);
        font-size: var(--design-font-size-sm);
        color: var(--design-text-primary);
        padding: var(--design-spacing-xs) var(--design-spacing-md);
        background: var(--design-bg-gray-100);
        border-bottom: 1px solid var(--design-border-gray-light);
        white-space: nowrap;
        user-select: none;
        border-left: 3px solid var(--design-primary);
    }

    /* ===== FOLDER CONTENT ===== */
    .folder-content {
        display: flex;
        flex-direction: column;
        gap: var(--design-spacing-xs);
        padding: var(--design-spacing-sm);
        box-sizing: border-box;
    }

    /* Sub-carpetas dentro de folder-content ocupan todo el ancho */
    .folder-content > .folder-box {
        flex: 0 0 auto;
        width: 100%;
        background: var(--design-bg-gray-50);
    }

    /* Carpetas de nivel 2+ tienen borde accent más suave */
    .folder-content > .folder-box > .folder-header {
        border-left-color: var(--design-primary-light);
        background: var(--design-bg-white);
        font-size: var(--design-font-size-xs);
    }

    /* ===== FILE CHIPS ROW — fila de archivos al final del folder ===== */
    .file-chips-row {
        display: flex;
        flex-wrap: wrap;
        gap: var(--design-spacing-xs);
        padding: 0;
        /* Sólo se muestra si hay chips */
    }

    /* ===== FILE CHIP ===== */
    .file-chip {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        padding: 3px 8px;
        border-radius: var(--design-radius-sm);
        font-size: var(--design-font-size-xs);
        font-family: var(--design-font-mono);
        font-weight: var(--design-font-weight-medium);
        /* Texto siempre oscuro para máximo contraste sobre el tinte de color */
        color: var(--design-text-primary);
        white-space: nowrap;
        cursor: default;
        transition: filter var(--design-transition-base),
                    box-shadow var(--design-transition-base);
        /* background y border-color vienen de inline style (color por extensión) */
        border: 1px solid;
    }

    .file-chip:hover {
        filter: brightness(0.93);
        box-shadow: var(--design-shadow-xs);
    }

    /* ===== LOADING & ERROR STATES ===== */
    .loading-state, .error-state {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: var(--design-text-secondary);
        flex-direction: column;
        gap: var(--design-spacing-md);
    }

    .loading-content {
        display: flex;
        align-items: center;
        gap: var(--design-spacing-md);
        font-size: var(--design-font-size-base);
    }

    /* Override spinner colors to match light theme */
    .spinner {
        border-color: var(--design-border-gray);
        border-top-color: var(--design-primary);
    }

    .error-content {
        text-align: center;
    }

    .error-icon {
        font-size: 2rem;
        margin-bottom: var(--design-spacing-md);
    }

    .retry-btn {
        margin-top: var(--design-spacing-lg);
        padding: var(--design-spacing-xs) var(--design-spacing-lg);
        background: var(--design-primary);
        border: none;
        border-radius: var(--design-radius-md);
        color: white;
        cursor: pointer;
        font-size: var(--design-font-size-sm);
        font-family: inherit;
        transition: opacity var(--design-transition-fast);
    }

    .retry-btn:hover {
        opacity: 0.9;
    }
`;
