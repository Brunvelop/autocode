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
 *   - Rojo punteado para dependencias circulares
 *   - Hover: tooltip con source→target e import_names concretos
 *
 * Controles:
 *   - 📏 Métrica de tamaño: SLOC, LOC, Funciones, CC media, CC máx, Fan-in+out
 *   - 🎨 Métrica de color: MI, CC media, CC máx, SLOC, Instabilidad
 *   - 🔍 Filtro texto: buscar por nombre/path
 *   - ⚡ Filtros rápidos: solo circulares · solo MI<40 · ocultar aislados · min conexiones ≥N
 *   - Toggle granularidad: package ↔ file
 *
 * Métricas de acoplamiento (calculadas client-side):
 *   - fan_in:      nº de archivos que importan este nodo
 *   - fan_out:     nº de archivos que este nodo importa
 *   - instability: fan_out / (fan_in + fan_out) — 0=estable, 1=inestable
 *   - fan_in_out:  fan_in + fan_out (grado total de acoplamiento)
 *
 * Interacciones:
 *   - Drag: mover nodos
 *   - Zoom/Pan: d3.zoom()
 *   - Hover nodo: tooltip con detalles + métricas de acoplamiento
 *   - Hover link: tooltip con source→target + import_names
 *   - Click: highlight solo las dependencias del nodo (entrantes azul, salientes naranja)
 *
 * Props:
 *   - nodes: Array<ArchitectureNode> — nodos tipo file del snapshot
 *   - dependencies: Array<FileDependency> — dependencias resueltas
 *   - circularDependencies: Array<[string, string]> — pares circulares
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import * as d3 from 'https://cdn.jsdelivr.net/npm/d3@7/+esm';
import { themeTokens } from './styles/theme.js';
import { dependencyGraphStyles } from './styles/dependency-graph.styles.js';

// ============================================================================
// METRIC CONFIGURATIONS
// ============================================================================

/**
 * Color scale configuration per color metric.
 * Low instability = stable = good (like CC, inverted scale).
 */
const METRIC_COLOR_CONFIGS = {
    mi: {
        domain: [0, 40, 70, 100],
        range:  ['#dc2626', '#eab308', '#22c55e', '#059669'],
        label:  'MI',
        legend: [
            { color: '#dc2626', text: 'MI bajo (0–40)' },
            { color: '#eab308', text: 'MI medio (40–70)' },
            { color: '#22c55e', text: 'MI bueno (70–100)' },
        ],
    },
    avg_complexity: {
        domain: [0, 5, 15, 25],
        range:  ['#059669', '#22c55e', '#eab308', '#dc2626'],
        label:  'CC media',
        legend: [
            { color: '#059669', text: 'CC baja (0–5)' },
            { color: '#eab308', text: 'CC media (5–15)' },
            { color: '#dc2626', text: 'CC alta (>15)' },
        ],
    },
    max_complexity: {
        domain: [0, 10, 25, 50],
        range:  ['#059669', '#22c55e', '#eab308', '#dc2626'],
        label:  'CC máx',
        legend: [
            { color: '#059669', text: 'CC máx baja (0–10)' },
            { color: '#eab308', text: 'CC máx media (10–25)' },
            { color: '#dc2626', text: 'CC máx alta (>25)' },
        ],
    },
    sloc: {
        domain: [0, 100, 500, 2000],
        range:  ['#dbeafe', '#93c5fd', '#3b82f6', '#1d4ed8'],
        label:  'SLOC',
        legend: [
            { color: '#dbeafe', text: 'Pequeño (<100)' },
            { color: '#3b82f6', text: 'Mediano (100–500)' },
            { color: '#1d4ed8', text: 'Grande (>500)' },
        ],
    },
    instability: {
        domain: [0, 0.3, 0.7, 1],
        range:  ['#059669', '#22c55e', '#eab308', '#dc2626'],
        label:  'Inestab.',
        legend: [
            { color: '#059669', text: 'Estable (0–0.3)' },
            { color: '#eab308', text: 'Parcial (0.3–0.7)' },
            { color: '#dc2626', text: 'Inestable (0.7–1)' },
        ],
    },
};

