import './graph-node.js';

/**
 * TreeLayout
 * Visualizador de estructuras de árbol jerárquico.
 * Organiza los nodos visualmente y dibuja conexiones.
 * 
 * Propiedades:
 * - data: Objeto con la estructura del árbol
 */
export class TreeLayout extends HTMLElement {
    constructor() {
        super();
        this._data = null;
    }

    set data(value) {
        this._data = value;
        this.render();
        // Esperar al DOM update para calcular líneas
        requestAnimationFrame(() => {
            this.drawConnections();
        });
    }

    get data() {
        return this._data;
    }

    connectedCallback() {
        if (!this.innerHTML) this.render();
        window.addEventListener('resize', this._handleResize.bind(this));
    }

    disconnectedCallback() {
        window.removeEventListener('resize', this._handleResize.bind(this));
    }

    _handleResize() {
        this.drawConnections();
    }

    render() {
        // Tailwind classes
        // min-w/h ensures the tree has space to grow and center
        this.className = "block w-full h-full relative min-w-[800px] min-h-[600px]"; 
        
        this.innerHTML = `
            <svg id="connections" class="absolute top-0 left-0 w-full h-full pointer-events-none z-0 overflow-visible">
                <!-- Paths will be injected here -->
            </svg>
            
            <div id="tree-root" class="flex flex-col-reverse items-center justify-center min-h-full w-full z-10 relative pb-20 pt-10">
                ${this._data ? this._buildNodeHTML(this._data) : ''}
            </div>
        `;
    }

    _buildNodeHTML(node, depth = 0) {
        if (!node) return '';

        const hasChildren = node.children && node.children.length > 0;
        
        // Atributos para graph-node
        const label = node.data?.label || node.name || '';
        const icon = node.data?.icon || '❓';
        const type = node.data?.type || 'file';
        const id = node.id || `node-${Math.random().toString(36).substr(2,9)}`;

        let childrenHTML = '';
        if (hasChildren) {
            // Layout: children in a row - Reduced gap for compactness
            childrenHTML = `
                <div class="flex flex-row justify-center items-end gap-2 mb-12 children-container">
                    ${node.children.map(child => this._buildNodeHTML(child, depth + 1)).join('')}
                </div>
            `;
        }

        return `
            <div class="flex flex-col-reverse items-center relative node-wrapper" data-id="${id}">
                <graph-node 
                    data-id="${id}"
                    label="${label}"
                    icon="${icon}"
                    type="${type}"
                    depth="${depth}"
                    class="z-20"
                ></graph-node>
                ${childrenHTML}
            </div>
        `;
    }

    drawConnections() {
        const svg = this.querySelector('#connections');
        const treeRoot = this.querySelector('#tree-root');
        
        if (!svg || !treeRoot) return;

        svg.innerHTML = '';
        
        // Coordenadas relativas al contenedor del árbol (this)
        const rootRect = this.getBoundingClientRect();
        
        // Función recursiva para trazar líneas desde un wrapper
        const drawLines = (wrapper) => {
            // Selector directo de hijos
            const pNode = wrapper.querySelector(':scope > graph-node');
            const childrenContainer = wrapper.querySelector(':scope > .children-container');
            
            if (pNode && childrenContainer) {
                // Coordenadas del padre (Top edge, porque conecta hacia arriba hacia los hijos)
                const pRect = pNode.getBoundingClientRect();
                const pX = pRect.left + pRect.width / 2 - rootRect.left;
                const pY = pRect.top - rootRect.top; // Top edge

                Array.from(childrenContainer.children).forEach(childWrapper => {
                    const cNode = childWrapper.querySelector(':scope > graph-node');
                    if (cNode) {
                        const cRect = cNode.getBoundingClientRect();
                        const cX = cRect.left + cRect.width / 2 - rootRect.left;
                        const cY = cRect.bottom - rootRect.top; // Bottom edge (conecta hacia abajo con padre)
                        
                        // Draw curve (Vertical S-curve)
                        const midY = (pY + cY) / 2;
                        
                        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                        const d = `M ${cX} ${cY} C ${cX} ${midY}, ${pX} ${midY}, ${pX} ${pY}`;
                        
                        path.setAttribute('d', d);
                        path.setAttribute('fill', 'none');
                        path.setAttribute('stroke', '#94a3b8'); // Slate-400
                        path.setAttribute('stroke-width', '2');
                        path.setAttribute('opacity', '0.6');
                        
                        svg.appendChild(path);
                        
                        // Recursion
                        drawLines(childWrapper);
                    }
                });
            }
        };

        const rootWrapper = treeRoot.querySelector('.node-wrapper');
        if (rootWrapper) drawLines(rootWrapper);
    }
}

customElements.define('tree-layout', TreeLayout);
