/**
 * code-node.js
 * Componente para renderizar un nodo individual del árbol de código.
 * Soporta expansión/colapso y muestra iconos según el tipo.
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { themeTokens } from './styles/theme.js';
import { codeNodeStyles } from './styles/code-node.styles.js';

// Mapeo de iconos por tipo y lenguaje
const ICONS = {
    directory: '📁',
    file: {
        python: '🐍',
        javascript: '🟨',
        default: '📄'
    },
    class: '🔷',
    function: '⚡',
    method: '🔹',
    import: '📥',
    variable: '📦'
};

export class CodeNode extends LitElement {
    static properties = {
        node: { type: Object },
        expanded: { type: Boolean },
        selected: { type: Boolean },
        expandedNodes: { type: Object }  // Set de IDs expandidos (pasado desde padre)
    };

    static styles = [themeTokens, codeNodeStyles];

    constructor() {
        super();
        this.node = null;
        this.expanded = false;
        this.selected = false;
        this.expandedNodes = new Set();
    }

    render() {
        if (!this.node) return html``;

        const hasChildren = this.node.children && this.node.children.length > 0;
        const isExpandable = hasChildren || this.node.type === 'directory';
        const isExpanded = this.expandedNodes.has(this.node.id);

        return html`
            <div class="node">
                <div 
                    class="node-row ${this.selected ? 'selected' : ''}"
                    @click=${this._handleClick}
                >
                    <!-- Expand/Collapse button -->
                    ${isExpandable ? html`
                        <button 
                            class="expand-btn ${isExpanded ? 'expanded' : ''}"
                            @click=${this._handleToggle}
                        >▶</button>
                    ` : html`<span class="expand-placeholder"></span>`}

                    <!-- Icon -->
                    <span class="node-icon ${this._getIconClass()}">${this._getIcon()}</span>

                    <!-- Decorators (si hay) -->
                    ${this._renderDecorators()}

                    <!-- Name -->
                    <span class="node-name" title="${this.node.path}">${this.node.name}</span>

                    <!-- Params for functions -->
                    ${this._renderParams()}

                    <!-- Async badge -->
                    ${this.node.is_async ? html`<span class="async-badge">async</span>` : ''}

                    <!-- LOC badge -->
                    ${this._renderLocBadge()}
                </div>

                <!-- Children -->
                ${isExpanded && hasChildren ? html`
                    <div class="node-children">
                        ${this.node.children.map(child => html`
                            <code-node
                                .node=${child}
                                .expandedNodes=${this.expandedNodes}
                                .selected=${false}
                            ></code-node>
                        `)}
                    </div>
                ` : ''}
            </div>
        `;
    }

    _getIcon() {
        const type = this.node.type;
        
        if (type === 'file') {
            const lang = this.node.language;
            return ICONS.file[lang] || ICONS.file.default;
        }
        
        return ICONS[type] || '📄';
    }

    _getIconClass() {
        const type = this.node.type;
        
        if (type === 'file') {
            const lang = this.node.language;
            return `icon-file-${lang || 'default'}`;
        }
        
        return `icon-${type}`;
    }

    _renderDecorators() {
        if (!this.node.decorators || this.node.decorators.length === 0) {
            return '';
        }

        // Mostrar solo los primeros 2 decoradores
        const decorators = this.node.decorators.slice(0, 2);
        const hasMore = this.node.decorators.length > 2;

        return html`
            <span class="node-decorators">
                ${decorators.map(d => html`<span class="decorator-badge">@${d}</span>`)}
                ${hasMore ? html`<span class="decorator-badge">+${this.node.decorators.length - 2}</span>` : ''}
            </span>
        `;
    }

    _renderParams() {
        if (!this.node.params || this.node.type === 'class') {
            return '';
        }

        // Mostrar params simplificados
        const params = this.node.params.slice(0, 3).join(', ');
        const hasMore = this.node.params.length > 3;

        return html`
            <span class="node-params">(${params}${hasMore ? ', ...' : ''})</span>
        `;
    }

    _renderLocBadge() {
        if (!this.node.loc || this.node.type === 'import') {
            return '';
        }

        const loc = this.node.loc;
        let sizeClass = '';
        
        if (loc > 500) {
            sizeClass = 'large';
        } else if (loc > 100) {
            sizeClass = 'medium';
        }

        return html`<span class="loc-badge ${sizeClass}">${loc}</span>`;
    }

    _handleClick(e) {
        // No propagar si el click fue en el botón de expandir
        if (e.target.classList.contains('expand-btn')) {
            return;
        }

        this.dispatchEvent(new CustomEvent('node-selected', {
            detail: { node: this.node },
            bubbles: true,
            composed: true
        }));
    }

    _handleToggle(e) {
        e.stopPropagation();
        
        const isExpanded = this.expandedNodes.has(this.node.id);
        
        this.dispatchEvent(new CustomEvent(isExpanded ? 'node-collapsed' : 'node-expanded', {
            detail: { node: this.node },
            bubbles: true,
            composed: true
        }));
    }
}

if (!customElements.get('code-node')) {
    customElements.define('code-node', CodeNode);
}
