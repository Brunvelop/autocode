/**
 * treemap-view.js
 * Treemap zoomable anidado de arquitectura de código con D3.
 *
 * Visualiza la jerarquía completa de directorios/archivos como rectángulos
 * proporcionales a la métrica de tamaño elegida (por defecto: SLOC).
 * El color refleja la métrica de calidad elegida (por defecto: MI).
 *
 * Métricas configurables:
 *   - sizeMetric: 'sloc' | 'loc' | 'functions_count' | 'classes_count' |
 *                 'avg_complexity' | 'max_complexity'   (default: 'sloc')
 *   - colorMetric: 'mi' | 'avg_complexity' | 'max_complexity' |
 *                  'sloc' | 'loc' | 'functions_count' | 'classes_count'  (default: 'mi')
 *
 * Colores (según colorMetric):
 *   MI           → Rojo (bajo) → Amarillo → Verde → Verde oscuro (alto, bueno)
 *   avg/max CC   → Verde (bajo=bueno) → Amarillo → Rojo (alto=malo)
 *   sloc/loc/etc → Azul claro (bajo) → Azul oscuro (alto, secuencial)
 *
 * Interacción:
 *   - Click en directorio → zoom in con animación espacial (750ms)
 *   - Click en segmento del breadcrumb → navega a ese nivel (instantáneo)
 *   - Hover → tooltip con métricas detalladas
 *   - Selectores en barra de controles → cambia la métrica de tamaño / color
 *
 * Props:
 *   - node:        Object — Nodo raíz del árbol anidado (con children recursivos)
 *   - zoomNodeId:  String — ID del nodo al que debe sincronizarse el zoom
 *   - sizeMetric:  String — Métrica que determina el área de cada nodo
 *   - colorMetric: String — Métrica que determina el color de los nodos hoja
 *
 * Events emitidos:
 *   - navigate-into: { detail: { nodeId } } — al hacer zoom in, zoom out o click en breadcrumb
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import * as d3 from 'https://cdn.jsdelivr.net/npm/d3@7/+esm';
import { themeTokens } from './styles/theme.js';
import { treemapViewStyles } from './styles/treemap-view.styles.js';

// ============================================================================
// METRIC CONFIGURATIONS
// ============================================================================

/**
 * Color scale configuration for each color metric.
 * domain: breakpoints, range: colors at those breakpoints.
 */
const METRIC_COLOR_CONFIGS = {
    mi: {
        domain: [0, 40, 70, 100],
        range:  ['#dc2626', '#eab308', '#22c55e', '#059669'],
        label:  'MI',
    },
    avg_complexity: {
        domain: [0, 5, 15, 25],
        range:  ['#059669', '#22c55e', '#eab308', '#dc2626'], // inverted: low=good
        label:  'CC media',
    },
    max_complexity: {
        domain: [0, 10, 25, 50],
        range:  ['#059669', '#22c55e', '#eab308', '#dc2626'], // inverted: low=good
        label:  'CC máx',
    },
    sloc: {
        domain: [0, 100, 500, 2000],
        range:  ['#dbeafe', '#93c5fd', '#3b82f6', '#1d4ed8'], // sequential blue
        label:  'SLOC',
    },
    loc: {
        domain: [0, 150, 750, 3000],
        range:  ['#dbeafe', '#93c5fd', '#3b82f6', '#1d4ed8'],
        label:  'LOC',
    },
    functions_count: {
        domain: [0, 5, 20, 50],
        range:  ['#ede9fe', '#a78bfa', '#7c3aed', '#4c1d95'],
        label:  'Funciones',
    },
    classes_count: {
        domain: [0, 2, 8, 20],
        range:  ['#ede9fe', '#a78bfa', '#7c3aed', '#4c1d95'],
        label:  'Clases',
    },
};

/** Metrics available for controlling node area (treemap size). */
const SIZE_METRICS = [
    { value: 'sloc',            label: 'SLOC' },
    { value: 'loc',             label: 'LOC' },
    { value: 'functions_count', label: 'Funciones' },
    { value: 'classes_count',   label: 'Clases' },
    { value: 'avg_complexity',  label: 'CC media' },
    { value: 'max_complexity',  label: 'CC máx' },
];

/** Metrics available for controlling leaf node color. */
const COLOR_METRICS = [
    { value: 'mi',              label: 'MI' },
    { value: 'avg_complexity',  label: 'CC media' },
    { value: 'max_complexity',  label: 'CC máx' },
    { value: 'sloc',            label: 'SLOC' },
    { value: 'loc',             label: 'LOC' },
    { value: 'functions_count', label: 'Funciones' },
    { value: 'classes_count',   label: 'Clases' },
];

