/**
 * index.js
 * CodeDashboard — Panel unificado de exploración de código.
 *
 * Commit 1: Shell mínimo con:
 *   - Registro como custom element
 *   - Carga de datos via get_architecture_snapshot
 *   - Estados: loading, error, success
 *   - Summary cards (6 métricas principales)
 *   - Content area placeholder
 *
 * Commit 2: View tabs + breadcrumb + navegación
 *   - 5 tabs: Files, Code, Treemap, Dependencies, Metrics
 *   - Breadcrumb para navegación en árbol
 *   - Reconstrucción de árbol desde nodos planos
 *   - Navegación into/up
 *   - Content area con placeholders por tab
 *
 * Usa AutoFunctionController.executeFunction() para llamar al backend.
 */

import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { AutoFunctionController } from '../auto-element-generator.js';

export class CodeDashboard extends LitElement {
    static properties = {
        // Data from API
        _snapshot: { state: true },

        // Navigation state
        _currentNodeId: { state: true },

        // View mode: 'files' | 'code' | 'treemap' | 'graph' | 'metrics'
        _viewMode: { state: true },

        // Loading / error
        _loading: { state: true },
        _error: { state: true },

        // Internal tree cache (rebuilt from flat nodes)
        _tree: { state: true },

        // Lazy activation flags for embedded components
        _filesActivated: { state: true },
        _codeActivated: { state: true },
        _metricsActivated: { state: true },
    };

    // Styles inline (Commit 3 extracts to separate file)
    static styles = css`
        :host {
            display: block;
            height: 100%;
            overflow-y: auto;
            font-family: var(--design-font-family, system-ui, sans-serif);
        }

        /* Design tokens */
        :host {
            --design-primary: #4f46e5;
            --design-primary-dark: #4338ca;
            --design-text-primary: #1f2937;
            --design-text-secondary: #6b7280;
            --design-text-tertiary: #9ca3af;
            --design-bg-white: #ffffff;
            --design-bg-gray-50: #f9fafb;
            --design-border-gray: #e5e7eb;
            --design-border-gray-light: #f3f4f6;
            --design-error-bg: #fef2f2;
            --design-error-text: #991b1b;
            --design-error-border: #fca5a5;
            --design-spacing-xs: 0.25rem;
            --design-spacing-sm: 0.5rem;
            --design-spacing-md: 0.75rem;
            --design-spacing-lg: 1rem;
            --design-spacing-xl: 1.25rem;
            --design-spacing-3xl: 2rem;
            --design-radius-md: 0.5rem;
            --design-radius-sm: 0.25rem;
            --design-font-size-sm: 0.75rem;
            --design-font-weight-medium: 500;
            --design-font-weight-semibold: 600;
            --design-font-weight-bold: 700;
            --design-font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            --design-transition-fast: 0.1s;
            --design-indigo-50: #eef2ff;
            --design-indigo-100: #e0e7ff;
        }

        .dashboard {
            padding: var(--design-spacing-lg) var(--design-spacing-xl);
            display: flex;
            flex-direction: column;
            gap: var(--design-spacing-lg);
            height: 100%;
            box-sizing: border-box;
        }

        /* ===== LOADING / ERROR ===== */
        .loading-container, .error-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: var(--design-spacing-3xl);
            gap: var(--design-spacing-md);
            color: var(--design-text-secondary);
        }

        .spinner {
            width: 28px;
            height: 28px;
            border: 3px solid var(--design-border-gray);
            border-top-color: var(--design-primary);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        .error-msg {
            padding: var(--design-spacing-md);
            background: var(--design-error-bg);
            border: 1px solid var(--design-error-border);
            border-radius: var(--design-radius-md);
            color: var(--design-error-text);
            font-size: 12px;
            text-align: center;
            max-width: 400px;
        }

        .retry-btn {
            padding: var(--design-spacing-xs) var(--design-spacing-md);
            background: var(--design-primary);
            color: white;
            border: none;
            border-radius: var(--design-radius-md);
            cursor: pointer;
            font-size: 12px;
            transition: opacity var(--design-transition-fast);
        }

        .retry-btn:hover {
            opacity: 0.9;
        }

        /* ===== SUMMARY CARDS ===== */
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: var(--design-spacing-sm);
        }

        @media (max-width: 700px) {
            .summary-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }

        .summary-card {
            padding: var(--design-spacing-sm) var(--design-spacing-md);
            background: var(--design-bg-white);
            border: 1px solid var(--design-border-gray);
            border-radius: var(--design-radius-md);
            display: flex;
            flex-direction: column;
            gap: 2px;
            position: relative;
        }

        .card-label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--design-text-tertiary);
            font-weight: var(--design-font-weight-medium);
        }

        .card-value {
            font-size: 1.1rem;
            font-weight: var(--design-font-weight-bold);
            color: var(--design-text-primary);
            font-family: var(--design-font-mono);
        }

        .card-status {
            font-size: 14px;
            position: absolute;
            top: 6px;
            right: 8px;
        }

        /* ===== BREADCRUMB ===== */
        .breadcrumb {
            display: flex;
            align-items: center;
            gap: var(--design-spacing-xs);
            font-size: var(--design-font-size-sm);
            color: var(--design-text-secondary);
            padding: var(--design-spacing-xs) 0;
            flex-wrap: wrap;
        }

        .breadcrumb-segment {
            cursor: pointer;
            color: var(--design-primary);
            font-weight: var(--design-font-weight-medium);
            padding: 2px var(--design-spacing-xs);
            border-radius: var(--design-radius-sm);
            transition: background-color var(--design-transition-fast);
            border: none;
            background: none;
            font-size: inherit;
            font-family: inherit;
        }

        .breadcrumb-segment:hover {
            background-color: var(--design-indigo-50);
            color: var(--design-primary-dark);
        }

        .breadcrumb-segment.current {
            color: var(--design-text-primary);
            font-weight: var(--design-font-weight-semibold);
            cursor: default;
        }

        .breadcrumb-segment.current:hover {
            background-color: transparent;
        }

        .breadcrumb-separator {
            color: var(--design-text-tertiary);
            font-size: 10px;
            user-select: none;
        }

        /* ===== VIEW TABS ===== */
        .view-tabs {
            display: flex;
            gap: var(--design-spacing-xs);
            border-bottom: 1px solid var(--design-border-gray);
            padding-bottom: 0;
        }

        .view-tab {
            padding: var(--design-spacing-xs) var(--design-spacing-md);
            background: transparent;
            border: 1px solid transparent;
            border-bottom: 2px solid transparent;
            border-radius: var(--design-radius-md) var(--design-radius-md) 0 0;
            color: var(--design-text-secondary);
            font-size: 12px;
            font-weight: var(--design-font-weight-medium);
            cursor: pointer;
            transition: all var(--design-transition-fast);
            font-family: inherit;
            display: flex;
            align-items: center;
            gap: var(--design-spacing-xs);
        }

        .view-tab:hover {
            color: var(--design-text-primary);
            background: var(--design-bg-gray-50);
        }

        .view-tab.active {
            color: var(--design-primary);
            border-bottom-color: var(--design-primary);
            background: var(--design-indigo-50);
        }

        /* ===== CONTENT AREA ===== */
        .content-area {
            flex: 1;
            min-height: 200px;
            background: var(--design-bg-white);
            border: 1px solid var(--design-border-gray);
            border-radius: var(--design-radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
        }

        .content-placeholder {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: var(--design-spacing-sm);
            color: var(--design-text-tertiary);
            font-size: var(--design-font-size-sm);
        }

        .content-placeholder-icon {
            font-size: 2rem;
            opacity: 0.3;
        }

        /* ===== SNAPSHOT INFO ===== */
        .snapshot-info {
            font-size: 10px;
            color: var(--design-text-tertiary);
            text-align: center;
            padding-top: var(--design-spacing-sm);
            border-top: 1px solid var(--design-border-gray-light);
        }
    `;

