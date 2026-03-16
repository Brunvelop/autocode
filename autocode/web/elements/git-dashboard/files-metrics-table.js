/**
 * files-metrics-table.js
 * Shared component: renders a combined table of file changes + code metrics.
 * Used by commit-detail and git-status panels.
 *
 * Props:
 *   .files         — Array of merged file objects:
 *                    { path, status, additions, deletions, metrics, staged? }
 *   .metricsLoading — Boolean, shows spinner in header while metrics load
 */

import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { themeTokens } from './styles/theme.js';

// Status icons for file changes
const STATUS_ICONS = {
    added: '✅',
    modified: '🔄',
    deleted: '❌',
    renamed: '📝',
    copied: '📋',
    type_changed: '🔀',
};

export class FilesMetricsTable extends LitElement {
    static properties = {
        files: { type: Array },
        metricsLoading: { type: Boolean },
    };

    static styles = [
        themeTokens,
        css`
            /* ===== COMBINED TABLE SECTION ===== */
            .table-section {
                display: flex;
                flex-direction: column;
                gap: var(--design-spacing-xs, 0.25rem);
            }

            .table-section-header {
                display: flex;
                align-items: center;
                gap: var(--design-spacing-sm, 0.5rem);
                font-size: 12px;
                font-weight: var(--design-font-weight-semibold, 600);
                color: var(--design-text-secondary, #6b7280);
                padding-bottom: 2px;
            }

            .table-py-count {
                font-size: 10px;
                color: var(--design-text-tertiary, #9ca3af);
                font-family: var(--design-font-mono, monospace);
                font-weight: var(--design-font-weight-normal, 400);
                margin-left: auto;
            }

            .table-scroll-wrapper {
                overflow-x: auto;
                border: 1px solid var(--design-border-gray, #e5e7eb);
                border-radius: var(--design-radius-md, 0.5rem);
                background: var(--design-bg-white, #ffffff);
            }

            /* ===== TABLE ===== */
            .combined-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 11px;
                font-family: var(--design-font-mono, monospace);
            }

            .combined-table thead {
                background: var(--design-bg-gray-50, #f9fafb);
                border-bottom: 1px solid var(--design-border-gray, #e5e7eb);
            }

            .combined-table th {
                padding: 4px 6px;
                font-size: 9px;
                font-weight: var(--design-font-weight-semibold, 600);
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: var(--design-text-tertiary, #9ca3af);
                text-align: left;
                white-space: nowrap;
                border-bottom: 1px solid var(--design-border-gray, #e5e7eb);
            }

            .th-status {
                width: 22px;
                text-align: center !important;
            }

            .th-path {
                min-width: 100px;
            }

            .th-loc {
                text-align: right !important;
                width: 60px;
            }

            .th-metric {
                text-align: right !important;
                width: 48px;
            }

            /* ===== TABLE BODY ===== */
            .combined-table tbody tr {
                border-bottom: 1px solid var(--design-border-gray, #e5e7eb);
                transition: background var(--design-transition-fast, 0.1s);
            }

            .combined-table tbody tr:last-child {
                border-bottom: none;
            }

            .combined-table tbody tr:hover {
                background: var(--design-bg-gray-50, #f9fafb);
            }

            .combined-table td {
                padding: 4px 6px;
                vertical-align: top;
            }

            .td-status {
                text-align: center;
                font-size: 11px;
                width: 22px;
                vertical-align: middle;
            }

            .td-path {
                color: var(--design-text-primary, #1f2937);
                word-break: break-word;
                overflow-wrap: break-word;
                max-width: 200px;
                line-height: 1.3;
                font-size: 10.5px;
            }

            .td-loc {
                text-align: right;
                white-space: nowrap;
                vertical-align: middle;
            }

            .td-metric {
                text-align: right;
                white-space: nowrap;
                vertical-align: middle;
            }

            .td-na {
                text-align: center !important;
                color: var(--design-text-tertiary, #9ca3af);
            }

            /* ===== LOC COLORS (less code = good, more code = bad) ===== */
            .loc-good {
                color: #16a34a;
                font-weight: var(--design-font-weight-medium, 500);
                margin-right: 2px;
            }

            .loc-bad {
                color: #dc2626;
                font-weight: var(--design-font-weight-medium, 500);
                margin-right: 2px;
            }

            .loc-zero {
                color: var(--design-text-tertiary, #9ca3af);
            }

            /* ===== METRIC VALUES ===== */
            .metric-val {
                color: var(--design-text-primary, #1f2937);
                font-weight: var(--design-font-weight-semibold, 600);
                font-size: 11px;
            }

            /* MI color indicators */
            .mi-good { color: #16a34a; }
            .mi-warn { color: #ca8a04; }
            .mi-bad  { color: #dc2626; }

            /* ===== DELTAS ===== */
            .delta {
                font-size: 9px;
                font-weight: var(--design-font-weight-semibold, 600);
                font-family: var(--design-font-mono, monospace);
                margin-left: 2px;
            }

            .delta-positive { color: #16a34a; }
            .delta-negative { color: #dc2626; }
            .delta-neutral  { color: var(--design-text-tertiary, #9ca3af); }

            /* ===== TOTALS ROW ===== */
            .combined-table tfoot {
                border-top: 2px solid var(--design-border-gray, #e5e7eb);
            }

            .totals-row {
                background: var(--design-bg-gray-50, #f9fafb);
            }

            .totals-row td {
                padding: 5px 6px;
                font-weight: var(--design-font-weight-semibold, 600);
            }

            .totals-row .td-status {
                font-size: 12px;
                color: var(--design-text-secondary, #6b7280);
            }

            .totals-label {
                font-family: var(--design-font-family, system-ui, sans-serif);
                font-size: 11px;
                color: var(--design-text-secondary, #6b7280);
            }

            .totals-py {
                font-size: 10px;
                color: var(--design-text-tertiary, #9ca3af);
                font-weight: var(--design-font-weight-normal, 400);
            }

            /* ===== SPINNER ===== */
            .spinner-sm {
                width: 16px;
                height: 16px;
                border: 2px solid var(--design-border-gray, #e5e7eb);
                border-top-color: var(--design-primary, #4f46e5);
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }

            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `,
    ];

