/**
 * architecture-treemap.js
 * Treemap zoomable de arquitectura de código con D3.
 *
 * Visualiza la jerarquía de directorios/archivos como rectángulos proporcionales
 * al SLOC (líneas de código fuente). El color refleja el Maintainability Index (MI):
 *   - Rojo (#dc2626): MI bajo (0-30) — código difícil de mantener
 *   - Amarillo (#eab308): MI medio (30-60) — necesita atención
 *   - Verde (#22c55e): MI bueno (60-80)
 *   - Verde oscuro (#059669): MI excelente (80-100)
 *
 * Muestra un nivel de profundidad a la vez (hijos directos del nodo actual).
 * Click en directorio → dispara `navigate-into` para hacer zoom.
 * Click en archivo → solo muestra tooltip detallado.
 *
 * Usa D3.js vía CDN ESM para layout treemap. Renderiza SVG dentro de Shadow DOM.
 * ResizeObserver para adaptarse al contenedor.
 *
 * Props:
 *   - node: Object — Nodo de árbol anidado con children (del dashboard _getCurrentSubtree)
 *
 * Events emitidos:
 *   - navigate-into: { detail: { nodeId } } — al hacer click en un directorio
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import * as d3 from 'https://cdn.jsdelivr.net/npm/d3@7/+esm';
import { themeTokens } from './styles/theme.js';
import { architectureTreemapStyles } from './styles/architecture-treemap.styles.js';

// MI → color scale (consistent across treemap and graph)
const MI_DOMAIN = [0, 40, 70, 100];
const MI_RANGE = ['#dc2626', '#eab308', '#22c55e', '#059669'];

export class ArchitectureTreemap extends LitElement {
    static properties = {
        /** Nested tree node with children (from dashboard _getCurrentSubtree) */
        node: { type: Object },

        /** Tooltip data: {x, y, nodeData} or null */
        _tooltipData: { state: true },
    };

    static styles = [themeTokens, architectureTreemapStyles];

    constructor() {
        super();
        this.node = null;
        this._tooltipData = null;
        this._resizeObserver = null;
        this._colorScale = d3.scaleLinear()
            .domain(MI_DOMAIN)
            .range(MI_RANGE)
            .clamp(true);
    }

    // ========================================================================
    // LIFECYCLE
    // ========================================================================

    firstUpdated() {
        const container = this.renderRoot.querySelector('.treemap-container');
        if (container) {
            this._resizeObserver = new ResizeObserver(() => {
                this._renderTreemap();
            });
            this._resizeObserver.observe(container);
        }
        this._renderTreemap();
    }

    updated(changed) {
        if (changed.has('node')) {
            this._renderTreemap();
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
    // RENDER (LitElement template)
    // ========================================================================

    render() {
        // Null / undefined node
        if (!this.node) {
            return html`
                <div class="empty-state">
                    <span class="empty-state-icon">🗺️</span>
                    <span class="empty-state-text">Sin datos de arquitectura</span>
                </div>
            `;
        }

        // Node with no children or empty children array
        const children = this.node.children;
        if (!children || children.length === 0) {
            // Single file node or empty dir
            if (this.node.type === 'file') {
                return this._renderSingleNode(this.node);
            }
            return html`
                <div class="empty-state">
                    <span class="empty-state-icon">📂</span>
                    <span class="empty-state-text">Directorio vacío</span>
                </div>
            `;
        }

        // Normal treemap rendering
        return html`
            <div class="treemap-container">
                <svg class="treemap-svg"></svg>
                ${this._renderTooltip()}
            </div>
        `;
    }

    // ========================================================================
    // SINGLE NODE (file without children)
    // ========================================================================

    _renderSingleNode(node) {
        const color = this._miColor(node.mi);
        return html`
            <div class="single-node" style="background: ${color}">
                <span class="single-node-name">${node.type === 'file' ? '📄' : '📂'} ${node.name}</span>
                <span class="single-node-metrics">
                    SLOC: ${node.sloc} · MI: ${node.mi?.toFixed(1)} · CC: ${node.avg_complexity?.toFixed(1)}
                </span>
            </div>
        `;
    }

    // ========================================================================
    // TOOLTIP (rendered via LitElement, positioned absolutely)
    // ========================================================================

    _renderTooltip() {
        if (!this._tooltipData) return html``;

        const d = this._tooltipData;
        const miColor = this._miColor(d.mi);
        const miStatus = d.mi >= 60 ? '✅' : d.mi >= 40 ? '⚠️' : '🔴';
        const ccStatus = d.avg_complexity < 5 ? '✅' : d.avg_complexity < 10 ? '⚠️' : '🔴';

        return html`
            <div class="treemap-tooltip visible"
                style="left: ${d.x}px; top: ${d.y}px;"
            >
                <div class="tooltip-header">
                    ${d.type === 'directory' ? '📂' : '📄'} ${d.name}
                </div>
                <div class="tooltip-path">${d.path}</div>
                <div class="tooltip-grid">
                    <span class="tooltip-label">LOC</span>
                    <span class="tooltip-value">${d.loc}</span>
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
                </div>
            </div>
        `;
    }

    // ========================================================================
    // D3 TREEMAP RENDERING
    // ========================================================================

    _renderTreemap() {
        const svgEl = this.renderRoot.querySelector('.treemap-svg');
        const container = this.renderRoot.querySelector('.treemap-container');
        if (!svgEl || !container || !this.node) return;

        const children = this.node.children;
        if (!children || children.length === 0) return;

        // Get container dimensions
        const width = container.clientWidth;
        const height = container.clientHeight;
        if (width <= 0 || height <= 0) return;

        // Clear previous SVG content
        d3.select(svgEl).selectAll('*').remove();

        const svg = d3.select(svgEl)
            .attr('width', width)
            .attr('height', height)
            .attr('viewBox', `0 0 ${width} ${height}`);

        // Build a shallow hierarchy: current node → direct children
        // We create a virtual root with only direct children for the treemap layout.
        // Each child's "value" is its SLOC (aggregated for directories).
        const treeData = {
            ...this.node,
            children: children.map(c => ({
                ...c,
                // For treemap: leaves need a value. Dirs use aggregated sloc.
                children: null, // flatten — we only show 1 level at a time
            })),
        };

        // D3 hierarchy
        const root = d3.hierarchy(treeData)
            .sum(d => {
                // Leaf in our flattened tree: use sloc (or 1 as minimum to be visible)
                if (!d.children || d.children.length === 0) {
                    return Math.max(d.sloc || 0, 1);
                }
                return 0;
            })
            .sort((a, b) => (b.value || 0) - (a.value || 0));

        // Treemap layout
        d3.treemap()
            .size([width, height])
            .padding(3)
            .round(true)(root);

        // Render cells for direct children (depth=1)
        const leaves = root.children || [];

        const cellGroups = svg.selectAll('.treemap-cell')
            .data(leaves)
            .join('g')
            .attr('class', 'treemap-cell')
            .attr('data-id', d => d.data.id)
            .attr('data-type', d => d.data.type)
            .attr('transform', d => `translate(${d.x0},${d.y0})`);

        // Rectangles
        cellGroups.append('rect')
            .attr('width', d => Math.max(0, d.x1 - d.x0))
            .attr('height', d => Math.max(0, d.y1 - d.y0))
            .attr('fill', d => this._miColor(d.data.mi))
            .attr('opacity', 0.85)
            .attr('rx', 2)
            .attr('ry', 2);

        // Labels (only for cells large enough)
        const MIN_LABEL_WIDTH = 60;
        const MIN_LABEL_HEIGHT = 30;

        cellGroups.each((d, i, nodes) => {
            const g = d3.select(nodes[i]);
            const cellW = d.x1 - d.x0;
            const cellH = d.y1 - d.y0;

            if (cellW >= MIN_LABEL_WIDTH && cellH >= MIN_LABEL_HEIGHT) {
                // Name label
                const labelGroup = g.append('g')
                    .attr('class', 'treemap-label');

                labelGroup.append('text')
                    .attr('class', 'treemap-label-name')
                    .attr('x', 6)
                    .attr('y', 16)
                    .text(this._truncateLabel(d.data.name, cellW - 12));

                // SLOC label
                if (cellH >= 44) {
                    labelGroup.append('text')
                        .attr('class', 'treemap-label-sloc')
                        .attr('x', 6)
                        .attr('y', 30)
                        .text(`${d.data.sloc} SLOC`);
                }

                // Directory indicator
                if (d.data.type === 'directory' && cellH >= 56) {
                    labelGroup.append('text')
                        .attr('class', 'dir-badge')
                        .attr('x', 6)
                        .attr('y', 42)
                        .text(`📂 ${d.data.children_count || '?'} items`);
                }
            }
        });

        // Event handlers on cell groups
        cellGroups
            .on('click', (event, d) => {
                this._handleCellClick(event, d);
            })
            .on('mouseenter', (event, d) => {
                this._handleCellMouseEnter(event, d);
            })
            .on('mouseleave', () => {
                this._handleCellMouseLeave();
            });
    }

    // ========================================================================
    // EVENT HANDLERS
    // ========================================================================

    _handleCellClick(event, d) {
        const nodeData = d.data;

        // Only navigate into directories that have children
        if (nodeData.type === 'directory') {
            this.dispatchEvent(new CustomEvent('navigate-into', {
                detail: { nodeId: nodeData.id },
                bubbles: true,
                composed: true,
            }));
        }
        // Files: do nothing (tooltip is shown on hover)
    }

    _handleCellMouseEnter(event, d) {
        const nodeData = d.data;
        const container = this.renderRoot.querySelector('.treemap-container');
        if (!container) return;

        const rect = container.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;

        // Position tooltip, flip if near edges
        const tooltipW = 200;
        const tooltipH = 160;
        let x = mouseX + 12;
        let y = mouseY + 12;

        if (x + tooltipW > rect.width) x = mouseX - tooltipW - 8;
        if (y + tooltipH > rect.height) y = mouseY - tooltipH - 8;
        if (x < 0) x = 4;
        if (y < 0) y = 4;

        this._tooltipData = {
            x,
            y,
            name: nodeData.name,
            path: nodeData.path,
            type: nodeData.type,
            loc: nodeData.loc || 0,
            sloc: nodeData.sloc || 0,
            mi: nodeData.mi ?? 100,
            avg_complexity: nodeData.avg_complexity ?? 0,
            max_complexity: nodeData.max_complexity ?? 0,
            functions_count: nodeData.functions_count || 0,
            classes_count: nodeData.classes_count || 0,
        };
    }

    _handleCellMouseLeave() {
        this._tooltipData = null;
    }

    // ========================================================================
    // HELPERS
    // ========================================================================

    /**
     * Convert MI value to a color string using the continuous scale.
     * Public method — also used by tests to validate color logic.
     *
     * @param {number} mi - Maintainability Index (0-100)
     * @returns {string} CSS color string (e.g., "rgb(220, 38, 38)")
     */
    _miColor(mi) {
        return this._colorScale(mi ?? 100);
    }

    /**
     * Truncate a label to fit within a given pixel width.
     * Approximate: 7px per character at 11px font size.
     *
     * @param {string} text - Original text
     * @param {number} maxWidth - Available width in pixels
     * @returns {string} Truncated text (with … if needed)
     */
    _truncateLabel(text, maxWidth) {
        const charWidth = 7; // approximate for 11px font
        const maxChars = Math.floor(maxWidth / charWidth);
        if (!text || text.length <= maxChars) return text || '';
        if (maxChars <= 3) return text.substring(0, maxChars);
        return text.substring(0, maxChars - 1) + '…';
    }
}

// Register the custom element
if (!customElements.get('architecture-treemap')) {
    customElements.define('architecture-treemap', ArchitectureTreemap);
}