    constructor() {
        super();
        this._snapshot = null;
        this._currentNodeId = '.';
        this._viewMode = 'treemap';
        this._loading = false;
        this._error = null;
        this._tree = null;
        this._filesActivated = false;
        this._codeActivated = false;
        this._metricsActivated = false;
    }

    connectedCallback() {
        super.connectedCallback();
        this.refresh();

        // Listen for navigation events from child components (treemap, graph)
        this.addEventListener('navigate-into', this._handleNavigateInto.bind(this));
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this.removeEventListener('navigate-into', this._handleNavigateInto.bind(this));
    }

    // ========================================================================
    // DATA LOADING
    // ========================================================================

    async refresh() {
        this._loading = true;
        this._error = null;
        try {
            const result = await AutoFunctionController.executeFunction(
                'get_architecture_snapshot',
                {}
            );
            this._snapshot = result;
            this._currentNodeId = result?.root_id || '.';

            // Build tree from flat nodes
            if (result?.nodes) {
                this._tree = this._buildTreeFromNodes(result.nodes, result.root_id);
            }
        } catch (e) {
            this._error = e.message || 'Error cargando arquitectura';
        } finally {
            this._loading = false;
        }
    }

    // ========================================================================
    // RENDER
    // ========================================================================

    render() {
        if (this._loading) {
            return html`
                <div class="loading-container">
                    <div class="spinner"></div>
                    <span>Analizando código...</span>
                </div>
            `;
        }

        if (this._error) {
            return html`
                <div class="error-container">
                    <div class="error-msg">❌ ${this._error}</div>
                    <button class="retry-btn" @click=${() => this.refresh()}>Reintentar</button>
                </div>
            `;
        }

        if (!this._snapshot) return html``;

        const snap = this._snapshot;

        return html`
            <div class="dashboard">
                ${this._renderSummary(snap)}
                ${this._viewMode === 'treemap' || this._viewMode === 'graph'
                    ? this._renderBreadcrumb() : ''}
                ${this._renderViewTabs()}
                ${this._renderContentArea()}
                ${this._renderSnapshotInfo(snap)}
            </div>
        `;
    }

