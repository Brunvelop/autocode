// Autocode Dashboard - Entry Point
// Modular architecture with ES6 imports

import { AppManager } from './js/app-manager.js';

// Global app manager instance
let appManager;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    appManager = new AppManager();
    appManager.init();
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Space bar to refresh all data
        if (event.code === 'Space' && event.target.tagName !== 'INPUT') {
            event.preventDefault();
            appManager.refreshSystem.refreshAll();
        }
        
        // 'R' to toggle auto-refresh
        if (event.code === 'KeyR' && event.target.tagName !== 'INPUT') {
            event.preventDefault();
            appManager.toggleAutoRefresh();
        }
    });
    
    // Handle visibility changes for page switching
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            appManager.refreshSystem.pause();
        } else {
            appManager.refreshSystem.resume();
        }
    });
});

// Handle page unload cleanup
window.addEventListener('beforeunload', function() {
    if (appManager) {
        appManager.destroy();
    }
});

// === GLOBAL FUNCTIONS FOR HTML TEMPLATE COMPATIBILITY ===
// These functions are called directly from HTML templates

window.runCheck = async function(checkName) {
    if (!appManager) {
        console.error('App manager not initialized');
        return;
    }
    
    const button = event.target;
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Running...';
    
    try {
        const result = await appManager.runCheck(checkName);
        return result;
    } catch (error) {
        console.error(`Error in global runCheck for ${checkName}:`, error);
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
};

window.generateDesign = async function() {
    if (!appManager) {
        console.error('App manager not initialized');
        return;
    }
    
    const button = event.target;
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Generating...';
    
    try {
        const result = await appManager.generateDesign();
        return result;
    } catch (error) {
        console.error('Error in global generateDesign:', error);
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
};

window.updateConfig = async function() {
    if (!appManager) {
        console.error('App manager not initialized');
        return;
    }
    
    try {
        const result = await appManager.updateConfig();
        return result;
    } catch (error) {
        console.error('Error in global updateConfig:', error);
    }
};

window.toggleAutoRefresh = function() {
    if (!appManager) {
        console.error('App manager not initialized');
        return;
    }
    
    appManager.toggleAutoRefresh();
};

window.changeRefreshSpeed = function(speed) {
    if (!appManager) {
        console.error('App manager not initialized');
        return;
    }
    
    appManager.changeRefreshSpeed(speed);
};

// === ARCHITECTURE DIAGRAM FUNCTIONS ===

window.refreshArchitecture = async function() {
    if (!appManager) {
        console.error('App manager not initialized');
        return;
    }
    
    const button = event.target;
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Loading...';
    
    try {
        const result = await appManager.refreshArchitecture();
        return result;
    } catch (error) {
        console.error('Error in global refreshArchitecture:', error);
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
};

window.regenerateArchitecture = async function() {
    if (!appManager) {
        console.error('App manager not initialized');
        return;
    }
    
    const button = event.target;
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Regenerating...';
    
    try {
        const result = await appManager.regenerateArchitecture();
        return result;
    } catch (error) {
        console.error('Error in global regenerateArchitecture:', error);
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
};

// === COMPONENT TREE FUNCTIONS ===

window.generateComponentTree = async function() {
    if (!appManager) {
        console.error('App manager not initialized');
        return;
    }
    
    const button = event.target;
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Generating...';
    
    try {
        const result = await appManager.generateComponentTree();
        return result;
    } catch (error) {
        console.error('Error in global generateComponentTree:', error);
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
};

window.refreshComponentTree = async function() {
    if (!appManager) {
        console.error('App manager not initialized');
        return;
    }
    
    const button = event.target;
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Refreshing...';
    
    try {
        const result = await appManager.refreshComponentTree();
        return result;
    } catch (error) {
        console.error('Error in global refreshComponentTree:', error);
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
};

console.log('Autocode Dashboard loaded - Modular ES6 architecture');