/** Short display labels for metrics (used in leaf sub-labels). */
const METRIC_SHORT_LABELS = {
    sloc:            'SLOC',
    loc:             'LOC',
    mi:              'MI',
    avg_complexity:  'CC',
    max_complexity:  'CCmax',
    functions_count: 'fn',
    classes_count:   'cls',
};

// Icons for each node type (shown in labels)
const NODE_TYPE_ICONS = {
    directory: '📂',
    file:      '📄',
    class:     '🔷',
    function:  '⚡',
    method:    '🔹',
};

// Node types that act as containers (rendered with padding, like directories)
const CONTAINER_TYPES = new Set(['directory', 'class']);

// Rank badge colors
const RANK_COLORS = { A:'#059669', B:'#22c55e', C:'#eab308', D:'#f97316', E:'#ef4444', F:'#dc2626' };

// Directory node colors by depth (darker = deeper hierarchy level)
const DIR_COLORS = [
    'rgba(30, 41, 59, 0.82)',   // depth 0 – root
    'rgba(30, 58, 138, 0.72)',  // depth 1
    'rgba(30, 64, 175, 0.62)',  // depth 2
    'rgba(37, 99, 235, 0.52)',  // depth 3
    'rgba(59, 130, 246, 0.42)', // depth 4
    'rgba(96, 165, 250, 0.35)', // depth 5+
];

export class TreemapView extends LitElement {
    static properties = {
        /** Full nested tree from dashboard */
        node: { type: Object },

        /** Node ID to sync zoom state with dashboard */
        zoomNodeId: { type: String },

        /** Metric used for node area (treemap sizing) */
        sizeMetric: { type: String },

        /** Metric used for leaf node color */
        colorMetric: { type: String },

        /**
         * Reactive: array of ancestor segments from root to current zoom node.
         * Each entry: { name: string, id: string, d3Node: HierarchyNode }
         */
        _zoomAncestors: { state: true },

        /** Reactive: tooltip data */
        _tooltipData: { state: true },

        /** Show function/class/method nodes inside files */
        showFunctions: { type: Boolean },
    };

    static styles = [themeTokens, treemapViewStyles];

    constructor() {
        super();
        this.node          = null;
        this.zoomNodeId    = null;
        this.sizeMetric    = 'sloc';
        this.colorMetric   = 'mi';
        this.showFunctions = true;

        // Reactive state for Lit template
        this._zoomAncestors = [];
        this._tooltipData   = null;

        // D3 state — managed manually, not reactive
        this._d3Root   = null;
        this._zoomNode = null;
        this._svgSel   = null;
        this._group    = null;
        this._xScale   = null;
        this._yScale   = null;
        this._canvasW  = 0;
        this._canvasH  = 0;

        this._resizeObserver = null;
        this._colorScale = null;
        this._buildColorScale();
    }

    // ========================================================================
    // COLOR SCALE
    // ========================================================================

    /**
     * Builds (or rebuilds) the D3 color scale for the current colorMetric.
     * Call whenever colorMetric changes.
     */
    _buildColorScale() {
        const config = METRIC_COLOR_CONFIGS[this.colorMetric] || METRIC_COLOR_CONFIGS.mi;
        this._colorScale = d3.scaleLinear()
            .domain(config.domain)
            .range(config.range)
            .clamp(true);
    }

    // ========================================================================
    // LIFECYCLE
    // ========================================================================

    firstUpdated() {
        const container = this.renderRoot.querySelector('.treemap-container');
        if (container) {
            this._resizeObserver = new ResizeObserver(() => this._rebuildTreemap());
            this._resizeObserver.observe(container);
        }
        this._rebuildTreemap();
    }

    updated(changed) {
        // Rebuild completely when tree data, size metric, or showFunctions changes
        if (changed.has('node') || changed.has('sizeMetric') || changed.has('showFunctions')) {
            this._rebuildTreemap();
            return; // _rebuildTreemap will also apply zoomNodeId
        }

        // On color metric change: rebuild scale + redraw current level (layout unchanged)
        if (changed.has('colorMetric')) {
            this._buildColorScale();
            if (this._svgSel && this._zoomNode) {
                this._group.selectAll('*').remove();
                this._drawLevel(this._group, this._zoomNode);
            }
            return;
        }

        if (changed.has('zoomNodeId') && this._d3Root) {
            this._applyZoomNodeId();
        }
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        if (this._resizeObserver) {
            this._resizeObserver.disconnect();
            this._resizeObserver = null;
        }
    }

    // ========================================================================
    // RENDER — Lit template (shell only; D3 draws inside SVG)
    // ========================================================================

