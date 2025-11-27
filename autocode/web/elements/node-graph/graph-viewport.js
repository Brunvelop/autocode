/**
 * GraphViewport
 * Componente genérico para visualización de grafos con soporte de Pan & Zoom.
 * Actúa como un contenedor "lienzo infinito" para cualquier contenido inyectado.
 * 
 * Uso:
 * <graph-viewport>
 *    <any-graph-content></any-graph-content>
 * </graph-viewport>
 */
export class GraphViewport extends HTMLElement {
    constructor() {
        super();
        this._container = null;
        this._transformLayer = null;
        
        // Transform State
        this.scale = 1;
        this.panning = false;
        this.pointX = 0;
        this.pointY = 0;
        this.startX = 0;
        this.startY = 0;
    }

    connectedCallback() {
        // Light DOM Slotting Strategy:
        // 1. Capture original children (content to be projected)
        const contentNodes = Array.from(this.childNodes);
        
        // 2. Render Template
        this.render();
        
        // 3. Project content into destination
        this._container = this.querySelector('#viewport-container');
        this._transformLayer = this.querySelector('#transform-layer');

        if (this._transformLayer) {
            contentNodes.forEach(node => this._transformLayer.appendChild(node));
        }
        
        this.setupInteractions();

        // Initial Layout attempt
        requestAnimationFrame(() => this.fitToScreen());
    }

    render() {
        // Prevent re-rendering if already rendered (to protect event listeners and state)
        if (this.querySelector('#viewport-container')) return;

        this.className = "block w-full h-full relative font-sans overflow-hidden";

        this.innerHTML = `
            <!-- Viewport Container -->
            <div id="viewport-container" class="w-full h-full overflow-hidden relative cursor-grab active:cursor-grabbing touch-none select-none bg-gradient-to-t from-gray-50 to-white">
                
                <!-- Transform Layer -->
                <div id="transform-layer" class="origin-top-left will-change-transform transition-transform duration-75 ease-out absolute top-0 left-0 min-w-full min-h-full flex items-center justify-center">
                    <!-- Manual Slot Injection Point -->
                </div>
            </div>

            <!-- UI Controls -->
            <div class="absolute bottom-6 right-6 flex flex-col gap-2 z-50">
                 <button id="btn-zoom-in" class="w-10 h-10 rounded-lg bg-white border border-gray-200 shadow-sm hover:bg-gray-50 hover:border-gray-300 flex items-center justify-center text-gray-600 transition-all active:scale-95" title="Zoom In">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                </button>
                 <button id="btn-zoom-out" class="w-10 h-10 rounded-lg bg-white border border-gray-200 shadow-sm hover:bg-gray-50 hover:border-gray-300 flex items-center justify-center text-gray-600 transition-all active:scale-95" title="Zoom Out">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                </button>
                <div class="h-2"></div>
                <button id="btn-fit" class="w-10 h-10 rounded-lg bg-white border border-gray-200 shadow-sm hover:bg-gray-50 hover:border-gray-300 flex items-center justify-center text-gray-600 transition-all active:scale-95" title="Center View">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
                    </svg>
                </button>
            </div>
        `;
    }

    setupInteractions() {
        this.querySelector('#btn-fit')?.addEventListener('click', (e) => { e.stopPropagation(); this.fitToScreen(); });
        this.querySelector('#btn-zoom-in')?.addEventListener('click', (e) => { e.stopPropagation(); this.zoom(1.2); });
        this.querySelector('#btn-zoom-out')?.addEventListener('click', (e) => { e.stopPropagation(); this.zoom(0.8); });

        if (!this._container) return;

        this._container.addEventListener('mousedown', (e) => {
            if (e.target.closest('button')) return;
            e.preventDefault();
            this.panning = true;
            this.startX = e.clientX - this.pointX;
            this.startY = e.clientY - this.pointY;
            this._container.style.cursor = 'grabbing';
        });

        window.addEventListener('mousemove', (e) => {
            if (!this.panning) return;
            e.preventDefault();
            this.pointX = e.clientX - this.startX;
            this.pointY = e.clientY - this.startY;
            this.updateTransform();
        });

        window.addEventListener('mouseup', () => {
            this.panning = false;
            if (this._container) this._container.style.cursor = 'grab';
        });

        this._container.addEventListener('wheel', (e) => {
            e.preventDefault();
            const xs = (e.clientX - this.pointX) / this.scale;
            const ys = (e.clientY - this.pointY) / this.scale;
            
            const delta = -Math.sign(e.deltaY);
            const step = 0.1;
            const zoomFactor = 1 + (delta * step);
            const newScale = Math.min(Math.max(0.1, this.scale * zoomFactor), 5);
            
            this.pointX = e.clientX - xs * newScale;
            this.pointY = e.clientY - ys * newScale;
            this.scale = newScale;
            
            this.updateTransform();
        }, { passive: false });
    }
    
    zoom(factor) {
        if (!this._container) return;
        const rect = this._container.getBoundingClientRect();
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const xs = (centerX - this.pointX) / this.scale;
        const ys = (centerY - this.pointY) / this.scale;
        
        const newScale = Math.min(Math.max(0.1, this.scale * factor), 5);
        
        this.pointX = centerX - xs * newScale;
        this.pointY = centerY - ys * newScale;
        this.scale = newScale;
        
        this.updateTransform();
    }

    updateTransform() {
        if (this._transformLayer) {
            this._transformLayer.style.transform = `translate(${this.pointX}px, ${this.pointY}px) scale(${this.scale})`;
        }
    }

    /**
     * Centra el contenido en el viewport.
     */
    fitToScreen() {
        if (!this._container) return;

        // Reset scale
        this.scale = 1;

        const containerRect = this._container.getBoundingClientRect();
        
        // Obtenemos el tamaño del contenido inyectado
        // Al usar slot, firstElementChild del transformLayer sería el slot
        // Necesitamos el assigned element o el tamaño del propio transformLayer si el layout lo permite
        // Pero transformLayer tiene min-w-full.
        // Vamos a intentar obtener el primer elemento hijo efectivo.
        
        let contentRect = { width: 0, height: 0, top: 0, left: 0 };
        const content = this.querySelector('node-graph') || this.children[0];
        
        if (content && content.getBoundingClientRect) {
            contentRect = content.getBoundingClientRect(); 
            // Cuidado: getBoundingClientRect incluye la transformacion actual.
            // Necesitamos las dimensiones "naturales" o resetear primero.
            // Pero como scale=1 ahora mismo (lo acabamos de poner), deberia ser correcto relativo a viewport.
        }

        // Si el contenido es dinámico y no ha cargado, width puede ser 0.
        // Asumimos centro absoluto si no hay dimensiones.
        
        // Simplemente centramos el layer container en el viewport container.
        // Al final, el usuario quiere ver el centro del "Garden".
        
        // El garden-tree original tenía su propio centro.
        // Vamos a centrar el (0,0) del transform layer en el centro del viewport.
        
        // Si el node-graph tiene un tamaño fijo min-w-[800px], queremos centrar ese bloque.
        
        // Estrategia simplificada:
        // Centrar: pointX = (ContainerW - ContentW) / 2
        
        // Si no detectamos contenido, usamos un valor por defecto
        const contentW = contentRect.width || 800;
        const contentH = contentRect.height || 600;

        this.pointX = (containerRect.width / 2) - (contentW / 2);
        this.pointY = (containerRect.height / 2) - (contentH / 2);
        
        this.updateTransform();
    }
}

customElements.define('graph-viewport', GraphViewport);
