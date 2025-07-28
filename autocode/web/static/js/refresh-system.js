// Refresh System - Auto-refresh + Activity detection
// Manages intelligent refresh intervals and user activity

import { apiClient } from './api-client.js';
import { updateRefreshStatus } from './utilities.js';

export class RefreshSystem {
    constructor() {
        // Multiple refresh configurations for different data types
        this.refreshConfig = {
            daemon_status: { interval: 3000, timer: null, enabled: true },    // 3s - critical
            check_results: { interval: 10000, timer: null, enabled: true },   // 10s - normal
            config_data: { interval: 30000, timer: null, enabled: true },     // 30s - slow
            design_data: { interval: 60000, timer: null, enabled: false }     // 60s - on demand
        };
        
        this.isLoading = {};
        this.lastUpdate = {};
        this.updatePaused = false;
        
        // Activity detection
        this.userActivityTimer = null;
        this.inactivityTimeout = 60000; // 1 minute of inactivity
        this.wasActiveRefresh = true;
        
        this.setupActivityDetection();
    }

    // === MAIN REFRESH CONTROL ===
    
    start() {
        Object.keys(this.refreshConfig).forEach(dataType => {
            this.startSpecificRefresh(dataType);
        });
        
        updateRefreshStatus('MULTI-ON');
        console.log('Auto-refresh system started');
    }
    
    pause() {
        this.updatePaused = true;
        Object.keys(this.refreshConfig).forEach(dataType => {
            this.stopSpecificRefresh(dataType);
        });
        updateRefreshStatus('PAUSED');
        console.log('Auto-refresh paused');
    }
    
    resume() {
        this.updatePaused = false;
        this.start();
        console.log('Auto-refresh resumed');
    }
    
    stop() {
        Object.keys(this.refreshConfig).forEach(dataType => {
            this.stopSpecificRefresh(dataType);
        });
        updateRefreshStatus('OFF');
        console.log('Auto-refresh stopped');
    }
    
    toggle() {
        if (this.updatePaused) {
            this.resume();
        } else {
            this.pause();
        }
    }

    // === SPECIFIC DATA TYPE REFRESH ===
    
    startSpecificRefresh(dataType) {
        const config = this.refreshConfig[dataType];
        
        if (!config.enabled || config.timer || this.updatePaused) {
            return;
        }
        
        config.timer = setInterval(async () => {
            if (this.isLoading[dataType]) {
                return;
            }
            
            try {
                await this.refreshSpecificData(dataType);
            } catch (error) {
                console.error(`Error refreshing ${dataType}:`, error);
            }
        }, config.interval);
        
        console.log(`Started auto-refresh for ${dataType} (${config.interval}ms)`);
    }
    
    stopSpecificRefresh(dataType) {
        const config = this.refreshConfig[dataType];
        if (config.timer) {
            clearInterval(config.timer);
            config.timer = null;
        }
    }
    
    async refreshSpecificData(dataType) {
        this.isLoading[dataType] = true;
        
        try {
            switch (dataType) {
                case 'daemon_status':
                    await this.refreshDaemonStatus();
                    break;
                case 'check_results':
                    await this.refreshCheckResults();
                    break;
                case 'config_data':
                    await this.refreshConfigData();
                    break;
                case 'design_data':
                    await this.refreshDesignContent();
                    break;
            }
            
            this.lastUpdate[dataType] = new Date();
            
        } finally {
            this.isLoading[dataType] = false;
        }
    }

    // === REFRESH DATA METHODS ===
    
    async refreshDaemonStatus() {
        try {
            const statusData = await apiClient.getStatus();
            
            // Emit event for dashboard to update
            window.dispatchEvent(new CustomEvent('daemonStatusUpdate', {
                detail: statusData.daemon
            }));
        } catch (error) {
            console.error('Error refreshing daemon status:', error);
            
            // Emit fallback status on error
            window.dispatchEvent(new CustomEvent('daemonStatusUpdate', {
                detail: {
                    is_running: false,
                    uptime_seconds: 0,
                    total_checks_run: 0,
                    last_check_run: null
                }
            }));
        }
    }
    
    async refreshCheckResults() {
        const checks = ['doc_check', 'git_check', 'test_check'];
        
        // Use Promise.allSettled to handle individual failures gracefully
        const checkPromises = checks.map(async (checkName) => {
            try {
                const result = await apiClient.getCheckResult(checkName);
                return { checkName, result, success: true };
            } catch (error) {
                console.error(`Failed to get result for ${checkName}:`, error);
                return { 
                    checkName, 
                    result: {
                        status: 'error',
                        message: `Failed to get ${checkName} result`,
                        timestamp: new Date().toISOString(),
                        details: null
                    }, 
                    success: false 
                };
            }
        });
        
        try {
            const results = await Promise.allSettled(checkPromises);
            
            results.forEach((result) => {
                if (result.status === 'fulfilled') {
                    const { checkName, result: checkResult } = result.value;
                    
                    // Emit event for dashboard to update
                    window.dispatchEvent(new CustomEvent('checkResultUpdate', {
                        detail: { checkName, result: checkResult }
                    }));
                } else {
                    console.error('Failed to process check result:', result.reason);
                }
            });
            
        } catch (error) {
            console.error('Error refreshing check results:', error);
        }
    }
    