    render() {
        if (!this.node) {
            return html`
                <div class="empty-state">
                    <span class="empty-state-icon">🗺️</span>
                    <span class="empty-state-text">Sin datos de arquitectura</span>
                </div>`;
        }

        const children = this.node.children;
        if (!children || children.length === 0) {
            if (this.node.type === 'file') return this._renderSingleNode(this.node);
            return html`
                <div class="empty-state">
                    <span class="empty-state-icon">📂</span>
                    <span class="empty-state-text">Directorio vacío</span>
                </div>`;
        }

        return html`
            <div class="treemap-wrapper">
                ${this._renderHeaderBar()}
                ${this._renderControls()}
                <div class="treemap-container">
                    <svg class="treemap-svg"></svg>
                    ${this._renderTooltip()}
                </div>
            </div>`;
    }

    // ========================================================================
    // HEADER BAR — breadcrumb clicable en HTML (no SVG)
    // ========================================================================

    _renderHeaderBar() {
        return html`
            <div class="tm-header-bar">
                ${this._zoomAncestors.map((seg, i, arr) => {
                    const isLast = i === arr.length - 1;
                    return html`
                        ${i > 0 ? html`<span class="tm-header-separator">›</span>` : ''}
                        <button
                            class="tm-header-segment ${isLast ? 'current' : ''}"
                            ?disabled=${isLast}
                            title="${seg.id}"
                            @click=${() => { if (!isLast) this._navigateTo(seg.d3Node); }}
                        >${i === 0 ? `🗺️ ${seg.name}` : seg.name}</button>
                    `;
                })}
            </div>`;
    }

    // ========================================================================
    // CONTROLS BAR — metric selectors
    // ========================================================================

    _renderControls() {
        return html`
            <div class="tm-controls">
                <label class="tm-control-label">
                    <span class="tm-control-icon">📏</span>
                    <select
                        class="tm-control-select"
                        .value=${this.sizeMetric}
                        @change=${e => this._onSizeMetricChange(e.target.value)}
                    >
                        ${SIZE_METRICS.map(m => html`
                            <option value="${m.value}" ?selected=${m.value === this.sizeMetric}>
                                ${m.label}
                            </option>
                        `)}
                    </select>
                </label>
                <label class="tm-control-label">
                    <span class="tm-control-icon">🎨</span>
                    <select
                        class="tm-control-select"
                        .value=${this.colorMetric}
                        @change=${e => this._onColorMetricChange(e.target.value)}
                    >
                        ${COLOR_METRICS.map(m => html`
                            <option value="${m.value}" ?selected=${m.value === this.colorMetric}>
                                ${m.label}
                            </option>
                        `)}
                    </select>
                </label>
                <label class="tm-control-label">
                    <input
                        type="checkbox"
                        class="tm-control-checkbox"
                        .checked=${this.showFunctions}
                        @change=${e => this._onShowFunctionsChange(e.target.checked)}
                    />
                    <span>⚡ fn</span>
                </label>
            </div>`;
    }

    _onSizeMetricChange(metric) {
        if (this.sizeMetric === metric) return;
        this.sizeMetric = metric;
    }

    _onColorMetricChange(metric) {
        if (this.colorMetric === metric) return;
        this.colorMetric = metric;
    }

    _onShowFunctionsChange(val) {
        if (this.showFunctions === val) return;
        this.showFunctions = val;
    }

    // ========================================================================
    // SINGLE NODE
    // ========================================================================

    _renderSingleNode(node) {
        const color = this._leafColor(node);
        return html`
            <div class="single-node" style="background: ${color}">
                <span class="single-node-name">📄 ${node.name}</span>
                <span class="single-node-metrics">
                    SLOC: ${node.sloc} · MI: ${node.mi?.toFixed(1)} · CC: ${node.avg_complexity?.toFixed(1)}
                </span>
            </div>`;
    }

    // ========================================================================
    // TOOLTIP — dispatcher + sub-renderers + helpers
    // ========================================================================

    /** Dispatches to the correct sub-renderer based on node type. CC ~4 */
    _renderTooltip() {
        if (!this._tooltipData) return html``;
        const d    = this._tooltipData;
        const icon = NODE_TYPE_ICONS[d.type] || '📄';
        if (d.type === 'function' || d.type === 'method') return this._renderFnMethodTooltip(d, icon);
        if (d.type === 'class')                           return this._renderClassTooltip(d, icon);
        return this._renderFileOrDirTooltip(d, icon);
    }

