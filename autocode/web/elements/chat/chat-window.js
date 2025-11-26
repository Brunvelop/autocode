/**
 * chat-window.js
 * Ventana flotante para el chat con drag y resize
 * 
 * Usa Shadow DOM para que los slots funcionen correctamente
 * 
 * Atributos:
 * - title: Título de la ventana
 * - open: Si la ventana está visible (boolean attribute)
 * 
 * Eventos:
 * - toggle: Emitido al abrir/cerrar
 * - close: Emitido al cerrar
 * 
 * Métodos:
 * - open(): Abre la ventana
 * - close(): Cierra la ventana
 * - toggle(): Alterna visibilidad
 * 
 * Slots:
 * - header-actions: Acciones adicionales en el header
 * - content: Contenido principal
 * - footer: Pie de la ventana
 */

class ChatWindow extends HTMLElement {
    static get observedAttributes() {
        return ['title', 'open'];
    }

    constructor() {
        super();
        this._isOpen = false;
        this._isDragging = false;
        this._isResizing = false;
        this._dragOffset = { x: 0, y: 0 };
        
        // Crear Shadow DOM para que los slots funcionen
        this.attachShadow({ mode: 'open' });
    }

    connectedCallback() {
        this.render();
        this._setupEvents();
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue === newValue) return;
        
        if (name === 'title') {
            const titleEl = this.shadowRoot.querySelector('[data-ref="title"]');
            if (titleEl) titleEl.textContent = newValue || 'Chat';
        }
        
