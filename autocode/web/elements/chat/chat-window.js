/**
 * chat-window.js
 * Ventana flotante para el chat con drag y resize
 * Refactorizado: Lógica pura separada de estilos
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { chatWindowStyles } from './styles/chat-window.styles.js';
import { themeTokens } from './styles/theme.js';

export class ChatWindow extends LitElement {
    static properties = {
        title: { type: String },
        open: { type: Boolean, reflect: true }
    };

    static styles = [themeTokens, chatWindowStyles];

    constructor() {
        super();
        this.title = 'Autocode AI Chat';
        this.open = false;
        
        // Estado interno para drag/resize
        this._isDragging = false;
        this._isResizing = false;
        this._dragOffset = { x: 0, y: 0 };
    }

    render() {
        return html`
            <!-- Botón flotante de toggle -->
            <button class="toggle-btn" @click=${this.toggle} title="Abrir Chat">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
            </button>

            <!-- Panel de la ventana -->
            <div class="panel ${this.open ? '' : 'hidden'}" part="panel">
                <div class="window" part="window" id="window">
                    <!-- Header con zonas separadas -->
                    <div class="header">
                        <!-- Zona draggable: Solo icono y título -->
                        <div class="drag-handle" @pointerdown=${this._startDrag}>
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="white">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                            </svg>
                            <h2 class="header-title">${this.title}</h2>
                        </div>
                        
                        <!-- Zona interactiva: Botones y acciones -->
                        <div class="header-actions">
                            <slot name="header-actions"></slot>
                            <button class="close-btn" @click=${this.close} title="Cerrar">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                    </div>

                    <!-- Content slot -->
                    <div class="content">
                        <slot name="content"></slot>
                    </div>

                    <!-- Footer slot -->
                    <div class="footer">
                        <slot name="footer"></slot>
                    </div>

                    <!-- Resize handle -->
                    <div class="resize-handle" @pointerdown=${this._startResize}>
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 11L11 21M17 7L7 17" />
                        </svg>
                    </div>
                </div>
            </div>
        `;
    }

    // ========================================================================
    // DRAG & DROP LOGIC
    // ========================================================================

    _startDrag(e) {
        const windowEl = this.shadowRoot.getElementById('window');
        if (!windowEl) return;

        this._isDragging = true;
        const rect = windowEl.getBoundingClientRect();
        this._dragOffset.x = e.clientX - rect.left;
        this._dragOffset.y = e.clientY - rect.top;

        // Capturar puntero para seguimiento suave
        e.target.setPointerCapture(e.pointerId);
        
        // Listeners temporales
        this._onDragMove = (ev) => this._handleDragMove(ev, windowEl);
        this._onDragUp = (ev) => this._stopDrag(ev, e.target);
        
        e.target.addEventListener('pointermove', this._onDragMove);
        e.target.addEventListener('pointerup', this._onDragUp);
    }

    _handleDragMove(e, windowEl) {
        if (!this._isDragging) return;

        const x = Math.max(0, Math.min(e.clientX - this._dragOffset.x, window.innerWidth - windowEl.offsetWidth));
        const y = Math.max(0, Math.min(e.clientY - this._dragOffset.y, window.innerHeight - windowEl.offsetHeight));

        windowEl.style.left = `${x}px`;
        windowEl.style.top = `${y}px`;
        windowEl.style.right = 'auto'; // Reset right si estaba seteado
    }

    _stopDrag(e, target) {
        this._isDragging = false;
        target.releasePointerCapture(e.pointerId);
        target.removeEventListener('pointermove', this._onDragMove);
        target.removeEventListener('pointerup', this._onDragUp);
    }

    // ========================================================================
    // RESIZE LOGIC
    // ========================================================================

    _startResize(e) {
        e.preventDefault(); // Evitar selección de texto
        this._isResizing = true;
        
        const windowEl = this.shadowRoot.getElementById('window');
        e.target.setPointerCapture(e.pointerId);

        this._onResizeMove = (ev) => this._handleResizeMove(ev, windowEl);
        this._onResizeUp = (ev) => this._stopResize(ev, e.target);

        e.target.addEventListener('pointermove', this._onResizeMove);
        e.target.addEventListener('pointerup', this._onResizeUp);
    }

    _handleResizeMove(e, windowEl) {
        if (!this._isResizing) return;

        const rect = windowEl.getBoundingClientRect();
        const newWidth = Math.max(320, e.clientX - rect.left);
        const newHeight = Math.max(300, e.clientY - rect.top);

        windowEl.style.width = `${newWidth}px`;
        windowEl.style.height = `${newHeight}px`;
    }

    _stopResize(e, target) {
        this._isResizing = false;
        target.releasePointerCapture(e.pointerId);
        target.removeEventListener('pointermove', this._onResizeMove);
        target.removeEventListener('pointerup', this._onResizeUp);
    }

    // ========================================================================
    // PUBLIC API
    // ========================================================================

    toggle() {
        this.open = !this.open;
        this.dispatchEvent(new CustomEvent('toggle', {
            detail: { open: this.open },
            bubbles: true,
            composed: true
        }));
    }

    openWindow() {
        this.open = true;
        this.dispatchEvent(new CustomEvent('toggle', {
            detail: { open: true },
            bubbles: true,
            composed: true
        }));
    }

    close() {
        this.open = false;
        this.dispatchEvent(new CustomEvent('close', { bubbles: true, composed: true }));
        this.dispatchEvent(new CustomEvent('toggle', {
            detail: { open: false },
            bubbles: true,
            composed: true
        }));
    }
}

if (!customElements.get('chat-window')) {
    customElements.define('chat-window', ChatWindow);
}
