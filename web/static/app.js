// Autocode Monitoring Dashboard JavaScript

class AutocodeDashboard {
    constructor() {
        this.refreshInterval = 5000; // 5 seconds
        this.refreshTimer = null;
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        console.log('Initializing Autocode Dashboard');
        this.startAutoRefresh();
        this.loadInitialData();
    }
    
    async loadInitialData() {
        await this.fetchAndUpdateStatus();
        await this.fetchAndUpdateConfig();
    }
    
    startAutoRefresh() {
        this.refreshTimer = setInterval(() => {
            if (!this.isLoading) {
                this.fetchAndUpdateStatus();
            }
        }, this.refreshInterval);
        
        this.updateRefreshStatus('ON');
    }
    
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
        this.updateRefreshStatus('OFF');
    }
    
    async fetchAndUpdateStatus() {
        try {
            this.isLoading = true;
            const response = await fetch('/api/status');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.updateUI(data);
            this.updateLastUpdated();
            
        } catch (error) {
            console.error('Error fetching status:', error);
            this.handleError(error);
        } finally {
            this.isLoading = false;
        }
    }
    
    async fetchAndUpdateConfig() {
        try {
            const response = await fetch('/api/config');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const config = await response.json();
            this.updateConfigUI(config);
            
        } catch (error) {
            console.error('Error fetching config:', error);
        }
    }
    
    updateUI(data) {
        // Update daemon status
        this.updateDaemonStatus(data.daemon);
        
        // Update system stats
        this.updateSystemStats(data.daemon);
        
        // Update check results
        this.updateCheckResults(data.checks);
    }
    
    updateDaemonStatus(daemon) {
        const indicator = document.getElementById('daemon-indicator');
        const text = document.getElementById('daemon-text');
        
        if (daemon.is_running) {
            indicator.className = 'status-indicator success';
            text.textContent = 'Running';
        } else {
            indicator.className = 'status-indicator error';
            text.textContent = 'Stopped';
        }
    }
    
    updateSystemStats(daemon) {
        // Update uptime
        const uptimeElement = document.getElementById('uptime');
        if (daemon.uptime_seconds) {
            uptimeElement.textContent = this.formatDuration(daemon.uptime_seconds);
        } else {
            uptimeElement.textContent = '--';
        }
        
        // Update total checks
        const totalChecksElement = document.getElementById('total-checks');
        totalChecksElement.textContent = daemon.total_checks_run || 0;
        
        // Update last check
        const lastCheckElement = document.getElementById('last-check');
        if (daemon.last_check_run) {
            lastCheckElement.textContent = this.formatTimestamp(daemon.last_check_run);
        } else {
            lastCheckElement.textContent = '--';
        }
    }
    
    updateCheckResults(checks) {
        for (const [checkName, result] of Object.entries(checks)) {
            this.updateCheckCard(checkName, result);
        }
    }
    
    updateCheckCard(checkName, result) {
        const card = document.getElementById(checkName.replace('_', '-'));
        if (!card) return;
        
        // Update status indicator
        const statusElement = card.querySelector('.check-status');
        const indicator = statusElement.querySelector('.status-indicator');
        const statusText = statusElement.querySelector('.status-text');
        
        indicator.className = `status-indicator ${result.status}`;
        statusText.textContent = result.status;
        
        // Update card border
        card.className = `check-card ${result.status}`;
        
        // Update message
        const messageElement = card.querySelector('.check-message');
        messageElement.textContent = result.message;
        
        // Update timestamp
        const timestampElement = card.querySelector('.check-timestamp');
        timestampElement.textContent = `Last run: ${this.formatTimestamp(result.timestamp)}`;
        
        // Update details
        const detailsElement = card.querySelector('.check-details-content');
        if (result.details) {
            if (checkName === 'doc_check' && result.details.formatted_output) {
                detailsElement.textContent = result.details.formatted_output;
            } else if (checkName === 'git_check' && result.details.repository_status) {
                detailsElement.textContent = this.formatGitDetails(result.details);
            } else {
                detailsElement.textContent = JSON.stringify(result.details, null, 2);
            }
        } else {
            detailsElement.textContent = 'No details available';
        }
    }
    
    updateConfigUI(config) {
        // Update doc check config
        const docCheckEnabled = document.getElementById('doc-check-enabled');
        const docCheckInterval = document.getElementById('doc-check-interval');
        
        docCheckEnabled.checked = config.daemon.doc_check.enabled;
        docCheckInterval.value = config.daemon.doc_check.interval_minutes;
        
        // Update git check config
        const gitCheckEnabled = document.getElementById('git-check-enabled');
        const gitCheckInterval = document.getElementById('git-check-interval');
        
        gitCheckEnabled.checked = config.daemon.git_check.enabled;
        gitCheckInterval.value = config.daemon.git_check.interval_minutes;
    }
    
    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }
    
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString();
    }
    
    formatGitDetails(details) {
        const status = details.repository_status;
        const files = details.modified_files || [];
        
        let output = `Repository Status:\n`;
        output += `  Total files: ${status.total_files}\n`;
        output += `  Modified: ${status.modified}\n`;
        output += `  Added: ${status.added}\n`;
        output += `  Deleted: ${status.deleted}\n`;
        output += `  Untracked: ${status.untracked}\n`;
        
        if (files.length > 0) {
            output += `\nModified files:\n`;
            files.forEach(file => {
                output += `  - ${file}\n`;
            });
        }
        
        return output;
    }
    
    updateLastUpdated() {
        const lastUpdatedElement = document.getElementById('last-updated');
        lastUpdatedElement.textContent = new Date().toLocaleTimeString();
    }
    
    updateRefreshStatus(status) {
        const refreshStatusElement = document.getElementById('auto-refresh-status');
        refreshStatusElement.textContent = status;
    }
    
    handleError(error) {
        console.error('Dashboard error:', error);
        
        // Update daemon status to error
        const indicator = document.getElementById('daemon-indicator');
        const text = document.getElementById('daemon-text');
        
        indicator.className = 'status-indicator error';
        text.textContent = 'Connection Error';
        
        // Show error in system stats
        document.getElementById('uptime').textContent = 'Error';
        document.getElementById('total-checks').textContent = 'Error';
        document.getElementById('last-check').textContent = 'Error';
    }
}