    // ========================================================================
    // SUMMARY CARDS
    // ========================================================================

    _renderSummary(snap) {
        return html`
            <div class="summary-grid">
                ${this._card('Archivos', snap.total_files)}
                ${this._card('SLOC', this._fmt(snap.total_sloc))}
                ${this._card('MI Media', snap.avg_mi?.toFixed(1),
                    snap.avg_mi >= 60 ? '✅' : snap.avg_mi >= 40 ? '⚠️' : '🔴')}
                ${this._card('CC Media', snap.avg_complexity?.toFixed(2),
                    snap.avg_complexity < 5 ? '✅' : snap.avg_complexity < 10 ? '⚠️' : '🔴')}
                ${this._card('Funciones', snap.total_functions)}
                ${this._card('Clases', snap.total_classes)}
            </div>
        `;
    }

    _card(label, value, status) {
        return html`
            <div class="summary-card">
                ${status ? html`<span class="card-status">${status}</span>` : ''}
                <span class="card-label">${label}</span>
                <span class="card-value">${value}</span>
            </div>
        `;
    }

    // ========================================================================
    // BREADCRUMB
    // ========================================================================

    _renderBreadcrumb() {
        const segments = this._getPathSegments();

        return html`
            <div class="breadcrumb">
                ${segments.map((seg, i) => {
                    const isLast = i === segments.length - 1;
                    return html`
                        ${i > 0 ? html`<span class="breadcrumb-separator">›</span>` : ''}
                        <button
                            class="breadcrumb-segment ${isLast ? 'current' : ''}"
                            @click=${() => { if (!isLast) this._navigateUp(seg.id); }}
                            ?disabled=${isLast}
                        >${seg.name}</button>
                    `;
                })}
            </div>
        `;
    }

    /**
     * Build breadcrumb segments from root to current node.
     * Walks the flat node list upward via parent_id.
     * @returns {Array<{id: string, name: string}>}
     */
    _getPathSegments() {
        if (!this._snapshot?.nodes) return [{ id: '.', name: '📊 root' }];

        const nodeMap = new Map(this._snapshot.nodes.map(n => [n.id, n]));
        const segments = [];
        let currentId = this._currentNodeId;

        // Walk up to root
        while (currentId != null) {
            const node = nodeMap.get(currentId);
            if (!node) break;
            segments.unshift({
                id: node.id,
                name: node.id === this._snapshot.root_id ? '📊 root' : node.name,
            });
            currentId = node.parent_id;
        }

        return segments.length > 0 ? segments : [{ id: '.', name: '📊 root' }];
    }

    // ========================================================================
    // VIEW TABS
    // ========================================================================

    _renderViewTabs() {
        const tabs = [
            { id: 'files',   label: '📁 Files' },
            { id: 'code',    label: '🧬 Code' },
            { id: 'treemap', label: '🗺️ Treemap' },
            { id: 'graph',   label: '🔗 Dependencies' },
            { id: 'metrics', label: '📊 Metrics' },
        ];

        return html`
            <div class="view-tabs">
                ${tabs.map(tab => html`
                    <button
                        class="view-tab ${this._viewMode === tab.id ? 'active' : ''}"
                        @click=${() => this._setViewMode(tab.id)}
                    >${tab.label}</button>
                `)}
            </div>
        `;
    }

    // ========================================================================
    // CONTENT AREA
    // ========================================================================