    /** Tooltip for function / method nodes: SLOC, MI, CC, Rank. */
    _renderFnMethodTooltip(d, icon) {
        const rankColor = this._rankColor(d.rank);
        const miColor   = this._tooltipMiColor(d.mi);
        const miStatus  = this._miStatusIcon(d.mi);
        return html`
            <div class="treemap-tooltip visible" style="left:${d.x}px;top:${d.y}px;">
                <div class="tooltip-header">${icon} ${d.name}</div>
                <div class="tooltip-path">${d.path}</div>
                <div class="tooltip-grid">
                    <span class="tooltip-label">SLOC</span>
                    <span class="tooltip-value">${d.sloc}</span>
                    <span class="tooltip-label">MI</span>
                    <span class="tooltip-value">
                        <span class="tooltip-mi-indicator" style="background:${miColor}"></span>
                        ${d.mi?.toFixed(1)} ${miStatus}
                    </span>
                    <span class="tooltip-label">CC</span>
                    <span class="tooltip-value">${d.complexity ?? d.avg_complexity?.toFixed(1)}</span>
                    <span class="tooltip-label">Rank</span>
                    <span class="tooltip-value" style="color:${rankColor};font-weight:700">${d.rank ?? '—'}</span>
                </div>
            </div>`;
    }

    /** Tooltip for class nodes: SLOC, MI, method count, avg CC. */
    _renderClassTooltip(d, icon) {
        const miColor  = this._tooltipMiColor(d.mi);
        const miStatus = this._miStatusIcon(d.mi);
        const ccStatus = this._ccStatusIcon(d.avg_complexity);
        return html`
            <div class="treemap-tooltip visible" style="left:${d.x}px;top:${d.y}px;">
                <div class="tooltip-header">${icon} ${d.name}</div>
                <div class="tooltip-path">${d.path}</div>
                <div class="tooltip-grid">
                    <span class="tooltip-label">SLOC</span>
                    <span class="tooltip-value">${d.sloc}</span>
                    <span class="tooltip-label">MI</span>
                    <span class="tooltip-value">
                        <span class="tooltip-mi-indicator" style="background:${miColor}"></span>
                        ${d.mi?.toFixed(1)} ${miStatus}
                    </span>
                    <span class="tooltip-label">Métodos</span>
                    <span class="tooltip-value">${d.functions_count}</span>
                    <span class="tooltip-label">CC media</span>
                    <span class="tooltip-value">${d.avg_complexity?.toFixed(1)} ${ccStatus}</span>
                </div>
            </div>`;
    }

    /** Tooltip for file / directory nodes: LOC, SLOC, MI, avg CC, functions, classes. */
    _renderFileOrDirTooltip(d, icon) {
        const miColor  = this._tooltipMiColor(d.mi);
        const miStatus = this._miStatusIcon(d.mi);
        const ccStatus = this._ccStatusIcon(d.avg_complexity);
        return html`
            <div class="treemap-tooltip visible" style="left:${d.x}px;top:${d.y}px;">
                <div class="tooltip-header">${icon} ${d.name}</div>
                <div class="tooltip-path">${d.path}</div>
                <div class="tooltip-grid">
                    <span class="tooltip-label">LOC</span>
                    <span class="tooltip-value">${d.loc}</span>
                    <span class="tooltip-label">SLOC</span>
                    <span class="tooltip-value">${d.sloc}</span>
                    <span class="tooltip-label">MI</span>
                    <span class="tooltip-value">
                        <span class="tooltip-mi-indicator" style="background:${miColor}"></span>
                        ${d.mi?.toFixed(1)} ${miStatus}
                    </span>
                    <span class="tooltip-label">CC media</span>
                    <span class="tooltip-value">${d.avg_complexity?.toFixed(1)} ${ccStatus}</span>
                    <span class="tooltip-label">Funciones</span>
                    <span class="tooltip-value">${d.functions_count}</span>
                    <span class="tooltip-label">Clases</span>
                    <span class="tooltip-value">${d.classes_count}</span>
                </div>
            </div>`;
    }

    /** Returns the badge color for a rank letter (A–F). */
    _rankColor(rank) { return RANK_COLORS[rank] || '#6b7280'; }

    /** Returns the MI color from the D3 scale for use in tooltips. */
    _tooltipMiColor(mi) {
        const cfg = METRIC_COLOR_CONFIGS.mi;
        return d3.scaleLinear().domain(cfg.domain).range(cfg.range).clamp(true)(mi);
    }

    /** Returns a status emoji for a Maintainability Index value. */
    _miStatusIcon(mi)  { return mi >= 60 ? '✅' : mi >= 40 ? '⚠️' : '🔴'; }

    /** Returns a status emoji for a cyclomatic complexity value. */
    _ccStatusIcon(cc)  { return cc < 5  ? '✅' : cc < 10  ? '⚠️' : '🔴'; }

    // ========================================================================
    // D3 — BUILD FULL TREEMAP (called on node change, resize, or sizeMetric change)
    // ========================================================================