        if (name === 'open') {
            this._isOpen = newValue !== null;
            this._updateVisibility();
        }
    }

    render() {
        const title = this.getAttribute('title') || 'Autocode AI Chat';
        
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: contents;
                }
                
                .toggle-btn {
                    position: fixed;
                    top: 1rem;
                    left: 1rem;
                    z-index: 110;
                    background: white;
                    color: #4f46e5;
                    border-radius: 9999px;
                    padding: 1rem;
                    box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
                    border: none;
                    cursor: pointer;
                    transition: transform 0.3s, box-shadow 0.3s;
                }
                
                .toggle-btn:hover {
                    transform: scale(1.05);
                    box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1);
                }
                
                .panel {
                    position: fixed;
                    inset: 0;
                    z-index: 100;
                    background: transparent;
                    pointer-events: none;
                }
                
                .panel.hidden {
                    display: none;
                }
                
                .window {
                    position: fixed;
                    top: 5rem;
                    right: 1.5rem;
                    width: min(92vw, 560px);
                    height: 70vh;
                    min-width: 320px;
                    min-height: 300px;
                    background: white;
                    border-radius: 1rem;
                    box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.25);
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                    pointer-events: auto;
                }
                
                .header {
                    background: linear-gradient(to right, #4f46e5, #7c3aed);
                    padding: 1rem;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    cursor: grab;
                    user-select: none;
                }
                
                .header:active {
                    cursor: grabbing;
                }
                
                .header-left {
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                }
                
                .header-title {
                    color: white;
                    font-weight: bold;
                    font-size: 1.25rem;
                    margin: 0;
                }
                
                .header-right {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }
                
                .close-btn {
                    color: white;
                    background: transparent;
                    border: none;
                    border-radius: 9999px;
                    padding: 0.5rem;
                    cursor: pointer;
                    transition: background 0.2s;
                }
                
                .close-btn:hover {
                    background: rgba(79, 70, 229, 0.8);
                }
                
                .content {
                    flex: 1;
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                }
                
                .footer {
                    background: white;
                    border-top: 1px solid #e5e7eb;
                }
                
                .resize-handle {
                    position: absolute;
                    bottom: 0.5rem;
                    right: 0.5rem;
                    width: 1rem;
                    height: 1rem;
                    cursor: se-resize;
                    color: rgba(99, 102, 241, 0.5);
                    user-select: none;
                }
                
                .resize-handle:hover {
                    color: rgba(99, 102, 241, 0.8);
                }
                
                /* Estilos para contenido slotted */
                ::slotted([slot="content"]) {
                    flex: 1;
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                }
                
                /* Tailwind-like utility for header-actions slot */
                ::slotted([slot="header-actions"]) {
                    color: rgba(238, 242, 255, 0.9);
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 9999px;
                    padding: 0.375rem 0.75rem;
                    font-size: 0.875rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: background 0.2s;
                }
                
                ::slotted([slot="header-actions"]:hover) {
                    background: rgba(255, 255, 255, 0.2);
                }
            </style>
            
            <!-- Botón flotante de toggle -->
            <button data-ref="toggleBtn" class="toggle-btn">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
            </button>

            <!-- Panel de la ventana -->
            <div data-ref="panel" class="panel hidden">
                <div data-ref="window" class="window">
                    <!-- Header con drag handle -->
                    <div data-ref="dragHandle" class="header">
                        <div class="header-left">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="white">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                            </svg>
                            <h2 data-ref="title" class="header-title">${title}</h2>
                        </div>
                        <div class="header-right">
                            <slot name="header-actions"></slot>
                            <button data-ref="closeBtn" class="close-btn">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                    </div>

                    <!-- Content slot -->
                    <div data-ref="content" class="content">
                        <slot name="content"></slot>
                    </div>

                    <!-- Footer slot -->
                    <div data-ref="footer" class="footer">
                        <slot name="footer"></slot>
                    </div>

                    <!-- Resize handle -->
                    <div data-ref="resizeHandle" class="resize-handle">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 11L11 21M17 7L7 17" />
                        </svg>
                    </div>
                </div>
            </div>
        `;
    }

    _setupEvents() {
        const toggleBtn = this.shadowRoot.querySelector('[data-ref="toggleBtn"]');
        const closeBtn = this.shadowRoot.querySelector('[data-ref="closeBtn"]');
        const dragHandle = this.shadowRoot.querySelector('[data-ref="dragHandle"]');
        const resizeHandle = this.shadowRoot.querySelector('[data-ref="resizeHandle"]');
        const windowEl = this.shadowRoot.querySelector('[data-ref="window"]');

        // Toggle button
        toggleBtn?.addEventListener('click', () => this.toggle());

        // Close button
        closeBtn?.addEventListener('click', () => this.close());

        // Drag functionality
        if (dragHandle && windowEl) {
            this._setupDrag(dragHandle, windowEl);
        }

        // Resize functionality
        if (resizeHandle && windowEl) {
            this._setupResize(resizeHandle, windowEl);
        }
    }

    _setupDrag(handle, windowEl) {
        handle.addEventListener('pointerdown', (e) => {
            if (e.target.closest('button')) return; // No drag si click en botón
            
            this._isDragging = true;
            const rect = windowEl.getBoundingClientRect();
            this._dragOffset.x = e.clientX - rect.left;
            this._dragOffset.y = e.clientY - rect.top;
            
            handle.setPointerCapture(e.pointerId);
        });

        handle.addEventListener('pointermove', (e) => {
            if (!this._isDragging) return;
            
            const x = Math.max(0, Math.min(e.clientX - this._dragOffset.x, globalThis.innerWidth - windowEl.offsetWidth));
            const y = Math.max(0, Math.min(e.clientY - this._dragOffset.y, globalThis.innerHeight - windowEl.offsetHeight));
            
            windowEl.style.left = `${x}px`;
            windowEl.style.top = `${y}px`;
            windowEl.style.right = 'auto';
        });

        handle.addEventListener('pointerup', (e) => {
            this._isDragging = false;
            handle.releasePointerCapture(e.pointerId);
        });
    }

    _setupResize(handle, windowEl) {
        handle.addEventListener('pointerdown', (e) => {
            this._isResizing = true;
            handle.setPointerCapture(e.pointerId);
            e.preventDefault();
        });

        handle.addEventListener('pointermove', (e) => {
            if (!this._isResizing) return;
            
            const rect = windowEl.getBoundingClientRect();
            const newWidth = Math.max(320, e.clientX - rect.left);
            const newHeight = Math.max(300, e.clientY - rect.top);
            
            windowEl.style.width = `${newWidth}px`;
            windowEl.style.height = `${newHeight}px`;
        });

        handle.addEventListener('pointerup', (e) => {
            this._isResizing = false;
            handle.releasePointerCapture(e.pointerId);
        });
    }

    _updateVisibility() {
        const panel = this.shadowRoot.querySelector('[data-ref="panel"]');
        if (!panel) return;

        if (this._isOpen) {
            panel.classList.remove('hidden');
        } else {
            panel.classList.add('hidden');
        }
    }

    // API Pública
    open() {
        this._isOpen = true;
        this._updateVisibility();
        this.dispatchEvent(new CustomEvent('toggle', { 
            detail: { open: true },
            bubbles: true 
        }));
    }

    close() {
        this._isOpen = false;
        this._updateVisibility();
        this.dispatchEvent(new CustomEvent('close', { bubbles: true }));
        this.dispatchEvent(new CustomEvent('toggle', { 
            detail: { open: false },
            bubbles: true 
        }));
    }

    toggle() {
        if (this._isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    isOpen() {
        return this._isOpen;
    }
}

if (!customElements.get('chat-window')) {
    customElements.define('chat-window', ChatWindow);
}

export { ChatWindow };
