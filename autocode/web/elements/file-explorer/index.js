/**
 * index.js
 * Componente de visualización de estructura de archivos
 * 
 * Características:
 * - NOMBRES SIEMPRE VISIBLES: Nunca se cortan
 * - Diseño de flujo natural con flexbox
 * - Scroll automático si el contenido excede el viewport
 * - Paleta consistente para carpetas (modo oscuro)
 * - Responsive
 */

class FileExplorer extends HTMLElement {
    constructor() {
        super();
        this._data = null;
    }

    connectedCallback() {
        this.render();
        this._fetchData();
    }

    render() {
        this.innerHTML = `
            <style>
                :host {
                    display: block;
                    width: 100%;
                    height: 100%;
                }
                
                .file-explorer-root {
                    width: 100%;
                    height: 100%;
                    overflow: auto;
                    background: #020617;
                    box-sizing: border-box;
                    padding: 8px;
                }
                
                .folder-box {
                    display: inline-flex;
                    flex-direction: column;
                    box-sizing: border-box;
                    border-radius: 6px;
                    margin: 3px;
                    vertical-align: top;
                    min-width: fit-content;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                }
                
                .folder-header {
                    font-weight: 700;
                    padding: 4px 8px;
                    white-space: nowrap;
                    border-radius: 4px 4px 0 0;
                    font-size: 10px;
                }
                
                .folder-content {
                    display: flex;
                    flex-wrap: wrap;
                    align-items: flex-start;
                    align-content: flex-start;
                    padding: 4px;
                    gap: 3px;
                    min-height: 20px;
                }
                
                .file-chip {
                    display: inline-flex;
                    align-items: center;
                    gap: 3px;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 9px;
                    white-space: nowrap;
                    cursor: default;
                    transition: filter 0.15s;
                }
                
                .file-chip:hover {
                    filter: brightness(1.2);
                }
                
                /* Loading & Error states */
                .loading-state, .error-state {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                    color: #94a3b8;
                }
                
                .spinner {
                    width: 24px;
                    height: 24px;
                    border: 2px solid #475569;
                    border-top-color: #818cf8;
                    border-radius: 50%;
                    animation: spin 0.8s linear infinite;
                    margin-right: 10px;
                }
                
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                
                .retry-btn {
                    margin-top: 12px;
                    padding: 6px 12px;
                    background: #334155;
                    border: none;
                    border-radius: 4px;
                    color: #e2e8f0;
                    cursor: pointer;
                    font-size: 12px;
                }
                
                .retry-btn:hover {
                    background: #475569;
                }

                /* Root level layout */
                .root-content {
                    display: flex;
                    flex-wrap: wrap;
                    align-items: flex-start;
                    align-content: flex-start;
                    gap: 4px;
                }
            </style>
            <div data-ref="container" class="file-explorer-root">
                <div class="loading-state">
                    <div class="spinner"></div>
                    <span>Cargando estructura...</span>
                </div>
            </div>
        `;
        this._container = this.querySelector('[data-ref="container"]');
    }

    async _fetchData() {
        try {
            const response = await fetch('/get_git_tree');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            if (data.success && data.result) {
                this._data = data.result;
                this._renderTree();
            } else {
                this._showError(data.message || 'Error al obtener estructura');
            }
        } catch (error) {
            this._showError(`Error de conexión: ${error.message}`);
        }
    }

    _showError(message) {
        if (!this._container) return;

        // Evitar inyección HTML: construir DOM con textContent
        const wrapper = document.createElement('div');
        wrapper.className = 'error-state';

        const inner = document.createElement('div');
        inner.style.textAlign = 'center';

        const icon = document.createElement('div');
        icon.style.fontSize = '32px';
        icon.style.marginBottom = '8px';
        icon.textContent = '⚠️';

        const msg = document.createElement('div');
        msg.textContent = String(message ?? 'Error');

        const retryBtn = document.createElement('button');
        retryBtn.className = 'retry-btn';
        retryBtn.type = 'button';
        retryBtn.textContent = 'Reintentar';
        retryBtn.addEventListener('click', () => this._fetchData());

        inner.append(icon, msg, retryBtn);
        wrapper.appendChild(inner);

        this._container.replaceChildren(wrapper);
    }

    _renderTree() {
        if (!this._container || !this._data) return;
        
        this._container.innerHTML = '';
        
        // Renderizar el nodo raíz
        const rootElement = this._renderNode(this._data, 0);
        if (rootElement) {
            this._container.appendChild(rootElement);
        }
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

    _renderFile(node) {
        const chip = document.createElement('div');
        chip.className = 'file-chip';
        
        const icon = this._getFileIcon(node.name);
        const color = this._getFileColor(node.name);
        
        // Estilo sutil para archivos: fondo oscuro neutro, color solo en texto/borde
        chip.style.cssText = `
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid ${color}40;
            color: ${color};
        `;
        
        // Evitar inyección HTML: no usar innerHTML con datos externos
        const iconEl = document.createElement('span');
        iconEl.textContent = icon;
        const nameEl = document.createElement('span');
        nameEl.textContent = node.name;
        chip.replaceChildren(iconEl, nameEl);

        chip.title = `${node.name}${node.size ? ` (${this._formatSize(node.size)})` : ''}`;

        return chip;
    }

    _renderFolder(node, depth) {
        const folder = document.createElement('div');
        folder.className = 'folder-box';
        
        const colors = this._getFolderColor(node.name);
        
        folder.style.cssText = `
            background: ${colors.bg};
            border: 1px solid ${colors.border};
        `;
        
        // Header
        const header = document.createElement('div');
        header.className = 'folder-header';
        header.style.cssText = `
            background: ${colors.headerBg};
            color: ${colors.text};
        `;
        
        const displayName = node.name === 'root' ? '📁 Proyecto' : `📂 ${node.name}`;
        header.textContent = displayName;
        header.title = node.name;
        folder.appendChild(header);
        
        // Content area
        const content = document.createElement('div');
        content.className = 'folder-content';
        folder.appendChild(content);
        
        // Renderizar hijos
        if (node.children && node.children.length > 0) {
            // Ordenar: carpetas primero, luego archivos
            const sorted = [...node.children].sort((a, b) => {
                if (a.type === b.type) return a.name.localeCompare(b.name);
                return a.type === 'directory' ? -1 : 1;
            });
            
            sorted.forEach(child => {
                const childElement = this._renderNode(child, depth + 1);
                if (childElement) {
                    content.appendChild(childElement);
                }
            });
        }
        
        return folder;
    }

    _getFolderColor(name) {
        // Diseño consistente Dark Mode (Slate theme)
        return {
            bg: '#1e293b',        // Slate 800
            border: '#334155',    // Slate 700
            headerBg: '#0f172a',  // Slate 900
            text: '#e2e8f0'       // Slate 200
        };
    }

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