    _rebuildTreemap() {
        const svgEl     = this.renderRoot.querySelector('.treemap-svg');
        const container = this.renderRoot.querySelector('.treemap-container');
        if (!svgEl || !container || !this.node) return;

        const children = this.node.children;
        if (!children || children.length === 0) return;

        const width  = container.clientWidth;
        const height = container.clientHeight;
        if (width <= 0 || height <= 0) return;

        this._canvasW = width;
        this._canvasH = height;

        // ── D3 hierarchy — sum by sizeMetric ─────────────────────────────
        // NOTE: Use ?? (nullish coalescing), NOT || (logical OR).
        // With ||, a value of 0 is treated as falsy and would silently fall
        // back to sloc, making zero-metric nodes appear huge.
        const sizeMetric    = this.sizeMetric || 'sloc';
        const showFunctions = this.showFunctions;

        // Children accessor: when showFunctions=false, file nodes become leaves
        // (their function/class children are hidden from the D3 hierarchy).
        const root = d3.hierarchy(this.node, d => {
            if (!showFunctions && d.type === 'file') return null;
            return d.children;
        })
            .sum(d => {
                // A node is a "leaf" if it has no children in raw data,
                // OR if it's a file and showFunctions=false (the children accessor treats it as a leaf,
                // but d.children still points to the raw functions array → would return 0 without this check).
                const isLeaf = !d.children || d.children.length === 0 || (!showFunctions && d.type === 'file');
                if (!isLeaf) return 0;
                const val = d[sizeMetric] ?? 0;
                return val > 0 ? val : 0.1; // 0 → tiny but visible; never falls back to sloc
            })

            .sort((a, b) => (b.value || 0) - (a.value || 0));

        // ── Treemap layout (full nested with padding) ─────────────────────
        d3.treemap()
            .size([width, height])
            .paddingOuter(4)
            .paddingTop(20)
            .paddingInner(1)
            .round(true)(root);

        this._d3Root   = root;
        this._zoomNode = root;

        // ── SVG shell ─────────────────────────────────────────────────────
        d3.select(svgEl).selectAll('*').remove();
        const svg = d3.select(svgEl)
            .attr('width', width)
            .attr('height', height)
            .attr('viewBox', `0 0 ${width} ${height}`)
            .style('font', '10px sans-serif');

        this._svgSel = svg;

        // Drop-shadow filter
        const filter = svg.append('defs')
            .append('filter').attr('id', 'tm-shadow');
        filter.append('feDropShadow')
            .attr('flood-opacity', 0.25)
            .attr('dx', 0).attr('dy', 1)
            .attr('stdDeviation', 3);

        // ── Zoom scales ───────────────────────────────────────────────────
        this._xScale = d3.scaleLinear()
            .domain([root.x0, root.x1])
            .rangeRound([0, width]);
        this._yScale = d3.scaleLinear()
            .domain([root.y0, root.y1])
            .rangeRound([0, height]);

        // ── Initial draw ──────────────────────────────────────────────────
        this._group = svg.append('g');
        this._drawLevel(this._group, root);
        this._updateHeader(root);

        // Apply zoomNodeId if set (e.g., breadcrumb navigated before tree built)
        if (this.zoomNodeId) {
            this._applyZoomNodeId();
        }
    }

    // ========================================================================
    // D3 — DRAW LEVEL (draws all descendants of focusNode)
    // ========================================================================