    constructor() {
        super();
        this.files = [];
        this.metricsLoading = false;
    }

    render() {
        const files = this.files || [];
        if (files.length === 0) {
            return html``;
        }

        const hasAnyMetrics = files.some(f => f.metrics != null);
        const totals = this._computeTotals(files);

        return html`
            <div class="table-section">
                <div class="table-section-header">
                    <span>📊 Archivos cambiados</span>
                    ${this.metricsLoading ? html`<div class="spinner-sm"></div>` : ''}
                    ${!this.metricsLoading && hasAnyMetrics ? html`
                        <span class="table-py-count">${files.filter(f => f.metrics).length} .py con métricas</span>
                    ` : ''}
                </div>
                <div class="table-scroll-wrapper">
                    <table class="combined-table">
                        <thead>
                            <tr>
                                <th class="th-status"></th>
                                <th class="th-path">Archivo</th>
                                <th class="th-loc">LOC</th>
                                ${hasAnyMetrics ? html`
                                    <th class="th-metric">SLOC</th>
                                    <th class="th-metric">CC</th>
                                    <th class="th-metric">MaxCC</th>
                                    <th class="th-metric">MI</th>
                                    <th class="th-metric">Fn</th>
                                    <th class="th-metric">Cls</th>
                                    <th class="th-metric">Nest</th>
                                ` : ''}
                            </tr>
                        </thead>
                        <tbody>
                            ${files.map(f => this._renderTableRow(f, hasAnyMetrics))}
                        </tbody>
                        <tfoot>
                            ${this._renderTotalsRow(totals, hasAnyMetrics)}
                        </tfoot>
                    </table>
                </div>
            </div>
        `;
    }

    // ========================================================================
    // TABLE RENDER HELPERS
    // ========================================================================