/** Métricas disponibles para el tamaño de los nodos. */
const SIZE_METRICS = [
    { value: 'sloc',            label: 'SLOC' },
    { value: 'loc',             label: 'LOC' },
    { value: 'functions_count', label: 'Funciones' },
    { value: 'avg_complexity',  label: 'CC media' },
    { value: 'max_complexity',  label: 'CC máx' },
    { value: 'fan_in_out',      label: 'Fan-in+out' },
];

/** Métricas disponibles para el color de los nodos. */
const COLOR_METRICS = [
    { value: 'mi',              label: 'MI' },
    { value: 'avg_complexity',  label: 'CC media' },
    { value: 'max_complexity',  label: 'CC máx' },
    { value: 'sloc',            label: 'SLOC' },
    { value: 'instability',     label: 'Inestabilidad' },
];

// Radius scale bounds
const MIN_RADIUS = 8;
const MAX_RADIUS = 35;

// Link width scale bounds
const MIN_LINK_WIDTH = 1;
const MAX_LINK_WIDTH = 4;

export class DependencyGraph extends LitElement {
    static properties = {
        /** Array of file nodes from architecture snapshot */
        nodes: { type: Array },

        /** Array of FileDependency objects */
        dependencies: { type: Array },

        /** Array of [source, target] circular dependency pairs */
        circularDependencies: { type: Array },

        /** Granularity: 'file' | 'package' */
        _granularity: { state: true },

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

        /** Show only nodes involved in circular dependencies */
        _filterCircular: { state: true },

        /** Show only nodes with MI < 40 */
        _filterMiRed: { state: true },

        /** Hide isolated nodes (no connections) */
        _filterHideIsolated: { state: true },

        /** Show only nodes with fan_in+fan_out >= N */
        _minConnections: { state: true },
    };

    static styles = [themeTokens, dependencyGraphStyles];