    /**
     * Draws all descendants of `focusNode` layered by depth (parents behind children).
     * Nodes are positioned using the CURRENT _xScale/_yScale at time of call.
     * Font sizes are computed dynamically based on cell dimensions.
     */
    _drawLevel(group, focusNode) {
        const descendants = focusNode.descendants().slice(1); // exclude focusNode itself
        if (descendants.length === 0) return;

        const maxDepth = d3.max(descendants, d => d.depth) ?? 0;

        for (let depth = focusNode.depth + 1; depth <= maxDepth; depth++) {
            const nodesAtDepth = descendants.filter(d => d.depth === depth);

            const layerGroup = group.append('g')
                .attr('filter', depth === focusNode.depth + 1 ? 'url(#tm-shadow)' : null);

            const nodeGroups = layerGroup.selectAll('g.tm-node')
                .data(nodesAtDepth)
                .join('g')
                .attr('class', 'tm-node')
                .attr('transform', d =>
                    `translate(${this._xScale(d.x0)},${this._yScale(d.y0)})`);

            // Rects — type-based CSS class for function/class/method nodes
            nodeGroups.append('rect')
                .attr('class', d => {
                    if (d.children) {
                        if (d.data.type === 'class') return 'tm-rect tm-class';
                        return 'tm-rect tm-dir';
                    } else {
                        if (d.data.type === 'function') return 'tm-rect tm-func';
                        if (d.data.type === 'method')   return 'tm-rect tm-method';
                        return 'tm-rect tm-leaf';
                    }
                })
                .attr('width',  d => Math.max(0, this._xScale(d.x1) - this._xScale(d.x0)))
                .attr('height', d => Math.max(0, this._yScale(d.y1) - this._yScale(d.y0)))
                .attr('fill', d => {
                    // Only true directory nodes get the depth-based blue color.
                    // Files and classes always show their metric color (MI, CC…)
                    // regardless of whether they have children in the D3 hierarchy.
                    if (!d.children || d.data.type === 'file' || d.data.type === 'class') {
                        return this._leafColor(d.data);
                    }
                    return this._dirColor(d.depth);
                })
                .attr('rx', 2);

            // Labels — dynamic font sizes + type-specific icons
            nodeGroups.each((d, i, nodes) => {
                const g     = d3.select(nodes[i]);
                const cellW = this._xScale(d.x1) - this._xScale(d.x0);
                const cellH = this._yScale(d.y1) - this._yScale(d.y0);
                const icon  = NODE_TYPE_ICONS[d.data.type] || '';

                if (d.children) {
                    // Container label (directory / class / file-as-container)
                    if (cellW >= 30 && cellH >= 14) {
                        const fontSize = Math.min(Math.max(cellH * 0.55, 9), 14);
                        g.append('text')
                            .attr('class', 'tm-dir-label')
                            .attr('x', 4).attr('y', fontSize + 2)
                            .style('font-size', `${fontSize}px`)
                            .text(this._truncate(`${icon} ${d.data.name}`, cellW - 8, fontSize));
                    }
                } else {
                    // Leaf label (file / function / method)
                    if (cellW >= 35 && cellH >= 18) {
                        const minDim       = Math.min(cellW, cellH);
                        const nameFontSize = Math.min(Math.max(minDim * 0.22, 8), 13);
                        const slocFontSize = Math.max(nameFontSize - 2, 7);

                        g.append('text')
                            .attr('class', 'tm-leaf-name')
                            .attr('x', 4).attr('y', nameFontSize + 2)
                            .style('font-size', `${nameFontSize}px`)
                            .text(this._truncate(`${icon} ${d.data.name}`, cellW - 8, nameFontSize));

                        if (cellH >= 30) {
                            g.append('text')
                                .attr('class', 'tm-leaf-sloc')
                                .attr('x', 4).attr('y', nameFontSize + slocFontSize + 5)
                                .style('font-size', `${slocFontSize}px`)
                                .text(`${d.data[this.sizeMetric] ?? 0} ${this._metricShortLabel(this.sizeMetric)}`);
                        }
                    }
                }
            });

            // Click: directories zoom in
            nodeGroups
                .filter(d => !!d.children)
                .attr('cursor', 'pointer')
                .on('click', (event, d) => {
                    event.stopPropagation();
                    this._zoomIn(d);
                });

            // Hover: tooltip
            nodeGroups
                .on('mouseenter', (event, d) => this._showTooltip(event, d))
                .on('mouseleave', () => { this._tooltipData = null; });
        }
    }

    // ========================================================================
    // D3 — POSITION NODES (reposition all g.tm-node transforms + rect sizes)
    // ========================================================================

    /**
     * Repositions all g.tm-node elements and their rects according to the
     * CURRENT _xScale/_yScale. Called on a selection (or transition) to
     * produce the spatial zoom animation effect.
     *
     * @param {d3.Selection | d3.Transition} selection — parent group selection
     */
    _positionNodes(selection) {
        selection.selectAll('g.tm-node')
            .attr('transform', d => `translate(${this._xScale(d.x0)},${this._yScale(d.y0)})`);
        selection.selectAll('g.tm-node rect')
            .attr('width',  d => Math.max(0, this._xScale(d.x1) - this._xScale(d.x0)))
            .attr('height', d => Math.max(0, this._yScale(d.y1) - this._yScale(d.y0)));
    }

    // ========================================================================
    // D3 — ZOOM IN (spatial animation + clean redraw after animation)
    // ========================================================================

