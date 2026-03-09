/**
 * index.js
 * CodeExplorer - Componente principal para exploración visual de código.
 * 
 * Usa AutoFunctionController.executeFunction() para llamar al backend,
 * pero extiende LitElement directamente (standalone con backend).
 * 
 * El backend devuelve una estructura plana (graph.nodes con parent_id)
 * para evitar recursión en OpenAPI schema. Este componente reconstruye
 * el árbol en el cliente.
 */

import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';
import { AutoFunctionController } from '../auto-element-generator.js';
import { themeTokens } from './styles/theme.js';
import { codeExplorerStyles } from './styles/code-explorer.styles.js';

// Importar sub-componentes
import './code-node.js';
import './code-metrics.js';

export class CodeExplorer extends LitElement {
    static properties = {
        // Configuración
        path: { type: String },
        depth: { type: Number },
        includeImports: { type: Boolean, attribute: 'include-imports' },
        
        // Estado interno
        _structure: { state: true },      // Datos del backend (graph + métricas)
        _rootNode: { state: true },       // Árbol reconstruido
        _expandedNodes: { state: true },
        _selectedNode: { state: true },
        _loading: { state: true },
        _error: { state: true },
    };

    static styles = [themeTokens, codeExplorerStyles];

    constructor() {
        super();
        
        // Configuración por defecto
        this.path = '.';
        this.depth = -1;  // Ilimitado
        this.includeImports = true;
        
        // Estado interno
        this._structure = null;
        this._rootNode = null;
        this._expandedNodes = new Set();
        this._selectedNode = null;
        this._loading = false;
        this._error = null;
    }

    connectedCallback() {
        super.connectedCallback();
        
        // Cargar estructura inicial
        this.refresh();
        
        // Setup event listeners para sub-componentes
        this.addEventListener('node-selected', this._handleNodeSelected.bind(this));
        this.addEventListener('node-expanded', this._handleNodeExpanded.bind(this));
        this.addEventListener('node-collapsed', this._handleNodeCollapsed.bind(this));
    }

    render() {
        return html`
            <div class="explorer-container">
                <!-- Header -->
                <div class="explorer-header">
                    <h3 class="explorer-title">
                        <span class="explorer-title-icon">🗂️</span>
                        Code Explorer
                    </h3>
                    <div class="explorer-actions">
                        <button class="action-btn" @click=${this.expandAll} title="Expandir todo">
                            ➕
                        </button>
                        <button class="action-btn" @click=${this.collapseAll} title="Colapsar todo">
                            ➖
                        </button>
                        <button 
                            class="action-btn"
                            @click=${this.refresh}
                            ?disabled=${this._loading}
                            title=${this._loading ? 'Cargando...' : 'Recargar'}
                        >
                            ${this._loading ? html`<span class="btn-spinner"></span>` : '🔄'}
                        </button>
                    </div>
                </div>

                <!-- Metrics -->
                ${this._structure ? html`
                    <code-metrics .metrics=${this._structure}></code-metrics>
                ` : ''}

                <!-- Content -->
                <div class="explorer-content">
                    ${this._renderCodeContent()}
                </div>
            </div>
        `;
    }

    _renderCodeContent() {
        // Loading state
        if (this._loading) {
            return html`
                <div class="loading-container">
                    <div class="spinner"></div>
                    <span>Analizando código...</span>
                </div>
            `;
        }

        // Error state
        if (this._error) {
            return html`
                <div class="error-container">
                    <span class="error-icon">❌</span>
                    <span class="error-message">${this._error}</span>
                    <button class="retry-btn" @click=${this.refresh}>Reintentar</button>
                </div>
            `;
        }

        // Empty state
        if (!this._rootNode) {
            return html`
                <div class="empty-container">
                    <span class="empty-icon">📭</span>
                    <span>No hay código para mostrar</span>
                </div>
            `;
        }

        // Tree
        return html`
            <code-node
                .node=${this._rootNode}
                .expandedNodes=${this._expandedNodes}
                .selected=${this._selectedNode === this._rootNode?.id}
            ></code-node>
        `;
    }

    // ========================================================================
    // PUBLIC API
    // ========================================================================

    /**
     * Recarga la estructura del código desde el backend.
     */
    async refresh() {
        this._loading = true;
        this._error = null;

        try {
            const result = await AutoFunctionController.executeFunction(
                'get_code_structure',
                {
                    path: this.path,
                    depth: this.depth,
                    include_imports: this.includeImports
                }
            );

            this._structure = result;
            
            // Reconstruir árbol desde lista plana
            if (result?.graph?.nodes && result?.graph?.root_id) {
                this._rootNode = this._buildTreeFromGraph(
                    result.graph.nodes, 
                    result.graph.root_id
                );
                
                // Expandir el nodo raíz por defecto
                this._expandedNodes = new Set([result.graph.root_id]);
            } else {
                this._rootNode = null;
            }

            this.dispatchEvent(new CustomEvent('structure-loaded', {
                detail: { structure: result },
                bubbles: true,
                composed: true
            }));

        } catch (error) {
            this._error = error.message || 'Error cargando estructura';
            console.error('❌ Error loading code structure:', error);
        } finally {
            this._loading = false;
        }
    }