// Global functions for button clicks
async function runCheck(checkName) {
    console.log(`Running check: ${checkName}`);
    
    // Disable button
    const button = event.target;
    button.disabled = true;
    button.textContent = 'Running...';
    
    try {
        const response = await fetch(`/api/checks/${checkName}/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            console.log(`Check ${checkName} executed successfully`);
            // Status will be updated on next refresh
        } else {
            console.error(`Check ${checkName} failed:`, result.error);
        }
        
    } catch (error) {
        console.error(`Error running check ${checkName}:`, error);
        
    } finally {
        // Re-enable button
        button.disabled = false;
        button.textContent = 'Run Now';
        
        // Refresh status immediately
        dashboard.fetchAndUpdateStatus();
    }
}

async function updateConfig() {
    console.log('Updating configuration');
    
    // Get current config values
    const config = {
        daemon: {
            doc_check: {
                enabled: document.getElementById('doc-check-enabled').checked,
                interval_minutes: parseInt(document.getElementById('doc-check-interval').value)
            },
            git_check: {
                enabled: document.getElementById('git-check-enabled').checked,
                interval_minutes: parseInt(document.getElementById('git-check-interval').value)
            }
        },
        api: {
            port: 8080,
            host: "127.0.0.1"
        }
    };
    
    try {
        const response = await fetch('/api/config', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('Configuration updated:', result);
        
    } catch (error) {
        console.error('Error updating configuration:', error);
    }
}

// Initialize dashboard when DOM is loaded
let dashboard;

document.addEventListener('DOMContentLoaded', function() {
    dashboard = new AutocodeDashboard();
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Space bar to refresh
        if (event.code === 'Space' && event.target.tagName !== 'INPUT') {
            event.preventDefault();
            dashboard.fetchAndUpdateStatus();
        }
        
        // 'R' to toggle auto-refresh
        if (event.code === 'KeyR' && event.target.tagName !== 'INPUT') {
            event.preventDefault();
            if (dashboard.refreshTimer) {
                dashboard.stopAutoRefresh();
            } else {
                dashboard.startAutoRefresh();
            }
        }
    });
    
    // Add visibility change handler to pause/resume refresh
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            dashboard.stopAutoRefresh();
        } else {
            dashboard.startAutoRefresh();
        }
    });
});

// Handle page unload
window.addEventListener('beforeunload', function() {
    if (dashboard) {
        dashboard.stopAutoRefresh();
    }
});
