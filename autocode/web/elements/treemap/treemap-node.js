/**
 * TreemapNode
 * Represents a single cell (file) or container (folder) in the treemap.
 * "Dumb" component: only renders what is passed to it.
 */
export class TreemapNode extends HTMLElement {
    // Legacy ShadowDOM class kept for reference if needed, but we use LightDOM one below.
}

// Redefining without ShadowDOM for Tailwind compatibility
export class TreemapNodeLight extends HTMLElement {
    static get observedAttributes() {
        return ['label', 'display-value', 'color-class'];
    }

    constructor() {
        super();
        this._resizeObserver = null;
    }

    connectedCallback() {
        this.render();
        this._initResizeObserver();
    }

    disconnectedCallback() {
        this._disconnectResizeObserver();
    }

    attributeChangedCallback() {
        this.render();
    }

    _initResizeObserver() {
        if (this._resizeObserver) return;
        
        this._resizeObserver = new ResizeObserver(entries => {
            for (const entry of entries) {
                this._updateVisibility(entry.contentRect);
            }
        });
        
        this._resizeObserver.observe(this);
    }

    _disconnectResizeObserver() {
        if (this._resizeObserver) {
            this._resizeObserver.disconnect();
            this._resizeObserver = null;
        }
    }

    _updateVisibility(rect) {
        // Obtenemos los elementos internos
        const labelEl = this.querySelector('.label')?.parentElement; // Contenedor del label
        const valueContainer = this.querySelector('.size')?.parentElement; // Contenedor del valor
        
        if (!labelEl) return;

        const height = rect.height;
        // const width = rect.width; // Podríamos usar width también si quisiéramos

        // Umbrales de visibilidad (ajustables)
        const HIDE_VALUE_THRESHOLD = 35; // px
        const HIDE_ALL_TEXT_THRESHOLD = 20; // px

        // Lógica de visibilidad progresiva
        
        // 1. Visibilidad del Valor (parte inferior)
        if (valueContainer) {
            // Si hay display-value configurado (no está hidden por defecto)
            const hasValue = this.getAttribute('display-value');
            if (hasValue) {
                if (height < HIDE_VALUE_THRESHOLD) {
                    valueContainer.classList.add('hidden');
                } else {
                    valueContainer.classList.remove('hidden');
                }
            }
        }

        // 2. Visibilidad del Label (parte superior)
        if (height < HIDE_ALL_TEXT_THRESHOLD) {
            labelEl.classList.add('hidden');
        } else {
            labelEl.classList.remove('hidden');
        }
    }

    render() {
        const label = this.getAttribute('label') || '';
        // display-value: pre-formatted text (e.g. "1.5 MB")
        const displayValue = this.getAttribute('display-value') || '';
        // color-class: complete tailwind classes strings (e.g. "bg-blue-100 ...")
        // Default to gray if not provided
        const colorClass = this.getAttribute('color-class') || 'bg-gray-100 border-gray-200 text-gray-700';
        
        // This component is the box itself.
        // We set its own classes.
        // Added container-type for simple CSS query
        this.style.containerType = 'size';
        // We assume the parent layout handles positioning/sizing (flex properties) via style attribute
        this.className = `box block w-full h-full border transition-all duration-200 overflow-hidden relative group p-1 ${colorClass}`;
        
        this.innerHTML = `
            <div class="content flex flex-col h-full w-full pointer-events-none p-0.5 overflow-hidden">
                <div class="flex-1 min-h-0">
                    <span class="label text-xs font-semibold leading-tight block truncate" title="${label}">${label}</span>
                </div>
                <div class="mt-auto pt-0.5 border-t border-black/5 ${!displayValue ? 'hidden' : ''}">
                     <span class="size text-[9px] opacity-70 text-right block truncate">${displayValue}</span>
                </div>
            </div>
            
            <title>${label} (${displayValue})</title>
        `;

        // Tras renderizar, si ya tenemos observer activo, forzamos una actualización inmediata
        // basada en las dimensiones actuales (si las tiene) para evitar parpadeo.
        if (this.offsetHeight > 0) {
            this._updateVisibility({ height: this.offsetHeight, width: this.offsetWidth });
        }
    }
}

if (!customElements.get('treemap-node')) {
    customElements.define('treemap-node', TreemapNodeLight);
}