    constructor() {
        super();
        this.nodes = [];
        this.dependencies = [];
        this.circularDependencies = [];
        this._granularity = 'file';
        this._tooltipData = null;
        this._linkTooltipData = null;
        this._selectedNode = null;

        // Controls
        this._sizeMetric  = 'sloc';
        this._colorMetric = 'mi';

        // Filters
        this._filterText          = '';
        this._filterCircular      = false;
        this._filterMiRed         = false;
        this._filterHideIsolated  = false;
        this._minConnections      = 0;

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
        // Full re-render on data or layout changes
        if (
            changed.has('nodes') || changed.has('dependencies') ||
            changed.has('circularDependencies') || changed.has('_granularity') ||
            changed.has('_sizeMetric') || changed.has('_filterText') ||
            changed.has('_filterCircular') || changed.has('_filterMiRed') ||
            changed.has('_filterHideIsolated') || changed.has('_minConnections')
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

                <!-- Quick filters -->
                <button
                    class="dg-filter-btn ${this._filterCircular ? 'active' : ''}"
                    @click=${() => this._filterCircular = !this._filterCircular}
                    title="Mostrar solo nodos con dependencias circulares"
                >⭕ Circulares</button>

                <button
                    class="dg-filter-btn ${this._filterMiRed ? 'active' : ''}"
                    @click=${() => this._filterMiRed = !this._filterMiRed}
                    title="Mostrar solo archivos con MI < 40"
                >🔴 MI&lt;40</button>

                <button
                    class="dg-filter-btn ${this._filterHideIsolated ? 'active' : ''}"
                    @click=${() => this._filterHideIsolated = !this._filterHideIsolated}
                    title="Ocultar archivos sin dependencias"
                >👻 Aislados</button>

                <label class="dg-control-label dg-control-min">
                    <span class="dg-control-icon" title="Mínimo de conexiones">Min:</span>
                    <input
                        type="number"
                        class="dg-min-input"
                        min="0"
                        max="50"
                        .value=${String(this._minConnections)}
                        @change=${e => this._minConnections = Math.max(0, parseInt(e.target.value) || 0)}
                    />
                </label>

                ${this._hasActiveFilters() ? html`
                    <button
                        class="dg-filter-btn dg-filter-reset"
                        @click=${this._resetFilters}
                        title="Limpiar todos los filtros"
                    >↺ Reset</button>
                ` : ''}

                <div class="dg-controls-spacer"></div>

                <!-- Granularity toggle -->
                <button
                    class="dg-granularity-btn ${this._granularity === 'package' ? 'active' : ''}"
                    @click=${this._toggleGranularity}
                    title="Alternar entre vista por archivo y por paquete"
                >
                    ${this._granularity === 'file' ? '📄 File' : '📦 Package'}
                </button>
            </div>
        `;
    }

    _onSizeMetricChange(metric) {
        if (this._sizeMetric !== metric) this._sizeMetric = metric;
    }

    _onColorMetricChange(metric) {
        if (this._colorMetric !== metric) this._colorMetric = metric;
    }

    _hasActiveFilters() {
        return this._filterText || this._filterCircular || this._filterMiRed ||
               this._filterHideIsolated || this._minConnections > 0;
    }

    _resetFilters() {
        this._filterText          = '';
        this._filterCircular      = false;
        this._filterMiRed         = false;
        this._filterHideIsolated  = false;
        this._minConnections      = 0;
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
                    <span>Circular</span>
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
    // GRANULARITY TOGGLE
    // ========================================================================

    _toggleGranularity() {
        this._granularity    = this._granularity === 'file' ? 'package' : 'file';
        this._selectedNode   = null;
        this._tooltipData    = null;
        this._linkTooltipData = null;
    }

    // ========================================================================
    // DATA PREPARATION
    // ========================================================================

    /**
     * Build the graph data (nodes + links) based on current granularity.
     * @returns {{ graphNodes: Array, graphLinks: Array }}
     */
    _buildGraphData() {
        return this._granularity === 'file'
            ? this._buildFileGraph()
            : this._buildPackageGraph();
    }

    /**
     * File-level graph: each file node is a graph node, each dependency is a link.
     * Also computes fan_in, fan_out, instability, fan_in_out per node.
     */
    _buildFileGraph() {
        const nodeIds = new Set(this.nodes.map(n => n.id));

        const graphNodes = this.nodes.map(n => ({
            id:              n.id,
            name:            n.name,
            path:            n.path,
            sloc:            n.sloc            || 0,
            loc:             n.loc             || 0,
            mi:              n.mi              ?? 100,
            avg_complexity:  n.avg_complexity  ?? 0,
            max_complexity:  n.max_complexity  ?? 0,
            functions_count: n.functions_count || 0,
            classes_count:   n.classes_count   || 0,
            // coupling metrics (filled below)
            fan_in:      0,
            fan_out:     0,
            instability: 0,
            fan_in_out:  0,
        }));

        const graphLinks = (this.dependencies || [])
            .filter(d => nodeIds.has(d.source) && nodeIds.has(d.target))
            .map(d => ({
                source:      d.source,
                target:      d.target,
                importCount: d.import_names?.length || 1,
                importNames: d.import_names || [],
                isCircular:  this._isCircular(d.source, d.target),
            }));

        // Compute coupling metrics
        this._computeCouplingMetrics(graphNodes, graphLinks);

        return { graphNodes, graphLinks };
    }

    /**
     * Package-level graph: group files by parent directory, aggregate metrics and deps.
     * Also computes fan_in, fan_out, instability, fan_in_out per package node.
     */
    _buildPackageGraph() {
        const packages = new Map();

        for (const node of this.nodes) {
            const pkgId = node.parent_id || '.';
            if (!packages.has(pkgId)) {
                packages.set(pkgId, {
                    id:              pkgId,
                    name:            pkgId === '.' ? 'root' : pkgId.split('/').pop(),
                    path:            pkgId,
                    files:           [],
                    sloc:            0,
                    loc:             0,
                    mi_sum:          0,
                    mi_weight:       0,
                    cc_sum:          0,
                    cc_max:          0,
                    functions_count: 0,
                    classes_count:   0,
                });
            }
            const pkg = packages.get(pkgId);
            pkg.files.push(node.id);
            pkg.sloc += node.sloc || 0;
            pkg.loc  += node.loc  || 0;
            const weight   = node.sloc || 1;
            pkg.mi_sum    += (node.mi ?? 100) * weight;
            pkg.mi_weight += weight;
            pkg.cc_sum    += (node.avg_complexity ?? 0) * weight;
            pkg.cc_max     = Math.max(pkg.cc_max, node.max_complexity ?? 0);
            pkg.functions_count += node.functions_count || 0;
            pkg.classes_count   += node.classes_count   || 0;
        }

        const graphNodes    = [];
        const fileToPackage = new Map();

        for (const [pkgId, pkg] of packages) {
            for (const fileId of pkg.files) {
                fileToPackage.set(fileId, pkgId);
            }
            graphNodes.push({
                id:              pkgId,
                name:            pkg.name,
                path:            pkg.path,
                sloc:            pkg.sloc,
                loc:             pkg.loc,
                mi:              pkg.mi_weight > 0 ? pkg.mi_sum / pkg.mi_weight : 100,
                avg_complexity:  pkg.mi_weight > 0 ? pkg.cc_sum / pkg.mi_weight : 0,
                max_complexity:  pkg.cc_max,
                functions_count: pkg.functions_count,
                classes_count:   pkg.classes_count,
                fan_in:      0,
                fan_out:     0,
                instability: 0,
                fan_in_out:  0,
            });
        }

        // Aggregate dependencies between packages
        const edgeMap = new Map();
        for (const dep of (this.dependencies || [])) {
            const srcPkg = fileToPackage.get(dep.source);
            const tgtPkg = fileToPackage.get(dep.target);
            if (!srcPkg || !tgtPkg || srcPkg === tgtPkg) continue;

            const key = `${srcPkg}→${tgtPkg}`;
            if (!edgeMap.has(key)) {
                edgeMap.set(key, {
                    source:      srcPkg,
                    target:      tgtPkg,
                    importCount: 0,
                    importNames: [],
                    isCircular:  false,
                });
            }
            const edge = edgeMap.get(key);
            edge.importCount += dep.import_names?.length || 1;
            if (dep.import_names) edge.importNames.push(...dep.import_names);
        }

        // Check circular at package level
        const edgeKeys = new Set(edgeMap.keys());
        for (const [key, edge] of edgeMap) {
            const reverseKey = `${edge.target}→${edge.source}`;
            if (edgeKeys.has(reverseKey)) {
                edge.isCircular = true;
                const rev = edgeMap.get(reverseKey);
                if (rev) rev.isCircular = true;
            }
        }

        const graphLinks = Array.from(edgeMap.values());

        // Compute coupling metrics
        this._computeCouplingMetrics(graphNodes, graphLinks);

        return { graphNodes, graphLinks };
    }

    /**
     * Computes fan_in, fan_out, instability, fan_in_out for each node in-place.
     * @param {Array} graphNodes
     * @param {Array} graphLinks  (source/target are IDs here, before D3 resolves them)
     */
    _computeCouplingMetrics(graphNodes, graphLinks) {
        const fanIn  = new Map(graphNodes.map(n => [n.id, 0]));
        const fanOut = new Map(graphNodes.map(n => [n.id, 0]));

        for (const link of graphLinks) {
            const srcId = typeof link.source === 'object' ? link.source.id : link.source;
            const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
            fanOut.set(srcId, (fanOut.get(srcId) || 0) + 1);
            fanIn.set(tgtId,  (fanIn.get(tgtId)  || 0) + 1);
        }

        for (const node of graphNodes) {
            node.fan_in    = fanIn.get(node.id)  || 0;
            node.fan_out   = fanOut.get(node.id) || 0;
            const total    = node.fan_in + node.fan_out;
            node.instability = total > 0 ? node.fan_out / total : 0;
            node.fan_in_out  = total;
        }
    }

    /**
     * Apply all active filters to the graph data.
     * @param {{ graphNodes: Array, graphLinks: Array }}
     * @returns {{ graphNodes: Array, graphLinks: Array }}
     */
    _applyFilters({ graphNodes, graphLinks }) {
        let visibleNodes = [...graphNodes];

        // Text filter (name or path)
        if (this._filterText) {
            const q = this._filterText.toLowerCase();
            visibleNodes = visibleNodes.filter(n =>
                n.name.toLowerCase().includes(q) || n.path.toLowerCase().includes(q));
        }

        // Only nodes involved in circular dependencies
        if (this._filterCircular) {
            const circularIds = new Set();
            for (const link of graphLinks) {
                if (link.isCircular) {
                    const srcId = typeof link.source === 'object' ? link.source.id : link.source;
                    const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
                    circularIds.add(srcId);
                    circularIds.add(tgtId);
                }
            }
            visibleNodes = visibleNodes.filter(n => circularIds.has(n.id));
        }

        // Only nodes with MI < 40
        if (this._filterMiRed) {
            visibleNodes = visibleNodes.filter(n => (n.mi ?? 100) < 40);
        }

        // Hide isolated nodes (no connections)
        if (this._filterHideIsolated) {
            visibleNodes = visibleNodes.filter(n => n.fan_in_out > 0);
        }

        // Min connections threshold
        if (this._minConnections > 0) {
            visibleNodes = visibleNodes.filter(n => n.fan_in_out >= this._minConnections);
        }

        // Filter links: only those with both endpoints visible
        const visibleIds    = new Set(visibleNodes.map(n => n.id));
        const visibleLinks  = graphLinks.filter(l => {
            const srcId = typeof l.source === 'object' ? l.source.id : l.source;
            const tgtId = typeof l.target === 'object' ? l.target.id : l.target;
            return visibleIds.has(srcId) && visibleIds.has(tgtId);
        });

        return { graphNodes: visibleNodes, graphLinks: visibleLinks };
    }

    /**
     * Check if a source→target link is part of a circular dependency.
     */
    _isCircular(source, target) {
        if (!this.circularDependencies) return false;
        return this.circularDependencies.some(pair => {
            const [a, b] = pair;
            return (a === source && b === target) || (a === target && b === source);
        });
    }

    // ========================================================================
    // D3 GRAPH RENDERING
    // ========================================================================

    _renderGraph() {
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

        // Build raw graph data (with coupling metrics)
        const raw = this._buildGraphData();

        // Apply filters
        const { graphNodes, graphLinks } = this._applyFilters(raw);
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
        this._graphRefs = { nodeElements, linkElements, graphNodes, graphLinks };

        // Render legend (DOM element inside graph-container)
        this._renderLegendDOM();
    }

    /**
     * Render the legend as a DOM element (appended to graph-container).
     * Called after graph render. Also called on color metric change.
     */
    _renderLegendDOM() {
        // Legend is handled by Lit via _renderLegend() in render() template.
        // We trigger a re-render by requesting update (legend is inside graph-container).
        // Since graph-container is inside the Lit template, nothing extra is needed —
        // the legend is rendered as part of render() → _renderLegend() already.
        // We just need to ensure it's included in the Lit template render cycle.
        // NOTE: Legend is now rendered via _renderLegend() which is called in render()
        // for the graph-container template. We need to insert it after graph renders.
        const container = this.renderRoot.querySelector('.graph-container');
        if (!container) return;

        // Remove existing legend DOM element (if any, from previous renders)
        const existing = container.querySelector('.graph-legend');
        if (existing) existing.remove();

        // Create legend using Lit's render into a div
        const legendEl = document.createElement('div');
        legendEl.innerHTML = ''; // will be filled
        container.appendChild(legendEl);

        // Use simple DOM approach for the legend (no Lit render needed)
        const config = METRIC_COLOR_CONFIGS[this._colorMetric] || METRIC_COLOR_CONFIGS.mi;
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
                <span>Circular</span>
            </div>
        `;
    }

    // ========================================================================
    // COLOR-ONLY UPDATE (no sim restart)
    // ========================================================================

    _updateNodeColors() {
        if (!this._graphRefs) return;
        const { nodeElements } = this._graphRefs;
        nodeElements.select('circle.node-circle')
            .attr('fill', d => this._nodeColor(d));
    }

    _updateLegend() {
        this._renderLegendDOM();
    }

    // ========================================================================
    // HIGHLIGHT (selected node connections)
    // ========================================================================

    _updateHighlight() {
        if (!this._graphRefs) return;
        const { nodeElements, linkElements } = this._graphRefs;
        const selectedId = this._selectedNode;

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
            .classed('selected', d => d.id === selectedId)
            .classed('dimmed',   d => !connectedIds.has(d.id));

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