    _renderTableRow(f, hasAnyMetrics) {
        const icon = STATUS_ICONS[f.status] || '📄';
        const stagedBadge = f.staged ? html`📦` : '';
        const m = f.metrics;
        const after = m?.after || {};
        const before = m?.before || {};

        return html`
            <tr class="file-row" title="${f.path}">
                <td class="td-status">${stagedBadge}${icon}</td>
                <td class="td-path">${this._breakablePath(f.path)}</td>
                <td class="td-loc">
                    ${f.additions > 0 ? html`<span class="loc-bad">+${f.additions}</span>` : ''}
                    ${f.deletions > 0 ? html`<span class="loc-good">-${f.deletions}</span>` : ''}
                    ${f.additions === 0 && f.deletions === 0 ? html`<span class="loc-zero">—</span>` : ''}
                </td>
                ${hasAnyMetrics ? html`
                    ${m ? html`
                        <!-- SLOC -->
                        <td class="td-metric">
                            <span class="metric-val">${after.sloc ?? '—'}</span>
                            ${this._renderDelta(m.delta_sloc, true)}
                        </td>
                        <!-- CC avg -->
                        <td class="td-metric">
                            <span class="metric-val">${after.avg_complexity?.toFixed(1) ?? '—'}</span>
                            ${this._renderDelta(m.delta_complexity, true, true)}
                        </td>
                        <!-- Max CC -->
                        <td class="td-metric">
                            <span class="metric-val">${after.max_complexity ?? '—'}</span>
                            ${this._renderDelta((after.max_complexity || 0) - (before.max_complexity || 0), true)}
                        </td>
                        <!-- MI -->
                        <td class="td-metric">
                            <span class="metric-val ${this._miClass(after.maintainability_index)}">${after.maintainability_index?.toFixed(0) ?? '—'}</span>
                            ${this._renderDelta(m.delta_mi, false, true, true)}
                        </td>
                        <!-- Functions -->
                        <td class="td-metric">
                            <span class="metric-val">${after.functions_count ?? '—'}</span>
                            ${this._renderDelta((after.functions_count || 0) - (before.functions_count || 0))}
                        </td>
                        <!-- Classes -->
                        <td class="td-metric">
                            <span class="metric-val">${after.classes_count ?? '—'}</span>
                            ${this._renderDelta((after.classes_count || 0) - (before.classes_count || 0))}
                        </td>
                        <!-- Max Nesting -->
                        <td class="td-metric">
                            <span class="metric-val">${after.max_nesting ?? '—'}</span>
                            ${this._renderDelta((after.max_nesting || 0) - (before.max_nesting || 0), true)}
                        </td>
                    ` : html`
                        <td class="td-metric td-na" colspan="7">—</td>
                    `}
                ` : ''}
            </tr>
        `;
    }

    _computeTotals(files) {
        let totalAdd = 0, totalDel = 0;
        let totalSlocAfter = 0, totalSlocBefore = 0;
        let totalFnAfter = 0, totalFnBefore = 0;
        let totalClsAfter = 0, totalClsBefore = 0;
        let sumMiAfter = 0, sumMiBefore = 0;
        let sumCcAfter = 0, sumCcBefore = 0;
        let maxCcAfter = 0, maxCcBefore = 0;
        let maxNestAfter = 0, maxNestBefore = 0;
        let metricsCount = 0;

        for (const f of files) {
            totalAdd += f.additions || 0;
            totalDel += f.deletions || 0;

            if (f.metrics) {
                const a = f.metrics.after || {};
                const b = f.metrics.before || {};
                totalSlocAfter += a.sloc || 0;
                totalSlocBefore += b.sloc || 0;
                totalFnAfter += a.functions_count || 0;
                totalFnBefore += b.functions_count || 0;
                totalClsAfter += a.classes_count || 0;
                totalClsBefore += b.classes_count || 0;
                sumMiAfter += a.maintainability_index || 0;
                sumMiBefore += b.maintainability_index || 0;
                sumCcAfter += a.avg_complexity || 0;
                sumCcBefore += b.avg_complexity || 0;
                maxCcAfter = Math.max(maxCcAfter, a.max_complexity || 0);
                maxCcBefore = Math.max(maxCcBefore, b.max_complexity || 0);
                maxNestAfter = Math.max(maxNestAfter, a.max_nesting || 0);
                maxNestBefore = Math.max(maxNestBefore, b.max_nesting || 0);
                metricsCount++;
            }
        }

        const avgMiAfter = metricsCount ? sumMiAfter / metricsCount : 0;
        const avgMiBefore = metricsCount ? sumMiBefore / metricsCount : 0;
        const avgCcAfter = metricsCount ? sumCcAfter / metricsCount : 0;
        const avgCcBefore = metricsCount ? sumCcBefore / metricsCount : 0;

        return {
            fileCount: files.length,
            pyCount: metricsCount,
            totalAdd,
            totalDel,
            slocAfter: totalSlocAfter,
            deltaSloc: totalSlocAfter - totalSlocBefore,
            avgCc: avgCcAfter,
            deltaCc: avgCcAfter - avgCcBefore,
            maxCcAfter,
            deltaMaxCc: maxCcAfter - maxCcBefore,
            avgMi: avgMiAfter,
            deltaMi: avgMiAfter - avgMiBefore,
            fnAfter: totalFnAfter,
            deltaFn: totalFnAfter - totalFnBefore,
            clsAfter: totalClsAfter,
            deltaCls: totalClsAfter - totalClsBefore,
            maxNestAfter,
            deltaMaxNest: maxNestAfter - maxNestBefore,
            hasMetrics: metricsCount > 0,
        };
    }

