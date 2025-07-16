// Design Documentation Viewer Component JavaScript

class UIDesigner {
    constructor() {
        this.isLoading = false;
        this.designFiles = [];
        this.init();
    }
    
    init() {
        console.log('Initializing Design Documentation Viewer');
        // Auto-load design files if we're on the UI Designer page
        if (window.location.pathname === '/ui-designer') {
            this.loadDesignFiles();
        }
    }
    
    async loadDesignFiles() {
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
                await this.renderDesignFiles();
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
    
    async renderDesignFiles() {
        const titleElement = document.getElementById('ui-designer-title');
        const summaryElement = document.getElementById('ui-designer-summary');
        const listElement = document.getElementById('design-files-list');
        
        if (!titleElement || !summaryElement || !listElement) {
            console.error('Required UI Designer elements not found');
            return;
        }
        
        // Update header info
        titleElement.textContent = 'Design Documentation Viewer';
        summaryElement.textContent = `Found ${this.designFiles.length} design files`;
        
        // Clear previous content
        listElement.innerHTML = '';
        
        if (this.designFiles.length === 0) {
            listElement.innerHTML = `
                <div class="loading-message">
                    <p>📄 No design files found</p>
                    <p style="color: #dc3545; font-size: 0.9rem;">
                        Run 'autocode code-to-design' to generate design documentation
                    </p>
                </div>
            `;
            return;
        }
        
        // Group files by directory for better organization
        const fileGroups = this.groupFilesByDirectory(this.designFiles);
        
        // Create accordion-style layout
        for (const [group, files] of Object.entries(fileGroups)) {
            await this.renderFileGroup(group, files, listElement);
        }
        
        // Initialize Mermaid after all content is loaded
        this.initializeMermaid();
    }
    
    groupFilesByDirectory(files) {
        const groups = {};
        
        for (const file of files) {
            const parts = file.split('/');
            const directory = parts.length > 1 ? parts.slice(0, -1).join('/') : 'root';
            
            if (!groups[directory]) {
                groups[directory] = [];
            }
            groups[directory].push(file);
        }
        
        return groups;
    }
    
    async renderFileGroup(groupName, files, parentElement) {
        // Create group container
        const groupDiv = document.createElement('div');
        groupDiv.className = 'design-file-group';
        
        // Create group header
        const groupHeader = document.createElement('div');
        groupHeader.className = 'design-file-group-header';
        groupHeader.innerHTML = `
            <h4>📁 ${groupName}</h4>
            <span class="file-count">${files.length} files</span>
        `;
        
        // Create group content
        const groupContent = document.createElement('div');
        groupContent.className = 'design-file-group-content';
        
        // Process each file in the group
        for (const file of files) {
            await this.renderDesignFile(file, groupContent);
        }
        
        groupDiv.appendChild(groupHeader);
        groupDiv.appendChild(groupContent);
        parentElement.appendChild(groupDiv);
    }
    
    async renderDesignFile(filePath, parentElement) {
        try {
            // Fetch file content
            const response = await fetch(`/design/${filePath}`);
            
            if (!response.ok) {
                throw new Error(`Failed to load ${filePath}: ${response.statusText}`);
            }
            
            const content = await response.text();
            
            // Extract Mermaid diagrams
            const diagrams = this.extractMermaidDiagrams(content);
            
            if (diagrams.length === 0) {
                // Show file info even if no diagrams
                this.renderFileWithoutDiagrams(filePath, parentElement);
                return;
            }
            
            // Create file container
            const fileDiv = document.createElement('div');
            fileDiv.className = 'design-file';
            
            // Create file header
            const fileHeader = document.createElement('div');
            fileHeader.className = 'design-file-header';
            fileHeader.innerHTML = `
                <h5>📄 ${filePath}</h5>
                <span class="diagram-count">${diagrams.length} diagram${diagrams.length > 1 ? 's' : ''}</span>
            `;
            
            // Create diagrams container
            const diagramsContainer = document.createElement('div');
            diagramsContainer.className = 'design-file-diagrams';
            
            // Render each diagram
            diagrams.forEach((diagram, index) => {
                const diagramDiv = document.createElement('div');
                diagramDiv.className = 'design-diagram';
                
                // Create unique ID for each diagram
                const diagramId = `diagram-${filePath.replace(/[^a-zA-Z0-9]/g, '_')}-${index}`;
                
                diagramDiv.innerHTML = `
                    <div class="diagram-header">
                        <span class="diagram-title">Diagram ${index + 1}</span>
                    </div>
                    <div class="diagram-content">
                        <div id="${diagramId}" class="mermaid">${diagram}</div>
                    </div>
                `;
                
                diagramsContainer.appendChild(diagramDiv);
            });
            
            fileDiv.appendChild(fileHeader);
            fileDiv.appendChild(diagramsContainer);
            parentElement.appendChild(fileDiv);
            
        } catch (error) {
            console.error(`Error rendering file ${filePath}:`, error);
            this.renderFileWithError(filePath, error, parentElement);
        }
    }
    
    extractMermaidDiagrams(content) {
        const diagrams = [];
        const mermaidRegex = /```mermaid\s*\n([\s\S]*?)\n```/g;
        let match;
        
        while ((match = mermaidRegex.exec(content)) !== null) {
            diagrams.push(match[1].trim());
        }
        
        return diagrams;
    }
    
    renderFileWithoutDiagrams(filePath, parentElement) {
        const fileDiv = document.createElement('div');
        fileDiv.className = 'design-file no-diagrams';
        fileDiv.innerHTML = `
            <div class="design-file-header">
                <h5>📄 ${filePath}</h5>
                <span class="diagram-count">No diagrams</span>
            </div>
            <div class="design-file-content">
                <p style="color: #6c757d; font-style: italic;">This file contains no Mermaid diagrams</p>
            </div>
        `;
        parentElement.appendChild(fileDiv);
    }
    
    renderFileWithError(filePath, error, parentElement) {
        const fileDiv = document.createElement('div');
        fileDiv.className = 'design-file error';
        fileDiv.innerHTML = `
            <div class="design-file-header">
                <h5>📄 ${filePath}</h5>
                <span class="diagram-count error">Error</span>
            </div>
            <div class="design-file-content">
                <p style="color: #dc3545;">Error loading file: ${error.message}</p>
            </div>
        `;
        parentElement.appendChild(fileDiv);
    }
    
    initializeMermaid() {
        if (typeof mermaid === 'undefined') {
            console.error('Mermaid is not loaded');
            return;
        }
        
        // Configure Mermaid
        mermaid.initialize({
            startOnLoad: false,
            theme: 'default',
            themeVariables: {
                primaryColor: '#e1f5fe',
                primaryTextColor: '#0277bd',
                primaryBorderColor: '#0277bd',
                lineColor: '#757575',
                secondaryColor: '#f3e5f5',
                tertiaryColor: '#e8f5e8'
            },
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true
            },
            securityLevel: 'loose'
        });
        
        // Find all mermaid elements and render them
        const mermaidElements = document.querySelectorAll('.mermaid');
        
        mermaidElements.forEach((element) => {
            try {
                mermaid.init(undefined, element);
            } catch (error) {
                console.error('Error rendering mermaid diagram:', error);
                element.innerHTML = `<p style="color: #dc3545;">Error rendering diagram: ${error.message}</p>`;
            }
        });
        
        console.log(`Rendered ${mermaidElements.length} Mermaid diagrams`);
    }
    
