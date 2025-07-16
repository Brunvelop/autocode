// API Fetch Utilities

class APIClient {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${url}`, error);
            throw error;
        }
    }
    
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }
    
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }
    
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }
    
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
    
    // Specific API endpoints
    async getStatus() {
        return this.get('/status');
    }
    
    async getConfig() {
        return this.get('/config');
    }
    
    async updateConfig(config) {
        return this.put('/config', config);
    }
    
    async runCheck(checkName) {
        return this.post(`/checks/${checkName}/run`);
    }
    
    async getComponentTree() {
        return this.get('/ui-designer/component-tree');
    }
    
    async getArchitectureDiagram() {
        return this.get('/architecture/diagram');
    }
    
    async regenerateArchitecture() {
        return this.post('/architecture/regenerate');
    }
}

// Create global API client instance
window.apiClient = new APIClient();
