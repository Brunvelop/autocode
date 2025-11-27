import '../graph/graph-viewport.js';
import '../graph/tree-layout.js';

/**
 * GitVisualizer
 * Componente orquestador que conecta los datos de Git con la visualización gráfica.
 * 
 * Responsabilidades:
 * - Fetch de datos (/get_git_tree)
 * - Adaptador de datos (Git -> TreeLayout)
 * - Gestión de estado de carga
 * - Composición de componentes (Viewport + Layout)
 */
export class GitVisualizer extends HTMLElement {
    constructor() {
        super();
        this._data = null;
    }

    connectedCallback() {
        this.render();
        this.fetchTree();
    }

    render() {
        this.className = "block w-full h-full relative";
        
        this.innerHTML = `
            <!-- Loading Overlay -->
            <div id="loading" class="absolute inset-0 flex items-center justify-center text-gray-500 bg-white/50 z-50 backdrop-blur-sm transition-opacity duration-300 pointer-events-none">
                <span class="flex items-center gap-2 font-medium">
                    <svg class="animate-spin h-5 w-5 text-green-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Growing garden...
                </span>
            </div>

            <!-- Graph Composition -->
            <graph-viewport>
                <tree-layout></tree-layout>
            </graph-viewport>
        `;
    }

    async fetchTree() {
        try {
            const response = await fetch('/get_git_tree');
            const data = await response.json();

            if (data.success && data.result) {
                this._data = this._formatGitData(data.result);

                const treeLayout = this.querySelector('tree-layout');
                if (treeLayout) {
                    treeLayout.data = this._data;
                }

                // Hide Loading
                const loadingInfo = this.querySelector('#loading');
                if (loadingInfo) {
                    loadingInfo.classList.add('opacity-0', 'pointer-events-none');
                }

                // Initial Fit
                // We need to wait for layout to render
                requestAnimationFrame(() => {
                    const viewport = this.querySelector('graph-viewport');
                    if (viewport && viewport.fitToScreen) {
                       viewport.fitToScreen();
                       
                       // Optional: Entrance animation could be here or in viewport
                    }
                });
            }
        } catch (e) {
            console.error(e);
            const loadingInfo = this.querySelector('#loading');
            if (loadingInfo) {
                loadingInfo.innerHTML = `Error loading garden: ${e.message}`;
            }
        }
    }

    /**
     * Mapper: Git Tree -> Graph/Tree Layout Format
     */
    _formatGitData(gitNode, isRoot = true) {
        if (!gitNode) return null;
        let type = 'file';
        let icon = '📄';
        if (isRoot) { type = 'root'; icon = '🌳'; } 
        else if (gitNode.type === 'directory') { type = 'directory'; icon = '📁'; }

        let children = [];
        if (gitNode.children) {
            children = gitNode.children.map(child => this._formatGitData(child, false));
        }

        return {
            id: `node-${Math.random().toString(36).substr(2,9)}`,
            data: { label: gitNode.name, icon: icon, type: type },
            children: children
        };
    }
}

if (!customElements.get('git-visualizer')) {
    customElements.define('git-visualizer', GitVisualizer);
}