    _renderTotalsRow(t, hasAnyMetrics) {
        return html`
            <tr class="totals-row">
                <td class="td-status">Σ</td>
                <td class="td-path totals-label">
                    ${t.fileCount} archivo${t.fileCount !== 1 ? 's' : ''}
                    ${t.pyCount > 0 ? html` <span class="totals-py">(${t.pyCount} .py)</span>` : ''}
                </td>
                <td class="td-loc">
                    ${t.totalAdd > 0 ? html`<span class="loc-bad">+${t.totalAdd}</span>` : ''}
                    ${t.totalDel > 0 ? html`<span class="loc-good">-${t.totalDel}</span>` : ''}
                </td>
                ${hasAnyMetrics ? html`
                    ${t.hasMetrics ? html`
                        <td class="td-metric">
                            <span class="metric-val">${t.slocAfter}</span>
                            ${this._renderDelta(t.deltaSloc, true)}
                        </td>
                        <td class="td-metric">
                            <span class="metric-val">${t.avgCc.toFixed(1)}</span>
                            ${this._renderDelta(t.deltaCc, true, true)}
                        </td>
                        <td class="td-metric">
                            <span class="metric-val">${t.maxCcAfter}</span>
                            ${this._renderDelta(t.deltaMaxCc, true)}
                        </td>
                        <td class="td-metric">
                            <span class="metric-val ${this._miClass(t.avgMi)}">${t.avgMi.toFixed(0)}</span>
                            ${this._renderDelta(t.deltaMi, false, true, true)}
                        </td>
                        <td class="td-metric">
                            <span class="metric-val">${t.fnAfter}</span>
                            ${this._renderDelta(t.deltaFn)}
                        </td>
                        <td class="td-metric">
                            <span class="metric-val">${t.clsAfter}</span>
                            ${this._renderDelta(t.deltaCls)}
                        </td>
                        <td class="td-metric">
                            <span class="metric-val">${t.maxNestAfter}</span>
                            ${this._renderDelta(t.deltaMaxNest, true)}
                        </td>
                    ` : html`
                        <td class="td-metric td-na" colspan="7">—</td>
                    `}
                ` : ''}
            </tr>
        `;
    }

    // ========================================================================
    // VALUE HELPERS
    // ========================================================================

    _renderDelta(delta, lowerBetter = false, isFloat = false, higherBetter = false) {
        if (delta == null || delta === 0) return html`<span class="delta delta-neutral">—</span>`;
        let cls = 'delta-neutral';
        if (lowerBetter) cls = delta < 0 ? 'delta-positive' : 'delta-negative';
        else if (higherBetter) cls = delta > 0 ? 'delta-positive' : 'delta-negative';
        const sign = delta > 0 ? '+' : '';
        const val = isFloat ? delta.toFixed(1) : delta;
        return html`<span class="delta ${cls}">${sign}${val}</span>`;
    }

    /** Returns MI color class based on value */
    _miClass(mi) {
        if (mi == null) return '';
        if (mi >= 60) return 'mi-good';
        if (mi >= 40) return 'mi-warn';
        return 'mi-bad';
    }

    /**
     * Makes a file path breakable by inserting <wbr> after each '/'.
     * Allows long paths to wrap naturally in table cells.
     */
    _breakablePath(p) {
        if (!p) return '';
        const parts = p.split('/');
        const result = [];
        for (let i = 0; i < parts.length; i++) {
            result.push(html`${i > 0 ? html`/<wbr>` : ''}${parts[i]}`);
        }
        return result;
    }
}

if (!customElements.get('files-metrics-table')) {
    customElements.define('files-metrics-table', FilesMetricsTable);
}
