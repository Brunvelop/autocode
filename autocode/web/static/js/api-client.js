// API Client - Updated for CLI wrapper integration
// Only uses available endpoints after thin layer migration

import { CLIAdapter } from './utils/cli-adapter.js';

export class APIClient {
    constructor() {
        this.baseUrl = '';
    }

    // === HTTP BASE METHODS ===
    
    async get(endpoint) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API GET error for ${endpoint}:`, error);
            throw error;
        }
    }
    
    async post(endpoint, data = null) {
        try {
            const options = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            };
            
            if (data) {
                options.body = JSON.stringify(data);
            }
            
            const response = await fetch(endpoint, options);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API POST error for ${endpoint}:`, error);
            throw error;
        }
    }

    // === CLI WRAPPER METHODS ===
    // These methods call the actual available endpoints
    
    async generateDocumentation() {
        try {
            console.log('Generating documentation...');
            const response = await this.post('/api/generate-docs');
            
            if (response.success) {
                const { showNotification } = await import('./utilities.js');
                showNotification('Documentation generation started', 'success');
            } else {
                const { showNotification } = await import('./utilities.js');
                showNotification(`Documentation error: ${response.error}`, 'error');
            }
            
            return response;
            
        } catch (error) {
            console.error('Error generating documentation:', error);
            const { showNotification } = await import('./utilities.js');
            showNotification('Failed to start documentation generation', 'error');
            throw error;
        }
    }
    
    async generateDesign(options = {}) {
        try {
            console.log('Generating design diagrams...');
            
            const params = new URLSearchParams();
            if (options.directory) params.append('directory', options.directory);
            if (options.output_dir) params.append('output_dir', options.output_dir);
            
            const endpoint = `/api/generate-design${params.toString() ? '?' + params.toString() : ''}`;
            const response = await this.post(endpoint);
            
            if (response.success) {
                const { showNotification } = await import('./utilities.js');
                showNotification('Design generation started', 'success');
            } else {
                const { showNotification } = await import('./utilities.js');
                showNotification(`Design error: ${response.error}`, 'error');
            }
            
            return response;
            
        } catch (error) {
            console.error('Error generating design:', error);
            const { showNotification } = await import('./utilities.js');
            showNotification('Failed to start design generation', 'error');
            throw error;
        }
    }
    
    async analyzeGitChanges(options = {}) {
        try {
            console.log('Analyzing git changes...');
            
            const params = new URLSearchParams();
            if (options.output) params.append('output', options.output);
            if (options.verbose) params.append('verbose', options.verbose);
            
            const endpoint = `/api/analyze-git${params.toString() ? '?' + params.toString() : ''}`;
            const response = await this.post(endpoint);
            
            if (response.success) {
                const { showNotification } = await import('./utilities.js');
                showNotification('Git analysis started', 'success');
            } else {
                const { showNotification } = await import('./utilities.js');
                showNotification(`Git analysis error: ${response.error}`, 'error');
            }
            
            return response;
            
        } catch (error) {
            console.error('Error analyzing git changes:', error);
            const { showNotification } = await import('./utilities.js');
            showNotification('Failed to start git analysis', 'error');
            throw error;
        }
    }
    
    async checkTests() {
        try {
            console.log('Checking tests...');
            const response = await this.post('/api/check-tests');
            
            if (response.success) {
                const { showNotification } = await import('./utilities.js');
                showNotification('Test check started', 'success');
            } else {
                const { showNotification } = await import('./utilities.js');
                showNotification(`Test check error: ${response.error}`, 'error');
            }
            
            return response;
            
        } catch (error) {
            console.error('Error checking tests:', error);
            const { showNotification } = await import('./utilities.js');
            showNotification('Failed to start test check', 'error');
            throw error;
        }
    }
    
    async loadConfigurationData() {
        try {
            const response = await this.get('/api/config/load');
            
            if (response.success) {
                return CLIAdapter.adaptConfigData(response.config);
            } else {
                throw new Error(response.error || 'Failed to load configuration');
            }
            
        } catch (error) {
            console.error('Error loading configuration:', error);
            // Return default config if loading fails
            return CLIAdapter.adaptConfigData({});
        }
    }

    // === ADAPTED STATUS & CHECK METHODS ===
    // These methods simulate the old API using CLIAdapter
    
    async getStatus() {
        try {
            // Get daemon status via health check + cache
            const daemonStatus = await CLIAdapter.getDaemonStatus(this);
            
            // Get cached check results
            const cachedChecks = CLIAdapter.getAllCachedCheckResults();
            
            // Create status response structure
            return CLIAdapter.createStatusResponse(daemonStatus, cachedChecks);
            
        } catch (error) {
            console.error('Error getting status:', error);
            
            // Return fallback status
            return CLIAdapter.createStatusResponse({
                is_running: false,
                uptime_seconds: 0,
                total_checks_run: 0,
                last_check_run: null
            });
        }
    }
    
    async getConfig() {
        return await this.loadConfigurationData();
    }
    
    async updateConfig(config) {
        // Note: No PUT /api/config endpoint available in thin layer
        // This is a placeholder - would need CLI wrapper implementation
        const { showNotification } = await import('./utilities.js');
        showNotification('Configuration save not implemented in thin layer', 'warning');
        
        return {
            success: false,
            error: 'Configuration save not available in thin layer API'
        };
    }
    
    async runCheck(checkName) {
        try {
            let response;
            
            // Map check names to appropriate CLI wrappers
            switch (checkName) {
                case 'doc_check':
                    response = await this.generateDocumentation();
                    break;
                case 'git_check':
                    response = await this.analyzeGitChanges();
                    break;
                case 'test_check':
                    response = await this.checkTests();
                    break;
                default:
                    throw new Error(`Unknown check: ${checkName}`);
            }
            
            // Convert CLI response to UI format
            const result = CLIAdapter.adaptCheckResult(response, checkName);
            
            // Cache the result
            CLIAdapter.setCachedCheckResult(checkName, result);
            
            return result;
            
        } catch (error) {
            console.error(`Error running check ${checkName}:`, error);
            const result = CLIAdapter.adaptCheckResult(null, checkName);
            CLIAdapter.setCachedCheckResult(checkName, result);
            return result;
        }
    }
    
    async getCheckResult(checkName) {
        // First try to get from cache
        const cached = CLIAdapter.getCachedCheckResult(checkName);
        if (cached) {
            return cached;
        }
        
        // Return default if no cache
        return CLIAdapter.getDefaultCheckResult(checkName);
    }

    // === ARCHITECTURE & DESIGN METHODS ===
    // Updated to use static files instead of eliminated endpoints
    
    async getArchitectureDiagram() {
        try {
            // Try to load from static files instead of eliminated endpoint
            const response = await fetch('/design/_index.md');
            
            if (!response.ok) {
                throw new Error('Architecture diagram not found. Generate it first with code-to-design.');
            }
            
            const content = await response.text();
            
            return {
                mermaid_content: CLIAdapter.extractMermaidFromMarkdown(content),
                project_summary: CLIAdapter.extractSummaryFromMarkdown(content)
            };
            
        } catch (error) {
            console.error('Error loading architecture diagram:', error);
            throw error;
        }
    }
    
    async regenerateArchitecture() {
        try {
            // Use generate-design CLI wrapper
            const result = await this.generateDesign({
                directory: 'autocode/',
                output_dir: 'design/'
            });
            
            console.log('Architecture regeneration started:', result);
            return result;
            
        } catch (error) {
            console.error('Error regenerating architecture:', error);
            throw error;
        }
    }
    
    async getComponentTree() {
        try {
            // Generate component tree using design generation
            await this.generateDesign({
                directory: 'autocode/web',
                output_dir: 'design/'
            });
            
            // Wait a bit for generation to complete
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Try to load the generated file
            const response = await fetch('/design/autocode/web/_index.md');
            
            if (response.ok) {
                const content = await response.text();
                const mermaidContent = CLIAdapter.extractMermaidFromMarkdown(content);
                
                if (mermaidContent) {
                    return {
                        status: 'success',
                        diagram: mermaidContent,
                        metrics: { 
                            total_components: 0, // Placeholder
                            total_files: 0 
                        }
                    };
                }
            }
            
            throw new Error('No component tree found in generated files');
            
        } catch (error) {
            console.error('Error getting component tree:', error);
            return {
                status: 'error',
                error: error.message,
                diagram: null,
                metrics: { total_components: 0, total_files: 0 }
            };
        }
    }

    // === ADDITIONAL CLI WRAPPERS ===
    
    async executeOpenCode(options = {}) {
        try {
            const response = await this.post('/api/opencode', options);
            
            if (response.success) {
                const { showNotification } = await import('./utilities.js');
                showNotification('OpenCode analysis started', 'success');
            } else {
                const { showNotification } = await import('./utilities.js');
                showNotification(`OpenCode error: ${response.error}`, 'error');
            }
            
            return response;
            
        } catch (error) {
            console.error('Error executing OpenCode:', error);
            throw error;
        }
    }
    
    async countTokens(options = {}) {
        try {
            const response = await this.post('/api/count-tokens', options);
            
            if (response.success) {
                const { showNotification } = await import('./utilities.js');
                showNotification('Token counting started', 'success');
            } else {
                const { showNotification } = await import('./utilities.js');
                showNotification(`Token counting error: ${response.error}`, 'error');
            }
            
            return response;
            
        } catch (error) {
            console.error('Error counting tokens:', error);
            throw error;
        }
    }
}

// Export singleton instance
export const apiClient = new APIClient();
