import '../node-graph/graph-viewport.js';
import '../node-graph/node-graph.js';
import '../treemap/treemap.js';

/**
 * GitVisualizer
 * Componente orquestador que conecta los datos de Git con la visualización gráfica.
 */
export class GitVisualizer extends HTMLElement {
    constructor() {
        super();
        this._rawData = null; // Data original from backend
        this.viewMode = 'graph'; // 'graph' | 'treemap'
        this.metric = 'size'; // 'size' | 'count'
    }

    connectedCallback() {
        this.render();
        this.setupEventListeners();
        this.fetchTree();
    }

    setupEventListeners() {
        this.querySelector('#view-graph')?.addEventListener('click', () => this.switchView('graph'));
        this.querySelector('#view-treemap')?.addEventListener('click', () => this.switchView('treemap'));
        this.querySelector('#view-toggle')?.addEventListener('click', () => this.toggleView());
        
        // Metric selector events
        this.querySelector('#metric-select')?.addEventListener('change', (e) => this.setMetric(e.target.value));
    }

    render() {
        this.className = "flex flex-col w-full h-full relative overflow-hidden bg-gray-50";
        
        // Header
        const headerHTML = `
            <div class="h-14 border-b bg-white flex items-center justify-between px-4 shrink-0 z-20 shadow-sm">
                <div class="flex items-center gap-2">
                    <span class="text-xl">🌳</span>
                    <h2 class="font-bold text-gray-800">Code Garden</h2>
                </div>
                
                <div class="flex items-center gap-2">
                    <!-- Metric Selector (Visible only in Heatmap) -->
                    <div id="metric-controls" class="mr-4 flex items-center gap-2 ${this.viewMode === 'treemap' ? '' : 'hidden'}">
                        <span class="text-xs font-medium text-gray-500 uppercase tracking-wider">Metric:</span>
                        <select id="metric-select" class="text-sm border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 py-1 pl-2 pr-7">
                            <option value="size" ${this.metric === 'size' ? 'selected' : ''}>📏 Size (KB)</option>
                            <option value="count" ${this.metric === 'count' ? 'selected' : ''}>🧮 Equal (Count)</option>
                        </select>
                    </div>

                    <div class="flex items-center gap-2 bg-gray-100 p-1 rounded-lg">
                        <button id="view-graph" class="px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${this.viewMode === 'graph' ? 'bg-white shadow text-indigo-600' : 'text-gray-600 hover:text-gray-900'}">
                            Graph
                        </button>
                        <button id="view-treemap" class="px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${this.viewMode === 'treemap' ? 'bg-white shadow text-indigo-600' : 'text-gray-600 hover:text-gray-900'}">
                            Heatmap
                        </button>
                        <!-- Button for TDD Test targeting -->
                        <button id="view-toggle" class="hidden"></button>
                    </div>
                </div>
            </div>
        `;

        // Content Area
        const contentHTML = `
            <div id="viz-container" class="flex-1 relative overflow-hidden">
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

                <!-- Visualization Slot -->
                <div id="viz-slot" class="w-full h-full"></div>
            </div>
        `;

        this.innerHTML = headerHTML + contentHTML;
        
        // Restore metric controls state if re-rendered
        this._updateMetricControlsVisibility();
        
        this.updateView();
    }

    setMetric(val) {
        if (this.metric === val) return;
        this.metric = val;
        this.updateView();
    }

    switchView(mode) {
        if (this.viewMode === mode) return;
        this.viewMode = mode;
        
        // Update tabs UI
        const graphBtn = this.querySelector('#view-graph');
        const mapBtn = this.querySelector('#view-treemap');
        
        if (graphBtn && mapBtn) {
            if (mode === 'graph') {
                graphBtn.className = 'px-3 py-1.5 rounded-md text-sm font-medium transition-colors bg-white shadow text-indigo-600';
                mapBtn.className = 'px-3 py-1.5 rounded-md text-sm font-medium transition-colors text-gray-600 hover:text-gray-900';
            } else {
                mapBtn.className = 'px-3 py-1.5 rounded-md text-sm font-medium transition-colors bg-white shadow text-indigo-600';
                graphBtn.className = 'px-3 py-1.5 rounded-md text-sm font-medium transition-colors text-gray-600 hover:text-gray-900';
            }
        }

        this._updateMetricControlsVisibility();
        this.updateView();
    }
    
    _updateMetricControlsVisibility() {
        const controls = this.querySelector('#metric-controls');
        if (controls) {
            if (this.viewMode === 'treemap') {
                controls.classList.remove('hidden');
            } else {
                controls.classList.add('hidden');
            }
        }
    }
    
    toggleView() {
        this.switchView(this.viewMode === 'graph' ? 'treemap' : 'graph');
    }

    updateView() {
        const slot = this.querySelector('#viz-slot');
        if (!slot) return;
        
        slot.innerHTML = ''; // Clear previous
        
        // Prepare Data
        const viewData = this._processData(this._rawData);
        
        if (this.viewMode === 'graph') {
            const viewport = document.createElement('graph-viewport');
            const layout = document.createElement('node-graph');
            if (viewData) layout.data = viewData;
            
            viewport.appendChild(layout);
            slot.appendChild(viewport);
            
            // Fit logic
            requestAnimationFrame(() => {
                if (viewport.fitToScreen) viewport.fitToScreen();
            });
            
        } else {
            const treemap = document.createElement('treemap-layout');
            treemap.metric = this.metric; // Pass metric for styling (hide values)
            if (viewData) treemap.data = viewData;
            slot.appendChild(treemap);
        }
    }

    async fetchTree() {
        try {
            const response = await fetch('/get_git_tree');
            const data = await response.json();

            if (data.success && data.result) {
                this._rawData = this._formatGitData(data.result);
                this.updateView();

                // Hide Loading
                const loadingInfo = this.querySelector('#loading');
                if (loadingInfo) {
                    loadingInfo.classList.add('opacity-0', 'pointer-events-none');
                }
            }
        } catch (e) {
            console.error(e);
            const loadingInfo = this.querySelector('#loading');
            if (loadingInfo) loadingInfo.innerHTML = `Error: ${e.message}`;
        }
    }

    _processData(node) {
        if (!node) return null;
        
        // Determine value approach
        // If metric is count, force size=1 for files.
        // If metric is size, use actual size.
        
        const processNode = (n) => {
            const newNode = { ...n, data: { ...n.data } };
            
            // Recurse first
            if (n.children && n.children.length > 0) {
                newNode.children = n.children.map(processNode);
            }
            
            // Set LEAF size
            // Note: treemap-layout will recalculate folder sizes.
            // We just need to ensure leaves have correct base value.
            if (!newNode.children || newNode.children.length === 0) {
                 if (this.metric === 'count') {
                     newNode.size = 1;
                 } else {
                     // Use original size (stored in _rawData)
                     // Since we cloned, newNode.size is already correct from _rawData if we didn't mutate it.
                     // But _formatGitData sets it.
                 }
            }
            
            // If metric is count, we might want to update the label to reflect that?
            // Or treemap-node handles display? treemap-node displays 'value' attr.
            // treemap-layout passes 'value' to node.
            
            return newNode;
        };
        
        return processNode(node);
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
            size: gitNode.size || 0, // Store original raw size
            children: children
        };
    }
}

if (!customElements.get('git-visualizer')) {
    customElements.define('git-visualizer', GitVisualizer);
}
