/**
 * dependency-graph.js
 * Grafo interactivo de dependencias entre archivos/paquetes con D3 force.
 *
 * Visualiza las relaciones de import entre archivos como un grafo
 * de nodos (circles) y enlaces dirigidos (lines con flechas).
 *
 * Nodos:
 *   - Radio ∝ métrica de tamaño elegida (SLOC, LOC, funciones, CC, fan-in+out)
 *   - Color = métrica de color elegida (MI, CC media, CC máx, SLOC, Instabilidad)
 *
 * Links:
 *   - Flechas dirigidas (source importa de target)
 *   - Grosor ∝ número de imports (1-4px)
 *   - Rojo punteado para dependencias circulares (detección SCC client-side)
 *   - Hover: tooltip con source→target e import_names concretos
 *
 * Controles:
 *   - 📏 Métrica de tamaño: SLOC, LOC, Funciones, CC media, CC máx, Fan-in+out
 *   - 🎨 Métrica de color: MI, CC media, CC máx, SLOC, Instabilidad
 *   - 🔍 Filtro texto: buscar por nombre/path
 *   - 🚫 Exclusión por path: patrones para ocultar nodos (tests, __init__, etc.)
 *   - Toggle granularidad: package ↔ file
 *   - ⬡ Layout: Force graph ↔ Circle Packing
 *
 * Métricas de acoplamiento (calculadas client-side):
 *   - fan_in:      nº de archivos que importan este nodo
 *   - fan_out:     nº de archivos que este nodo importa
 *   - instability: fan_out / (fan_in + fan_out) — 0=estable, 1=inestable
 *   - fan_in_out:  fan_in + fan_out (grado total de acoplamiento)
 *
 * Detección de ciclos (client-side):
 *   - Algoritmo de Tarjan (Strongly Connected Components)
 *   - Cualquier SCC con >1 nodo forma un ciclo real
 *   - Captura circulares directas (A↔B) y transitivas (A→B→C→A)
 *
 * Interacciones:
 *   - Drag: mover nodos (force mode)
 *   - Zoom/Pan: d3.zoom() (ambos modos)
 *   - Hover nodo: tooltip con detalles + métricas de acoplamiento
 *   - Hover link: tooltip con source→target + import_names (force mode)
 *   - Click: highlight solo las dependencias del nodo (entrantes azul, salientes naranja)
 *
 * Props:
 *   - nodes: Array<ArchitectureNode> — nodos tipo file del snapshot
 *   - dependencies: Array<FileDependency> — dependencias resueltas
 *   - circularDependencies: Array<[string, string]> — pares circulares (no usado, SCC client-side)
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import * as d3 from 'https://cdn.jsdelivr.net/npm/d3@7/+esm';
import { themeTokens } from './styles/theme.js';
import { dependencyGraphStyles } from './styles/dependency-graph.styles.js';
import {
    METRIC_COLOR_CONFIGS,
    SIZE_METRICS,
    COLOR_METRICS,
    EXCLUDE_PRESETS,
    MIN_RADIUS,
    MAX_RADIUS,
    MIN_LINK_WIDTH,
    MAX_LINK_WIDTH,
} from './graph-config.js';
import {
    buildFileGraph,
    buildPackageGraph,
    buildPackHierarchy,
    applyFilters,
} from './graph-algorithms.js';

export class DependencyGraph extends LitElement {
    static properties = {
        /** Array of file nodes from architecture snapshot */
        nodes: { type: Array },

        /** Array of FileDependency objects */
        dependencies: { type: Array },

        /** Array of [source, target] circular dependency pairs (kept for API compat) */
        circularDependencies: { type: Array },

        /** Profundidad de agrupación: 1=top-level, 2=paquete, N=archivo */
        _depth: { state: true },

        /** Tooltip data for node hover: {x, y, ...nodeData} or null */
        _tooltipData: { state: true },

        /** Tooltip data for link hover: {x, y, source, target, import_names} or null */
        _linkTooltipData: { state: true },

        /** Currently selected node ID or null */
        _selectedNode: { state: true },

        // ── Controls ────────────────────────────────────────────────────
        /** Metric used for node radius */
        _sizeMetric: { state: true },

        /** Metric used for node color */
        _colorMetric: { state: true },

        // ── Filters ─────────────────────────────────────────────────────
        /** Text filter: match node name or path */
        _filterText: { state: true },

        /** Array of path patterns to exclude */
        _excludePatterns: { state: true },

        /** Current value of the exclude input field */
        _excludeInput: { state: true },

        // ── Layout ──────────────────────────────────────────────────────
        /** Active layout: 'force' | 'pack' */
        _layoutMode: { state: true },

        /** Show dependency links overlay in circle pack mode */
        _showPackLinks: { state: true },
    };

    static styles = [themeTokens, dependencyGraphStyles];

    constructor() {
        super();
        this.nodes = [];
        this.dependencies = [];
        this.circularDependencies = [];
        this._depth = 2;          // default: paquete (alineado con coupling.py depth=2)
        this._tooltipData = null;
        this._linkTooltipData = null;
        this._selectedNode = null;

        // Controls
        this._sizeMetric  = 'sloc';
        this._colorMetric = 'mi';

        // Filters
        this._filterText      = '';
        this._excludePatterns = [];
        this._excludeInput    = '';

        // Layout
        this._layoutMode    = 'force';
        this._showPackLinks = true;

        this._resizeObserver = null;
        this._simulation     = null;
        this._colorScale     = null;
        this._buildColorScale();
    }

    // ========================================================================
    // COLOR SCALE
    // ========================================================================

    _buildColorScale() {
        const config = METRIC_COLOR_CONFIGS[this._colorMetric] || METRIC_COLOR_CONFIGS.mi;
        this._colorScale = d3.scaleLinear()
            .domain(config.domain)
            .range(config.range)
            .clamp(true);
    }

    // ========================================================================
    // LIFECYCLE
    // ========================================================================

    firstUpdated() {
        const container = this.renderRoot.querySelector('.graph-container');
        if (container) {
            this._resizeObserver = new ResizeObserver(() => {
                this._renderGraph();
            });
            this._resizeObserver.observe(container);
        }
        this._renderGraph();
    }

    updated(changed) {
        // Full re-render on data, layout, or filter changes
        if (
            changed.has('nodes') || changed.has('dependencies') ||
            changed.has('circularDependencies') || changed.has('_depth') ||
            changed.has('_sizeMetric') || changed.has('_filterText') ||
            changed.has('_excludePatterns') || changed.has('_layoutMode') ||
            changed.has('_showPackLinks')
        ) {
            this._renderGraph();
            return;
        }

        // Color-only change: rebuild scale + update node colors (no sim restart)
        if (changed.has('_colorMetric')) {
            this._buildColorScale();
            this._updateNodeColors();
            this._updateLegend();
            return;
        }

        if (changed.has('_selectedNode')) {
            this._updateHighlight();
        }
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        if (this._resizeObserver) {
            this._resizeObserver.disconnect();
            this._resizeObserver = null;
        }
        if (this._simulation) {
            this._simulation.stop();
            this._simulation = null;
        }
    }

    // ========================================================================
    // RENDER (LitElement template)
    // ========================================================================

    render() {
        if (!this.nodes || this.nodes.length === 0) {
            return html`
                <div class="empty-state">
                    <span class="empty-state-icon">🔗</span>
                    <span class="empty-state-text">Sin datos de dependencias</span>
                </div>
            `;
        }

        return html`
            <div class="dg-wrapper">
                ${this._renderControls()}
                <div class="graph-container">
                    <svg class="graph-svg"></svg>
                    ${this._renderTooltip()}
                    ${this._renderLinkTooltip()}
                </div>
            </div>
        `;
    }

    // ========================================================================
    // CONTROLS BAR
    // ========================================================================

    _renderControls() {
        return html`
            <div class="dg-controls">
                <!-- Size metric -->
                <label class="dg-control-label">
                    <span class="dg-control-icon">📏</span>
                    <select
                        class="dg-control-select"
                        .value=${this._sizeMetric}
                        @change=${e => this._onSizeMetricChange(e.target.value)}
                    >
                        ${SIZE_METRICS.map(m => html`
                            <option value="${m.value}" ?selected=${m.value === this._sizeMetric}>
                                ${m.label}
                            </option>
                        `)}
                    </select>
                </label>

                <!-- Color metric -->
                <label class="dg-control-label">
                    <span class="dg-control-icon">🎨</span>
                    <select
                        class="dg-control-select"
                        .value=${this._colorMetric}
                        @change=${e => this._onColorMetricChange(e.target.value)}
                    >
                        ${COLOR_METRICS.map(m => html`
                            <option value="${m.value}" ?selected=${m.value === this._colorMetric}>
                                ${m.label}
                            </option>
                        `)}
                    </select>
                </label>

                <!-- Text filter -->
                <label class="dg-control-label dg-control-search">
                    <span class="dg-control-icon">🔍</span>
                    <input
                        type="text"
                        class="dg-filter-input"
                        placeholder="Filtrar por nombre..."
                        .value=${this._filterText}
                        @input=${e => this._filterText = e.target.value}
                    />
                    ${this._filterText ? html`
                        <button class="dg-filter-clear" @click=${() => this._filterText = ''} title="Limpiar">✕</button>
                    ` : ''}
                </label>

                <div class="dg-controls-separator"></div>

                <!-- Exclude presets -->
                ${EXCLUDE_PRESETS.map(p => html`
                    <button
                        class="dg-filter-btn ${this._excludePatterns.includes(p.pattern) ? 'active' : ''}"
                        @click=${() => this._togglePreset(p.pattern)}
                        title="Excluir paths con '${p.pattern}'"
                    >${p.label}</button>
                `)}

                <!-- Custom exclude input -->
                <label class="dg-control-label dg-control-search">
                    <span class="dg-control-icon">🚫</span>
                    <input
                        type="text"
                        class="dg-filter-input"
                        placeholder="excluir path..."
                        .value=${this._excludeInput}
                        @input=${e => this._excludeInput = e.target.value}
                        @keydown=${e => e.key === 'Enter' && this._addExcludePattern()}
                    />
                </label>
                ${this._excludeInput ? html`
                    <button
                        class="dg-filter-btn dg-filter-add"
                        @click=${this._addExcludePattern}
                        title="Añadir patrón de exclusión"
                    >+ Add</button>
                ` : ''}

                <!-- Active exclusion chips -->
                ${this._excludePatterns
                    .filter(p => !EXCLUDE_PRESETS.some(pr => pr.pattern === p))
                    .map(p => html`
                        <span class="dg-exclude-chip">
                            ${p}
                            <button class="dg-chip-remove" @click=${() => this._removeExcludePattern(p)} title="Quitar">✕</button>
                        </span>
                    `)
                }

                ${this._hasActiveFilters() ? html`
                    <button
                        class="dg-filter-btn dg-filter-reset"
                        @click=${this._resetFilters}
                        title="Limpiar todos los filtros"
                    >↺ Reset</button>
                ` : ''}

                <div class="dg-controls-spacer"></div>

                <!-- Layout toggle: Force ↔ Circle Pack -->
                <div class="dg-controls-separator"></div>
                <button
                    class="dg-filter-btn ${this._layoutMode === 'pack' ? 'active' : ''}"
                    @click=${() => this._layoutMode = this._layoutMode === 'force' ? 'pack' : 'force'}
                    title="Cambiar layout: Force graph ↔ Circle Packing"
                >⬡ Pack</button>
                ${this._layoutMode === 'pack' ? html`
                    <button
                        class="dg-filter-btn ${this._showPackLinks ? 'active' : ''}"
                        @click=${() => this._showPackLinks = !this._showPackLinks}
                        title="Mostrar/ocultar enlaces de dependencia en Circle Pack"
                    >🔗 Links</button>
                ` : ''}

                ${this._layoutMode === 'force' ? html`
                    <div class="dg-controls-separator"></div>
                    <!-- Depth stepper: − [ 📦 Label ] + -->
                    <div class="dg-depth-stepper">
                        <button
                            class="dg-depth-btn"
                            ?disabled=${this._depth <= 1}
                            @click=${() => this._setDepth(this._depth - 1)}
                            title="Menos detalle (agrupar más)"
                        >−</button>
                        <span class="dg-depth-label">
                            ${this._depth >= this._getMaxDepth() ? '📄' : '📦'} ${this._depthLabel(this._depth, this._getMaxDepth())}
                        </span>
                        <button
                            class="dg-depth-btn"
                            ?disabled=${this._depth >= this._getMaxDepth()}
                            @click=${() => this._setDepth(this._depth + 1)}
                            title="Más detalle (desglosar más)"
                        >+</button>
                    </div>
                ` : ''}
            </div>
        `;
    }

    _onSizeMetricChange(metric) {
        if (this._sizeMetric !== metric) this._sizeMetric = metric;
    }

    _onColorMetricChange(metric) {
        if (this._colorMetric !== metric) this._colorMetric = metric;
    }

    _togglePreset(pattern) {
        if (this._excludePatterns.includes(pattern)) {
            this._excludePatterns = this._excludePatterns.filter(p => p !== pattern);
        } else {
            this._excludePatterns = [...this._excludePatterns, pattern];
        }
    }

    _addExcludePattern() {
        const val = this._excludeInput.trim().toLowerCase();
        if (val && !this._excludePatterns.includes(val)) {
            this._excludePatterns = [...this._excludePatterns, val];
        }
        this._excludeInput = '';
    }

    _removeExcludePattern(pattern) {
        this._excludePatterns = this._excludePatterns.filter(p => p !== pattern);
    }

    _hasActiveFilters() {
        return this._filterText || this._excludePatterns.length > 0;
    }

    _resetFilters() {
        this._filterText      = '';
        this._excludePatterns = [];
        this._excludeInput    = '';
    }

    // ========================================================================
    // LEGEND (dynamic)
    // ========================================================================

    _renderLegend() {
        const config = METRIC_COLOR_CONFIGS[this._colorMetric] || METRIC_COLOR_CONFIGS.mi;
        return html`
            <div class="graph-legend" id="dg-legend">
                <div class="legend-title">${config.label}</div>
                ${config.legend.map(row => html`
                    <div class="legend-row">
                        <span class="legend-color" style="background: ${row.color}"></span>
                        <span>${row.text}</span>
                    </div>
                `)}
                <div class="legend-row" style="margin-top: 4px">
                    <span class="legend-line solid"></span>
                    <span>Dependencia</span>
                </div>
                <div class="legend-row">
                    <span class="legend-line dashed"></span>
                    <span>Ciclo</span>
                </div>
            </div>
        `;
    }

    // ========================================================================
    // NODE TOOLTIP
    // ========================================================================

    _renderTooltip() {
        if (!this._tooltipData) return html``;
        const d = this._tooltipData;
        return html`
            <div class="graph-tooltip visible" style="left: ${d.x}px; top: ${d.y}px;">
                <div class="tooltip-header">📄 ${d.name}</div>
                <div class="tooltip-path">${d.path}</div>
                ${this._renderTooltipMetrics(d)}
                <div class="tooltip-section">Acoplamiento</div>
                ${this._renderTooltipCoupling(d)}
            </div>
        `;
    }

    /** Renders the quality metrics grid rows for the node tooltip. */
    _renderTooltipMetrics(d) {
        const miScale  = d3.scaleLinear()
            .domain(METRIC_COLOR_CONFIGS.mi.domain)
            .range(METRIC_COLOR_CONFIGS.mi.range)
            .clamp(true);
        const miColor  = miScale(d.mi ?? 100);
        const miStatus = (d.mi ?? 100) >= 60 ? '✅' : (d.mi ?? 100) >= 40 ? '⚠️' : '🔴';
        const ccStatus = (d.avg_complexity ?? 0) < 5 ? '✅' : (d.avg_complexity ?? 0) < 10 ? '⚠️' : '🔴';
        return html`
            <div class="tooltip-grid">
                <span class="tooltip-label">SLOC</span>
                <span class="tooltip-value">${d.sloc}</span>
                <span class="tooltip-label">MI</span>
                <span class="tooltip-value">
                    <span class="tooltip-indicator" style="background: ${miColor}"></span>
                    ${(d.mi ?? 100).toFixed(1)} ${miStatus}
                </span>
                <span class="tooltip-label">CC media</span>
                <span class="tooltip-value">${(d.avg_complexity ?? 0).toFixed(1)} ${ccStatus}</span>
                <span class="tooltip-label">Funciones</span>
                <span class="tooltip-value">${d.functions_count}</span>
                <span class="tooltip-label">Clases</span>
                <span class="tooltip-value">${d.classes_count}</span>
            </div>
        `;
    }

    /** Renders the coupling metrics grid rows for the node tooltip. */
    _renderTooltipCoupling(d) {
        const instabScale  = d3.scaleLinear()
            .domain(METRIC_COLOR_CONFIGS.instability.domain)
            .range(METRIC_COLOR_CONFIGS.instability.range)
            .clamp(true);
        const instabColor  = instabScale(d.instability ?? 0);
        const instabStatus = (d.instability ?? 0) <= 0.3 ? '✅' : (d.instability ?? 0) <= 0.7 ? '⚠️' : '🔴';
        return html`
            <div class="tooltip-grid">
                <span class="tooltip-label">Fan-in</span>
                <span class="tooltip-value">${d.fan_in}</span>
                <span class="tooltip-label">Fan-out</span>
                <span class="tooltip-value">${d.fan_out}</span>
                <span class="tooltip-label">Inestab.</span>
                <span class="tooltip-value">
                    <span class="tooltip-indicator" style="background: ${instabColor}"></span>
                    ${(d.instability ?? 0).toFixed(2)} ${instabStatus}
                </span>
            </div>
        `;
    }

    // ========================================================================
    // LINK TOOLTIP
    // ========================================================================

    _renderLinkTooltip() {
        if (!this._linkTooltipData) return html``;

        const d = this._linkTooltipData;
        return html`
            <div class="link-tooltip visible"
                style="left: ${d.x}px; top: ${d.y}px;"
            >
                <div class="tooltip-header">
                    📤 ${d.sourceName} <span class="link-tooltip-arrow">→</span> ${d.targetName}
                </div>
                ${d.importNames && d.importNames.length > 0 ? html`
                    <div class="link-tooltip-imports">
                        ${d.importNames.map(name => html`
                            <div class="link-tooltip-import-row">• ${name}</div>
                        `)}
                    </div>
                ` : html`
                    <div class="link-tooltip-empty">import sin nombres explícitos</div>
                `}
            </div>
        `;
    }

    // ========================================================================
    // DEPTH CONTROL
    // ========================================================================

    /**
     * Set depth and reset interaction state.
     * @param {number} d — desired depth level
     */
    _setDepth(d) {
        const maxDepth = this._getMaxDepth();
        this._depth          = Math.max(1, Math.min(d, maxDepth));
        this._selectedNode   = null;
        this._tooltipData    = null;
        this._linkTooltipData = null;
    }

    /**
     * Compute the maximum meaningful depth (= file level) from the node tree.
     * Returns the number of path segments in the deepest file node.
     * At this depth, _buildFileGraph() is used instead of _buildPackageGraph().
     */
    _getMaxDepth() {
        if (!this.nodes || this.nodes.length === 0) return 4;
        let max = 1;
        for (const n of this.nodes) {
            if (n.type === 'file') {
                const d = (n.path || '').split('/').length;
                if (d > max) max = d;
            }
        }
        return max;
    }

    /**
     * Returns a human-readable label for the given depth level.
     * @param {number} depth
     * @param {number} maxDepth — file-level depth
     */
    _depthLabel(depth, maxDepth) {
        if (depth >= maxDepth) return 'Archivo';
        if (depth === 1)       return 'Top-level';
        if (depth === 2)       return 'Paquete';
        if (depth === 3)       return 'Sub-paquete';
        return `Módulo (L${depth})`;
    }

    // ========================================================================
    // DATA PREPARATION
    // ========================================================================

    /**
     * Build the graph data (nodes + links) based on current depth.
     * - depth >= maxDepth  → file-level graph (one node per file)
     * - depth < maxDepth   → package graph (files grouped by first N path segments)
     * @returns {{ graphNodes: Array, graphLinks: Array }}
     */
    _buildGraphData() {
        const maxDepth = this._getMaxDepth();
        return this._depth >= maxDepth
            ? buildFileGraph(this.nodes, this.dependencies)
            : buildPackageGraph(this.nodes, this.dependencies, Math.max(1, this._depth));
    }

    // ========================================================================
    // D3 GRAPH RENDERING — dispatcher
    // ========================================================================

    _renderGraph() {
        // Dispatch to the appropriate layout renderer
        if (this._layoutMode === 'pack') {
            this._renderPackLayout();
            return;
        }
        this._renderForceLayout();
    }

    // ========================================================================
    // CIRCLE PACK LAYOUT
    // ========================================================================

    /**
     * Render the dependency graph using D3 circle packing.
     * Files are positioned hierarchically by their directory structure.
     * Dependency links are optionally overlaid as thin lines.
     * Color = colorMetric, size ∝ sizeMetric.
     */
    _renderPackLayout() {
        const svgEl    = this.renderRoot.querySelector('.graph-svg');
        const container = this.renderRoot.querySelector('.graph-container');
        if (!svgEl || !container) return;
        if (!this.nodes || this.nodes.length === 0) return;

        const width  = container.clientWidth;
        const height = container.clientHeight;
        if (width <= 0 || height <= 0) return;

        // Stop any running force simulation
        if (this._simulation) {
            this._simulation.stop();
            this._simulation = null;
        }

        // Always use file-level data for pack (full hierarchy)
        const rawFileGraph = buildFileGraph(this.nodes, this.dependencies);
        const { graphNodes: filteredFiles, graphLinks: filteredLinks } = applyFilters(
            rawFileGraph.graphNodes, rawFileGraph.graphLinks,
            this._filterText, this._excludePatterns
        );

        // Rebuild color scale
        this._buildColorScale();

        const svg = d3.select(svgEl);
        svg.selectAll('*').remove();
        svg.attr('width', width).attr('height', height);

        if (filteredFiles.length === 0) {
            svg.append('text')
                .attr('x', width / 2).attr('y', height / 2)
                .attr('text-anchor', 'middle')
                .attr('fill', '#9ca3af')
                .attr('font-size', 13)
                .text('Sin nodos para los filtros activos');
            return;
        }

        // ── Build d3 hierarchy ────────────────────────────────────────────
        const treeData = buildPackHierarchy(filteredFiles);

        const hierRoot = d3.hierarchy(
            treeData,
            d => (d.children && d.children.length > 0) ? d.children : null
        )
        .sum(d => {
            const isLeaf = !d.children || d.children.length === 0;
            if (!isLeaf) return 0;
            return Math.max(d[this._sizeMetric] ?? 0, 1);
        })
        .sort((a, b) => b.value - a.value);

        // ── Pack layout ───────────────────────────────────────────────────
        const margin = 6;
        const pack = d3.pack()
            .size([width - margin * 2, height - margin * 2])
            .padding(d => {
                if (d.depth === 0) return 10;
                if (d.depth === 1) return 6;
                return 3;
            });

        const packedRoot = pack(hierRoot);

        // Build lookup: file node id → packed leaf node (for link drawing)
        const packNodeMap = new Map();
        packedRoot.descendants().forEach(d => {
            if (!d.children) {
                packNodeMap.set(d.data.id, d);
            }
        });

        // ── Zoom container ────────────────────────────────────────────────
        const zoomG = svg.append('g')
            .attr('class', 'zoom-container')
            .attr('transform', `translate(${margin},${margin})`);

        const zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on('zoom', event => zoomG.attr('transform', event.transform));
        svg.call(zoom);
        svg.on('click', () => { this._selectedNode = null; });

        // ── Draw links (optional overlay behind circles) ──────────────────
        const linkGroup = zoomG.append('g').attr('class', 'pack-links');
        let linkElements;

        if (this._showPackLinks && filteredLinks.length > 0) {
            linkElements = linkGroup.selectAll('.graph-link')
                .data(filteredLinks)
                .join('line')
                .attr('class', d => `graph-link ${d.isCircular ? 'circular' : ''}`)
                .attr('stroke',         d => d.isCircular ? '#dc2626' : '#6366f1')
                .attr('stroke-width',   d => d.isCircular ? 1.5 : 1)
                .attr('stroke-dasharray', d => d.isCircular ? '4 2' : null)
                .attr('stroke-opacity', d => d.isCircular ? 0.55 : 0.18)
                .attr('x1', d => {
                    const src = packNodeMap.get(
                        typeof d.source === 'object' ? d.source.id : d.source
                    );
                    return src ? src.x : 0;
                })
                .attr('y1', d => {
                    const src = packNodeMap.get(
                        typeof d.source === 'object' ? d.source.id : d.source
                    );
                    return src ? src.y : 0;
                })
                .attr('x2', d => {
                    const tgt = packNodeMap.get(
                        typeof d.target === 'object' ? d.target.id : d.target
                    );
                    return tgt ? tgt.x : 0;
                })
                .attr('y2', d => {
                    const tgt = packNodeMap.get(
                        typeof d.target === 'object' ? d.target.id : d.target
                    );
                    return tgt ? tgt.y : 0;
                });
        } else {
            // Empty selection so _updateHighlight still works without errors
            linkElements = linkGroup.selectAll('.graph-link').data([]).join('line');
        }

        // ── Draw circles for all nodes ────────────────────────────────────
        const nodeGroup = zoomG.append('g').attr('class', 'pack-nodes');

        const allNodes = nodeGroup.selectAll('g.pack-node')
            .data(packedRoot.descendants())
            .join('g')
            .attr('class', d => `pack-node ${d.children ? 'pack-container' : 'pack-leaf'}`)
            .attr('data-id', d => d.data.id)
            .attr('transform', d => `translate(${d.x},${d.y})`);

        // Circles
        allNodes.append('circle')
            .attr('r', d => d.r)
            .attr('fill', d => {
                if (d.data.isPackage) {
                    // Container circles: subtle layered fill
                    const alpha = Math.min(0.04 + d.depth * 0.018, 0.12);
                    return `rgba(99, 102, 241, ${alpha})`;
                }
                return this._nodeColor(d.data);
            })
            .attr('stroke', d => {
                if (d.data.isPackage) {
                    const alpha = Math.min(0.2 + d.depth * 0.08, 0.55);
                    return `rgba(99, 102, 241, ${alpha})`;
                }
                return 'rgba(255, 255, 255, 0.3)';
            })
            .attr('stroke-width', d => d.data.isPackage ? 1.5 : 1)
            .attr('opacity',      d => d.data.isPackage ? 1 : 0.88);

        // Package/directory labels (for containers with enough radius)
        allNodes.filter(d => d.data.isPackage && d.r > 18)
            .append('text')
            .attr('class', 'pack-label-container')
            .attr('text-anchor', 'middle')
            .attr('y', d => -d.r + Math.min(d.r * 0.25, 14))
            .attr('font-size', d => `${Math.min(Math.max(d.r * 0.18, 8), 13)}px`)
            .attr('fill', 'rgba(180, 185, 220, 0.8)')
            .attr('pointer-events', 'none')
            .attr('user-select', 'none')
            .text(d => d.data.name);

        // File labels (for leaf nodes with enough radius)
        const leafTextGroup = allNodes.filter(d => !d.data.isPackage && d.r > 10);

        // Split name by CamelCase or spaces (from the original Observable example)
        leafTextGroup.append('text')
            .attr('class', 'pack-label-leaf')
            .attr('text-anchor', 'middle')
            .attr('pointer-events', 'none')
            .attr('user-select', 'none')
            .attr('clip-path', d => `circle(${d.r - 1})`)
            .each(function(d) {
                const el       = d3.select(this);
                const words    = d.data.name.replace(/\.[^.]+$/, '') // strip extension
                    .split(/(?=[A-Z][a-z])|[_\-.\s]+/g)
                    .filter(Boolean);
                const fontSize = Math.min(Math.max(d.r * 0.28, 7), 11);
                const lineH    = fontSize * 1.2;
                const halfH    = (words.length - 1) * lineH / 2;

                el.attr('font-size', `${fontSize}px`).attr('fill', 'rgba(255,255,255,0.92)');

                words.forEach((word, i) => {
                    el.append('tspan')
                        .attr('x', 0)
                        .attr('dy', i === 0 ? `-${halfH}px` : `${lineH}px`)
                        .text(word);
                });
            });

        // ── Interactions on leaf nodes only ───────────────────────────────
        const leafNodes = allNodes.filter(d => !d.data.isPackage);

        leafNodes
            .style('cursor', 'pointer')
            .on('click', (event, d) => {
                event.stopPropagation();
                this._handleNodeClick(d.data);
            })
            .on('mouseenter', (event, d) => this._handleNodeMouseEnter(event, d.data))
            .on('mouseleave', () => { this._tooltipData = null; });

        // ── Store graph refs for highlight + color-only updates ───────────
        this._graphRefs = {
            nodeElements: leafNodes,
            linkElements,
            graphNodes:   filteredFiles,
            graphLinks:   filteredLinks,
            packNodeMap,
            isPack:       true,
        };

        // Apply current selected state
        if (this._selectedNode) this._updateHighlight();

        // Render legend
        this._renderLegendDOM();
    }

    // ========================================================================
    // FORCE LAYOUT (original _renderGraph body)
    // ========================================================================

    _renderForceLayout() {
        const svgEl    = this.renderRoot.querySelector('.graph-svg');
        const container = this.renderRoot.querySelector('.graph-container');
        if (!svgEl || !container) return;
        if (!this.nodes || this.nodes.length === 0) return;

        const width  = container.clientWidth;
        const height = container.clientHeight;
        if (width <= 0 || height <= 0) return;

        // Stop previous simulation
        if (this._simulation) {
            this._simulation.stop();
            this._simulation = null;
        }

        // Build raw graph data (with coupling metrics + SCC circular marking)
        const raw = this._buildGraphData();

        // Apply filters
        const { graphNodes, graphLinks } = applyFilters(
            raw.graphNodes, raw.graphLinks,
            this._filterText, this._excludePatterns
        );
        if (graphNodes.length === 0) {
            const svg = d3.select(svgEl);
            svg.selectAll('*').remove();
            svg.attr('width', width).attr('height', height);
            svg.append('text')
                .attr('x', width / 2).attr('y', height / 2)
                .attr('text-anchor', 'middle')
                .attr('fill', '#9ca3af')
                .attr('font-size', 13)
                .text('Sin nodos para los filtros activos');
            return;
        }

        // Rebuild color scale
        this._buildColorScale();

        // Clear previous SVG content
        const svg = d3.select(svgEl);
        svg.selectAll('*').remove();
        svg.attr('width', width).attr('height', height);

        // ── Radius scale ─────────────────────────────────────────────────
        const sizeValues = graphNodes.map(d => d[this._sizeMetric] ?? 0);
        const sizeExtent = d3.extent(sizeValues);
        const radiusScale = d3.scaleSqrt()
            .domain([0, Math.max(sizeExtent[1] || 1, 1)])
            .range([MIN_RADIUS, MAX_RADIUS]);

        // ── Link width scale ──────────────────────────────────────────────
        const importExtent = d3.extent(graphLinks, d => d.importCount) || [1, 1];
        const linkWidthScale = d3.scaleLinear()
            .domain([Math.min(importExtent[0], 1), Math.max(importExtent[1], 2)])
            .range([MIN_LINK_WIDTH, MAX_LINK_WIDTH])
            .clamp(true);

        // ── Arrow marker definitions ──────────────────────────────────────
        const defs = svg.append('defs');

        defs.append('marker')
            .attr('id', 'arrow')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('markerWidth', 8)
            .attr('markerHeight', 8)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-4L10,0L0,4')
            .attr('fill', '#d1d5db');

        defs.append('marker')
            .attr('id', 'arrow-circular')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('markerWidth', 8)
            .attr('markerHeight', 8)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-4L10,0L0,4')
            .attr('fill', '#dc2626');

        // ── Zoom container ────────────────────────────────────────────────
        const zoomG = svg.append('g').attr('class', 'zoom-container');

        const zoom = d3.zoom()
            .scaleExtent([0.2, 4])
            .on('zoom', (event) => {
                zoomG.attr('transform', event.transform);
            });
        svg.call(zoom);

        // ── Links (visible) ───────────────────────────────────────────────
        const linkGroup    = zoomG.append('g').attr('class', 'links');
        const linkElements = linkGroup.selectAll('.graph-link')
            .data(graphLinks)
            .join('line')
            .attr('class',        d => `graph-link ${d.isCircular ? 'circular' : ''}`)
            .attr('stroke',       d => d.isCircular ? '#dc2626' : '#d1d5db')
            .attr('stroke-width', d => linkWidthScale(d.importCount))
            .attr('stroke-dasharray', d => d.isCircular ? '6 3' : null)
            .attr('marker-end',   d => d.isCircular ? 'url(#arrow-circular)' : 'url(#arrow)');

        // ── Link hit areas (invisible, wider for easy hover) ──────────────
        const linkHitElements = linkGroup.selectAll('.graph-link-hit')
            .data(graphLinks)
            .join('line')
            .attr('class',  'graph-link-hit')
            .attr('stroke', 'transparent')
            .attr('stroke-width', 14)
            .style('cursor', 'crosshair')
            .on('mouseenter', (event, d) => this._handleLinkMouseEnter(event, d))
            .on('mouseleave', () => { this._linkTooltipData = null; });

        // ── Nodes ─────────────────────────────────────────────────────────
        const nodeGroup    = zoomG.append('g').attr('class', 'nodes');
        const nodeElements = nodeGroup.selectAll('.graph-node')
            .data(graphNodes, d => d.id)
            .join('g')
            .attr('class',    'graph-node')
            .attr('data-id',  d => d.id);

        nodeElements.append('circle')
            .attr('class', 'node-circle')
            .attr('r',    d => radiusScale(d[this._sizeMetric] ?? 0))
            .attr('fill', d => this._nodeColor(d));

        nodeElements.append('text')
            .attr('class', 'graph-node-label')
            .attr('dy',    d => radiusScale(d[this._sizeMetric] ?? 0) + 12)
            .text(d => d.name);

        // ── Drag ──────────────────────────────────────────────────────────
        const drag = d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this._simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this._simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });

        nodeElements.call(drag);

        // ── Node event handlers ───────────────────────────────────────────
        nodeElements
            .on('click', (event, d) => {
                event.stopPropagation();
                this._handleNodeClick(d);
            })
            .on('mouseenter', (event, d) => this._handleNodeMouseEnter(event, d))
            .on('mouseleave', () => { this._tooltipData = null; });

        svg.on('click', () => { this._selectedNode = null; });

        // ── Force simulation ──────────────────────────────────────────────
        this._simulation = d3.forceSimulation(graphNodes)
            .force('link', d3.forceLink(graphLinks)
                .id(d => d.id)
                .distance(100))
            .force('charge', d3.forceManyBody()
                .strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collide', d3.forceCollide()
                .radius(d => radiusScale(d[this._sizeMetric] ?? 0) + 5));

        this._simulation.on('tick', () => {
            linkElements
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            linkHitElements
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            nodeElements
                .attr('transform', d => `translate(${d.x},${d.y})`);
        });

        // ── Legend + store refs ───────────────────────────────────────────
        this._graphRefs = {
            nodeElements,
            linkElements,
            graphNodes,
            graphLinks,
            isPack: false,
        };

        // Render legend (DOM element inside graph-container)
        this._renderLegendDOM();
    }

    /**
     * Render the legend as a DOM element (appended to graph-container).
     * Called after graph render. Also called on color metric change.
     */
    _renderLegendDOM() {
        const container = this.renderRoot.querySelector('.graph-container');
        if (!container) return;

        // Remove existing legend DOM element (if any, from previous renders)
        const existing = container.querySelector('.graph-legend');
        if (existing) existing.remove();

        // Use simple DOM approach for the legend (no Lit render needed)
        const config = METRIC_COLOR_CONFIGS[this._colorMetric] || METRIC_COLOR_CONFIGS.mi;
        const legendEl = document.createElement('div');
        legendEl.className = 'graph-legend';
        legendEl.innerHTML = `
            <div class="legend-title">${config.label}</div>
            ${config.legend.map(row => `
                <div class="legend-row">
                    <span class="legend-color" style="background: ${row.color}; width:10px; height:10px; border-radius:50%; display:inline-block; flex-shrink:0; border:1px solid rgba(0,0,0,0.1)"></span>
                    <span>${row.text}</span>
                </div>
            `).join('')}
            <div class="legend-row" style="margin-top:4px">
                <span class="legend-line solid" style="display:inline-block; width:20px; height:2px; background:#d1d5db; flex-shrink:0"></span>
                <span>Dependencia</span>
            </div>
            <div class="legend-row">
                <span class="legend-line dashed" style="display:inline-block; width:20px; height:2px; background: repeating-linear-gradient(to right,#dc2626 0,#dc2626 4px,transparent 4px,transparent 7px); flex-shrink:0"></span>
                <span>Ciclo</span>
            </div>
        `;
        container.appendChild(legendEl);
    }

    // ========================================================================
    // COLOR-ONLY UPDATE (no sim restart / no pack rebuild)
    // ========================================================================

    _updateNodeColors() {
        if (!this._graphRefs) return;
        const { nodeElements, isPack } = this._graphRefs;

        if (isPack) {
            // In pack mode, the circle is the first child of each leaf g
            nodeElements.select('circle')
                .attr('fill', d => this._nodeColor(d.data));
        } else {
            nodeElements.select('circle.node-circle')
                .attr('fill', d => this._nodeColor(d));
        }
    }

    _updateLegend() {
        this._renderLegendDOM();
    }

    // ========================================================================
    // HIGHLIGHT (selected node connections)
    // ========================================================================

    _updateHighlight() {
        if (!this._graphRefs) return;
        const { nodeElements, linkElements, isPack } = this._graphRefs;
        const selectedId = this._selectedNode;

        // Helper to get node ID regardless of layout mode
        // Force: d = raw node object (d.id)
        // Pack:  d = d3 pack node (d.data.id)
        const getId = isPack
            ? d => (d.data?.id ?? d.id)
            : d => d.id;

        if (!selectedId) {
            nodeElements.classed('dimmed', false).classed('selected', false);
            linkElements
                .classed('dimmed', false)
                .classed('highlight-out', false)
                .classed('highlight-in', false);
            return;
        }

        const outTargets = new Set();
        const inSources  = new Set();

        linkElements.each(function (d) {
            const srcId = typeof d.source === 'object' ? d.source.id : d.source;
            const tgtId = typeof d.target === 'object' ? d.target.id : d.target;
            if (srcId === selectedId) outTargets.add(tgtId);
            if (tgtId === selectedId) inSources.add(srcId);
        });

        const connectedIds = new Set([selectedId, ...outTargets, ...inSources]);

        nodeElements
            .classed('selected', d => getId(d) === selectedId)
            .classed('dimmed',   d => !connectedIds.has(getId(d)));

        linkElements
            .classed('highlight-out', d => {
                const srcId = typeof d.source === 'object' ? d.source.id : d.source;
                return srcId === selectedId;
            })
            .classed('highlight-in', d => {
                const tgtId = typeof d.target === 'object' ? d.target.id : d.target;
                return tgtId === selectedId;
            })
            .classed('dimmed', d => {
                const srcId = typeof d.source === 'object' ? d.source.id : d.source;
                const tgtId = typeof d.target === 'object' ? d.target.id : d.target;
                return srcId !== selectedId && tgtId !== selectedId;
            });
    }

    // ========================================================================
    // EVENT HANDLERS
    // ========================================================================

    _handleNodeClick(d) {
        this._selectedNode = this._selectedNode === d.id ? null : d.id;
    }

    _handleNodeMouseEnter(event, d) {
        const container = this.renderRoot.querySelector('.graph-container');
        if (!container) return;

        const rect   = container.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;

        const tooltipW = 240;
        const tooltipH = 230;
        let x = mouseX + 14;
        let y = mouseY + 14;
        if (x + tooltipW > rect.width)  x = mouseX - tooltipW - 8;
        if (y + tooltipH > rect.height) y = mouseY - tooltipH - 8;
        if (x < 0) x = 4;
        if (y < 0) y = 4;

        this._linkTooltipData = null;
        this._tooltipData = {
            x, y,
            name:            d.name,
            path:            d.path,
            sloc:            d.sloc            || 0,
            loc:             d.loc             || 0,
            mi:              d.mi              ?? 100,
            avg_complexity:  d.avg_complexity  ?? 0,
            max_complexity:  d.max_complexity  ?? 0,
            functions_count: d.functions_count || 0,
            classes_count:   d.classes_count   || 0,
            fan_in:          d.fan_in          || 0,
            fan_out:         d.fan_out         || 0,
            instability:     d.instability     || 0,
            fan_in_out:      d.fan_in_out      || 0,
        };
    }

    _handleLinkMouseEnter(event, d) {
        const container = this.renderRoot.querySelector('.graph-container');
        if (!container) return;

        const rect   = container.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;

        const tooltipW = 220;
        const tooltipH = 160;
        let x = mouseX + 14;
        let y = mouseY + 14;
        if (x + tooltipW > rect.width)  x = mouseX - tooltipW - 8;
        if (y + tooltipH > rect.height) y = mouseY - tooltipH - 8;
        if (x < 0) x = 4;
        if (y < 0) y = 4;

        const srcNode = typeof d.source === 'object' ? d.source : { id: d.source, name: d.source };
        const tgtNode = typeof d.target === 'object' ? d.target : { id: d.target, name: d.target };

        this._tooltipData = null;
        this._linkTooltipData = {
            x, y,
            sourceName:  srcNode.name || srcNode.id,
            targetName:  tgtNode.name || tgtNode.id,
            importNames: d.importNames || [],
        };
    }

    // ========================================================================
    // HELPERS
    // ========================================================================

    /**
     * Returns the color for a node based on the current colorMetric.
     * @param {Object} d — node data
     */
    _nodeColor(d) {
        const value = d[this._colorMetric] ?? 0;
        return this._colorScale(value);
    }
}

// Register the custom element
if (!customElements.get('dependency-graph')) {
    customElements.define('dependency-graph', DependencyGraph);
}
