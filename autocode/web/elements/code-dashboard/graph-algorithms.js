/**
 * graph-algorithms.js
 * Algoritmos puros de transformación de datos para el grafo de dependencias.
 *
 * Todas las funciones son puras (sin `this`, sin DOM, sin D3 selections):
 * reciben datos como parámetros y devuelven nuevos datos.
 * Zero side effects excepto donde se documenta mutación in-place
 * (computeCouplingMetrics, markCircularLinks — mutan el array recibido).
 *
 * Funciones exportadas:
 *   - buildFileGraph(nodes, dependencies)       → {graphNodes, graphLinks}
 *   - buildPackageGraph(nodes, dependencies, depth) → {graphNodes, graphLinks}
 *   - computeCouplingMetrics(graphNodes, graphLinks) → void (muta in-place)
 *   - markCircularLinks(graphNodes, graphLinks)  → void (muta in-place, Tarjan SCC)
 *   - buildPackHierarchy(filteredNodes)          → hierarchyRoot
 *   - applyFilters(graphNodes, graphLinks, filterText, excludePatterns) → {graphNodes, graphLinks}
 */

// ============================================================================
// FILE-LEVEL GRAPH
// ============================================================================

/**
 * File-level graph: each file node is a graph node, each dependency is a link.
 * Computes fan_in, fan_out, instability, fan_in_out per node.
 * Circular detection via Tarjan SCC (client-side).
 *
 * @param {Array} nodes        — Array<ArchitectureNode> file nodes
 * @param {Array} dependencies — Array<FileDependency> resolved dependencies
 * @returns {{ graphNodes: Array, graphLinks: Array }}
 */
export function buildFileGraph(nodes, dependencies) {
    const nodeIds = new Set(nodes.map(n => n.id));

    const graphNodes = nodes.map(n => ({
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
        // coupling metrics (filled by computeCouplingMetrics)
        fan_in:      0,
        fan_out:     0,
        instability: 0,
        fan_in_out:  0,
    }));

    const graphLinks = (dependencies || [])
        .filter(d => nodeIds.has(d.source) && nodeIds.has(d.target))
        .map(d => ({
            source:      d.source,
            target:      d.target,
            importCount: d.import_names?.length || 1,
            importNames: d.import_names || [],
            isCircular:  false, // filled by markCircularLinks
        }));

    // Compute coupling metrics
    computeCouplingMetrics(graphNodes, graphLinks);

    // Mark circular links via Tarjan SCC
    markCircularLinks(graphNodes, graphLinks);

    return { graphNodes, graphLinks };
}

// ============================================================================
// PACKAGE-LEVEL GRAPH
// ============================================================================

/**
 * Package-level graph: group file nodes by the first `depth` path segments,
 * aggregate metrics and dependencies between resulting package nodes.
 * Computes fan_in, fan_out, instability, fan_in_out per package node.
 *
 * Example at depth=2: "autocode/core/ai/pipelines.py" → group "autocode/core"
 *
 * @param {Array}  nodes        — Array<ArchitectureNode> file nodes
 * @param {Array}  dependencies — Array<FileDependency> resolved dependencies
 * @param {number} depth        — number of path segments used as group key (≥1)
 * @returns {{ graphNodes: Array, graphLinks: Array }}
 */
export function buildPackageGraph(nodes, dependencies, depth) {
    const { packages, fileToPackage } = groupFilesByPackage(nodes, depth);
    const graphNodes = packagesToGraphNodes(packages, fileToPackage);
    const graphLinks = aggregatePackageEdges(dependencies, fileToPackage);
    computeCouplingMetrics(graphNodes, graphLinks);
    markCircularLinks(graphNodes, graphLinks);
    return { graphNodes, graphLinks };
}

/**
 * Phase 1: Group file nodes into package buckets by path prefix.
 * Only processes nodes of type 'file'; skips directories/classes/methods.
 *
 * @param {Array}  nodes — Array<ArchitectureNode>
 * @param {number} depth — number of path segments used as group key (≥1)
 * @returns {{ packages: Map, fileToPackage: Map }}
 */