    async refreshConfigData() {
        if (this.getCurrentPage() === 'config') {
            try {
                const configData = await apiClient.loadConfigurationData();
                
                // Emit event for config manager to update
                window.dispatchEvent(new CustomEvent('configDataUpdate', {
                    detail: configData
                }));
            } catch (error) {
                console.error('Error refreshing config data:', error);
                
                // Emit default config on error
                const { CLIAdapter } = await import('./utils/cli-adapter.js');
                window.dispatchEvent(new CustomEvent('configDataUpdate', {
                    detail: CLIAdapter.adaptConfigData({})
                }));
            }
        }
    }
    
    async refreshDesignContent() {
        if (this.getCurrentPage() === 'design' || this.getCurrentPage() === 'ui-designer') {
            try {
                // Check if design files are available by trying to fetch architecture diagram
                await apiClient.getArchitectureDiagram();
                
                // Emit event for design content refresh
                window.dispatchEvent(new CustomEvent('designContentUpdate'));
            } catch (error) {
                // Silent failure - design content may not be generated yet
                console.log('Design content not available for refresh:', error.message);
            }
        }
    }

    // === CONFIGURATION METHODS ===
    
    setRefreshInterval(dataType, newInterval) {
        const config = this.refreshConfig[dataType];
        const wasRunning = config.timer !== null;
        
        // Stop current timer
        this.stopSpecificRefresh(dataType);
        
        // Update interval
        config.interval = newInterval;
        
        // Restart if was running
        if (wasRunning && config.enabled) {
            this.startSpecificRefresh(dataType);
        }
        
        console.log(`Updated refresh interval for ${dataType}: ${newInterval}ms`);
    }
    
    toggleRefreshForDataType(dataType, enabled = null) {
        const config = this.refreshConfig[dataType];
        config.enabled = enabled !== null ? enabled : !config.enabled;
        
        if (config.enabled) {
            this.startSpecificRefresh(dataType);
        } else {
            this.stopSpecificRefresh(dataType);
        }
        
        console.log(`Refresh for ${dataType}: ${config.enabled ? 'enabled' : 'disabled'}`);
    }

    // === ACTIVITY DETECTION SYSTEM ===
    
    setupActivityDetection() {
        // Events that indicate user activity
        const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
        
        activityEvents.forEach(event => {
            document.addEventListener(event, () => {
                this.handleUserActivity();
            }, true);
        });
        
        // Page visibility detection
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.handlePageHidden();
            } else {
                this.handlePageVisible();
            }
        });
    }
    
    handleUserActivity() {
        // Reset inactivity timer
        clearTimeout(this.userActivityTimer);
        
        // Resume refresh if was paused due to inactivity
        if (this.updatePaused && !this.wasActiveRefresh) {
            this.resume();
            this.wasActiveRefresh = true;
        }
        
        // Set new inactivity timer
        this.userActivityTimer = setTimeout(() => {
            this.handleUserInactivity();
        }, this.inactivityTimeout);
    }
    
    async handleUserInactivity() {
        console.log('User inactive, slowing down refresh...');
        
        // Slow down refresh instead of stopping completely
        this.setRefreshInterval('daemon_status', 10000); // 10s instead of 3s
        this.setRefreshInterval('check_results', 30000);  // 30s instead of 10s
        
        // Show notification about slowed refresh
        const { showNotification } = await import('./utilities.js');
        showNotification('Slowed refresh due to inactivity', 'info', 3000);
    }
    
    handlePageHidden() {
        console.log('Page hidden, pausing refresh...');
        this.pause();
        this.wasActiveRefresh = false;
    }
    
    handlePageVisible() {
        console.log('Page visible, resuming refresh...');
        this.resume();
        this.wasActiveRefresh = true;
        
        // Immediately refresh to get latest data
        this.refreshAll();
    }

    // === UTILITY METHODS ===
    
    getCurrentPage() {
        const path = window.location.pathname;
        if (path === '/ui-designer') return 'ui-designer';
        if (path === '/design') return 'design';
        if (path === '/config') return 'config';
        return 'dashboard';
    }
    
    async refreshAll() {
        console.log('Refreshing all data...');
        
        const refreshPromises = Object.keys(this.refreshConfig).map(dataType => {
            if (this.refreshConfig[dataType].enabled) {
                return this.refreshSpecificData(dataType);
            }
            return Promise.resolve();
        });
        
        try {
            await Promise.allSettled(refreshPromises);
            console.log('All data refreshed successfully');
        } catch (error) {
            console.error('Error refreshing all data:', error);
        }
    }
    
    getRefreshStatus() {
        const enabledTypes = Object.keys(this.refreshConfig).filter(
            type => this.refreshConfig[type].enabled
        );
        
        return {
            isPaused: this.updatePaused,
            enabledTypes,
            lastUpdate: this.lastUpdate,
            isLoading: this.isLoading
        };
    }
}
