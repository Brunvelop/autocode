/**
 * chat-debug-info.js
 * Componente para visualizar metadatos técnicos de la respuesta del chat
 * Muestra métricas de tokens, modelo utilizado y JSON crudo de la respuesta.
 */

class ChatDebugInfo extends HTMLElement {
    constructor() {
        super();
        this._data = null;
    }

    set data(value) {
        this._data = value;
        this.render();
    }

    get data() {
        return this._data;
    }

    connectedCallback() {
        if (!this.innerHTML && this._data) {
            this.render();
        }
    }

    render() {
        if (!this._data) {
            this.innerHTML = '';
            return;
        }

        const metrics = this._extractMetrics(this._data);
        const hasMetrics = metrics.model || metrics.total_tokens;

        this.innerHTML = `
            <details class="group bg-gray-50/50 rounded-lg border border-gray-200 overflow-hidden mt-4 text-xs">
                <summary class="px-3 py-2 cursor-pointer hover:bg-gray-100 transition-colors flex items-center select-none text-gray-500 gap-2">
                    <span class="flex items-center gap-2">
                        <span>🐞 Info Técnica</span>
                        ${hasMetrics ? `
                            <span class="text-gray-300">|</span>
                            <span class="font-mono text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-100">
                                ${metrics.model ? metrics.model.split('/').pop() : 'Unknown Model'}
                            </span>
                            ${metrics.total_tokens ? `
                                <span class="font-mono text-gray-600 bg-gray-100 px-1.5 py-0.5 rounded border border-gray-200">
                                    ${metrics.total_tokens} tokens
                                </span>
                            ` : ''}
                        ` : ''}
                    </span>
                    <svg class="w-4 h-4 ml-auto transform group-open:rotate-180 transition-transform text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                </summary>

                <div class="p-3 border-t border-gray-200 space-y-3">
                    <!-- Metrics Grid -->
                    ${this._renderMetricsGrid(metrics)}

                    <!-- JSON Viewer -->
                    <div class="space-y-1">
                        <div class="text-[10px] uppercase font-bold text-gray-400 tracking-wider">Raw Response</div>
                        <pre class="bg-gray-900 text-gray-100 p-3 rounded-lg overflow-x-auto font-mono text-[10px] leading-relaxed">${JSON.stringify(this._data, null, 2)}</pre>
                    </div>
                </div>
            </details>
        `;
    }

    _extractMetrics(data) {
        // Valores por defecto
        let metrics = {
            model: null,
            prompt_tokens: 0,
            completion_tokens: 0,
            total_tokens: 0,
            cost: null
        };

        // 1. Intentar sacar de la raíz (algunos backends lo ponen directo)
        if (data.model) metrics.model = data.model;
        if (data.usage) {
            metrics.prompt_tokens = data.usage.prompt_tokens || 0;
            metrics.completion_tokens = data.usage.completion_tokens || 0;
            metrics.total_tokens = data.usage.total_tokens || 0;
        }

        // 2. Intentar sacar del último paso del historial (DSPy suele ponerlo ahí)
        if (data.history && Array.isArray(data.history) && data.history.length > 0) {
            const lastStep = data.history[data.history.length - 1];
            
            // Modelo
            if (lastStep.model) metrics.model = lastStep.model;
            
            // Usage (a veces está en response.usage o directo en usage)
            let usage = lastStep.usage;
            if (!usage && lastStep.response && lastStep.response.usage) {
                usage = lastStep.response.usage;
            }

            if (usage) {
                metrics.prompt_tokens = usage.prompt_tokens || metrics.prompt_tokens;
                metrics.completion_tokens = usage.completion_tokens || metrics.completion_tokens;
                metrics.total_tokens = usage.total_tokens || metrics.total_tokens;
            }
        }

        return metrics;
    }

    _renderMetricsGrid(metrics) {
        // Solo renderizar si hay al menos alguna métrica relevante
        if (!metrics.total_tokens && !metrics.model) return '';

        return `
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <div class="bg-white p-2 rounded border border-gray-100">
                    <div class="text-[10px] text-gray-400 uppercase">Prompt</div>
                    <div class="font-mono font-semibold text-gray-700">${metrics.prompt_tokens}</div>
                </div>
                <div class="bg-white p-2 rounded border border-gray-100">
                    <div class="text-[10px] text-gray-400 uppercase">Completion</div>
                    <div class="font-mono font-semibold text-gray-700">${metrics.completion_tokens}</div>
                </div>
                <div class="bg-white p-2 rounded border border-gray-100">
                    <div class="text-[10px] text-gray-400 uppercase">Total</div>
                    <div class="font-mono font-bold text-indigo-600">${metrics.total_tokens}</div>
                </div>
                <div class="bg-white p-2 rounded border border-gray-100">
                    <div class="text-[10px] text-gray-400 uppercase">Model</div>
                    <div class="font-mono text-gray-600 truncate" title="${metrics.model}">
                        ${metrics.model ? metrics.model.split('/').pop() : '-'}
                    </div>
                </div>
            </div>
        `;
    }
}

if (!customElements.get('chat-debug-info')) {
    customElements.define('chat-debug-info', ChatDebugInfo);
}

export { ChatDebugInfo };