    _renderContentArea() {
        const mode = this._viewMode;

        // Files tab — placeholder (Commit 8 integrates file-explorer)
        if (mode === 'files') {
            return html`
                <div class="content-area">
                    <div class="content-placeholder">
                        <span class="content-placeholder-icon">📁</span>
                        <span>File Explorer — coming in Commit 8</span>
                    </div>
                </div>
            `;
        }

        // Code tab — placeholder (Commit 8 integrates code-explorer)
        if (mode === 'code') {
            return html`
                <div class="content-area">
                    <div class="content-placeholder">
                        <span class="content-placeholder-icon">🧬</span>
                        <span>Code Explorer — coming in Commit 8</span>
                    </div>
                </div>
            `;
        }

        // Treemap tab — placeholder (Commit 4 integrates treemap-view)
        if (mode === 'treemap') {
            return html`
                <div class="content-area">
                    <div class="content-placeholder">
                        <span class="content-placeholder-icon">🗺️</span>
                        <span>Treemap View — coming in Commit 4</span>
                    </div>
                </div>
            `;
        }

        // Dependencies graph tab — placeholder (Commit 5 integrates dependency-graph)
        if (mode === 'graph') {
            return html`
                <div class="content-area">
                    <div class="content-placeholder">
                        <span class="content-placeholder-icon">🔗</span>
                        <span>Dependency Graph — coming in Commit 5</span>
                    </div>
                </div>
            `;
        }

        // Metrics tab — placeholder (Commit 8 integrates metrics-panel)
        if (mode === 'metrics') {
            return html`
                <div class="content-area">
                    <div class="content-placeholder">
                        <span class="content-placeholder-icon">📊</span>
                        <span>Metrics Panel — coming in Commit 6-8</span>
                    </div>
                </div>
            `;
        }

        return html``;
    }

    // ========================================================================
    // SNAPSHOT INFO
    // ========================================================================

    _renderSnapshotInfo(snap) {
        return html`
            <div class="snapshot-info">
                📊 Commit ${snap.commit_short} · ${snap.branch} · ${this._formatDate(snap.timestamp)}
            </div>
        `;
    }

    // ========================================================================
    // VIEW MODE MANAGEMENT
    // ========================================================================

    /**
     * Change the active view tab.
     * Activates lazy-loaded components on first access.
     * @param {'files'|'code'|'treemap'|'graph'|'metrics'} mode
     */
    _setViewMode(mode) {
        if (this._viewMode === mode) return;
        this._viewMode = mode;

        if (mode === 'files') this._filesActivated = true;
        if (mode === 'code') this._codeActivated = true;
        if (mode === 'metrics') this._metricsActivated = true;
    }

    // ========================================================================
    // TREE BUILDING
    // ========================================================================

    /**
     * Reconstruct a nested tree from flat adjacency-list nodes.
     *
     * @param {Array} nodes - Flat list of nodes with parent_id
     * @param {string} rootId - ID of the root node
     * @returns {Object|null} Root node with nested children arrays
     */
    _buildTreeFromNodes(nodes, rootId) {
        if (!nodes || nodes.length === 0) return null;

        // Create map id → node (copy to avoid mutating original)
        const nodeMap = new Map();
        for (const node of nodes) {
            nodeMap.set(node.id, { ...node, children: [] });
        }

        // Build parent-child relationships
        for (const node of nodeMap.values()) {
            if (node.parent_id && nodeMap.has(node.parent_id)) {
                const parent = nodeMap.get(node.parent_id);
                parent.children.push(node);
            }
        }

        // Sort children: directories first, then by name
        for (const node of nodeMap.values()) {
            if (node.children.length > 0) {
                node.children.sort((a, b) => {
                    if (a.type === 'directory' && b.type !== 'directory') return -1;
                    if (a.type !== 'directory' && b.type === 'directory') return 1;
                    return a.name.localeCompare(b.name);
                });
            } else {
                node.children = null;
            }
        }

        return nodeMap.get(rootId) || null;
    }

    /**
     * Get the subtree rooted at _currentNodeId.
     */
    _getCurrentSubtree() {
        if (!this._tree) return null;
        if (this._currentNodeId === this._snapshot?.root_id) return this._tree;
        return this._findNode(this._tree, this._currentNodeId);
    }

    /**
     * DFS to find a node by id in a nested tree.
     */
    _findNode(node, targetId) {
        if (!node) return null;
        if (node.id === targetId) return node;
        if (!node.children) return null;
        for (const child of node.children) {
            const found = this._findNode(child, targetId);
            if (found) return found;
        }
        return null;
    }

    // ========================================================================
    // NAVIGATION
    // ========================================================================

    _navigateInto(nodeId) {
        this._currentNodeId = nodeId;
    }

    _navigateUp(nodeId) {
        this._currentNodeId = nodeId;
    }

    _handleNavigateInto(e) {
        const nodeId = e.detail?.nodeId;
        if (nodeId) {
            this._navigateInto(nodeId);
        }
    }

    // ========================================================================
    // HELPERS
    // ========================================================================

    _fmt(n) {
        if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
        return n;
    }

    _formatDate(iso) {
        if (!iso) return '';
        try {
            return new Date(iso).toLocaleString('es-ES', {
                dateStyle: 'short',
                timeStyle: 'short',
            });
        } catch {
            return iso;
        }
    }
}

// Register the custom element
if (!customElements.get('code-dashboard')) {
    customElements.define('code-dashboard', CodeDashboard);
}