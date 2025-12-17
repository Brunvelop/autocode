/**
 * recorder-controls.js
 * Botón flotante FAB para controlar la grabación
 * UI minimalista con estados: idle → recording → stopped
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { themeTokens } from './styles/theme.js';
import { recorderControlsStyles } from './styles/recorder-controls.styles.js';

export class RecorderControls extends LitElement {
    static properties = {
        isRecording: { type: Boolean },
        isSupported: { type: Boolean },
        recordingTime: { type: Number }
    };

    static styles = [themeTokens, recorderControlsStyles];

    constructor() {
        super();
        this.isRecording = false;
        this.isSupported = true;
        this.recordingTime = 0;
        this._timerInterval = null;
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this._stopTimer();
    }

    updated(changedProperties) {
        // Iniciar/detener timer cuando cambia el estado de grabación
        if (changedProperties.has('isRecording')) {
            if (this.isRecording) {
                this._startTimer();
            } else {
                this._stopTimer();
            }
        }
    }

    render() {
        const fabClass = this.isSupported 
            ? (this.isRecording ? 'recording' : '')
            : 'unsupported';

        const tooltip = this.isSupported
            ? (this.isRecording ? 'Detener grabación' : 'Iniciar grabación')
            : 'Grabación no soportada en este navegador';

        return html`
            <button 
                class="fab ${fabClass}" 
                @click=${this._handleToggle}
                ?disabled=${!this.isSupported}
                title="${tooltip}"
            >
                ${this.isRecording ? '⏹️' : '🎬'}
            </button>

            ${this.isRecording ? html`
                <div class="recording-indicator">
                    <span class="pulse-dot"></span>
                    <span>${this._formatTime(this.recordingTime)}</span>
                </div>
            ` : ''}
        `;
    }

    // ========================================================================
    // EVENT HANDLERS
    // ========================================================================

    _handleToggle() {
        if (!this.isSupported) return;

        this.dispatchEvent(new CustomEvent('toggle', {
            detail: { isRecording: this.isRecording },
            bubbles: true,
            composed: true
        }));
    }

    // ========================================================================
    // TIMER LOGIC
    // ========================================================================

    _startTimer() {
        this.recordingTime = 0;
        this._timerInterval = setInterval(() => {
            this.recordingTime++;
        }, 1000);
    }

    _stopTimer() {
        if (this._timerInterval) {
            clearInterval(this._timerInterval);
            this._timerInterval = null;
        }
        this.recordingTime = 0;
    }

    // ========================================================================
    // HELPERS
    // ========================================================================

    _formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
}

if (!customElements.get('recorder-controls')) {
    customElements.define('recorder-controls', RecorderControls);
}
