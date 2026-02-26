/**
 * index.js
 * GitGraph - Componente principal para visualización interactiva del historial git.
 *
 * Muestra un grafo de commits con branches, tags, merge lines, etc.
 * Panel lateral con detalle del commit seleccionado (archivos cambiados, stats).
 *
 * Usa AutoFunctionController.executeFunction() para llamar al backend
 * (get_git_log, get_commit_detail) pero extiende LitElement directamente.
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { AutoFunctionController } from '../auto-element-generator.js';
import { themeTokens } from './styles/theme.js';
import { gitGraphStyles } from './styles/git-graph.styles.js';

// Sub-components
import './commit-node.js';
import './commit-detail.js';
import './metrics-dashboard.js';

export class GitGraph extends LitElement {
    static properties = {
        maxCount: { type: Number, attribute: 'max-count' },

        // Internal state
        _commits: { state: true },
        _branches: { state: true },
        _currentBranch: { state: true },
        _selectedCommit: { state: true },
        _selectedBranch: { state: true },   // Filter by branch
        _loading: { state: true },
        _error: { state: true },

        // Graph layout computed data
        _layoutData: { state: true },

        // Metrics dashboard toggle
        _showMetrics: { state: true },

        // Collapsible commit panel
        _panelCollapsed: { state: true },
    };

    static styles = [themeTokens, gitGraphStyles];

    constructor() {
        super();
        this.maxCount = 50;

        this._commits = [];
        this._branches = [];
        this._currentBranch = '';
        this._selectedCommit = null;
        this._selectedBranch = '';
        this._loading = false;
        this._error = null;
        this._layoutData = null;
        this._showMetrics = false;
        this._panelCollapsed = false;
    }

    connectedCallback() {
        super.connectedCallback();
        this.refresh();

        // Listen for events from sub-components
        this.addEventListener('commit-selected', this._handleCommitSelected.bind(this));
        this.addEventListener('detail-closed', this._handleDetailClosed.bind(this));
        this.addEventListener('navigate-commit', this._handleNavigateCommit.bind(this));
    }

    render() {
        return html`
            <div class="graph-container">
                <!-- Header -->
                ${this._renderHeader()}

                <!-- Body: graph + detail panel -->
                <div class="graph-body">
                    ${this._renderGraphPanel()}
                    ${this._renderDetailPanel()}
                </div>
            </div>
        `;
    }

    // ========================================================================
    // HEADER
    // ========================================================================

    _renderHeader() {
        return html`
            <div class="graph-header">
                <div class="header-left">
                    <span class="header-title-icon">🌳</span>
                    <h3 class="header-title">Git Graph</h3>
                </div>
                <div class="header-actions">
                    <!-- Branch filter -->
                    <select 
                        class="branch-select"
                        .value=${this._selectedBranch}
                        @change=${this._handleBranchFilter}
                    >
                        <option value="">Todas las ramas</option>
                        ${this._branches.map(b => html`
                            <option value="${b.name}" ?selected=${b.name === this._selectedBranch}>
                                ${b.is_current ? '● ' : ''}${b.name}
                            </option>
                        `)}
                    </select>
                    <button 
                        class="action-btn ${this._showMetrics ? 'active' : ''}" 
                        @click=${() => { this._showMetrics = !this._showMetrics; }}
                        title="Métricas de código"
                    >📊</button>
                    <button class="action-btn" @click=${this.refresh} title="Recargar">
                        🔄
                    </button>
                </div>
            </div>
        `;
    }

    // ========================================================================
    // GRAPH PANEL (left)
    // ========================================================================

    _renderGraphPanel() {
        const collapsed = this._panelCollapsed;

        if (this._loading) {
            return html`
                <div class="graph-panel ${collapsed ? 'collapsed' : ''}">
                    <div class="loading-container">
                        <div class="spinner"></div>
                        <span>Cargando...</span>
                    </div>
                    <button class="panel-toggle" @click=${() => { this._panelCollapsed = true; }} title="Ocultar commits">◀</button>
                </div>
            `;
        }

        if (this._error) {
            return html`
                <div class="graph-panel ${collapsed ? 'collapsed' : ''}">
                    <div class="error-container">
                        <div class="error-box">❌ ${this._error}</div>
                        <button class="retry-btn" @click=${this.refresh}>Reintentar</button>
                    </div>
                </div>
            `;
        }

        if (collapsed) {
            return html`<div class="graph-panel collapsed"></div>`;
        }

        if (!this._layoutData || this._layoutData.rows.length === 0) {
            return html`
                <div class="graph-panel">
                    <div class="loading-container">
                        <span style="font-size:1.5rem; opacity:0.4;">📭</span>
                        <span>Sin commits</span>
                    </div>
                    <button class="panel-toggle" @click=${() => { this._panelCollapsed = true; }} title="Ocultar commits">◀</button>
                </div>
            `;
        }

        return html`
            <div class="graph-panel">
                <div class="commit-list">
                    ${this._layoutData.rows.map(row => html`
                        <commit-node
                            .commit=${row.commit}
                            .selected=${this._selectedCommit?.hash === row.commit.hash}
                            .laneIndex=${row.lane}
                            .totalLanes=${this._layoutData.maxLanes}
                            .connections=${row.connections}
                            .currentBranch=${this._currentBranch}
                        ></commit-node>
                    `)}

                    <!-- Load more button -->
                    ${this._commits.length >= this.maxCount ? html`
                        <div class="load-more">
                            <button class="load-more-btn" @click=${this._loadMore}>
                                ⬇️ Más...
                            </button>
                        </div>
                    ` : ''}
                </div>
                <button class="panel-toggle" @click=${() => { this._panelCollapsed = true; }} title="Ocultar commits">◀</button>
            </div>
        `;
    }

    // ========================================================================
    // DETAIL PANEL (right)
    // ========================================================================

    _renderDetailPanel() {
        return html`
            <div class="detail-panel">
                ${this._panelCollapsed ? html`
                    <button class="panel-toggle-collapsed" @click=${() => { this._panelCollapsed = false; }} title="Mostrar commits">▶</button>
                ` : ''}
                ${this._showMetrics ? html`
                    <metrics-dashboard></metrics-dashboard>
                ` : this._selectedCommit ? html`
                    <commit-detail
                        .commitHash=${this._selectedCommit.hash}
                        .commitSummary=${this._selectedCommit}
                    ></commit-detail>
                ` : html`
                    <div class="detail-placeholder">
                        <span class="detail-placeholder-icon">${this._panelCollapsed ? '📊' : '👈'}</span>
                        <span class="detail-placeholder-text">
                            ${this._panelCollapsed 
                                ? 'Usa 📊 para ver métricas o expande el panel de commits'
                                : 'Selecciona un commit para ver sus detalles'}
                        </span>
                    </div>
                `}
            </div>
        `;
    }

    // ========================================================================
    // PUBLIC API
    // ========================================================================

    async refresh() {
        this._loading = true;
        this._error = null;

        try {
            const result = await AutoFunctionController.executeFunction(
                'get_git_log',
                {
                    max_count: this.maxCount,
                    branch: this._selectedBranch || '',
                }
            );

            if (result) {
                this._commits = result.commits || [];
                this._branches = result.branches || [];

                // Find current branch
                const current = this._branches.find(b => b.is_current);
                this._currentBranch = current ? current.name : '';

                // Compute graph layout
                this._layoutData = this._computeLayout(this._commits);
            }

            this.dispatchEvent(new CustomEvent('graph-loaded', {
                detail: { commits: this._commits.length, branches: this._branches.length },
                bubbles: true,
                composed: true,
            }));

        } catch (error) {
            this._error = error.message || 'Error cargando historial git';
            console.error('❌ Error loading git log:', error);
        } finally {
            this._loading = false;
        }
    }

    // ========================================================================
    // GRAPH LAYOUT ALGORITHM
    // ========================================================================

    /**
     * Computes the visual layout for the commit graph.
     *
     * Assigns each commit to a "lane" (column) and generates connection
     * descriptors for drawing lines between commits and their parents.
     *
     * Algorithm:
     * - Process commits top to bottom (newest first)
     * - Maintain a set of "active lanes" tracking which commit hash occupies each lane
     * - When a commit is processed, it takes a lane; its first parent inherits that lane
     * - Additional parents (merges) get their own lanes or reuse existing ones
     * - When a lane's commit is not a parent of any future commit, the lane closes
     */
    _computeLayout(commits) {
        if (!commits || commits.length === 0) {
            return { rows: [], maxLanes: 0 };
        }

        // Active lanes: array where index = lane column, value = commit hash expected next
        let activeLanes = [];
        const rows = [];
        let maxLanes = 0;

        for (let i = 0; i < commits.length; i++) {
            const commit = commits[i];
            const connections = [];

            // 1. Find which lane this commit occupies
            let myLane = activeLanes.indexOf(commit.hash);

            if (myLane === -1) {
                // New commit not expected by any lane — assign to first free lane or append
                myLane = activeLanes.indexOf(null);
                if (myLane === -1) {
                    myLane = activeLanes.length;
                    activeLanes.push(null);
                }
            }

            // 2. Process parents
            const parents = commit.parents || [];

            if (parents.length === 0) {
                // Root commit: close this lane
                activeLanes[myLane] = null;
            } else {
                // First parent: continues in the same lane
                activeLanes[myLane] = parents[0];

                // Additional parents (merge): find or create lanes
                for (let p = 1; p < parents.length; p++) {
                    const parentHash = parents[p];
                    let parentLane = activeLanes.indexOf(parentHash);

                    if (parentLane === -1) {
                        // Assign parent to a free lane
                        parentLane = activeLanes.indexOf(null);
                        if (parentLane === -1) {
                            parentLane = activeLanes.length;
                            activeLanes.push(null);
                        }
                        activeLanes[parentLane] = parentHash;
                    }

                    // Draw merge line from parent lane to this commit
                    connections.push({
                        fromLane: parentLane,
                        toLane: myLane,
                        type: 'merge-up',
                        colorLane: parentLane,
                    });
                }
            }

            // 3. Draw pass-through lines for all active lanes that aren't this commit
            for (let lane = 0; lane < activeLanes.length; lane++) {
                if (activeLanes[lane] !== null && lane !== myLane) {
                    // Check if this lane was just involved in a merge connection
                    const isMergeConn = connections.some(c => c.fromLane === lane);
                    if (!isMergeConn) {
                        connections.push({
                            fromLane: lane,
                            toLane: lane,
                            type: 'straight',
                            colorLane: lane,
                        });
                    }
                }
            }

            // 4. If first parent is in a different lane, draw branch-down
            if (parents.length > 0) {
                const firstParentLane = activeLanes.indexOf(parents[0]);
                if (firstParentLane !== -1 && firstParentLane !== myLane) {
                    connections.push({
                        fromLane: myLane,
                        toLane: firstParentLane,
                        type: 'branch-down',
                        colorLane: myLane,
                    });
                }
            }

            maxLanes = Math.max(maxLanes, activeLanes.filter(l => l !== null).length);

            rows.push({
                commit,
                lane: myLane,
                connections,
            });

            // 5. Clean up: compact lanes by removing trailing nulls
            while (activeLanes.length > 0 && activeLanes[activeLanes.length - 1] === null) {
                activeLanes.pop();
            }
        }

        return { rows, maxLanes: Math.max(maxLanes, 1) };
    }

    // ========================================================================
    // EVENT HANDLERS
    // ========================================================================

    _handleCommitSelected(e) {
        const commit = e.detail.commit;
        // Toggle: if clicking same commit, deselect
        if (this._selectedCommit?.hash === commit.hash) {
            this._selectedCommit = null;
        } else {
            this._selectedCommit = commit;
        }
    }

    _handleDetailClosed() {
        this._selectedCommit = null;
    }

    _handleNavigateCommit(e) {
        const hash = e.detail.hash;
        // Find commit in loaded commits
        const target = this._commits.find(c => c.hash === hash || c.hash.startsWith(hash));
        if (target) {
            this._selectedCommit = target;

            // Scroll to the commit node
            this.updateComplete.then(() => {
                const nodes = this.shadowRoot.querySelectorAll('commit-node');
                for (const node of nodes) {
                    if (node.commit?.hash === target.hash) {
                        node.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        break;
                    }
                }
            });
        }
    }

    _handleBranchFilter(e) {
        this._selectedBranch = e.target.value;
        this._selectedCommit = null;
        this.refresh();
    }

    async _loadMore() {
        this.maxCount += 50;
        await this.refresh();
    }
}

// Register the custom element
if (!customElements.get('git-graph')) {
    customElements.define('git-graph', GitGraph);
}
