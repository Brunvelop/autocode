// Docs Viewer Component
class DocsViewer {
    constructor() {
        this.init();
    }

    init() {
        this.loadFileTree();
        
        // Add refresh button handler
        const refreshBtn = document.getElementById('refresh-tree');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadFileTree());
        }
    }

    async loadFileTree() {
        const fileTree = document.getElementById('file-tree');
        
        try {
            // Show loading state
            fileTree.innerHTML = '<div class="file-tree-loading">Cargando archivos...</div>';
            
            // Get docs structure from the docs check endpoint
            const response = await fetch('/api/docs/check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Extract file paths from the docs check data
            const files = [];
            if (data.data && data.data.issues) {
                data.data.issues.forEach(issue => {
                    if (issue.doc_path) {
                        // Convert backslashes to forward slashes for web URLs
                        let normalizedPath = issue.doc_path.replace(/\\/g, '/');
                        // Remove 'docs/' prefix since FastAPI mount already serves from docs directory
                        if (normalizedPath.startsWith('docs/')) {
                            normalizedPath = normalizedPath.substring(5);
                        }
                        files.push(normalizedPath);
                    }
                });
            }
            
            this.renderFileTree(files);
            
        } catch (err) {
            console.error('Error loading file tree:', err);
            fileTree.innerHTML = `
                <div class="file-tree-error">
                    Error cargando archivos: ${err.message}
                </div>
            `;
        }
    }

    renderFileTree(files) {
        const fileTree = document.getElementById('file-tree');
        
        if (!files || files.length === 0) {
            fileTree.innerHTML = '<div class="file-tree-empty">No se encontraron archivos</div>';
            return;
        }

        // Create a simple tree structure
        const tree = this.buildTree(files);
        fileTree.innerHTML = this.renderTree(tree);
    }

    buildTree(files) {
        const tree = {};
        
        files.forEach(filePath => {
            const parts = filePath.split('/');
            let current = tree;
            
            parts.forEach((part, index) => {
                if (!current[part]) {
                    current[part] = {
                        isFile: index === parts.length - 1,
                        path: parts.slice(0, index + 1).join('/'),
                        children: {}
                    };
                }
                current = current[part].children;
            });
        });
        
        return tree;
    }

    renderTree(tree, level = 0) {
        let html = '';
        
        Object.keys(tree).forEach(key => {
            const item = tree[key];
            const indentClass = `tree-indent-${level}`;
            
            if (item.isFile) {
                const fileName = key.endsWith('.md') ? key.slice(0, -3) : key;
                html += `
                    <div class="tree-file ${indentClass}"
                         onclick="docsViewer.loadFile('${item.path}')">
                        <span class="tree-file-icon">📄</span>
                        <span class="tree-file-name">${fileName}</span>
                    </div>
                `;
            } else {
                html += `
                    <div class="tree-folder ${indentClass}">
                        <span class="tree-folder-icon">📁</span>
                        <span class="tree-folder-name">${key}</span>
                    </div>
                `;
                html += this.renderTree(item.children, level + 1);
            }
        });
        
        return html;
    }

    async loadFile(filePath) {
        const contentArea = document.getElementById('content-area');
        
        // Show loading
        contentArea.innerHTML = `
            <div class="content-loading">
                <div class="content-loading-spinner"></div>
                <p class="content-loading-text">Cargando archivo...</p>
            </div>
        `;
        
        try {
            const response = await fetch(`/documentation/${filePath}`);
            
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            
            const markdownContent = await response.text();
            
            // Render markdown with marked.js
            const htmlContent = marked.parse(markdownContent);
            
            contentArea.innerHTML = `
                <div class="content-header">
                    <h2 class="content-title">${filePath}</h2>
                </div>
                <div class="content-body">
                    ${htmlContent}
                </div>
            `;
            
        } catch (err) {
            console.error('Error loading file:', err);
            contentArea.innerHTML = `
                <div class="content-error">
                    <div class="content-error-icon">⚠️</div>
                    <p class="content-error-title">Error cargando archivo</p>
                    <p class="content-error-message">${err.message}</p>
                </div>
            `;
        }
    }
}

// Global instance for onclick handlers
let docsViewer;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    docsViewer = new DocsViewer();
});
