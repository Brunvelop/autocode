// CLI Adapter - Converts CLI wrapper responses to UI-compatible format
// This adapter bridges the gap between simple CLI responses and rich UI data

export class CLIAdapter {
    /**
     * Convert CLI response to check result format expected by UI
     * @param {Object} cliResponse - Response from CLI wrapper endpoint
     * @param {string} checkName - Name of the check (doc_check, git_check, test_check)
     * @returns {Object} UI-compatible check result
     */
    static adaptCheckResult(cliResponse, checkName) {
        if (!cliResponse) {
            return {
                status: 'error',
                message: 'No response from CLI',
                timestamp: new Date().toISOString(),
                details: null
            };
        }
        
        if (cliResponse.success) {
            return {
                status: 'success',
                message: `${checkName.replace('_', ' ')} completed successfully`,
                timestamp: new Date().toISOString(),
                details: cliResponse.result || null
            };
        } else {
            return {
                status: 'error', 
                message: cliResponse.error || 'Unknown error occurred',
                timestamp: new Date().toISOString(),
                details: null
            };
        }
    }
    
    /**
     * Simulate daemon status based on health check
     * Since we don't have a real daemon, we simulate status based on API availability
     * @param {APIClient} apiClient - API client instance
     * @returns {Object} Daemon status object
     */
    static async getDaemonStatus(apiClient) {
        try {
            const health = await apiClient.get('/health');
            return {
                is_running: health.status === 'healthy',
                uptime_seconds: 0, // Not available without real daemon
                total_checks_run: this.getTotalChecksFromCache(),
                last_check_run: this.getLastCheckFromCache()
            };
        } catch (error) {
            return {
                is_running: false,
                uptime_seconds: 0,
                total_checks_run: 0,
                last_check_run: null
            };
        }
    }
    
    /**
     * Simulate config data structure
     * @param {Object} configData - Raw config from load endpoint
     * @returns {Object} UI-compatible config structure
     */
    static adaptConfigData(configData) {
        // If configData is already in the expected format, return as-is
        if (configData && configData.daemon && configData.api) {
            return configData;
        }
        
        // Otherwise, provide defaults
        return {
            daemon: {
                doc_check: {
                    enabled: true,
                    interval_minutes: 30
                },
                git_check: {
                    enabled: true,
                    interval_minutes: 15
                },
                test_check: {
                    enabled: true,
                    interval_minutes: 45
                },
                token_alerts: {
                    enabled: true,
                    threshold: 50000,
                    model: "gpt-4"
                }
            },
            api: {
                host: "127.0.0.1",
                port: 8080
            },
            // Add any additional config sections from configData
            ...configData
        };
    }
    
    /**
     * Create fake status response structure expected by UI
     * @param {Object} daemonStatus - Daemon status object
     * @param {Object} cachedChecks - Cached check results
     * @returns {Object} Status response structure
     */
    static createStatusResponse(daemonStatus, cachedChecks = {}) {
        return {
            daemon: daemonStatus,
            checks: {
                doc_check: cachedChecks.doc_check || this.getDefaultCheckResult('doc_check'),
                git_check: cachedChecks.git_check || this.getDefaultCheckResult('git_check'),
                test_check: cachedChecks.test_check || this.getDefaultCheckResult('test_check')
            }
        };
    }
    
    /**
     * Get default check result for a specific check type
     * @param {string} checkName - Name of the check
     * @returns {Object} Default check result
     */
    static getDefaultCheckResult(checkName) {
        const checkDisplayName = checkName.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
        
        return {
            status: 'unknown',
            message: `${checkDisplayName} not run yet. Click 'Run Check' to execute.`,
            timestamp: new Date().toISOString(),
            details: null
        };
    }
    
    /**
     * Extract Mermaid content from Markdown text
     * @param {string} markdown - Markdown content
     * @returns {string|null} Mermaid diagram content
     */
    static extractMermaidFromMarkdown(markdown) {
        if (!markdown) return null;
        
        const mermaidMatch = markdown.match(/```mermaid\n(.*?)\n```/s);
        return mermaidMatch ? mermaidMatch[1] : null;
    }
    
    /**
     * Extract project summary from design Markdown
     * @param {string} markdown - Markdown content
     * @returns {string} Project summary
     */
    static extractSummaryFromMarkdown(markdown) {
        if (!markdown) return "Architecture diagram";
        
        const summaryMatch = markdown.match(/\*\*Project Summary:\*\* (.+)/);
        return summaryMatch ? summaryMatch[1] : "Architecture diagram generated by autocode";
    }
    
    /**
     * Cache management for check results
     */
    static setCachedCheckResult(checkName, result) {
        const cacheKey = `autocode_check_${checkName}`;
        const cacheData = {
            result: result,
            timestamp: Date.now()
        };
        
        try {
            localStorage.setItem(cacheKey, JSON.stringify(cacheData));
            
            // Update total checks counter
            this.incrementTotalChecks();
            
            // Update last check timestamp
            localStorage.setItem('autocode_last_check', new Date().toISOString());
            
        } catch (error) {
            console.warn('Failed to cache check result:', error);
        }
    }
    
    static getCachedCheckResult(checkName) {
        const cacheKey = `autocode_check_${checkName}`;
        
        try {
            const cached = localStorage.getItem(cacheKey);
            if (!cached) return null;
            
            const data = JSON.parse(cached);
            // Cache valid for 5 minutes
            if (Date.now() - data.timestamp < 5 * 60 * 1000) {
                return data.result;
            } else {
                // Remove expired cache
                localStorage.removeItem(cacheKey);
                return null;
            }
        } catch (error) {
            console.warn('Error reading cached result:', error);
            return null;
        }
    }
    
    static getAllCachedCheckResults() {
        const checks = ['doc_check', 'git_check', 'test_check'];
        const results = {};
        
        checks.forEach(checkName => {
            const cached = this.getCachedCheckResult(checkName);
            if (cached) {
                results[checkName] = cached;
            }
        });
        
        return results;
    }
    
    static getTotalChecksFromCache() {
        try {
            const total = localStorage.getItem('autocode_total_checks');
            return total ? parseInt(total, 10) : 0;
        } catch (error) {
            return 0;
        }
    }
    
    static incrementTotalChecks() {
        try {
            const current = this.getTotalChecksFromCache();
            localStorage.setItem('autocode_total_checks', (current + 1).toString());
        } catch (error) {
            console.warn('Failed to increment total checks:', error);
        }
    }
    
    static getLastCheckFromCache() {
        try {
            const lastCheck = localStorage.getItem('autocode_last_check');
            return lastCheck || null;
        } catch (error) {
            return null;
        }
    }
    
    /**
     * Clear all cached data (useful for development/debugging)
     */
    static clearCache() {
        const keys = Object.keys(localStorage).filter(key => key.startsWith('autocode_'));
        keys.forEach(key => localStorage.removeItem(key));
        console.log('Autocode cache cleared');
    }
}