    _zoomIn(d) {
        if (!this._svgSel || !d.children) return;

        const svg    = this._svgSel;
        const group0 = this._group.attr('pointer-events', 'none');

        // 1. Draw new group at CURRENT (old) scale positions
        //    → nodes appear at their pre-zoom size/position
        const group1 = this._group = svg.append('g');
        this._drawLevel(group1, d);

        // 2. Update scales to zoom into node d
        this._xScale.domain([d.x0, d.x1]);
        this._yScale.domain([d.y0, d.y1]);
        this._zoomNode = d;

        // 3. Transition BOTH groups to new scale positions (spatial zoom)
        //    - Old group: its nodes expand/fly off screen as we zoom in
        //    - New group: its nodes expand from small to fill the viewport
        const t = svg.transition().duration(750);

        group0.transition(t).remove();
        group0.selectAll('g.tm-node').transition(t)
            .attr('transform', d2 => `translate(${this._xScale(d2.x0)},${this._yScale(d2.y0)})`);
        group0.selectAll('g.tm-node rect').transition(t)
            .attr('width',  d2 => Math.max(0, this._xScale(d2.x1) - this._xScale(d2.x0)))
            .attr('height', d2 => Math.max(0, this._yScale(d2.y1) - this._yScale(d2.y0)));

        group1.selectAll('g.tm-node').transition(t)
            .attr('transform', d2 => `translate(${this._xScale(d2.x0)},${this._yScale(d2.y0)})`);
        group1.selectAll('g.tm-node rect').transition(t)
            .attr('width',  d2 => Math.max(0, this._xScale(d2.x1) - this._xScale(d2.x0)))
            .attr('height', d2 => Math.max(0, this._yScale(d2.y1) - this._yScale(d2.y0)));

        this._updateHeader(d);

        // 4. After animation completes, clean redraw so labels reflect actual cell sizes
        setTimeout(() => {
            if (this._svgSel && this._zoomNode === d) {
                this._group.selectAll('*').remove();
                this._drawLevel(this._group, d);
            }
        }, 800); // 750ms animation + 50ms buffer

        // Sync dashboard
        this.dispatchEvent(new CustomEvent('navigate-into', {
            detail: { nodeId: d.data.id },
            bubbles: true, composed: true,
        }));
    }

    // ========================================================================
    // D3 — ZOOM OUT (spatial animation + clean redraw after animation)
    // ========================================================================

    _zoomOut(d) {
        if (!d || !d.parent || !this._svgSel) return;

        const parent = d.parent;
        const svg    = this._svgSel;
        const group0 = this._group.attr('pointer-events', 'none');

        // 1. Draw new group (parent level) at CURRENT (zoomed-in) scale positions
        //    → parent's nodes appear very large (most off-screen at current scale)
        const group1 = this._group = svg.insert('g', '*');
        this._drawLevel(group1, parent);

        // 2. Update scales to zoom out to parent
        this._xScale.domain([parent.x0, parent.x1]);
        this._yScale.domain([parent.y0, parent.y1]);
        this._zoomNode = parent;

        // 3. Transition BOTH groups to new scale positions
        //    - Old group: its nodes shrink back (zoom out effect)
        //    - New group: its nodes collapse from large to normal size
        const t = svg.transition().duration(750);

        group0.transition(t).remove();
        group0.selectAll('g.tm-node').transition(t)
            .attr('transform', d2 => `translate(${this._xScale(d2.x0)},${this._yScale(d2.y0)})`);
        group0.selectAll('g.tm-node rect').transition(t)
            .attr('width',  d2 => Math.max(0, this._xScale(d2.x1) - this._xScale(d2.x0)))
            .attr('height', d2 => Math.max(0, this._yScale(d2.y1) - this._yScale(d2.y0)));

        group1.selectAll('g.tm-node').transition(t)
            .attr('transform', d2 => `translate(${this._xScale(d2.x0)},${this._yScale(d2.y0)})`);
        group1.selectAll('g.tm-node rect').transition(t)
            .attr('width',  d2 => Math.max(0, this._xScale(d2.x1) - this._xScale(d2.x0)))
            .attr('height', d2 => Math.max(0, this._yScale(d2.y1) - this._yScale(d2.y0)));

        this._updateHeader(parent);

        // 4. After animation completes, clean redraw so labels reflect actual cell sizes
        setTimeout(() => {
            if (this._svgSel && this._zoomNode === parent) {
                this._group.selectAll('*').remove();
                this._drawLevel(this._group, parent);
            }
        }, 800);

        // Sync dashboard
        this.dispatchEvent(new CustomEvent('navigate-into', {
            detail: { nodeId: parent.data.id },
            bubbles: true, composed: true,
        }));
    }

    // ========================================================================
    // D3 — NAVIGATE TO (instant — used for breadcrumb clicks & external sync)
    // ========================================================================

