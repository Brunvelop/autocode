/**
 * dependency-graph.js
 * Grafo interactivo de dependencias entre archivos/paquetes con D3 force.
 *
 * Visualiza las relaciones de import entre archivos como un grafo
 * de nodos (circles) y enlaces dirigidos (lines con flechas).
 *
 * Nodos:
 *   - Radio ∝ sqrt(SLOC) — archivos más grandes son más prominentes
 *   - Color = MI (misma escala que treemap): rojo(0) → amarillo(40) → verde(70) → verde oscuro(100)
 *
 * Links:
 *   - Flechas dirigidas (source importa de target)
 *   - Grosor ∝ número de imports (1-4px)
 *   - Rojo punteado para dependencias circulares
 *
 * Interacciones:
 *   - Drag: mover nodos
 *   - Zoom/Pan: d3.zoom()
 *   - Hover: tooltip con detalles (nombre, LOC, MI, CC, imports/imported_by)
 *   - Click: highlight solo las dependencias del nodo (entrantes azul, salientes naranja, resto dimmed)
 *   - Toggle granularidad: package ↔ file
 *
 * Props:
 *   - nodes: Array<ArchitectureNode> — nodos tipo file del snapshot
 *   - dependencies: Array<FileDependency> — dependencias resueltas
 *   - circularDependencies: Array<[string, string]> — pares circulares
 *
 * Adaptado de architecture/architecture-graph.js
 * Cambios: ArchitectureGraph → DependencyGraph, 'architecture-graph' → 'dependency-graph'
 * Usa D3.js vía CDN ESM para force simulation. Renderiza SVG dentro de Shadow DOM.
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import * as d3 from 'https://cdn.jsdelivr.net/npm/d3@7/+esm';
import { themeTokens } from './styles/theme.js';
import { dependencyGraphStyles } from './styles/dependency-graph.styles.js';

// MI → color scale (consistent with treemap)
const MI_DOMAIN = [0, 40, 70, 100];
const MI_RANGE = ['#dc2626', '#eab308', '#22c55e', '#059669'];

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

        /** Tooltip data: {x, y, ...nodeData} or null */
        _tooltipData: { state: true },

        /** Currently selected node ID or null */
        _selectedNode: { state: true },
    };

    static styles = [themeTokens, dependencyGraphStyles];

    constructor() {
        super();
        this.nodes = [];
        this.dependencies = [];
        this.circularDependencies = [];
        this._granularity = 'file';
        this._tooltipData = null;
        this._selectedNode = null;
        this._resizeObserver = null;
        this._simulation = null;
        this._colorScale = d3.scaleLinear()
            .domain(MI_DOMAIN)
            .range(MI_RANGE)
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
        if (changed.has('nodes') || changed.has('dependencies') ||
            changed.has('circularDependencies') || changed.has('_granularity')) {
            this._renderGraph();
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
            <div class="graph-container">
                <svg class="graph-svg"></svg>
                <button
                    class="granularity-toggle ${this._granularity === 'package' ? 'active' : ''}"
                    @click=${this._toggleGranularity}
                    title="Alternar entre vista por archivo y por paquete"
                >
                    ${this._granularity === 'file' ? '📄 File' : '📦 Package'}
                </button>
                ${this._renderLegend()}
                ${this._renderTooltip()}
            </div>
        `;
    }

    // ========================================================================
    // LEGEND
    // ========================================================================

    _renderLegend() {
        return html`
            <div class="graph-legend">
                <div class="legend-title">Leyenda</div>
                <div class="legend-row">
                    <span class="legend-color" style="background: #dc2626"></span>
                    <span>MI bajo (0-40)</span>
                </div>
                <div class="legend-row">
                    <span class="legend-color" style="background: #eab308"></span>
                    <span>MI medio (40-70)</span>
                </div>
                <div class="legend-row">
                    <span class="legend-color" style="background: #22c55e"></span>
                    <span>MI bueno (70-100)</span>
                </div>
                <div class="legend-row">
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
    // TOOLTIP
    // ========================================================================

    _renderTooltip() {
        if (!this._tooltipData) return html``;

        const d = this._tooltipData;
        const miColor = this._miColor(d.mi);
        const miStatus = d.mi >= 60 ? '✅' : d.mi >= 40 ? '⚠️' : '🔴';
        const ccStatus = d.avg_complexity < 5 ? '✅' : d.avg_complexity < 10 ? '⚠️' : '🔴';

        return html`
            <div class="graph-tooltip visible"
                style="left: ${d.x}px; top: ${d.y}px;"
            >
                <div class="tooltip-header">
                    📄 ${d.name}
                </div>
                <div class="tooltip-path">${d.path}</div>
                <div class="tooltip-grid">
                    <span class="tooltip-label">SLOC</span>
                    <span class="tooltip-value">${d.sloc}</span>
                    <span class="tooltip-label">MI</span>
                    <span class="tooltip-value">
                        <span class="tooltip-mi-indicator" style="background: ${miColor}"></span>
                        ${d.mi?.toFixed(1)} ${miStatus}
                    </span>
                    <span class="tooltip-label">CC media</span>
                    <span class="tooltip-value">${d.avg_complexity?.toFixed(1)} ${ccStatus}</span>
                    <span class="tooltip-label">Funciones</span>
                    <span class="tooltip-value">${d.functions_count}</span>
                    <span class="tooltip-label">Clases</span>
                    <span class="tooltip-value">${d.classes_count}</span>
                    ${d.importsOut != null ? html`
                        <span class="tooltip-section-label">Dependencias</span>
                        <span class="tooltip-label">Importa de</span>
                        <span class="tooltip-value">${d.importsOut}</span>
                        <span class="tooltip-label">Importado por</span>
                        <span class="tooltip-value">${d.importsIn}</span>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // ========================================================================
    // GRANULARITY TOGGLE
    // ========================================================================

    _toggleGranularity() {
        this._granularity = this._granularity === 'file' ? 'package' : 'file';
        this._selectedNode = null;
        this._tooltipData = null;
    }

    // ========================================================================
    // DATA PREPARATION
    // ========================================================================

    /**
     * Build the graph data (nodes + links) based on current granularity.
     * @returns {{ graphNodes: Array, graphLinks: Array }}
     */
    _buildGraphData() {
        if (this._granularity === 'file') {
            return this._buildFileGraph();
        }
        return this._buildPackageGraph();
    }

    /**
     * File-level graph: each file node is a graph node, each dependency is a link.
     */
    _buildFileGraph() {
        const nodeIds = new Set(this.nodes.map(n => n.id));

        const graphNodes = this.nodes.map(n => ({
            id: n.id,
            name: n.name,
            path: n.path,
            sloc: n.sloc || 0,
            loc: n.loc || 0,
            mi: n.mi ?? 100,
            avg_complexity: n.avg_complexity ?? 0,
            functions_count: n.functions_count || 0,
            classes_count: n.classes_count || 0,
        }));

        const graphLinks = (this.dependencies || [])
            .filter(d => nodeIds.has(d.source) && nodeIds.has(d.target))
            .map(d => ({
                source: d.source,
                target: d.target,
                importCount: d.import_names?.length || 1,
                isCircular: this._isCircular(d.source, d.target),
            }));

        return { graphNodes, graphLinks };
    }

    /**
     * Package-level graph: group files by parent directory, aggregate metrics and deps.
     */
    _buildPackageGraph() {
        // Group nodes by parent_id (directory)
        const packages = new Map();

        for (const node of this.nodes) {
            const pkgId = node.parent_id || '.';
            if (!packages.has(pkgId)) {
                packages.set(pkgId, {
                    id: pkgId,
                    name: pkgId === '.' ? 'root' : pkgId.split('/').pop(),
                    path: pkgId,
                    files: [],
                    sloc: 0,
                    loc: 0,
                    mi_sum: 0,
                    mi_weight: 0,
                    cc_sum: 0,
                    functions_count: 0,
                    classes_count: 0,
                });
            }
            const pkg = packages.get(pkgId);
            pkg.files.push(node.id);
            pkg.sloc += node.sloc || 0;
            pkg.loc += node.loc || 0;
            const weight = node.sloc || 1;
            pkg.mi_sum += (node.mi ?? 100) * weight;
            pkg.mi_weight += weight;
            pkg.cc_sum += (node.avg_complexity ?? 0) * weight;
            pkg.functions_count += node.functions_count || 0;
            pkg.classes_count += node.classes_count || 0;
        }

        const graphNodes = [];
        const fileToPackage = new Map();

        for (const [pkgId, pkg] of packages) {
            for (const fileId of pkg.files) {
                fileToPackage.set(fileId, pkgId);
            }
            graphNodes.push({
                id: pkgId,
                name: pkg.name,
                path: pkg.path,
                sloc: pkg.sloc,
                loc: pkg.loc,
                mi: pkg.mi_weight > 0 ? pkg.mi_sum / pkg.mi_weight : 100,
                avg_complexity: pkg.mi_weight > 0 ? pkg.cc_sum / pkg.mi_weight : 0,
                functions_count: pkg.functions_count,
                classes_count: pkg.classes_count,
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
                    source: srcPkg,
                    target: tgtPkg,
                    importCount: 0,
                    isCircular: false,
                });
            }
            const edge = edgeMap.get(key);
            edge.importCount += dep.import_names?.length || 1;
        }

        // Check circular at package level
        const edgeKeys = new Set(edgeMap.keys());
        for (const [key, edge] of edgeMap) {
            const reverseKey = `${edge.target}→${edge.source}`;
            if (edgeKeys.has(reverseKey)) {
                edge.isCircular = true;
                const reverseEdge = edgeMap.get(reverseKey);
                if (reverseEdge) reverseEdge.isCircular = true;
            }
        }

        const graphLinks = Array.from(edgeMap.values());

        return { graphNodes, graphLinks };
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
        const svgEl = this.renderRoot.querySelector('.graph-svg');
        const container = this.renderRoot.querySelector('.graph-container');
        if (!svgEl || !container) return;
        if (!this.nodes || this.nodes.length === 0) return;

        const width = container.clientWidth;
        const height = container.clientHeight;
        if (width <= 0 || height <= 0) return;

        // Stop previous simulation
        if (this._simulation) {
            this._simulation.stop();
            this._simulation = null;
        }

        // Build graph data
        const { graphNodes, graphLinks } = this._buildGraphData();
        if (graphNodes.length === 0) return;

        // Clear previous SVG content
        const svg = d3.select(svgEl);
        svg.selectAll('*').remove();
        svg.attr('width', width).attr('height', height);

        // Radius scale: sqrt(sloc) mapped to [MIN_RADIUS, MAX_RADIUS]
        const slocExtent = d3.extent(graphNodes, d => d.sloc) || [0, 100];
        const radiusScale = d3.scaleSqrt()
            .domain([0, Math.max(slocExtent[1], 1)])
            .range([MIN_RADIUS, MAX_RADIUS]);

        // Link width scale
        const importExtent = d3.extent(graphLinks, d => d.importCount) || [1, 1];
        const linkWidthScale = d3.scaleLinear()
            .domain([Math.min(importExtent[0], 1), Math.max(importExtent[1], 2)])
            .range([MIN_LINK_WIDTH, MAX_LINK_WIDTH])
            .clamp(true);

        // Arrow marker definitions
        const defs = svg.append('defs');

        // Normal arrow
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

        // Circular arrow (red)
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

        // Create zoom container
        const zoomG = svg.append('g').attr('class', 'zoom-container');

        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.2, 4])
            .on('zoom', (event) => {
                zoomG.attr('transform', event.transform);
            });
        svg.call(zoom);

        // Links
        const linkGroup = zoomG.append('g').attr('class', 'links');
        const linkElements = linkGroup.selectAll('.graph-link')
            .data(graphLinks)
            .join('line')
            .attr('class', d => `graph-link ${d.isCircular ? 'circular' : ''}`)
            .attr('stroke', d => d.isCircular ? '#dc2626' : '#d1d5db')
            .attr('stroke-width', d => linkWidthScale(d.importCount))
            .attr('stroke-dasharray', d => d.isCircular ? '6 3' : null)
            .attr('marker-end', d => d.isCircular ? 'url(#arrow-circular)' : 'url(#arrow)');

        // Nodes
        const nodeGroup = zoomG.append('g').attr('class', 'nodes');
        const nodeElements = nodeGroup.selectAll('.graph-node')
            .data(graphNodes, d => d.id)
            .join('g')
            .attr('class', 'graph-node')
            .attr('data-id', d => d.id);

        // Node circles
        nodeElements.append('circle')
            .attr('r', d => radiusScale(d.sloc))
            .attr('fill', d => this._miColor(d.mi))
            .attr('opacity', 0.85);

        // Node labels
        nodeElements.append('text')
            .attr('class', 'graph-node-label')
            .attr('dy', d => radiusScale(d.sloc) + 12)
            .text(d => d.name);

        // Drag behavior
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

        // Event handlers
        nodeElements
            .on('click', (event, d) => {
                event.stopPropagation();
                this._handleNodeClick(d);
            })
            .on('mouseenter', (event, d) => {
                this._handleNodeMouseEnter(event, d);
            })
            .on('mouseleave', () => {
                this._handleNodeMouseLeave();
            });

        // Click on SVG background to deselect
        svg.on('click', () => {
            this._selectedNode = null;
        });

        // Force simulation
        this._simulation = d3.forceSimulation(graphNodes)
            .force('link', d3.forceLink(graphLinks)
                .id(d => d.id)
                .distance(100))
            .force('charge', d3.forceManyBody()
                .strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collide', d3.forceCollide()
                .radius(d => radiusScale(d.sloc) + 5));

        // Tick handler: update positions
        this._simulation.on('tick', () => {
            linkElements
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            nodeElements
                .attr('transform', d => `translate(${d.x},${d.y})`);
        });

        // Store references for highlight updates
        this._graphRefs = { nodeElements, linkElements, graphNodes, graphLinks };
    }

    // ========================================================================
    // HIGHLIGHT (selected node connections)
    // ========================================================================

    _updateHighlight() {
        if (!this._graphRefs) return;
        const { nodeElements, linkElements } = this._graphRefs;
        const selectedId = this._selectedNode;

        if (!selectedId) {
            // Reset all
            nodeElements.classed('dimmed', false).classed('selected', false);
            linkElements
                .classed('dimmed', false)
                .classed('highlight-out', false)
                .classed('highlight-in', false);
            return;
        }

        // Determine connected nodes
        const outTargets = new Set();
        const inSources = new Set();

        linkElements.each(function (d) {
            const srcId = typeof d.source === 'object' ? d.source.id : d.source;
            const tgtId = typeof d.target === 'object' ? d.target.id : d.target;

            if (srcId === selectedId) outTargets.add(tgtId);
            if (tgtId === selectedId) inSources.add(srcId);
        });

        const connectedIds = new Set([selectedId, ...outTargets, ...inSources]);

        // Highlight nodes
        nodeElements
            .classed('selected', d => d.id === selectedId)
            .classed('dimmed', d => !connectedIds.has(d.id));

        // Highlight links
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
        if (this._selectedNode === d.id) {
            this._selectedNode = null;
        } else {
            this._selectedNode = d.id;
        }
    }

    _handleNodeMouseEnter(event, d) {
        const container = this.renderRoot.querySelector('.graph-container');
        if (!container) return;

        const rect = container.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;

        // Count imports in/out
        const importsOut = (this.dependencies || []).filter(dep => {
            if (this._granularity === 'file') return dep.source === d.id;
            // Package mode: not straightforward, skip
            return false;
        }).length;
        const importsIn = (this.dependencies || []).filter(dep => {
            if (this._granularity === 'file') return dep.target === d.id;
            return false;
        }).length;

        // Position tooltip, flip if near edges
        const tooltipW = 220;
        const tooltipH = 180;
        let x = mouseX + 12;
        let y = mouseY + 12;

        if (x + tooltipW > rect.width) x = mouseX - tooltipW - 8;
        if (y + tooltipH > rect.height) y = mouseY - tooltipH - 8;
        if (x < 0) x = 4;
        if (y < 0) y = 4;

        this._tooltipData = {
            x,
            y,
            name: d.name,
            path: d.path,
            sloc: d.sloc || 0,
            loc: d.loc || 0,
            mi: d.mi ?? 100,
            avg_complexity: d.avg_complexity ?? 0,
            functions_count: d.functions_count || 0,
            classes_count: d.classes_count || 0,
            importsOut,
            importsIn,
        };
    }

    _handleNodeMouseLeave() {
        this._tooltipData = null;
    }

    // ========================================================================
    // HELPERS
    // ========================================================================

    /**
     * Convert MI value to a color string using the continuous scale.
     * @param {number} mi - Maintainability Index (0-100)
     * @returns {string} CSS color string
     */
    _miColor(mi) {
        return this._colorScale(mi ?? 100);
    }
}

// Register the custom element
if (!customElements.get('dependency-graph')) {
    customElements.define('dependency-graph', DependencyGraph);
}