function groupFilesByPackage(nodes, depth) {
    const packages    = new Map();
    const fileToPackage = new Map();

    for (const node of nodes) {
        if (node.type !== 'file') continue;
        const parts = (node.path || '').split('/');
        const pkgId = parts.slice(0, depth).join('/') || '.';

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

        const pkg    = packages.get(pkgId);
        const weight = node.sloc || 1;
        pkg.files.push(node.id);
        pkg.sloc            += node.sloc            || 0;
        pkg.loc             += node.loc             || 0;
        pkg.mi_sum          += (node.mi             ?? 100) * weight;
        pkg.mi_weight       += weight;
        pkg.cc_sum          += (node.avg_complexity ?? 0)   * weight;
        pkg.cc_max           = Math.max(pkg.cc_max, node.max_complexity ?? 0);
        pkg.functions_count += node.functions_count || 0;
        pkg.classes_count   += node.classes_count   || 0;
        fileToPackage.set(node.id, pkgId);
    }

    return { packages, fileToPackage };
}

/**
 * Phase 2: Convert the packages Map into a flat graphNodes array.
 * Computes weighted-average MI and CC; zero-initialises coupling fields.
 *
 * @param {Map} packages     — output of groupFilesByPackage
 * @param {Map} fileToPackage — file-id → package-id mapping (unused here, kept for symmetry)
 * @returns {Array} graphNodes
 */
