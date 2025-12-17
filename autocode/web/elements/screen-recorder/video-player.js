/**
 * video-player.js
 * Modal para previsualizar y gestionar el video grabado
 * Muestra el video con controles nativos y opciones para descargar o regrabar
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { themeTokens } from './styles/theme.js';
import { videoPlayerStyles } from './styles/video-player.styles.js';

export class VideoPlayer extends LitElement {
    static properties = {
        blob: { type: Object },
        visible: { type: Boolean }
    };

    static styles = [themeTokens, videoPlayerStyles];

    constructor() {
        super();
        this.blob = null;
        this.visible = true;
        this._videoUrl = null;
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this._revokeUrl();
    }

    updated(changedProperties) {
        if (changedProperties.has('blob') && this.blob) {
            this._createVideoUrl();
        }
    }

    render() {
        if (!this.visible || !this.blob) {
            return html``;
        }

        const videoInfo = this._getVideoInfo();

        return html`
            <div class="overlay" @click=${this._handleOverlayClick}>
                <div class="player-container" @click=${e => e.stopPropagation()}>
                    <!-- Header -->
                    <div class="header">
                        <h3 class="title">
                            🎬 Vista previa de la grabación
                        </h3>
                        <button class="close-btn" @click=${this._handleClose} title="Cerrar">
                            ✕
                        </button>
                    </div>

                    <!-- Video -->
                    <div class="video-wrapper">
                        ${this._videoUrl ? html`
                            <video 
                                src="${this._videoUrl}" 
                                controls 
                                autoplay
                                @error=${this._handleVideoError}
                            ></video>
                        ` : html`
                            <div style="color: white; padding: 40px;">
                                Cargando video...
                            </div>
                        `}
                    </div>

                    <!-- Info del video -->
                    <div class="video-info">
                        <span>📊 ${videoInfo.size}</span>
                        <span>🎞️ ${videoInfo.format}</span>
                    </div>

                    <!-- Acciones -->
                    <div class="actions">
                        <button 
                            class="action-btn primary" 
                            @click=${this._handleDownload}
                        >
                            💾 Descargar
                        </button>
                        <button 
                            class="action-btn secondary" 
                            @click=${this._handleRerecord}
                        >
                            🔄 Grabar de nuevo
                        </button>
                        <button 
                            class="action-btn secondary" 
                            @click=${this._handleClose}
                        >
                            ❌ Cerrar
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // ========================================================================
    // EVENT HANDLERS
    // ========================================================================

    _handleOverlayClick() {
        // Cerrar al hacer click fuera del modal
        this._handleClose();
    }

    _handleClose() {
        this.dispatchEvent(new CustomEvent('close', {
            bubbles: true,
            composed: true
        }));
    }

    _handleDownload() {
        if (!this.blob) return;

        const filename = this._generateFilename();
        const url = URL.createObjectURL(this.blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);

        this.dispatchEvent(new CustomEvent('download', {
            detail: { filename },
            bubbles: true,
            composed: true
        }));
    }

    _handleRerecord() {
        this.dispatchEvent(new CustomEvent('rerecord', {
            bubbles: true,
            composed: true
        }));
    }

    _handleVideoError(e) {
        console.error('Error cargando video:', e);
        this.dispatchEvent(new CustomEvent('video-error', {
            detail: { error: e },
            bubbles: true,
            composed: true
        }));
    }

    // ========================================================================
    // VIDEO MANAGEMENT
    // ========================================================================

    _createVideoUrl() {
        // Revocar URL anterior si existe
        this._revokeUrl();

        if (this.blob) {
            this._videoUrl = URL.createObjectURL(this.blob);
            this.requestUpdate();
        }
    }

    _revokeUrl() {
        if (this._videoUrl) {
            URL.revokeObjectURL(this._videoUrl);
            this._videoUrl = null;
        }
    }

    // ========================================================================
    // HELPERS
    // ========================================================================

    _getVideoInfo() {
        if (!this.blob) {
            return { size: '-', format: '-' };
        }

        return {
            size: this._formatSize(this.blob.size),
            format: this._getFormat(this.blob.type)
        };
    }

    _formatSize(bytes) {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }

    _getFormat(mimeType) {
        if (!mimeType) return 'WebM';
        
        if (mimeType.includes('webm')) return 'WebM';
        if (mimeType.includes('mp4')) return 'MP4';
        if (mimeType.includes('ogg')) return 'OGG';
        
        return mimeType.split('/')[1]?.toUpperCase() || 'Unknown';
    }

    _generateFilename() {
        const date = new Date();
        const dateStr = date.toISOString().slice(0, 10);
        const timeStr = date.toTimeString().slice(0, 8).replace(/:/g, '-');
        const extension = this._getFormat(this.blob.type).toLowerCase();
        
        return `recording-${dateStr}-${timeStr}.${extension}`;
    }
}

if (!customElements.get('video-player')) {
    customElements.define('video-player', VideoPlayer);
}
