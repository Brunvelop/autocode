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

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { AutoFunctionController } from '../auto-element-generator.js';
import { themeTokens } from './styles/theme.js';
import { codeDashboardStyles } from './styles/code-dashboard.styles.js';
import './treemap-view.js';
import './dependency-graph.js';
import './metrics-panel.js';
import '../code-explorer/index.js';

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
        _codeActivated: { state: true },
        _metricsActivated: { state: true },

        // Commit history for selector (loaded from get_git_log)
        _commits: { state: true },

        // Currently selected commit hash ('' = HEAD / current)
        _selectedCommitHash: { state: true },
    };

    // Styles extracted in Commit 3: theme tokens + component styles
    static styles = [themeTokens, codeDashboardStyles];

    constructor() {
        super();
        this._snapshot = null;
        this._currentNodeId = '.';
        this._viewMode = 'treemap';
        this._loading = false;
        this._error = null;
        this._tree = null;
        this._codeActivated = false;
        this._metricsActivated = false;
        this._commits = [];
        this._selectedCommitHash = '';
    }

    connectedCallback() {
        super.connectedCallback();
        this.refresh();
        this._loadCommits();

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

    async _loadCommits() {
        try {
            const result = await AutoFunctionController.executeFunction(
                'get_git_log',
                { max_count: 20 }
            );
            if (result?.commits) {
                this._commits = result.commits;
            }
        } catch (e) {
            // Silently fail — selector simply won't appear
        }
    }

    async refresh(commitHash = '') {
        // Preserve navigation state before reload
        const savedNodeId = this._currentNodeId;
        const savedViewMode = this._viewMode;

        this._loading = true;
        this._error = null;
        try {
            const params = commitHash ? { commit_hash: commitHash } : {};
            const result = await AutoFunctionController.executeFunction(
                'get_architecture_snapshot',
                params
            );
            this._snapshot = result;

            // Build tree from flat nodes
            if (result?.nodes) {
                this._tree = this._buildTreeFromNodes(result.nodes, result.root_id);
            }

            // Restore node: keep saved node if it still exists in the new tree,
            // otherwise fall back to root (e.g. file was deleted/renamed)
            if (savedNodeId && this._tree && this._findNode(this._tree, savedNodeId)) {
                this._currentNodeId = savedNodeId;
            } else {
                this._currentNodeId = result?.root_id || '.';
            }

            // Restore view mode (unchanged, but explicit for clarity)
            this._viewMode = savedViewMode;

            // Store selected commit hash
            this._selectedCommitHash = commitHash;

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
        // Primera carga: aún no hay snapshot, mostrar spinner full-page
        if (this._loading && !this._snapshot) {
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

        // Recargas posteriores: mantener el dashboard visible con overlay no intrusivo
        return html`
            <div class="dashboard-wrapper">
                ${this._loading ? html`
                    <div class="loading-overlay">
                        <div class="spinner"></div>
                    </div>
                ` : ''}
                <div class="dashboard">
                    ${this._renderViewTabs()}
                    ${this._renderContentArea()}
                    ${this._renderSnapshotInfo(snap)}
                </div>
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

        // Code tab — code-explorer
        if (mode === 'code') {
            return html`
                <div class="content-area">
                    <code-explorer></code-explorer>
                </div>
            `;
        }

        // Treemap tab — renders <treemap-view> with full tree.
        // zoomNodeId keeps the internal zoom in sync with the dashboard breadcrumb.
        if (mode === 'treemap') {
            return html`
                <div class="content-area">
                    <treemap-view
                        .node=${this._tree}
                        .zoomNodeId=${this._currentNodeId}
                    ></treemap-view>
                </div>
            `;
        }

        // Dependencies graph tab — renders <dependency-graph> with file nodes + deps
        if (mode === 'graph') {
            const fileNodes = (this._snapshot.nodes || []).filter(n => n.type === 'file');
            return html`
                <div class="content-area">
                    <dependency-graph
                        .nodes=${fileNodes}
                        .dependencies=${this._snapshot.dependencies || []}
                        .circularDependencies=${this._snapshot.circular_dependencies || []}
                    ></dependency-graph>
                </div>
            `;
        }

        // Metrics tab — metrics-panel (summary cards shown inside the panel)
        if (mode === 'metrics') {
            return html`
                <div class="content-area">
                    <metrics-panel></metrics-panel>
                </div>
            `;
        }

        return html``;
    }

    // ========================================================================
    // SNAPSHOT INFO
    // ========================================================================

    _renderSnapshotInfo(snap) {
        const isHistorical = this._selectedCommitHash !== '';

        const commitSelector = this._commits.length > 0
            ? html`
                <select class="commit-select" @change=${this._onCommitSelect.bind(this)}>
                    ${this._commits.map(c => html`
                        <option
                            value="${c.hash}"
                            ?selected=${this._selectedCommitHash
                                ? c.hash === this._selectedCommitHash
                                : c.hash === this._commits[0]?.hash}
                        >${c.short_hash} · ${c.message.length > 45 ? c.message.slice(0, 45) + '…' : c.message}</option>
                    `)}
                </select>
            `
            : html`Commit ${snap.commit_short}`;

        return html`
            ${isHistorical ? html`
                <div class="historical-banner">
                    📸 Viendo snapshot histórico
                    <button class="back-to-current-btn" @click=${() => this.refresh('')}>Volver al actual</button>
                </div>
            ` : ''}
            <div class="snapshot-info">
                📊 ${commitSelector} · ${snap.branch} · ${this._formatDate(snap.timestamp)}
                <button class="refresh-btn" @click=${() => this.refresh(this._selectedCommitHash)} title="Recargar snapshot">🔄</button>
            </div>
        `;
    }

    _onCommitSelect(e) {
        const selectedHash = e.target.value;
        // If user selects the most recent commit (HEAD), use '' so backend uses current mode
        const isHead = selectedHash === this._commits[0]?.hash;
        this.refresh(isHead ? '' : selectedHash);
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