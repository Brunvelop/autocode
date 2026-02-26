/**
 * commit-node.js
 * Componente para renderizar una fila de commit en el grafo git.
 * Incluye el nodo SVG del grafo (punto + líneas) y la info del commit.
 */

import { LitElement, html, svg } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { themeTokens } from './styles/theme.js';
import { commitNodeStyles } from './styles/commit-node.styles.js';

// Paleta de colores para las columnas del grafo (branches)
const LANE_COLORS = [
    '#4f46e5', // indigo
    '#16a34a', // green
    '#ea580c', // orange
    '#dc2626', // red
    '#7c3aed', // violet
    '#0891b2', // cyan
    '#ca8a04', // yellow
    '#be185d', // pink
    '#059669', // emerald
    '#6d28d9', // purple
];

const NODE_RADIUS = 5;
const LANE_WIDTH = 20;
const ROW_HEIGHT = 40;

export class CommitNode extends LitElement {
    static properties = {
        commit: { type: Object },
        selected: { type: Boolean },
        laneIndex: { type: Number },      // Columna donde va el nodo de este commit
        totalLanes: { type: Number },     // Total de columnas activas
        connections: { type: Array },     // [{fromLane, toLane, type}] líneas a dibujar
        currentBranch: { type: String },  // Nombre de la rama actual
    };

    static styles = [themeTokens, commitNodeStyles];

    constructor() {
        super();
        this.commit = null;
        this.selected = false;
        this.laneIndex = 0;
        this.totalLanes = 1;
        this.connections = [];
        this.currentBranch = '';
    }

    render() {
        if (!this.commit) return html``;

        const isSelected = this.selected;

        return html`
            <div 
                class="commit-row ${isSelected ? 'selected' : ''}"
                @click=${this._handleClick}
            >
                <!-- Graph lane with SVG -->
                <div class="graph-lane" style="width: ${this._svgWidth}px;">
                    ${this._renderGraphSvg()}
                </div>

                <!-- Commit info -->
                <div class="commit-info">
                    <div class="commit-top-row">
                        ${this._renderBadges()}
                        <span class="commit-message" title="${this.commit.message}">
                            ${this.commit.message}
                        </span>
                    </div>
                    <div class="commit-meta">
                        <span class="commit-hash">${this.commit.short_hash}</span>
                        <span class="commit-author">${this.commit.author}</span>
                        <span class="commit-date">${this._formatDate(this.commit.date)}</span>
                        ${this.commit.is_merge ? html`
                            <span class="merge-indicator">merge</span>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    // ========================================================================
    // SVG GRAPH RENDERING
    // ========================================================================

    get _svgWidth() {
        return Math.max((this.totalLanes + 1) * LANE_WIDTH, 40);
    }

    _renderGraphSvg() {
        const w = this._svgWidth;
        const h = ROW_HEIGHT;
        const cx = this.laneIndex * LANE_WIDTH + LANE_WIDTH / 2 + LANE_WIDTH / 2;
        const cy = h / 2;
        const color = this._getColor(this.laneIndex);

        return svg`
            <svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
                <!-- Connection lines -->
                ${(this.connections || []).map(conn => this._renderConnection(conn, h))}

                <!-- Commit node circle -->
                ${this.commit.is_merge ? svg`
                    <circle cx="${cx}" cy="${cy}" r="${NODE_RADIUS + 1}" 
                        fill="white" stroke="${color}" stroke-width="2.5"/>
                ` : svg`
                    <circle cx="${cx}" cy="${cy}" r="${NODE_RADIUS}" 
                        fill="${color}" stroke="white" stroke-width="1.5"/>
                `}
            </svg>
        `;
    }

    _renderConnection(conn, height) {
        const fromX = conn.fromLane * LANE_WIDTH + LANE_WIDTH / 2 + LANE_WIDTH / 2;
        const toX = conn.toLane * LANE_WIDTH + LANE_WIDTH / 2 + LANE_WIDTH / 2;
        const color = this._getColor(conn.colorLane !== undefined ? conn.colorLane : conn.fromLane);

        if (conn.type === 'straight') {
            // Vertical line passing through
            return svg`
                <line x1="${fromX}" y1="0" x2="${toX}" y2="${height}"
                    stroke="${color}" stroke-width="1.5" opacity="0.6"/>
            `;
        }

        if (conn.type === 'merge-up') {
            // Curve from side lane up to this commit's lane
            const midY = height * 0.3;
            return svg`
                <path d="M ${fromX} 0 C ${fromX} ${midY}, ${toX} ${midY}, ${toX} ${height / 2}"
                    stroke="${color}" stroke-width="1.5" fill="none" opacity="0.6"/>
            `;
        }

        if (conn.type === 'branch-down') {
            // Curve from this commit's lane down to a side lane
            const midY = height * 0.7;
            return svg`
                <path d="M ${fromX} ${height / 2} C ${fromX} ${midY}, ${toX} ${midY}, ${toX} ${height}"
                    stroke="${color}" stroke-width="1.5" fill="none" opacity="0.6"/>
            `;
        }

        // Default: simple vertical
        return svg`
            <line x1="${fromX}" y1="0" x2="${toX}" y2="${height}"
                stroke="${color}" stroke-width="1.5" opacity="0.4"/>
        `;
    }

    // ========================================================================
    // BADGES
    // ========================================================================

    _renderBadges() {
        const badges = [];

        // Branch badges
        if (this.commit.branches && this.commit.branches.length > 0) {
            for (const branch of this.commit.branches) {
                const isCurrent = branch === this.currentBranch;
                badges.push(html`
                    <span class="branch-badge ${isCurrent ? 'current' : 'other'}">
                        ${isCurrent ? '●' : '○'} ${branch}
                    </span>
                `);
            }
        }

        // Tag badges
        if (this.commit.tags && this.commit.tags.length > 0) {
            for (const tag of this.commit.tags) {
                badges.push(html`
                    <span class="tag-badge">🏷️ ${tag}</span>
                `);
            }
        }

        return badges;
    }

    // ========================================================================
    // HELPERS
    // ========================================================================

    _getColor(laneIndex) {
        return LANE_COLORS[laneIndex % LANE_COLORS.length];
    }

    _formatDate(isoDate) {
        if (!isoDate) return '';
        try {
            const date = new Date(isoDate);
            const now = new Date();
            const diff = now - date;
            const days = Math.floor(diff / 86400000);

            if (days === 0) {
                const hours = Math.floor(diff / 3600000);
                if (hours === 0) {
                    const mins = Math.floor(diff / 60000);
                    return mins <= 1 ? 'ahora' : `hace ${mins}m`;
                }
                return `hace ${hours}h`;
            }
            if (days === 1) return 'ayer';
            if (days < 7) return `hace ${days}d`;
            if (days < 30) return `hace ${Math.floor(days / 7)}sem`;

            return date.toLocaleDateString('es-ES', {
                day: 'numeric',
                month: 'short',
                year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
            });
        } catch {
            return isoDate;
        }
    }

    _handleClick() {
        this.dispatchEvent(new CustomEvent('commit-selected', {
            detail: { commit: this.commit },
            bubbles: true,
            composed: true,
        }));
    }
}

if (!customElements.get('commit-node')) {
    customElements.define('commit-node', CommitNode);
}
