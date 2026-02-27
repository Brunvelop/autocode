/**
 * metrics-chart.js
 * Gráfica temporal de métricas de código a lo largo de commits.
 *
 * Usa D3.js (vía CDN ESM) para escalas, ejes y generación de paths SVG.
 * Renderiza dentro de Shadow DOM (LitElement) — D3 opera sobre el SVG
 * del shadow root, no sobre document.
 *
 * Features:
 * - Multi-line chart con métricas toggleables
 * - Auto-scaling Y axis según métricas visibles
 * - Hover tooltip con valores del punto más cercano
 * - Agrupación de métricas por categoría (volume, quality, distribution, coupling)
 * - Colores consistentes por métrica
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import * as d3 from 'https://cdn.jsdelivr.net/npm/d3@7/+esm';
import { AutoFunctionController } from '../auto-element-generator.js';
import { themeTokens } from './styles/theme.js';
import { metricsChartStyles } from './styles/metrics-chart.styles.js';

// Color palette for metric series
const METRIC_COLORS = {
    total_sloc: '#4f46e5',       // indigo
    total_files: '#0891b2',      // cyan
    total_functions: '#16a34a',  // green
    total_classes: '#7c3aed',    // violet
    total_comments: '#ca8a04',   // yellow
    total_blanks: '#9ca3af',     // gray
    avg_complexity: '#dc2626',   // red
    avg_mi: '#059669',           // emerald
    rank_a: '#22c55e',           // green
    rank_b: '#84cc16',           // lime
    rank_c: '#eab308',           // yellow
    rank_d: '#f97316',           // orange
    rank_e: '#ef4444',           // red
    rank_f: '#991b1b',           // dark red
    circular_deps_count: '#be185d', // pink
};

// Default active metrics on first load
const DEFAULT_ACTIVE = new Set(['total_sloc', 'avg_complexity', 'avg_mi']);

// Chart dimensions
const MARGIN = { top: 12, right: 16, bottom: 32, left: 48 };
const CHART_HEIGHT = 240;

export class MetricsChart extends LitElement {
    static properties = {
        _history: { state: true },       // MetricsHistory from API
        _loading: { state: true },
        _error: { state: true },
        _activeMetrics: { state: true }, // Set<string> of active metric keys
        _tooltipData: { state: true },   // {x, y, point, metrics} or null
    };

    static styles = [themeTokens, metricsChartStyles];

    constructor() {
        super();
        this._history = null;
        this._loading = false;
        this._error = null;
        this._activeMetrics = new Set(DEFAULT_ACTIVE);
        this._tooltipData = null;
        this._resizeObserver = null;
    }

    connectedCallback() {
        super.connectedCallback();
        this.refresh();
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        if (this._resizeObserver) {
            this._resizeObserver.disconnect();
        }
    }

    async refresh() {
        this._loading = true;
        this._error = null;
        try {
            const result = await AutoFunctionController.executeFunction(
                'get_metrics_history', {}
            );
            this._history = result;
        } catch (e) {
            this._error = e.message || 'Error cargando historial';
        } finally {
            this._loading = false;
        }
    }

    updated(changed) {
        if (changed.has('_history') || changed.has('_activeMetrics')) {
            this._renderChart();
        }
    }

    firstUpdated() {
        // Observe resize to redraw chart
        const chartArea = this.renderRoot.querySelector('.chart-area');
        if (chartArea) {
            this._resizeObserver = new ResizeObserver(() => this._renderChart());
            this._resizeObserver.observe(chartArea);
        }
    }

    render() {
        if (this._loading) {
            return html`
                <div class="chart-container">
                    <div class="loading-state">
                        <div class="spinner-sm"></div>
                        <span>Cargando historial...</span>
                    </div>
                </div>
            `;
        }

        if (this._error) {
            return html`
                <div class="chart-container">
                    <div class="empty-state">
                        <span class="empty-state-icon">❌</span>
                        <span class="empty-state-text">${this._error}</span>
                    </div>
                </div>
            `;
        }

        const points = this._history?.points || [];
        if (points.length < 2) {
            return html`
                <div class="chart-container">
                    <div class="empty-state">
                        <span class="empty-state-icon">📊</span>
                        <span class="empty-state-text">
                            Se necesitan al menos 2 snapshots para graficar.<br>
                            Genera métricas en diferentes commits con 📊 en el dashboard.
                        </span>
                    </div>
                </div>
            `;
        }

        const metrics = this._history?.available_metrics || [];
        const grouped = this._groupMetrics(metrics);

        return html`
            <div class="chart-container">
                <div class="chart-header">
                    <span class="chart-title">📈 Evolución de Métricas</span>
                    <span class="chart-info">${points.length} commits</span>
                </div>

                <!-- Metric toggles grouped by category -->
                <div class="toggles-container">
                    <div class="toggle-groups">
                        ${Object.entries(grouped).map(([group, items]) => html`
                            <div class="toggle-group">
                                <span class="toggle-group-label">${this._groupLabel(group)}</span>
                                ${items.map(m => html`
                                    <button
                                        class="metric-toggle ${this._activeMetrics.has(m.key) ? 'active' : ''}"
                                        style="${this._activeMetrics.has(m.key)
                                            ? `background: ${METRIC_COLORS[m.key]}; border-color: ${METRIC_COLORS[m.key]};`
                                            : ''}"
                                        title="${m.description}"
                                        @click=${() => this._toggleMetric(m.key)}
                                    >
                                        <span class="color-dot"
                                            style="background: ${METRIC_COLORS[m.key]}"
                                        ></span>
                                        ${m.label}
                                    </button>
                                `)}
                            </div>
                        `)}
                    </div>
                </div>

                <!-- Chart SVG area -->
                <div class="chart-area"
                    @mousemove=${this._handleMouseMove}
                    @mouseleave=${this._handleMouseLeave}
                >
                    <svg class="chart-svg"></svg>

                    <!-- Tooltip -->
                    ${this._tooltipData ? html`
                        <div class="chart-tooltip visible"
                            style="left: ${this._tooltipData.x}px; top: ${this._tooltipData.y}px;"
                        >
                            <div class="tooltip-header">${this._tooltipData.commit}</div>
                            ${this._tooltipData.rows.map(r => html`
                                <div class="tooltip-row">
                                    <span class="tooltip-color" style="background: ${r.color}"></span>
                                    <span class="tooltip-label">${r.label}</span>
                                    <span class="tooltip-value">${r.value}</span>
                                </div>
                            `)}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // ========================================================================
    // D3 CHART RENDERING
    // ========================================================================

    _renderChart() {
        const svgEl = this.renderRoot.querySelector('.chart-svg');
        const chartArea = this.renderRoot.querySelector('.chart-area');
        if (!svgEl || !chartArea) return;

        const points = this._history?.points || [];
        if (points.length < 2) return;

        const activeKeys = [...this._activeMetrics];
        if (activeKeys.length === 0) return;

        // Dimensions
        const width = chartArea.clientWidth - 16; // padding
        const height = CHART_HEIGHT;
        const innerW = width - MARGIN.left - MARGIN.right;
        const innerH = height - MARGIN.top - MARGIN.bottom;

        if (innerW <= 0 || innerH <= 0) return;

        // Clear previous
        d3.select(svgEl).selectAll('*').remove();

        const svg = d3.select(svgEl)
            .attr('width', width)
            .attr('height', height)
            .attr('viewBox', `0 0 ${width} ${height}`);

        const g = svg.append('g')
            .attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

        // Scales
        const xScale = d3.scalePoint()
            .domain(points.map(p => p.commit_short))
            .range([0, innerW])
            .padding(0.1);

        // Compute Y domain across all active metrics
        let yMin = Infinity, yMax = -Infinity;
        for (const key of activeKeys) {
            for (const p of points) {
                const v = p[key] ?? 0;
                if (v < yMin) yMin = v;
                if (v > yMax) yMax = v;
            }
        }
        // Add 10% padding
        const yPad = (yMax - yMin) * 0.1 || 1;
        yMin = Math.max(0, yMin - yPad);
        yMax = yMax + yPad;

        const yScale = d3.scaleLinear()
            .domain([yMin, yMax])
            .range([innerH, 0])
            .nice();

        // Grid lines
        g.append('g')
            .attr('class', 'grid')
            .call(d3.axisLeft(yScale)
                .ticks(5)
                .tickSize(-innerW)
                .tickFormat('')
            );

        // X axis
        const xAxis = g.append('g')
            .attr('class', 'axis axis-x')
            .attr('transform', `translate(0,${innerH})`)
            .call(d3.axisBottom(xScale));

        // Rotate labels if too many points
        if (points.length > 15) {
            xAxis.selectAll('text')
                .attr('transform', 'rotate(-45)')
                .style('text-anchor', 'end')
                .attr('dx', '-0.5em')
                .attr('dy', '0.15em');
        }

        // Y axis
        g.append('g')
            .attr('class', 'axis axis-y')
            .call(d3.axisLeft(yScale).ticks(5));

        // Line generator
        const lineGen = d3.line()
            .x((d) => xScale(d.commit_short))
            .y((d, i, data) => yScale(d._value))
            .curve(d3.curveMonotoneX);

        // Area generator (for subtle fill under line)
        const areaGen = d3.area()
            .x((d) => xScale(d.commit_short))
            .y0(innerH)
            .y1((d) => yScale(d._value))
            .curve(d3.curveMonotoneX);

        // Draw each active metric
        for (const key of activeKeys) {
            const color = METRIC_COLORS[key] || '#6b7280';
            const data = points.map(p => ({ ...p, _value: p[key] ?? 0 }));

            // Area fill
            g.append('path')
                .datum(data)
                .attr('class', 'metric-area')
                .attr('fill', color)
                .attr('d', areaGen);

            // Line
            g.append('path')
                .datum(data)
                .attr('class', 'metric-line')
                .attr('stroke', color)
                .attr('d', lineGen);

            // Dots
            g.selectAll(`.dot-${key}`)
                .data(data)
                .join('circle')
                .attr('class', `metric-dot dot-${key}`)
                .attr('cx', d => xScale(d.commit_short))
                .attr('cy', d => yScale(d._value))
                .attr('r', points.length > 30 ? 2 : 3)
                .attr('fill', color);
        }

        // Hover line (invisible, shown on mousemove)
        g.append('line')
            .attr('class', 'hover-line')
            .attr('y1', 0)
            .attr('y2', innerH);

        // Store scales for mouse interaction
        this._chartScales = { xScale, yScale, points, innerW, innerH, activeKeys };
    }

    // ========================================================================
    // MOUSE INTERACTION
    // ========================================================================

    _handleMouseMove(e) {
        if (!this._chartScales) return;

        const chartArea = this.renderRoot.querySelector('.chart-area');
        const svgEl = this.renderRoot.querySelector('.chart-svg');
        if (!chartArea || !svgEl) return;

        const rect = svgEl.getBoundingClientRect();
        const mouseX = e.clientX - rect.left - MARGIN.left;

        const { xScale, points, activeKeys } = this._chartScales;

        // Find nearest point
        const domain = xScale.domain();
        const step = xScale.step();
        let nearestIdx = 0;
        let minDist = Infinity;

        for (let i = 0; i < domain.length; i++) {
            const px = xScale(domain[i]);
            const dist = Math.abs(mouseX - px);
            if (dist < minDist) {
                minDist = dist;
                nearestIdx = i;
            }
        }

        if (minDist > step * 0.7) {
            this._tooltipData = null;
            this._updateHoverLine(null);
            return;
        }

        const point = points[nearestIdx];
        const px = xScale(point.commit_short) + MARGIN.left;

        // Build tooltip rows
        const rows = activeKeys.map(key => {
            const meta = this._history?.available_metrics?.find(m => m.key === key);
            const val = point[key] ?? 0;
            return {
                color: METRIC_COLORS[key] || '#6b7280',
                label: meta?.label || key,
                value: typeof val === 'number' && !Number.isInteger(val)
                    ? val.toFixed(2) : val,
            };
        });

        // Position tooltip
        const chartRect = chartArea.getBoundingClientRect();
        const tooltipX = px + 12;
        const tooltipY = 8;

        // Flip if near right edge
        const flipX = (tooltipX + 150) > chartArea.clientWidth;

        this._tooltipData = {
            x: flipX ? px - 160 : tooltipX,
            y: tooltipY,
            commit: `${point.commit_short} · ${point.branch}`,
            rows,
        };

        this._updateHoverLine(xScale(point.commit_short));
    }

    _handleMouseLeave() {
        this._tooltipData = null;
        this._updateHoverLine(null);
    }

    _updateHoverLine(x) {
        const line = this.renderRoot.querySelector('.hover-line');
        if (!line) return;
        if (x === null) {
            line.style.opacity = '0';
        } else {
            line.setAttribute('x1', x);
            line.setAttribute('x2', x);
            line.style.opacity = '1';
        }
    }

    // ========================================================================
    // TOGGLE LOGIC
    // ========================================================================

    _toggleMetric(key) {
        const next = new Set(this._activeMetrics);
        if (next.has(key)) {
            next.delete(key);
        } else {
            next.add(key);
        }
        this._activeMetrics = next;
    }

    // ========================================================================
    // HELPERS
    // ========================================================================

    _groupMetrics(metrics) {
        const groups = {};
        for (const m of metrics) {
            const g = m.group || 'other';
            if (!groups[g]) groups[g] = [];
            groups[g].push(m);
        }
        return groups;
    }

    _groupLabel(group) {
        const labels = {
            volume: '📦 Volumen',
            quality: '🎯 Calidad',
            distribution: '🧩 Distrib.',
            coupling: '🏗️ Acoplam.',
        };
        return labels[group] || group;
    }
}

if (!customElements.get('metrics-chart')) {
    customElements.define('metrics-chart', MetricsChart);
}