    showLoadingState() {
        const listElement = document.getElementById('design-files-list');
        if (listElement) {
            listElement.innerHTML = `
                <div class="loading-message">
                    <p>🔄 Loading design files...</p>
                    <p style="color: #6c757d;">Please wait while we fetch the documentation</p>
                </div>
            `;
        }
    }
    
    handleError(error) {
        console.error('Design Documentation Viewer error:', error);
        
        const titleElement = document.getElementById('ui-designer-title');
        const summaryElement = document.getElementById('ui-designer-summary');
        const listElement = document.getElementById('design-files-list');
        
        if (titleElement) titleElement.textContent = 'Design Documentation Error';
        if (summaryElement) summaryElement.textContent = error.message;
        
        if (listElement) {
            listElement.innerHTML = `
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
    
    async refreshDesignFiles() {
        if (this.isLoading) return;
        
        console.log('Refreshing design files...');
        await this.loadDesignFiles();
    }
}

// Global functions for button clicks
async function loadDesignFiles() {
    const button = event.target;
    const originalText = button.textContent;
    
    button.disabled = true;
    button.textContent = 'Loading...';
    
    try {
        if (window.uiDesigner) {
            await window.uiDesigner.loadDesignFiles();
        }
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}

async function refreshDesignFiles() {
    const button = event.target;
    const originalText = button.textContent;
    
    button.disabled = true;
    button.textContent = 'Refreshing...';
    
    try {
        if (window.uiDesigner) {
            await window.uiDesigner.refreshDesignFiles();
        }
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}

// Initialize UI Designer when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.uiDesigner = new UIDesigner();
});
