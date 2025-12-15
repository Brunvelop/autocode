/**
 * context-bar.js
 * Barra de progreso para mostrar uso de la ventana de contexto
 * Refactorizado: Lógica pura separada de estilos
 * 
 * Propiedades:
 * - current: Tokens actuales usados
 * - max: Tokens máximos disponibles
 * 
 * La barra cambia de color según el porcentaje:
 * - Verde: < 70%
 * - Amarillo: 70-90%
 * - Rojo: > 90%
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { contextBarStyles } from './styles/context-bar.styles.js';
import { themeTokens } from './styles/theme.js';

export class ContextBar extends LitElement {
    static properties = {
        current: { type: Number },
        max: { type: Number }
    };

    static styles = [themeTokens, contextBarStyles];

    constructor() {
        super();
        this.current = 0;
        this.max = 0;
    }

    render() {
        const percentage = this._getPercentage();
        const colorClass = this._getColorClass(percentage);
        
        return html`
            <div class="container">
                <div class="header">
                    <span>Ventana de contexto</span>
                    <span class="stats">${this._formatNumber(this.current)} / ${this._formatNumber(this.max)}</span>
                </div>
                <div class="track">
                    <div 
                        class="bar ${colorClass}" 
                        style="width: ${Math.min(percentage, 100)}%"
                    ></div>
                </div>
            </div>
        `;
    }

    // ========================================================================
    // API PÚBLICA
    // ========================================================================

    update(current, max) {
        this.current = current;
        this.max = max;
    }

    getPercentage() {
        return this._getPercentage();
    }

    // ========================================================================
    // HELPERS INTERNOS
    // ========================================================================

    _getPercentage() {
        return this.max > 0 ? (this.current / this.max) * 100 : 0;
    }

    _getColorClass(percentage) {
        if (percentage < 70) return 'green';
        if (percentage < 90) return 'yellow';
        return 'red';
    }

    _formatNumber(num) {
        return num.toLocaleString();
    }
}

if (!customElements.get('context-bar')) {
    customElements.define('context-bar', ContextBar);
}
