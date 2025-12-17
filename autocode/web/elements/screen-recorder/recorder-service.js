/**
 * recorder-service.js
 * Servicio de lógica pura para grabación de pantalla
 * Encapsula MediaRecorder API y gestión de streams
 */

export class RecorderService {
    constructor() {
        this.mediaRecorder = null;
        this.chunks = [];
        this.stream = null;
        this.startTime = null;
    }

    /**
     * Inicia la grabación de pantalla
     * @param {string} target - 'fullscreen' o selector CSS (fase 2)
     * @param {object} options - Opciones de grabación
     * @returns {Promise<void>}
     */
    async startRecording(target = 'fullscreen', options = {}) {
        // Limpiar chunks anteriores
        this.chunks = [];

        // Obtener stream de pantalla
        if (target === 'fullscreen') {
            try {
                this.stream = await navigator.mediaDevices.getDisplayMedia({
                    video: {
                        cursor: 'always',
                        displaySurface: 'monitor'
                    },
                    audio: options.audio ?? true
                });
            } catch (error) {
                throw new Error(`Error al capturar pantalla: ${error.message}`);
            }
        } else {
            // Captura de elementos específicos (fase 2)
            throw new Error('Captura de elementos específicos no implementada aún');
        }

        // Configurar MediaRecorder
        const mimeType = this._getSupportedMimeType();
        const recorderOptions = {
            mimeType,
            videoBitsPerSecond: options.videoBitsPerSecond || 2500000
        };

        try {
            this.mediaRecorder = new MediaRecorder(this.stream, recorderOptions);
        } catch (error) {
            this.stream.getTracks().forEach(track => track.stop());
            throw new Error(`Error al crear MediaRecorder: ${error.message}`);
        }

        // Capturar datos
        this.mediaRecorder.ondataavailable = (e) => {
            if (e.data && e.data.size > 0) {
                this.chunks.push(e.data);
            }
        };

        // Detectar cuando el usuario cierra el compartir pantalla
        this.stream.getVideoTracks()[0].addEventListener('ended', () => {
            if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                this.mediaRecorder.stop();
            }
        });

        // Iniciar grabación
        this.startTime = Date.now();
        this.mediaRecorder.start(100); // Chunks cada 100ms para mejor granularidad
    }

    /**
     * Detiene la grabación y retorna el blob del video
     * @returns {Promise<Blob>}
     */
    stopRecording() {
        return new Promise((resolve, reject) => {
            if (!this.mediaRecorder) {
                reject(new Error('No hay grabación activa'));
                return;
            }

            this.mediaRecorder.onstop = () => {
                // Detener tracks del stream
                if (this.stream) {
                    this.stream.getTracks().forEach(track => track.stop());
                }

                // Crear blob del video
                const mimeType = this.mediaRecorder.mimeType || 'video/webm';
                const blob = new Blob(this.chunks, { type: mimeType });
                
                // Limpiar
                this.mediaRecorder = null;
                this.stream = null;
                
                resolve(blob);
            };

            this.mediaRecorder.onerror = (error) => {
                reject(new Error(`Error durante la grabación: ${error.message}`));
            };

            this.mediaRecorder.stop();
        });
    }

    /**
     * Pausa la grabación (si está activa)
     */
    pauseRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.pause();
        }
    }

    /**
     * Resume la grabación (si está pausada)
     */
    resumeRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'paused') {
            this.mediaRecorder.resume();
        }
    }

    /**
     * Obtiene el estado actual de la grabación
     * @returns {string} - 'inactive', 'recording', 'paused'
     */
    getState() {
        return this.mediaRecorder ? this.mediaRecorder.state : 'inactive';
    }

    /**
     * Obtiene el tiempo transcurrido de grabación en segundos
     * @returns {number}
     */
    getElapsedTime() {
        if (!this.startTime) return 0;
        return Math.floor((Date.now() - this.startTime) / 1000);
    }

    /**
     * Verifica si el navegador soporta grabación de pantalla
     * @returns {boolean}
     */
    static isSupported() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia);
    }

    /**
     * Obtiene el primer mime type soportado por el navegador
     * @private
     * @returns {string}
     */
    _getSupportedMimeType() {
        const types = [
            'video/webm;codecs=vp9,opus',
            'video/webm;codecs=vp9',
            'video/webm;codecs=vp8,opus',
            'video/webm;codecs=vp8',
            'video/webm',
            'video/mp4'
        ];

        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }

        return 'video/webm'; // Fallback
    }
}
