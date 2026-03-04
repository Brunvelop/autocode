/**
 * commit-detail.js
 * Panel de detalle de un commit seleccionado.
 * Lazy-loads the commit detail (files changed, stats) via API.
 * Shows a combined table merging file changes with code metrics.
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { AutoFunctionController } from '../auto-element-generator.js';
import { themeTokens } from './styles/theme.js';
import { commitDetailStyles } from './styles/commit-detail.styles.js';

// Status icons for file changes
const STATUS_ICONS = {
    added: '✅',
    modified: '🔄',
    deleted: '❌',
    renamed: '📝',
    copied: '📋',
    type_changed: '🔀',
};

export class CommitDetail extends LitElement {
    static properties = {
        commitHash: { type: String, attribute: 'commit-hash' },
        commitSummary: { type: Object },
        _detail: { state: true },
        _loading: { state: true },
        _error: { state: true },
        _metrics: { state: true },
        _metricsLoading: { state: true },
    };

    static styles = [themeTokens, commitDetailStyles];

    constructor() {
        super();
        this.commitHash = null;
        this.commitSummary = null;
        this._detail = null;
        this._loading = false;
        this._error = null;
        this._metrics = null;
        this._metricsLoading = false;
    }

    willUpdate(changed) {
        if (changed.has('commitHash') && this.commitHash) {
            this._loadDetail();
            this._metrics = null;
            this._loadMetrics();
        }
    }

    render() {
        if (this._loading) {
            return html`
                <div class="loading-detail">
                    <div class="spinner-sm"></div>
                    <span>Cargando detalle...</span>
                </div>
            `;
        }

        if (this._error) {
            return html`
                <div class="detail-container">
                    <div class="error-msg">❌ ${this._error}</div>
                </div>
            `;
        }

        const detail = this._detail;
        if (!detail) return html``;

        return html`
            <div class="detail-container">
                <!-- Header -->
                <div class="detail-header">
                    <h4 class="detail-title">${detail.message_full?.split('\n')[0] || 'Commit'}</h4>
                    <button class="close-btn" @click=${this._handleClose} title="Cerrar">✕</button>
                </div>

                <!-- Meta info -->
                <div class="meta-section">
                    <div class="meta-row">
                        <span class="meta-label">Hash</span>
                        <span class="meta-value hash">${detail.hash}</span>
                    </div>
                    <div class="meta-row">
                        <span class="meta-label">Autor</span>
                        <span class="meta-value author">${detail.author} &lt;${detail.author_email}&gt;</span>
                    </div>
                    <div class="meta-row">
                        <span class="meta-label">Fecha</span>
                        <span class="meta-value">${this._formatFullDate(detail.date)}</span>
                    </div>
                </div>

                <!-- Parents -->
                ${detail.parents && detail.parents.length > 0 ? html`
                    <div class="parents-section">
                        <span class="parent-label">
                            ${detail.parents.length > 1 ? 'Padres:' : 'Padre:'}
                        </span>
                        ${detail.parents.map(p => html`
                            <span class="parent-hash" 
                                @click=${() => this._navigateToCommit(p)}
                                title="Ver commit ${p.substring(0, 7)}"
                            >${p.substring(0, 7)}</span>
                        `)}
                    </div>
                ` : ''}

                <!-- Full message (if multiline) -->
                ${this._isMultilineMessage(detail.message_full) ? html`
                    <div class="message-section">${detail.message_full}</div>
                ` : ''}

                <!-- Combined files + metrics table -->
                ${this._renderCombinedTable()}
            </div>
        `;
    }

    // ========================================================================
    // API
    // ========================================================================

    async _loadDetail() {
        if (!this.commitHash) return;
        this._loading = true;
        this._error = null;
        this._detail = null;

        try {
            const result = await AutoFunctionController.executeFunction(
                'get_commit_detail',
                { commit_hash: this.commitHash }
            );
            this._detail = result;
        } catch (error) {
            this._error = error.message || 'Error cargando detalle del commit';
            console.error('❌ Error loading commit detail:', error);
        } finally {
            this._loading = false;
        }
    }

    async _loadMetrics() {
        if (!this.commitHash) return;
        this._metricsLoading = true;
        try {
            const result = await AutoFunctionController.executeFunction(
                'get_commit_metrics',
                { commit_hash: this.commitHash }
            );
            this._metrics = result;
        } catch (e) {
            console.error('❌ Error loading commit metrics:', e);
            this._metrics = { files: [], summary: {} };
        } finally {
            this._metricsLoading = false;
        }
    }

    // ========================================================================
    // COMBINED TABLE
    // ========================================================================

    /**
     * Merge detail.files (all changed files) with metrics.files (.py metrics)
     * Returns array of { path, status, additions, deletions, metrics: {before, after, delta_*} | null }
     */
    _mergeFilesWithMetrics() {
        const detailFiles = this._detail?.files || [];
        const metricsFiles = this._metrics?.files || [];

        // Build lookup by path from metrics
        const metricsMap = new Map();
        for (const mf of metricsFiles) {
            metricsMap.set(mf.path, mf);
        }

        return detailFiles.map(f => ({
            path: f.path,
            status: f.status,
            additions: f.additions || 0,
            deletions: f.deletions || 0,
            metrics: metricsMap.get(f.path) || null,
        }));
    }

    _renderCombinedTable() {
        const detailFiles = this._detail?.files;
        if (!detailFiles || detailFiles.length === 0) {
            return html``;
        }

        const merged = this._mergeFilesWithMetrics();
        const hasAnyMetrics = merged.some(f => f.metrics != null);

        // Compute totals
        const totals = this._computeTotals(merged);

        return html`
            <div class="table-section">
                <div class="table-section-header">
                    <span>📊 Archivos cambiados</span>
                    ${this._metricsLoading ? html`<div class="spinner-sm"></div>` : ''}
                    ${!this._metricsLoading && hasAnyMetrics ? html`
                        <span class="table-py-count">${merged.filter(f => f.metrics).length} .py con métricas</span>
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
                            ${merged.map(f => this._renderTableRow(f, hasAnyMetrics))}
                        </tbody>
                        <tfoot>
                            ${this._renderTotalsRow(totals, hasAnyMetrics)}
                        </tfoot>
                    </table>
                </div>
            </div>
        `;
    }

    _renderTableRow(f, hasAnyMetrics) {
        const icon = STATUS_ICONS[f.status] || '📄';
        const m = f.metrics;
        const after = m?.after || {};
        const before = m?.before || {};

        return html`
            <tr class="file-row" title="${f.path}">
                <td class="td-status">${icon}</td>
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

    _computeTotals(merged) {
        let totalAdd = 0, totalDel = 0;
        let totalSlocAfter = 0, totalSlocBefore = 0;
        let totalFnAfter = 0, totalFnBefore = 0;
        let totalClsAfter = 0, totalClsBefore = 0;
        let sumMiAfter = 0, sumMiBefore = 0;
        let sumCcAfter = 0, sumCcBefore = 0;
        let maxCcAfter = 0, maxCcBefore = 0;
        let maxNestAfter = 0, maxNestBefore = 0;
        let metricsCount = 0;

        for (const f of merged) {
            totalAdd += f.additions;
            totalDel += f.deletions;

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
            fileCount: merged.length,
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
    // RENDER HELPERS
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
     * This allows long paths to wrap naturally in table cells.
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

    _isMultilineMessage(msg) {
        if (!msg) return false;
        const lines = msg.split('\n').filter(l => l.trim());
        return lines.length > 1;
    }

    _formatFullDate(isoDate) {
        if (!isoDate) return '';
        try {
            return new Date(isoDate).toLocaleString('es-ES', {
                weekday: 'short',
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            });
        } catch {
            return isoDate;
        }
    }

    // ========================================================================
    // EVENTS
    // ========================================================================

    _handleClose() {
        this.dispatchEvent(new CustomEvent('detail-closed', {
            bubbles: true,
            composed: true,
        }));
    }

    _navigateToCommit(hash) {
        this.dispatchEvent(new CustomEvent('navigate-commit', {
            detail: { hash },
            bubbles: true,
            composed: true,
        }));
    }
}

if (!customElements.get('commit-detail')) {
    customElements.define('commit-detail', CommitDetail);
}
