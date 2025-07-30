// Docs Viewer Component
class DocsViewer {
    constructor() {
        this.init();
    }

    init() {
        this.loadFileTree();
    }

    async loadFileTree() {
        const fileTree = document.getElementById('file-tree');
        
        try {
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
                <div class="text-red-500 text-sm">
                    Error cargando archivos: ${err.message}
                </div>
            `;
        }
    }

    renderFileTree(files) {
        const fileTree = document.getElementById('file-tree');
        
        if (!files || files.length === 0) {
            fileTree.innerHTML = '<div class="text-gray-500 text-sm">No se encontraron archivos</div>';
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
            const indent = 'pl-' + (level * 4);
            
            if (item.isFile) {
                const fileName = key.endsWith('.md') ? key.slice(0, -3) : key;
                html += `
                    <div class="cursor-pointer hover:bg-gray-100 py-1 px-2 rounded text-sm ${indent} flex items-center"
                         onclick="docsViewer.loadFile('${item.path}')">
                        <span class="mr-2">📄</span>
                        <span>${fileName}</span>
                    </div>
                `;
            } else {
                html += `
                    <div class="py-1 px-2 text-sm font-medium text-gray-700 ${indent} flex items-center">
                        <span class="mr-2">📁</span>
                        <span>${key}</span>
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
            <div class="text-center py-8">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
                <p class="text-gray-500">Cargando archivo...</p>
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
                <div class="mb-4 pb-4 border-b border-gray-200">
                    <h2 class="text-xl font-semibold text-gray-800">${filePath}</h2>
                </div>
                <div class="prose prose-sm max-w-none">
                    ${htmlContent}
                </div>
            `;
            
        } catch (err) {
            console.error('Error loading file:', err);
            contentArea.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-red-500">
                        <p class="font-semibold">Error cargando archivo</p>
                        <p class="text-sm">${err.message}</p>
                    </div>
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
