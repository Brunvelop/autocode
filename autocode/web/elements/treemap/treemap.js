import './treemap-node.js';

/**
 * Treemap
 * Algoritmo "Slice and Dice" usando Flexbox recursivo.
 * Smart container: Handles logic for formatting and coloring nodes.
 */
export class Treemap extends HTMLElement {
    constructor() {
        super();
        this._data = null;
        this._processedData = null;
        this._metric = 'size'; // 'size' | 'count'
    }

    set data(value) {
        this._data = value;
        this._processedData = this._calculateValues(this._data);
        this.render();
    }

    get data() {
        return this._data;
    }
    
    set metric(val) {
        this._metric = val;
        this.render();
    }

    connectedCallback() {
        if (!this.innerHTML) this.render();
    }

    /**
     * Recursively computes value (size sum) for directories.
     */
    _calculateValues(node) {
        if (!node) return null;
        
        // Clone to avoid mutating original source
        const newNode = { ...node, data: { ...node.data } };
        
        if (node.children && node.children.length > 0) {
            newNode.children = node.children.map(child => this._calculateValues(child));
            // Sum children values
            const sum = newNode.children.reduce((acc, child) => acc + (child.value || 0), 0);
            newNode.value = sum;
            newNode.size = sum; // Keep metadata consistent
        } else {
            // Leaf node: use provided size or default to 1 (equal weight fallback)
            newNode.value = node.size || 1;
        }
        
        return newNode;
    }

    _formatSize(bytes) {
        if (!bytes) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    _getColorClass(label, type) {
        if (type === 'directory') return 'bg-gray-50 border-gray-200 text-gray-400';
        
        const ext = label.split('.').pop().toLowerCase();
        
        // Color Palette Logic
        if (['py', 'pyc'].includes(ext)) return 'bg-blue-100 hover:bg-blue-200 border-blue-200 text-blue-800';
        if (['js', 'ts', 'jsx', 'tsx'].includes(ext)) return 'bg-yellow-100 hover:bg-yellow-200 border-yellow-200 text-yellow-800';
        if (['html', 'css'].includes(ext)) return 'bg-orange-100 hover:bg-orange-200 border-orange-200 text-orange-800';
        if (['md', 'txt'].includes(ext)) return 'bg-gray-100 hover:bg-gray-200 border-gray-200 text-gray-700';
        if (['json', 'yml', 'yaml', 'toml'].includes(ext)) return 'bg-purple-100 hover:bg-purple-200 border-purple-200 text-purple-800';
        
        // Default / Other
        return 'bg-emerald-100 hover:bg-emerald-200 border-emerald-200 text-emerald-800';
    }

    render() {
        if (!this._processedData) return;
        
        this.className = "block w-full h-full relative overflow-hidden bg-gray-50";
        
        // Root container (Depth 0)
        this.innerHTML = this._buildNodeHTML(this._processedData, 0);
    }

    _buildNodeHTML(node, depth) {
        if (!node) return '';

        const isLeaf = !node.children || node.children.length === 0;
        const value = node.value || 0;
        const label = node.data?.label || node.name || 'node';
        const type = node.data?.type || (isLeaf ? 'file' : 'directory');
        
        if (isLeaf) {
            // Calculate presentation props here
            const displayValue = (this._metric === 'count') ? '' : this._formatSize(value);
            const colorClass = this._getColorClass(label, type);

            return `
                <treemap-node 
                    label="${label}" 
                    display-value="${displayValue}" 
                    color-class="${colorClass}"
                    style="flex-grow: ${value}; flex-basis: 0; min-width: 0; min-height: 0;"
                ></treemap-node>
            `;
        } else {
            // Directory / Container
            const direction = depth % 2 === 0 ? 'flex-row' : 'flex-col';
            
            // Sort children by size descending for better aesthetics
            const sortedChildren = [...node.children].sort((a, b) => b.value - a.value);
            
            const childrenHTML = sortedChildren.map(child => this._buildNodeHTML(child, depth + 1)).join('');
            
            // Directory Structure
            if (depth === 0) {
                 return `
                    <div class="flex ${direction} depth-${depth} w-full h-full relative overflow-hidden" style="flex-grow: 1">
                         ${childrenHTML}
                    </div>
                `;
            }

            // Sub-directories
            const nestingBg = depth % 2 === 0 ? 'bg-gray-50/50' : 'bg-gray-100/50';
            
            return `
                <div class="flex flex-col depth-${depth} ${nestingBg} border-l border-t border-white/50 w-full h-full min-w-0 min-h-0 overflow-hidden shadow-sm" 
                     style="flex-grow: ${value}; flex-basis: 0;">
                     
                     <!-- Explicit Header Bar -->
                     <div class="flex-none px-1.5 py-0.5 bg-white/40 border-b border-white/20 text-[10px] text-gray-500 font-mono font-medium truncate select-none"
                          title="${label}">
                        📂 ${label}
                     </div>

                     <!-- Content Body -->
                     <div class="flex-1 flex ${direction} min-h-0 min-w-0 overflow-hidden">
                        ${childrenHTML}
                     </div>
                </div>
            `;
        }
    }
}

if (!customElements.get('treemap-layout')) {
    customElements.define('treemap-layout', Treemap);
}
