/**
 * index.js (screen-recorder)
 * Componente orquestador principal que integra todos los subcomponentes
 * Patrón standalone: No extiende AutoFunctionController (no hay backend)
 * 
 * Uso:
 * <screen-recorder></screen-recorder>
 * 
 * API Programática:
 * const recorder = document.querySelector('screen-recorder');
 * await recorder.startRecording();
 * await recorder.stopRecording();
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { themeTokens } from './styles/theme.js';
import { RecorderService } from './recorder-service.js';

// Importar sub-componentes
import './recorder-controls.js';
import './video-player.js';

export class ScreenRecorder extends LitElement {
    static properties = {
        _isRecording: { type: Boolean, state: true },
        _recordingBlob: { type: Object, state: true },
        _showPlayer: { type: Boolean, state: true },
        _isSupported: { type: Boolean, state: true }
    };

    static styles = [themeTokens];

    constructor() {
        super();
        
        // Estado
        this._isRecording = false;
        this._recordingBlob = null;
        this._showPlayer = false;
        
        // Servicio de grabación (lógica pura)
        this._service = new RecorderService();
        
        // Verificar soporte del navegador
        this._isSupported = RecorderService.isSupported();
        
        if (!this._isSupported) {
            console.warn('⚠️ Screen recording no soportado en este navegador');
        }
    }

    connectedCallback() {
        super.connectedCallback();
        
        // Escuchar eventos de los sub-componentes
        this.addEventListener('toggle', this._handleToggle);
        this.addEventListener('close', this._handlePlayerClose);
        this.addEventListener('rerecord', this._handleRerecord);
        this.addEventListener('download', this._handleDownload);
    }

    render() {
        return html`
            <!-- Controles flotantes (FAB) -->
            <recorder-controls
                .isRecording=${this._isRecording}
                .isSupported=${this._isSupported}>
            </recorder-controls>

            <!-- Modal del reproductor (solo visible después de grabar) -->
            ${this._showPlayer && this._recordingBlob ? html`
                <video-player
                    .blob=${this._recordingBlob}
                    .visible=${this._showPlayer}>
                </video-player>
            ` : ''}
        `;
    }

    // ========================================================================
    // EVENT HANDLERS
    // ========================================================================

    async _handleToggle(e) {
        // Toggle entre iniciar y detener grabación
        if (this._isRecording) {
            await this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    _handlePlayerClose() {
        this._showPlayer = false;
        this._recordingBlob = null;
    }

    _handleRerecord() {
        // Cerrar player y preparar para nueva grabación
        this._showPlayer = false;
        this._recordingBlob = null;
        
        // Opcionalmente, iniciar grabación automáticamente
        // this.startRecording();
    }

    _handleDownload(e) {
        console.log('📥 Video descargado:', e.detail.filename);
    }

    // ========================================================================
    // PUBLIC API (para uso programático)
    // ========================================================================

    /**
     * Inicia la grabación de pantalla
     * @param {string} target - 'fullscreen' o selector CSS (fase 2)
     * @param {object} options - Opciones de grabación
     * @returns {Promise<void>}
     */
    async startRecording(target = 'fullscreen', options = {}) {
        if (!this._isSupported) {
            throw new Error('Screen recording no soportado en este navegador');
        }

        if (this._isRecording) {
            console.warn('⚠️ Ya hay una grabación en progreso');
            return;
        }

        try {
            // Iniciar servicio de grabación
            await this._service.startRecording(target, options);
            
            this._isRecording = true;
            
            // Emitir evento
            this.dispatchEvent(new CustomEvent('recording-start', {
                detail: { target, options },
                bubbles: true,
                composed: true
            }));
            
            console.log('🎬 Grabación iniciada');
        } catch (error) {
            console.error('❌ Error al iniciar grabación:', error);
            
            this.dispatchEvent(new CustomEvent('recording-error', {
                detail: { error: error.message },
                bubbles: true,
                composed: true
            }));
            
            throw error;
        }
    }

    /**
     * Detiene la grabación y muestra el preview
     * @returns {Promise<Blob>}
     */
    async stopRecording() {
        if (!this._isRecording) {
            console.warn('⚠️ No hay grabación activa');
            return null;
        }

        try {
            // Detener servicio y obtener blob
            this._recordingBlob = await this._service.stopRecording();
            
            this._isRecording = false;
            this._showPlayer = true;
            
            // Emitir evento
            this.dispatchEvent(new CustomEvent('recording-stop', {
                detail: { blob: this._recordingBlob },
                bubbles: true,
                composed: true
            }));
            
            console.log('⏹️ Grabación detenida:', {
                size: this._formatSize(this._recordingBlob.size),
                type: this._recordingBlob.type
            });
            
            return this._recordingBlob;
        } catch (error) {
            console.error('❌ Error al detener grabación:', error);
            this._isRecording = false;
            
            this.dispatchEvent(new CustomEvent('recording-error', {
                detail: { error: error.message },
                bubbles: true,
                composed: true
            }));
            
            throw error;
        }
    }

    /**
     * Pausa la grabación (si está activa)
     */
    pauseRecording() {
        if (this._isRecording) {
            this._service.pauseRecording();
            
            this.dispatchEvent(new CustomEvent('recording-pause', {
                bubbles: true,
                composed: true
            }));
        }
    }

    /**
     * Resume la grabación (si está pausada)
     */
    resumeRecording() {
        if (this._isRecording) {
            this._service.resumeRecording();
            
            this.dispatchEvent(new CustomEvent('recording-resume', {
                bubbles: true,
                composed: true
            }));
        }
    }

    /**
     * Obtiene el estado actual de la grabación
     * @returns {Object}
     */
    getState() {
        return {
            isRecording: this._isRecording,
            isSupported: this._isSupported,
            hasRecording: !!this._recordingBlob,
            recordingState: this._service.getState(),
            elapsedTime: this._service.getElapsedTime()
        };
    }

    /**
     * Obtiene el blob de la última grabación
     * @returns {Blob|null}
     */
    getRecording() {
        return this._recordingBlob;
    }

    /**
     * Limpia la grabación actual sin mostrar el player
     */
    clearRecording() {
        this._recordingBlob = null;
        this._showPlayer = false;
    }

    /**
     * Muestra el player con la grabación actual (si existe)
     */
    showPlayer() {
        if (this._recordingBlob) {
            this._showPlayer = true;
        }
    }

    /**
     * Oculta el player
     */
    hidePlayer() {
        this._showPlayer = false;
    }

    // ========================================================================
    // STATIC METHODS
    // ========================================================================

    /**
     * Verifica si el navegador soporta grabación de pantalla
     * @returns {boolean}
     */
    static isSupported() {
        return RecorderService.isSupported();
    }

    // ========================================================================
    // HELPERS
    // ========================================================================

    _formatSize(bytes) {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }
}

// Registrar el custom element
if (!customElements.get('screen-recorder')) {
    customElements.define('screen-recorder', ScreenRecorder);
}

// Verificar soporte al cargar el módulo
if (!ScreenRecorder.isSupported()) {
    console.warn('⚠️ Screen Recorder: Este navegador no soporta la API de captura de pantalla (MediaDevices.getDisplayMedia)');
}
