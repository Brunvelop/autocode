/**
 * context-bar.js
 * Barra de progreso para mostrar uso de la ventana de contexto
 * 
 * Atributos:
 * - current: Tokens actuales usados
 * - max: Tokens máximos disponibles
 * 
 * La barra cambia de color según el porcentaje:
 * - Verde: < 70%
 * - Amarillo: 70-90%
 * - Rojo: > 90%
 */

class ContextBar extends HTMLElement {
    static get observedAttributes() {
        return ['current', 'max'];
    }

    constructor() {
        super();
        this._current = 0;
        this._max = 0;
    }

    connectedCallback() {
        this.render();
        this._updateDisplay();
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue === newValue) return;
        
        if (name === 'current') {
            this._current = parseInt(newValue) || 0;
        }
        if (name === 'max') {
            this._max = parseInt(newValue) || 0;
        }
        
        this._updateDisplay();
    }

    render() {
        this.innerHTML = `
            <div class="w-full">
                <div class="flex items-center justify-between text-xs text-gray-600 mb-1">
                    <span>Ventana de contexto</span>
                    <span data-ref="stats" class="font-mono">0 / 0</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div 
                        data-ref="bar" 
                        class="h-full bg-green-500 transition-all duration-300" 
                        style="width: 0%"
                    ></div>
                </div>
            </div>
        `;
    }

    _updateDisplay() {
        const stats = this.querySelector('[data-ref="stats"]');
        const bar = this.querySelector('[data-ref="bar"]');
        
        if (!stats || !bar) return;

        // Formatear números con separador de miles
        const currentFormatted = this._current.toLocaleString();
        const maxFormatted = this._max.toLocaleString();
        stats.textContent = `${currentFormatted} / ${maxFormatted}`;

        // Calcular porcentaje
        const percentage = this._max > 0 ? (this._current / this._max) * 100 : 0;
        bar.style.width = `${Math.min(percentage, 100)}%`;

        // Actualizar color según porcentaje
        bar.classList.remove('bg-green-500', 'bg-yellow-500', 'bg-red-500');
        
        if (percentage < 70) {
            bar.classList.add('bg-green-500');
        } else if (percentage < 90) {
            bar.classList.add('bg-yellow-500');
        } else {
            bar.classList.add('bg-red-500');
        }
    }

    // API Pública
    update(current, max) {
        this._current = current;
        this._max = max;
        this._updateDisplay();
    }

    getPercentage() {
        return this._max > 0 ? (this._current / this._max) * 100 : 0;
    }
}

if (!customElements.get('context-bar')) {
    customElements.define('context-bar', ContextBar);
}

export { ContextBar };
