/**
 * index.js
 * Componente de visualización de estructura de archivos
 * 
 * Características:
 * - Usa Lit para reactividad y renderizado declarativo
 * - Hereda de AutoFunctionController para integración con el registry
 * - Ejecuta automáticamente la función get_git_tree al conectarse
 * - Manejo de estados (loading, error, success) automático
 * - Usa sistema de diseño compartido
 */

import { html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { AutoFunctionController } from '../auto-element-generator.js';
import { fileExplorerStyles } from './styles/file-explorer.styles.js';

class FileExplorer extends AutoFunctionController {
    static styles = [fileExplorerStyles];

    constructor() {
        super();
        this.funcName = 'get_git_tree'; // Carga automática de metadata
    }

    updated(changedProperties) {
        super.updated(changedProperties);
        
        // Cuando funcInfo se carga, ejecutar automáticamente
        if (changedProperties.has('funcInfo') && this.funcInfo) {
            this.execute();
        }
    }

    render() {
        // Estado: Ejecutando
        if (this._isExecuting) {
            return html`
                <div class="loading-state">
                    <div class="loading-content">
                        <div class="spinner"></div>
                        <span>Cargando estructura...</span>
                    </div>
                </div>
            `;
        }

        // Estado: Error
        if (this._errorMessage) {
            return html`
                <div class="error-state">
                    <div class="error-content">
                        <div class="error-icon">⚠️</div>
                        <div>${this._errorMessage}</div>
                        <button 
                            class="retry-btn" 
                            type="button"
                            @click=${() => this.execute()}
                        >
                            Reintentar
                        </button>
                    </div>
                </div>
            `;
        }

        // Estado: Sin datos
        if (!this.result) {
            return html`
                <div class="error-state">
                    <div>Sin datos disponibles</div>
                </div>
            `;
        }

        // Estado: Success - Renderizar árbol
        return html`
            <div class="file-explorer-root">
                ${this._renderNode(this.result, 0)}
            </div>
        `;
    }

    /**
     * Renderiza un nodo (carpeta o archivo)
     */
    _renderNode(node, depth) {
        if (node.type === 'file') {
            return this._renderFile(node);
        } else {
            return this._renderFolder(node, depth);
        }
    }

    /**
     * Renderiza un archivo como chip
     */
    _renderFile(node) {
        const icon = this._getFileIcon(node.name);
        const color = this._getFileColor(node.name);
        const title = `${node.name}${node.size ? ` (${this._formatSize(node.size)})` : ''}`;
        
        return html`
            <div 
                class="file-chip" 
                style="border-color: ${color}40; color: ${color};"
                title="${title}"
            >
                <span>${icon}</span>
                <span>${node.name}</span>
            </div>
        `;
    }

    /**
     * Renderiza una carpeta con su contenido
     */
    _renderFolder(node, depth) {
        const displayName = node.name === 'root' ? '📁 Proyecto' : `📂 ${node.name}`;
        
        // Ordenar hijos: carpetas primero, luego archivos
        let children = [];
        if (node.children && node.children.length > 0) {
            children = [...node.children].sort((a, b) => {
                if (a.type === b.type) return a.name.localeCompare(b.name);
                return a.type === 'directory' ? -1 : 1;
            });
        }
        
        return html`
            <div class="folder-box">
                <div class="folder-header" title="${node.name}">
                    ${displayName}
                </div>
                <div class="folder-content">
                    ${children.map(child => this._renderNode(child, depth + 1))}
                </div>
            </div>
        `;
    }

    /**
     * Obtiene el ícono según el tipo de archivo
     */
    _getFileIcon(filename) {
        const ext = filename.split('.').pop()?.toLowerCase();
        const iconMap = {
            'py': '🐍', 'js': '⚡', 'ts': '💠', 'html': '🌐', 'css': '🎨',
            'json': '📋', 'md': '📝', 'txt': '📄', 'yml': '⚙️', 'yaml': '⚙️',
            'toml': '⚙️', 'sh': '🔧', 'lock': '🔒', 'ini': '⚙️',
        };
        
        if (filename.includes('test')) return '🧪';
        if (filename === 'README.md') return '📖';
        if (filename === 'LICENSE') return '⚖️';
        if (filename.startsWith('.')) return '⚙️';
        
        return iconMap[ext] || '📄';
    }

    /**
     * Obtiene el color según el tipo de archivo
     */
    _getFileColor(filename) {
        const ext = filename.split('.').pop()?.toLowerCase();
        const colorMap = {
            'py': '#60a5fa', 'js': '#facc15', 'ts': '#38bdf8', 'html': '#fb923c',
            'css': '#22d3ee', 'json': '#a3e635', 'md': '#a78bfa', 'txt': '#94a3b8',
            'yml': '#f472b6', 'yaml': '#f472b6', 'toml': '#f472b6', 'sh': '#4ade80',
            'lock': '#6b7280', 'ini': '#f472b6',
        };
        
        if (filename.includes('test')) return '#22d3ee';
        return colorMap[ext] || '#94a3b8';
    }

    /**
     * Formatea el tamaño del archivo
     */
    _formatSize(bytes) {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }
}

if (!customElements.get('file-explorer')) {
    customElements.define('file-explorer', FileExplorer);
}

export { FileExplorer };
