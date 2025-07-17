// Design Documentation Viewer Component JavaScript

class DesignViewer {
    constructor() {
        this.isLoading = false;
        this.designFiles = [];
        this.currentFile = null;
        this.fileTree = {};
        this.init();
    }
    
    init() {
        console.log('Initializing Design Viewer');
        
        // Set up search functionality
        this.setupSearch();
        
        // Auto-load design files if we're on the design page
        if (window.location.pathname === '/design') {
            this.loadDesign();
        }
    }
    
    setupSearch() {
        const searchInput = document.getElementById('design-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterTree(e.target.value);
            });
        }
    }
    
    async loadDesign() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        console.log('Loading design files...');
        
        try {
            // Show loading state
            this.showLoadingState();
            
            // Fetch list of design files
            const response = await fetch('/api/design/files');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.designFiles = data.files;
                this.renderFileTree();
                console.log(`Loaded ${data.files.length} design files successfully`);
            } else {
                throw new Error(data.error || 'Unknown error loading design files');
            }
            
        } catch (error) {
            console.error('Error loading design files:', error);
            this.handleError(error);
        } finally {
            this.isLoading = false;
        }
    }
    
    buildFileTree(files) {
        const tree = {};
        
        files.forEach(file => {
            const parts = file.split('/');
            let current = tree;
            
            parts.forEach((part, index) => {
                if (!current[part]) {
                    current[part] = {
                        type: index === parts.length - 1 ? 'file' : 'directory',
                        path: index === parts.length - 1 ? file : null,
                        children: {},
                        parent: current
                    };
                }
                if (current[part].type === 'directory') {
                    current = current[part].children;
                }
            });
        });
        
        return tree;
    }
    
    renderFileTree() {
        const treeElement = document.getElementById('design-tree');
        if (!treeElement) return;
        
        if (this.designFiles.length === 0) {
            treeElement.innerHTML = `
                <div class="loading-message">
                    <p>📄 No design files found</p>
                    <p style="color: #dc3545; font-size: 0.9rem;">
                        Run 'autocode code-to-design' to generate design documentation
                    </p>
                </div>
            `;
            return;
        }
        
        this.fileTree = this.buildFileTree(this.designFiles);
        treeElement.innerHTML = '';
        this.renderTreeNode(this.fileTree, treeElement, 0);
    }
    
    renderTreeNode(node, parentElement, level) {
        Object.entries(node).forEach(([key, value]) => {
            const nodeDiv = document.createElement('div');
            nodeDiv.className = `design-tree-node ${value.type}`;
            nodeDiv.style.paddingLeft = `${level * 1}rem`;
            
            const icon = value.type === 'directory' ? '📁' : '📄';
            const nodeContent = document.createElement('div');
            nodeContent.className = 'design-tree-node-content';
            nodeContent.innerHTML = `${icon} ${key}`;
            
            if (value.type === 'file') {
                nodeContent.style.cursor = 'pointer';
                nodeContent.onclick = () => this.loadFile(value.path);
            } else {
                // Directory - make it collapsible
                nodeContent.style.cursor = 'pointer';
                const childrenContainer = document.createElement('div');
                childrenContainer.className = 'design-tree-children';
                childrenContainer.style.display = 'block'; // Initially expanded
                
                nodeContent.onclick = () => {
                    const isExpanded = childrenContainer.style.display === 'block';
                    childrenContainer.style.display = isExpanded ? 'none' : 'block';
                    nodeContent.innerHTML = `${isExpanded ? '📂' : '📁'} ${key}`;
                };
                
                nodeDiv.appendChild(nodeContent);
                this.renderTreeNode(value.children, childrenContainer, level + 1);
                nodeDiv.appendChild(childrenContainer);
                parentElement.appendChild(nodeDiv);
                return;
            }
            
            nodeDiv.appendChild(nodeContent);
            parentElement.appendChild(nodeDiv);
        });
    }
    
    async loadFile(filePath) {
        if (this.isLoading) return;
        
        this.currentFile = filePath;
        this.updateBreadcrumbs(filePath);
        
        try {
            // Update header
            const titleElement = document.getElementById('design-title');
            const summaryElement = document.getElementById('design-summary');
            
            if (titleElement) titleElement.textContent = `Design: ${filePath}`;
            if (summaryElement) summaryElement.textContent = 'Loading file content...';
            
            // Fetch file content
            const response = await fetch(`/design/${filePath}`);
            
            if (!response.ok) {
                throw new Error(`Failed to load ${filePath}: ${response.statusText}`);
            }
            
            const content = await response.text();
            
            // Extract Mermaid diagrams
            const diagrams = this.extractMermaidDiagrams(content);
            
            // Render file content
            this.renderFileContent(filePath, content, diagrams);
            
        } catch (error) {
            console.error(`Error loading file ${filePath}:`, error);
            this.renderFileError(filePath, error);
        }
    }
    
    renderFileContent(filePath, content, diagrams) {
        const contentElement = document.getElementById('design-content');
        const summaryElement = document.getElementById('design-summary');
        
        if (!contentElement) return;
        
        if (summaryElement) {
            summaryElement.textContent = `${diagrams.length} diagram${diagrams.length !== 1 ? 's' : ''} found`;
        }
        
        contentElement.innerHTML = '';
        
        if (diagrams.length === 0) {
            contentElement.innerHTML = `
                <div class="design-no-diagrams">
                    <h3>📄 ${filePath}</h3>
                    <p>This file contains no Mermaid diagrams.</p>
                    <div class="design-file-content">
                        <pre>${content}</pre>
                    </div>
                </div>
            `;
            return;
        }
        
        // Render diagrams directly in simple containers
        diagrams.forEach((diagram, index) => {
            const diagramContainer = document.createElement('div');
            diagramContainer.className = 'diagram-container';
            diagramContainer.style.marginBottom = 'var(--spacing-4)';
            
            const diagramId = `diagram-${filePath.replace(/[^a-zA-Z0-9]/g, '_')}-${index}`;
            const diagramDiv = document.createElement('div');
            diagramDiv.id = diagramId;
            diagramDiv.className = 'mermaid';
            diagramDiv.style.display = 'flex';
            diagramDiv.style.justifyContent = 'center';
            diagramDiv.style.alignItems = 'center';
            diagramDiv.style.minHeight = '200px';
            diagramDiv.textContent = diagram;
            
            diagramContainer.appendChild(diagramDiv);
            contentElement.appendChild(diagramContainer);
        });
        
        // Initialize Mermaid for new diagrams
        this.initializeMermaid();
    }
    
    toggleAccordion(accordionDiv) {
        const content = accordionDiv.querySelector('.design-accordion-content');
        const toggle = accordionDiv.querySelector('.accordion-toggle');
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            toggle.textContent = '▼';
        } else {
            content.style.display = 'none';
            toggle.textContent = '▶';
        }
    }
    
    renderFileError(filePath, error) {
        const contentElement = document.getElementById('design-content');
        const summaryElement = document.getElementById('design-summary');
        
        if (summaryElement) {
            summaryElement.textContent = 'Error loading file';
        }
        
        if (contentElement) {
            contentElement.innerHTML = `
                <div class="design-error">
                    <h3>❌ Error Loading File</h3>
                    <p><strong>File:</strong> ${filePath}</p>
                    <p><strong>Error:</strong> ${error.message}</p>
                </div>
            `;
        }
    }
    
    updateBreadcrumbs(filePath) {
        const breadcrumbsElement = document.getElementById('design-breadcrumbs');
        if (!breadcrumbsElement) return;
        
        const parts = filePath.split('/');
        let breadcrumbs = ['<span class="breadcrumb-item">design</span>'];
        
        let currentPath = '';
        parts.forEach((part, index) => {
            if (index === parts.length - 1) {
                // Last part (file)
                breadcrumbs.push(`<span class="breadcrumb-item current">${part}</span>`);
            } else {
                // Directory part
                currentPath += part + '/';
                breadcrumbs.push(`<span class="breadcrumb-item">${part}</span>`);
            }
        });
        
        breadcrumbsElement.innerHTML = breadcrumbs.join(' / ');
    }
    
    extractMermaidDiagrams(content) {
        const diagrams = [];
        const mermaidRegex = /```mermaid\s*\n([\s\S]*?)\n```/g;
        let match;
        
        while ((match = mermaidRegex.exec(content)) !== null) {
            const diagramContent = match[1].trim();
            
            // Validate that the diagram content is not empty and seems valid
            if (diagramContent && diagramContent.length > 0) {
                // Log the extracted diagram for debugging
                console.log('Extracted diagram:', diagramContent.substring(0, 100) + '...');
                diagrams.push(diagramContent);
            }
        }
        
        return diagrams;
    }
    
    filterTree(searchTerm) {
        const treeElement = document.getElementById('design-tree');
        if (!treeElement) return;
        
        const nodes = treeElement.querySelectorAll('.design-tree-node');
        
        if (!searchTerm.trim()) {
            // Show all nodes
            nodes.forEach(node => node.style.display = 'block');
            return;
        }
        
        const lowerSearchTerm = searchTerm.toLowerCase();
        
        nodes.forEach(node => {
            const text = node.textContent.toLowerCase();
            const matches = text.includes(lowerSearchTerm);
            node.style.display = matches ? 'block' : 'none';
        });
    }
    
    initializeMermaid() {
        if (typeof mermaid === 'undefined') {
            console.error('Mermaid is not loaded');
            return;
        }
        
        try {
            // Configure Mermaid with simple, reliable settings
            mermaid.initialize({
                startOnLoad: false,
                theme: 'default',
                securityLevel: 'loose',
                logLevel: 'error',
                flowchart: {
                    useMaxWidth: true,
                    htmlLabels: true
                },
                classDiagram: {
                    useMaxWidth: true,
                    htmlLabels: true
                }
            });
            
            // Find all mermaid elements that haven't been rendered yet
            const mermaidElements = document.querySelectorAll('.mermaid:not([data-processed])');
            
            if (mermaidElements.length === 0) {
                console.log('No new Mermaid diagrams to render');
                return;
            }
            
            console.log(`Found ${mermaidElements.length} diagrams to render`);
            
            // Process each element with a robust approach
            mermaidElements.forEach((element, index) => {
                try {
                    const diagramText = element.textContent.trim();
                    
                    if (!diagramText) {
                        console.warn(`Empty diagram text found at index ${index}, skipping`);
                        return;
                    }
                    
                    // Validate diagram text
                    if (diagramText.length < 10 || !diagramText.includes('classDiagram')) {
                        console.warn(`Invalid diagram text at index ${index}:`, diagramText);
                        return;
                    }
                    
                    // Log the full diagram text for debugging
                    console.log(`Processing diagram ${index + 1}:`);
                    console.log('Full diagram text:', diagramText);
                    
                    // Mark as processed to avoid re-processing
                    element.setAttribute('data-processed', 'true');
                    
                    // Generate unique ID
                    const uniqueId = `mermaid-diagram-${Date.now()}-${index}`;
                    element.id = uniqueId;
                    
                    // Create a clean container for the diagram
                    const container = document.createElement('div');
                    container.id = uniqueId + '-container';
                    container.style.width = '100%';
                    container.style.textAlign = 'center';
                    
                    // Try the new API first, fallback to old API
                    if (mermaid.render && typeof mermaid.render === 'function') {
                        // Use modern async API
                        mermaid.render(uniqueId + '-svg', diagramText)
                            .then(result => {
                                console.log(`Successfully rendered diagram ${index + 1} with new API`);
                                container.innerHTML = result.svg;
                                element.innerHTML = '';
                                element.appendChild(container);
                            })
                            .catch(renderError => {
                                console.error(`Mermaid render error for diagram ${index + 1}:`, renderError);
                                this.renderDiagramError(element, index + 1, renderError, diagramText);
                            });
                    } else {
                        // Fallback to old API
                        try {
                            const tempDiv = document.createElement('div');
                            tempDiv.innerHTML = diagramText;
                            tempDiv.id = uniqueId + '-temp';
                            tempDiv.className = 'mermaid';
                            
                            container.appendChild(tempDiv);
                            element.innerHTML = '';
                            element.appendChild(container);
                            
                            mermaid.init(undefined, tempDiv);
                            console.log(`Successfully rendered diagram ${index + 1} with old API`);
                        } catch (fallbackError) {
                            console.error(`Fallback render error for diagram ${index + 1}:`, fallbackError);
                            this.renderDiagramError(element, index + 1, fallbackError, diagramText);
                        }
                    }
                    
                } catch (processingError) {
                    console.error(`Error processing diagram element ${index + 1}:`, processingError);
                    this.renderDiagramError(element, index + 1, processingError, null);
                }
            });
            
        } catch (error) {
            console.error('Error initializing Mermaid:', error);
        }
    }
    
    renderDiagramError(element, diagramNumber, error, diagramText) {
        element.innerHTML = `
            <div style="color: #dc3545; padding: 20px; text-align: center; border: 1px solid #dc3545; border-radius: 4px; background: #f8d7da; margin: 10px 0;">
                <p><strong>⚠️ Error rendering diagram ${diagramNumber}</strong></p>
                <p style="font-size: 0.9em; margin-top: 10px;">${error.message}</p>
                ${diagramText ? `
                    <details style="margin-top: 15px; text-align: left;">
                        <summary style="cursor: pointer; font-weight: bold;">Show diagram source</summary>
                        <pre style="margin-top: 10px; font-size: 0.8em; background: #fff; padding: 10px; border-radius: 4px; overflow-x: auto;">${diagramText}</pre>
                    </details>
                ` : ''}
            </div>
        `;
    }
    
    showLoadingState() {
        const treeElement = document.getElementById('design-tree');
        if (treeElement) {
            treeElement.innerHTML = `
                <div class="loading-message">
                    <p>🔄 Loading design files...</p>
                    <p style="color: #6c757d;">Please wait while we fetch the documentation</p>
                </div>
            `;
        }
    }
    
    handleError(error) {
        console.error('Design Viewer error:', error);
        
        const titleElement = document.getElementById('design-title');
        const summaryElement = document.getElementById('design-summary');
        const treeElement = document.getElementById('design-tree');
        
        if (titleElement) titleElement.textContent = 'Design Viewer Error';
        if (summaryElement) summaryElement.textContent = error.message;
        
        if (treeElement) {
            treeElement.innerHTML = `
                <div class="loading-message">
                    <p>❌ Error loading design files</p>
                    <p style="color: #dc3545; font-size: 0.9rem; margin-top: 10px;">${error.message}</p>
                    <p style="color: #6c757d; font-size: 0.85rem; margin-top: 10px;">
                        Make sure the design directory exists and contains markdown files with Mermaid diagrams.
                    </p>
                </div>
            `;
        }
    }
    
    async refreshDesign() {
        if (this.isLoading) return;
        
        console.log('Refreshing design files...');
        await this.loadDesign();
    }
}

// Global functions for button clicks
async function loadDesign() {
    const button = event.target;
    const originalText = button.textContent;
    
    button.disabled = true;
    button.textContent = 'Loading...';
    
    try {
        if (window.designViewer) {
            await window.designViewer.loadDesign();
        }
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}

async function refreshDesign() {
    const button = event.target;
    const originalText = button.textContent;
    
    button.disabled = true;
    button.textContent = 'Refreshing...';
    
    try {
        if (window.designViewer) {
            await window.designViewer.refreshDesign();
        }
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}

// Initialize Design Viewer when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.designViewer = new DesignViewer();
});
