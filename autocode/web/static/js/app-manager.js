// App Manager - Main coordinator
// Orchestrates all modules and provides unified interface

import { apiClient } from './api-client.js';
import { DashboardCore } from './dashboard-core.js';
import { RefreshSystem } from './refresh-system.js';
import { setLoadingState, updateLastUpdated } from './utilities.js';

export class AppManager {
    constructor() {
        this.apiClient = apiClient;
        this.dashboardCore = new DashboardCore();
        this.refreshSystem = new RefreshSystem();
        
        this.currentPage = this.getCurrentPage();
        this.isInitialized = false;
    }

    // === INITIALIZATION ===
    
    async init() {
        console.log('Initializing Autocode Dashboard');
        
        try {
            this.setupNavigation();
            await this.loadInitialData();
            this.refreshSystem.start();
            
            this.isInitialized = true;
            console.log('Dashboard initialized successfully');
            
        } catch (error) {
            console.error('Error initializing dashboard:', error);
            this.dashboardCore.handleError(error);
        }
    }
    
    getCurrentPage() {
        const path = window.location.pathname;
        if (path === '/ui-designer') return 'ui-designer';
        if (path === '/design') return 'design';
        if (path === '/config') return 'config';
        return 'dashboard';
    }
    
    setupNavigation() {
        // Update active nav link
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === window.location.pathname) {
                link.classList.add('active');
            }
        });
    }
    
    async loadInitialData() {
        setLoadingState(true);
        
        try {
            if (this.currentPage === 'dashboard') {
                await this.loadDashboardData();
            } else if (this.currentPage === 'config') {
                await this.dashboardCore.loadConfigPage();
            } else if (this.currentPage === 'design') {
                await this.dashboardCore.loadArchitectureDiagram();
            }
            
        } finally {
            setLoadingState(false);
            updateLastUpdated();
        }
    }
    
    async loadDashboardData() {
        try {
            // Load status data first
            const statusData = await this.apiClient.getStatus();
            this.dashboardCore.updateDaemonStatus(statusData.daemon);
            this.dashboardCore.updateSystemStats(statusData.daemon);
            
            // Load config data
            const configData = await this.apiClient.getConfig();
            this.dashboardCore.updateConfigUI(configData);
            
            // Load check results
            const checks = ['doc_check', 'git_check', 'test_check'];
            const checkPromises = checks.map(checkName => 
                this.apiClient.getCheckResult(checkName)
            );
            
            const results = await Promise.allSettled(checkPromises);
            results.forEach((result, index) => {
                const checkName = checks[index];
                if (result.status === 'fulfilled') {
                    this.dashboardCore.updateCheckCard(checkName, result.value);
                } else {
                    console.error(`Failed to load ${checkName}:`, result.reason);
                    // Show default check result on error
                    this.dashboardCore.updateCheckCard(checkName, {
                        status: 'unknown',
                        message: `${checkName.replace('_', ' ')} not run yet`,
                        timestamp: new Date().toISOString(),
                        details: null
                    });
                }
            });
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.dashboardCore.handleError(error);
        }
    }

    // === GLOBAL ACTION HANDLERS ===
    // These methods are exposed to the global scope for HTML template compatibility
    
    async runCheck(checkName) {
        console.log(`Running check: ${checkName}`);
        
        try {
            // Use the unified runCheck method from apiClient
            // which handles CLI wrapper mapping and caching
            const result = await this.apiClient.runCheck(checkName);
            
            // Update UI immediately with result
            this.dashboardCore.updateCheckCard(checkName, result);
            
            if (result.status === 'success') {
                console.log(`Check ${checkName} executed successfully`);
            } else if (result.status === 'error') {
                console.error(`Check ${checkName} failed:`, result.message);
            }
            
            // Auto-refresh to get any updated data
            setTimeout(() => {
                this.refreshSystem.refreshSpecificData('check_results');
            }, 2000);
            
            return result;
            
        } catch (error) {
            console.error(`Error running check ${checkName}:`, error);
            
            // Create error result and update UI
            const errorResult = {
                status: 'error',
                message: `Failed to execute ${checkName}: ${error.message}`,
                timestamp: new Date().toISOString(),
                details: null
            };
            
            this.dashboardCore.updateCheckCard(checkName, errorResult);
            throw error;
        }
    }
    
    async generateDesign(options = {}) {
        try {
            const result = await this.apiClient.generateDesign({
                directory: 'autocode/',
                output_dir: 'design/',
                ...options
            });
            
            // Auto-refresh design content after generation
            setTimeout(() => {
                this.refreshSystem.refreshSpecificData('design_data');
            }, 3000);
            
            return result;
            
        } catch (error) {
            console.error('Error generating design:', error);
            throw error;
        }
    }
    
    async updateConfig(config = null) {
        try {
            // If no config provided, get from form
            const configToUpdate = config || this.dashboardCore.getConfigFromForm();
            
            const result = await this.apiClient.updateConfig(configToUpdate);
            console.log('Configuration updated:', result);
            
            // Refresh config data
            setTimeout(() => {
                this.refreshSystem.refreshSpecificData('config_data');
            }, 1000);
            
            return result;
            
        } catch (error) {
            console.error('Error updating configuration:', error);
            throw error;
        }
    }

    // === ARCHITECTURE DIAGRAM HANDLERS ===
    
    async refreshArchitecture() {
        try {
            // Use the updated method that loads from static files
            await this.dashboardCore.loadArchitectureDiagram();
            console.log('Architecture diagram refreshed successfully');
            return { success: true };
            
        } catch (error) {
            console.error('Error refreshing architecture diagram:', error);
            this.dashboardCore.handleArchitectureError(error);
            throw error;
        }
    }
    
    async regenerateArchitecture() {
        try {
            console.log('Regenerating architecture diagram...');
            const result = await this.apiClient.regenerateArchitecture();
            console.log('Architecture regeneration started:', result);
            
            if (result.success) {
                // Wait for regeneration to complete, then refresh
                setTimeout(async () => {
                    try {
                        await this.dashboardCore.loadArchitectureDiagram();
                    } catch (error) {
                        console.error('Error refreshing after regeneration:', error);
                    }
                }, 3000);
            }
            
            return result;
            
        } catch (error) {
            console.error('Error regenerating architecture diagram:', error);
            this.dashboardCore.handleArchitectureError(error);
            throw error;
        }
    }

    // === COMPONENT TREE HANDLERS ===
    
    async generateComponentTree() {
        try {
            console.log('Generating component tree...');
            const result = await this.apiClient.getComponentTree();
            
            if (result.status === 'success') {
                this.dashboardCore.renderComponentTree(result);
                console.log('Component tree generated successfully');
            } else {
                throw new Error(result.error || 'Unknown error generating component tree');
            }
            
            return result;
            
        } catch (error) {
            console.error('Error generating component tree:', error);
            this.dashboardCore.handleComponentTreeError(error);
            throw error;
        }
    }
    
    async refreshComponentTree() {
        try {
            console.log('Refreshing component tree...');
            const result = await this.apiClient.getComponentTree();
            
            if (result.status === 'success') {
                this.dashboardCore.renderComponentTree(result);
                console.log('Component tree refreshed successfully');
            } else {
                throw new Error(result.error || 'Unknown error refreshing component tree');
            }
            
            return result;
            
        } catch (error) {
            console.error('Error refreshing component tree:', error);
            this.dashboardCore.handleComponentTreeError(error);
            throw error;
        }
    }

    // === REFRESH CONTROL METHODS ===
    
    toggleAutoRefresh() {
        this.refreshSystem.toggle();
        
        const button = document.getElementById('pause-refresh-btn');
        if (button) {
            if (this.refreshSystem.updatePaused) {
                button.textContent = 'Resume';
            } else {
                button.textContent = 'Pause';
            }
        }
    }
    
    changeRefreshSpeed(speed) {
        const intervals = {
            'fast': { daemon_status: 2000, check_results: 5000 },
            'normal': { daemon_status: 3000, check_results: 10000 },
            'slow': { daemon_status: 5000, check_results: 20000 }
        };
        
        const config = intervals[speed];
        if (config) {
            Object.keys(config).forEach(dataType => {
                this.refreshSystem.setRefreshInterval(dataType, config[dataType]);
            });
            
            console.log(`Refresh speed changed to ${speed}`);
        }
    }

    // === CLEANUP ===
    
    destroy() {
        console.log('Destroying dashboard...');
        this.refreshSystem.stop();
        this.isInitialized = false;
    }

    // === UTILITY METHODS ===
    
    getStatus() {
        return {
            isInitialized: this.isInitialized,
            currentPage: this.currentPage,
            refreshStatus: this.refreshSystem.getRefreshStatus()
        };
    }
}