    /**
     * Instantly jump to a D3 node without animation.
     * Dispatches navigate-into to keep dashboard in sync.
     * Used when:
     *   - A breadcrumb segment is clicked
     *   - `zoomNodeId` prop changes externally (_applyZoomNodeId)
     *
     * @param {HierarchyNode} d3Node
     * @param {boolean} emit — whether to dispatch navigate-into event
     */
    _navigateTo(d3Node, emit = true) {
        if (!this._svgSel || !d3Node) return;

        this._xScale.domain([d3Node.x0, d3Node.x1]);
        this._yScale.domain([d3Node.y0, d3Node.y1]);
        this._zoomNode = d3Node;

        const svg    = this._svgSel;
        const group0 = this._group;
        group0.remove();

        this._group = svg.append('g');
        this._drawLevel(this._group, d3Node);
        this._updateHeader(d3Node);

        if (emit) {
            this.dispatchEvent(new CustomEvent('navigate-into', {
                detail: { nodeId: d3Node.data.id },
                bubbles: true, composed: true,
            }));
        }
    }

    // ========================================================================
    // HEADER STATE (reactive Lit update)
    // ========================================================================

    /**
     * Builds the ancestor breadcrumb array from root to d3Node.
     * Triggers a Lit re-render of the header bar.
     *
     * @param {HierarchyNode} d3Node — current zoom node
     */
    _updateHeader(d3Node) {
        this._zoomAncestors = d3Node.ancestors().reverse().map(n => ({
            name:   n.data.name,
            id:     n.data.id,
            d3Node: n,
        }));
    }

    // ========================================================================
    // zoomNodeId SYNC
    // ========================================================================

    /**
     * Called when `zoomNodeId` prop changes (dashboard breadcrumb click).
     * Navigates instantly to target node without emitting navigate-into
     * (since the dashboard is the origin of the change — no feedback loop).
     */
    _applyZoomNodeId() {
        if (!this._d3Root) return;

        const targetId = this.zoomNodeId;
        let target;

        if (!targetId || targetId === this._d3Root.data.id) {
            target = this._d3Root;
        } else {
            target = this._d3Root.descendants().find(d => d.data.id === targetId);
        }

        // If not found or already there, skip
        if (!target || target === this._zoomNode) return;

        this._navigateTo(target, false); // don't re-emit: dashboard is the origin
    }

    // ========================================================================
    // TOOLTIP
    // ========================================================================

    _showTooltip(event, d) {
        const data      = d.data;
        const container = this.renderRoot.querySelector('.treemap-container');
        if (!container) return;

        const rect   = container.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;

        const tooltipW = 200, tooltipH = 180;
        let x = mouseX + 14, y = mouseY + 14;
        if (x + tooltipW > rect.width)  x = mouseX - tooltipW - 8;
        if (y + tooltipH > rect.height) y = mouseY - tooltipH - 8;
        if (x < 0) x = 4;
        if (y < 0) y = 4;

        this._tooltipData = {
            x, y,
            name:            data.name,
            path:            data.path,
            type:            data.type,
            loc:             data.loc  || 0,
            sloc:            data.sloc || 0,
            mi:              data.mi   ?? 100,
            avg_complexity:  data.avg_complexity  ?? 0,
            functions_count: data.functions_count || 0,
            classes_count:   data.classes_count   || 0,
            // function/method specific
            complexity:      data.complexity ?? null,
            rank:            data.rank       ?? null,
        };
    }

    // ========================================================================
    // HELPERS
    // ========================================================================

    /**
     * Returns the color for a leaf node's data based on the current colorMetric.
     * @param {Object} data — raw node data (d.data)
     */
    _leafColor(data) {
        const value = data[this.colorMetric] ?? 0;
        return this._colorScale(value);
    }

    /**
     * Legacy alias for backward compatibility (used in _renderSingleNode).
     * @deprecated Use _leafColor instead.
     */
    _miColor(mi) {
        const scale = d3.scaleLinear()
            .domain(METRIC_COLOR_CONFIGS.mi.domain)
            .range(METRIC_COLOR_CONFIGS.mi.range)
            .clamp(true);
        return scale(mi ?? 100);
    }

    _dirColor(depth) {
        return DIR_COLORS[Math.min(depth, DIR_COLORS.length - 1)];
    }

    /**
     * Truncates text to fit within maxWidth pixels at the given fontSize.
     * @param {string} text
     * @param {number} maxWidth — available width in pixels
     * @param {number} fontSize — font size in px (used to estimate char width)
     */
    _truncate(text, maxWidth, fontSize = 10) {
        if (!text) return '';
        const charW    = fontSize * 0.62; // approximate character width ratio
        const maxChars = Math.max(3, Math.floor(maxWidth / charW));
        if (text.length <= maxChars) return text;
        return text.substring(0, maxChars - 1) + '…';
    }

    /**
     * Returns a short display label for a metric key.
     * @param {string} metric
     */
    _metricShortLabel(metric) {
        return METRIC_SHORT_LABELS[metric] || metric;
    }
}

if (!customElements.get('treemap-view')) {
    customElements.define('treemap-view', TreemapView);
}