    /**
     * Expande un nodo específico.
     * @param {string} nodeId - ID del nodo a expandir
     */
    expandNode(nodeId) {
        this._expandedNodes = new Set([...this._expandedNodes, nodeId]);
    }

    /**
     * Colapsa un nodo específico.
     * @param {string} nodeId - ID del nodo a colapsar
     */
    collapseNode(nodeId) {
        const newSet = new Set(this._expandedNodes);
        newSet.delete(nodeId);
        this._expandedNodes = newSet;
    }

    /**
     * Selecciona un nodo específico.
     * @param {string} nodeId - ID del nodo a seleccionar
     */
    selectNode(nodeId) {
        this._selectedNode = nodeId;
    }

    /**
     * Expande todos los nodos.
     */
    expandAll() {
        const allIds = this._collectAllNodeIds(this._rootNode);
        this._expandedNodes = new Set(allIds);
    }

    /**
     * Colapsa todos los nodos.
     */
    collapseAll() {
        // Mantener solo el root expandido
        if (this._rootNode?.id) {
            this._expandedNodes = new Set([this._rootNode.id]);
        } else {
            this._expandedNodes = new Set();
        }
    }

    // ========================================================================
    // EVENT HANDLERS
    // ========================================================================

    _handleNodeSelected(e) {
        if (e.composedPath()[0] === this) return;  // guard: evitar re-entrar con el evento re-emitido
        const node = e.detail.node;
        this._selectedNode = node.id;
        
        // Re-emit con el nodo completo
        this.dispatchEvent(new CustomEvent('node-selected', {
            detail: { node },
            bubbles: true,
            composed: true
        }));
    }

    _handleNodeExpanded(e) {
        if (e.composedPath()[0] === this) return;  // guard: evitar re-entrar con el evento re-emitido
        const node = e.detail.node;
        this.expandNode(node.id);
        
        this.dispatchEvent(new CustomEvent('node-expanded', {
            detail: { node },
            bubbles: true,
            composed: true
        }));
    }

    _handleNodeCollapsed(e) {
        if (e.composedPath()[0] === this) return;  // guard: evitar re-entrar con el evento re-emitido
        const node = e.detail.node;
        this.collapseNode(node.id);
        
        this.dispatchEvent(new CustomEvent('node-collapsed', {
            detail: { node },
            bubbles: true,
            composed: true
        }));
    }

    // ========================================================================
    // HELPERS
    // ========================================================================

    /**
     * Reconstruye el árbol a partir de la lista plana de nodos.
     * 
     * El backend devuelve nodos con parent_id para evitar recursión
     * en el schema OpenAPI. Este método reconstruye la estructura
     * de árbol con children para renderizar.
     * 
     * @param {Array} nodes - Lista plana de nodos
     * @param {string} rootId - ID del nodo raíz
     * @returns {Object} Nodo raíz con children anidados
     */
    _buildTreeFromGraph(nodes, rootId) {
        // Crear mapa id -> nodo (copia para no mutar original)
        const nodeMap = new Map();
        for (const node of nodes) {
            nodeMap.set(node.id, { ...node, children: [] });
        }
        
        // Construir relaciones padre-hijo
        for (const node of nodeMap.values()) {
            if (node.parent_id && nodeMap.has(node.parent_id)) {
                const parent = nodeMap.get(node.parent_id);
                parent.children.push(node);
            }
        }
        
        // Ordenar children de cada nodo (directorios primero, luego por nombre)
        for (const node of nodeMap.values()) {
            if (node.children.length > 0) {
                node.children.sort((a, b) => {
                    // Directorios primero
                    if (a.type === 'directory' && b.type !== 'directory') return -1;
                    if (a.type !== 'directory' && b.type === 'directory') return 1;
                    // Luego por nombre
                    return a.name.localeCompare(b.name);
                });
            } else {
                // Si no tiene hijos, establecer children como null
                node.children = null;
            }
        }
        
        return nodeMap.get(rootId) || null;
    }

    /**
     * Recolecta todos los IDs de nodos en el árbol.
     */
    _collectAllNodeIds(node, ids = []) {
        if (!node) return ids;
        
        ids.push(node.id);
        
        if (node.children) {
            for (const child of node.children) {
                this._collectAllNodeIds(child, ids);
            }
        }
        
        return ids;
    }
}

// Registrar el custom element
if (!customElements.get('code-explorer')) {
    customElements.define('code-explorer', CodeExplorer);
}
