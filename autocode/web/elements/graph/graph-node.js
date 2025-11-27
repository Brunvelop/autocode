/**
 * GraphNode
 * Un nodo visual genérico dentro del grafo
 * 
 * Atributos:
 * - label: Texto a mostrar
 * - icon: Emoji o caracter a mostrar en la burbuja
 * - type: Variación visual ('directory', 'file', 'root', etc.) -> Esto podría ser más genérico (variant='primary|secondary') pero mantengamos compatibilidad semántica por ahora.
 * - depth: Profundidad en el árbol (0-based)
 * 
 * Eventos:
 * - node-click: Emitido al hacer click (detail: { id, type })
 */
export class GraphNode extends HTMLElement {
    static get observedAttributes() {
        return ['label', 'icon', 'type', 'depth'];
    }

    constructor() {
        super();
        // Removed Shadow DOM for Tailwind
    }

    connectedCallback() {
        this.render();
        this.addEventListener('click', this._handleClick.bind(this));
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue === newValue) return;
        this.render();
    }

    _handleClick(e) {
        e.stopPropagation();
        this.dispatchEvent(new CustomEvent('node-click', {
            detail: {
                id: this.dataset.id,
                type: this.getAttribute('type')
            },
            bubbles: true,
            composed: true
        }));
    }

    render() {
        const label = this.getAttribute('label') || '';
        const icon = this.getAttribute('icon') || '❓';
        const type = this.getAttribute('type') || 'default';
        const depth = parseInt(this.getAttribute('depth') || '0', 10);

        // Styling Logic (Tailwind)
        // Depth-based sizing
        let sizeClass = "w-8 h-8 text-base"; // Default small
        let labelClass = "text-xs opacity-80";

        if (depth === 0) {
            sizeClass = "w-24 h-24 text-5xl border-[4px]";
            labelClass = "text-lg font-bold opacity-100";
        } else if (depth === 1) {
            sizeClass = "w-16 h-16 text-3xl border-[3px]";
            labelClass = "text-sm font-medium opacity-90";
        } else if (depth === 2) {
            sizeClass = "w-12 h-12 text-xl border-[2px]";
            labelClass = "text-xs opacity-85";
        } else {
            // Depth 3+
            sizeClass = "w-8 h-8 text-sm border-[1.5px]";
            labelClass = "text-[10px] opacity-70";
        }

        // Color variants logic
        // TODO: Make this configurable via CSS variables or specific attributes instead of hardcoded types
        let bgClass = "bg-sky-100 border-sky-400 text-sky-700"; // Default
        
        if (type === 'directory' || type === 'group') {
            bgClass = "bg-amber-100 border-amber-400 text-amber-800";
        } else if (type === 'root' || type === 'main') {
            bgClass = "bg-green-100 border-green-500 text-green-800";
        } else if (type === 'file' || type === 'item') {
            bgClass = "bg-sky-50 border-sky-300 text-sky-700";
        }

        this.className = "flex flex-col-reverse items-center relative z-20 select-none group cursor-pointer";

        this.innerHTML = `
            <div class="label writing-mode-vertical transform rotate-180 mb-2 whitespace-nowrap text-gray-600 transition-all group-hover:opacity-100 group-hover:font-semibold group-hover:text-gray-900 [writing-mode:vertical-rl] ${labelClass}">
                ${label}
            </div>
            
            <div class="bubble rounded-full flex items-center justify-center shadow-sm transition-all duration-200 group-hover:scale-110 group-hover:z-30 group-hover:shadow-md group-active:scale-95 ${sizeClass} ${bgClass}">
                ${icon}
            </div>
        `;
    }
}

customElements.define('graph-node', GraphNode);