function packagesToGraphNodes(packages) {
    const graphNodes = [];
    for (const pkg of packages.values()) {
        graphNodes.push({
            id:              pkg.id,
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
    return graphNodes;
}

/**
 * Phase 3: Aggregate file-level dependencies into package-level edges.
 * Self-loops (srcPkg === tgtPkg) are discarded.
 *
 * @param {Array} dependencies  — Array<FileDependency>
 * @param {Map}   fileToPackage — file-id → package-id mapping
 * @returns {Array} graphLinks
 */
function aggregatePackageEdges(dependencies, fileToPackage) {
    const edgeMap = new Map();

    for (const dep of (dependencies || [])) {
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

    return Array.from(edgeMap.values());
}

// ============================================================================
// COUPLING METRICS
// ============================================================================

/**
 * Computes fan_in, fan_out, instability, fan_in_out for each node in-place.
 *
 * @param {Array} graphNodes
 * @param {Array} graphLinks  (source/target are IDs here, before D3 resolves them)
 */
export function computeCouplingMetrics(graphNodes, graphLinks) {
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

// ============================================================================
// CIRCULAR DEPENDENCY DETECTION (Tarjan SCC)
// ============================================================================

/**
 * Tarjan's Strongly Connected Components algorithm.
 * Marks links as isCircular=true if both endpoints belong to an SCC with >1 node.
 * Detects direct (A↔B) and transitive (A→B→C→A) cycles.
 * Uses iterative implementation to avoid call stack overflow on large graphs.
 *
 * @param {Array} graphNodes
 * @param {Array} graphLinks  (source/target are IDs, pre-D3)
 */
export function markCircularLinks(graphNodes, graphLinks) {
    // Build adjacency list (node id → list of neighbor ids)
    const adj = new Map();
    for (const n of graphNodes) adj.set(n.id, []);

    for (const l of graphLinks) {
        const src = typeof l.source === 'object' ? l.source.id : l.source;
        const tgt = typeof l.target === 'object' ? l.target.id : l.target;
        if (adj.has(src)) adj.get(src).push(tgt);
    }

    // Tarjan's SCC (iterative to avoid call stack overflow on large graphs)
    let idx = 0;
    const stack      = [];
    const onStack    = new Set();
    const indices    = new Map();
    const lowlinks   = new Map();
    const cycleNodes = new Set(); // nodes that belong to a cycle (SCC size > 1)

    const strongConnect = (startV) => {
        const callStack = [{ v: startV, neighborIdx: 0 }];
        indices.set(startV, idx);
        lowlinks.set(startV, idx);
        idx++;
        stack.push(startV);
        onStack.add(startV);

        while (callStack.length > 0) {
            const frame = callStack[callStack.length - 1];
            const { v } = frame;
            const neighbors = adj.get(v) || [];

            if (frame.neighborIdx < neighbors.length) {
                const w = neighbors[frame.neighborIdx++];
                if (!indices.has(w)) {
                    indices.set(w, idx);
                    lowlinks.set(w, idx);
                    idx++;
                    stack.push(w);
                    onStack.add(w);
                    callStack.push({ v: w, neighborIdx: 0 });
                } else if (onStack.has(w)) {
                    lowlinks.set(v, Math.min(lowlinks.get(v), indices.get(w)));
                }
            } else {
                // Finished processing v's neighbors
                callStack.pop();
                if (callStack.length > 0) {
                    const parent = callStack[callStack.length - 1].v;
                    lowlinks.set(parent, Math.min(lowlinks.get(parent), lowlinks.get(v)));
                }

                // Check if v is root of an SCC
                if (lowlinks.get(v) === indices.get(v)) {
                    const scc = [];
                    let w;
                    do {
                        w = stack.pop();
                        onStack.delete(w);
                        scc.push(w);
                    } while (w !== v);

                    if (scc.length > 1) {
                        for (const nodeId of scc) cycleNodes.add(nodeId);
                    }
                }
            }
        }
    };

    for (const n of graphNodes) {
        if (!indices.has(n.id)) strongConnect(n.id);
    }

    // Mark links where both endpoints are in a cycle
    for (const l of graphLinks) {
        const src = typeof l.source === 'object' ? l.source.id : l.source;
        const tgt = typeof l.target === 'object' ? l.target.id : l.target;
        l.isCircular = cycleNodes.has(src) && cycleNodes.has(tgt);
    }
}

// ============================================================================
// PACK HIERARCHY BUILDER
// ============================================================================

/**
 * Build a nested tree from flat file nodes for d3.hierarchy / d3.pack.
 * Groups nodes by path segments to create package/directory nodes.
 * File nodes with no path prefix are placed directly under root.
 *
 * @param {Array} filteredNodes — file nodes after filter application
 * @returns {Object} Root node compatible with d3.hierarchy
 */
export function buildPackHierarchy(filteredNodes) {
    const root = {
        name:      'root',
        id:        '__root__',
        isPackage: true,
        children:  [],
    };
    const nodeMap = new Map([['__root__', root]]);

    for (const node of filteredNodes) {
        const parts = (node.path || node.name || '').split('/').filter(Boolean);
        let parentId = '__root__';

        // Create intermediate directory/package nodes from path segments
        for (let i = 0; i < parts.length - 1; i++) {
            const pathId = parts.slice(0, i + 1).join('/');
            if (!nodeMap.has(pathId)) {
                const dirNode = {
                    name:      parts[i],
                    id:        pathId,
                    path:      pathId,
                    isPackage: true,
                    children:  [],
                };
                nodeMap.set(pathId, dirNode);
                nodeMap.get(parentId).children.push(dirNode);
            }
            parentId = pathId;
        }

        // Add leaf file node (copy to avoid mutating original)
        const parent = nodeMap.get(parentId);
        if (parent) {
            parent.children.push({ ...node, isPackage: false, children: null });
        }
    }

    // Prune empty package nodes (safety: shouldn't happen with valid data)
    const prune = (n) => {
        if (!n.children) return true; // leaf: keep
        n.children = n.children.filter(prune);
        return n.children.length > 0 || !n.isPackage;
    };
    prune(root);

    return root;
}

// ============================================================================
// FILTERS
// ============================================================================

/**
 * Apply text and path-exclusion filters to a graph dataset.
 * Returns new arrays (non-destructive); filters links whose endpoints
 * become hidden after node filtering.
 *
 * @param {Array}  graphNodes      — full node list
 * @param {Array}  graphLinks      — full link list
 * @param {string} filterText      — substring to match against name/path ('' = no filter)
 * @param {Array}  excludePatterns — path patterns to exclude ([] = no exclusions)
 * @returns {{ graphNodes: Array, graphLinks: Array }}
 */
export function applyFilters(graphNodes, graphLinks, filterText, excludePatterns) {
    let visibleNodes = [...graphNodes];

    // Text filter (name or path)
    if (filterText) {
        const q = filterText.toLowerCase();
        visibleNodes = visibleNodes.filter(n =>
            n.name.toLowerCase().includes(q) || n.path.toLowerCase().includes(q));
    }

    // Path exclusion patterns
    if (excludePatterns && excludePatterns.length > 0) {
        visibleNodes = visibleNodes.filter(n => {
            const pathLower = n.path.toLowerCase();
            const nameLower = n.name.toLowerCase();
            return !excludePatterns.some(p =>
                pathLower.includes(p) || nameLower.includes(p));
        });
    }

    // Filter links: only those with both endpoints visible
    const visibleIds   = new Set(visibleNodes.map(n => n.id));
    const visibleLinks = graphLinks.filter(l => {
        const srcId = typeof l.source === 'object' ? l.source.id : l.source;
        const tgtId = typeof l.target === 'object' ? l.target.id : l.target;
        return visibleIds.has(srcId) && visibleIds.has(tgtId);
    });

    return { graphNodes: visibleNodes, graphLinks: visibleLinks };
}
