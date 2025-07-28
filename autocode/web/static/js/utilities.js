// Utilities - Formatters + Notifications + DOM helpers
// Pure functions and UI helpers

// === FORMATTING FUNCTIONS ===

export function formatDuration(seconds) {
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

export function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

export function formatGitDetails(details) {
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

export function formatTestDetails(details) {
    let output = `Test Status:\n`;
    output += `  Total tests: ${details.total_tests || 0}\n`;
    output += `  Missing: ${details.missing_count || 0}\n`;
    output += `  Passing: ${details.passing_count || 0}\n`;
    output += `  Failing: ${details.failing_count || 0}\n`;
    output += `  Orphaned: ${details.orphaned_count || 0}\n`;
    
    output += `\nTest Types:\n`;
    output += `  Unit tests: ${details.unit_tests || 0}\n`;
    output += `  Integration tests: ${details.integration_tests || 0}\n`;
    
    if (details.execution_results) {
        output += `\nExecution Results:\n`;
        output += `  Exit code: ${details.execution_results.exit_code}\n`;
        if (details.execution_results.stdout) {
            output += `  Output: ${details.execution_results.stdout.substring(0, 200)}...\n`;
        }
    }
    
    if (details.execution_error) {
        output += `\nExecution Error: ${details.execution_error}\n`;
    }
    
    return output;
}

// === NOTIFICATION SYSTEM ===

export function showNotification(message, type = 'info', duration = 5000) {
    const notificationContainer = getOrCreateNotificationContainer();
    
    const notification = document.createElement('div');
    notification.className = `notification ${type} animate-slide-in`;
    
    const bgColor = {
        'success': 'bg-green-50 border-green-200 text-green-800',
        'error': 'bg-red-50 border-red-200 text-red-800',
        'warning': 'bg-yellow-50 border-yellow-200 text-yellow-800',
        'info': 'bg-blue-50 border-blue-200 text-blue-800'
    }[type] || 'bg-gray-50 border-gray-200 text-gray-800';
    
    notification.innerHTML = `
        <div class="flex items-center justify-between p-4 border rounded-lg ${bgColor}">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" 
                    class="ml-4 text-sm opacity-70 hover:opacity-100">×</button>
        </div>
    `;
    
    notificationContainer.appendChild(notification);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (notification.parentElement) {
            notification.classList.add('animate-slide-out');
            setTimeout(() => notification.remove(), 300);
        }
    }, duration);
}

function getOrCreateNotificationContainer() {
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
    }
    return container;
}

// === DOM HELPERS ===

export function setLoadingState(isLoading, target = null) {
    if (target) {
        const element = typeof target === 'string' ? document.getElementById(target) : target;
        if (element) {
            if (isLoading) {
                element.classList.add('loading');
                element.style.opacity = '0.6';
            } else {
                element.classList.remove('loading');
                element.style.opacity = '1';
            }
        }
    } else {
        // Global loading state indicator
        const indicator = document.getElementById('global-loading-indicator');
        if (indicator) {
            indicator.style.display = isLoading ? 'block' : 'none';
        }
    }
}

export function updateElement(id, content, attribute = 'textContent') {
    const element = document.getElementById(id);
    if (element) {
        if (attribute === 'className') {
            element.className = content;
        } else if (attribute === 'innerHTML') {
            element.innerHTML = content;
        } else {
            element[attribute] = content;
        }
    }
}

export function toggleElementVisibility(id, show) {
    const element = document.getElementById(id);
    if (element) {
        if (show) {
            element.classList.remove('hidden');
            element.style.display = '';
        } else {
            element.classList.add('hidden');
            element.style.display = 'none';
        }
    }
}

// === FORM HELPERS ===

export function getCheckboxValue(id) {
    const element = document.getElementById(id);
    return element ? element.checked : false;
}

export function setCheckboxValue(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.checked = value;
    }
}

export function getInputValue(id) {
    const element = document.getElementById(id);
    return element ? element.value : '';
}

export function setInputValue(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.value = value;
    }
}

export function getNumberValue(id) {
    const element = document.getElementById(id);
    return element ? parseInt(element.value) || 0 : 0;
}

export function setTextareaValue(id, value) {
    const element = document.getElementById(id);
    if (element && Array.isArray(value)) {
        element.value = value.join('\n');
    }
}

export function getTextareaArrayValue(id) {
    const element = document.getElementById(id);
    if (!element) return [];
    return element.value.split('\n').filter(line => line.trim() !== '');
}

// === TIME HELPERS ===

export function updateLastUpdated() {
    const lastUpdatedElement = document.getElementById('last-updated');
    if (lastUpdatedElement) {
        lastUpdatedElement.textContent = new Date().toLocaleTimeString();
    }
}

export function updateRefreshStatus(status) {
    const refreshStatusElement = document.getElementById('auto-refresh-status');
    if (refreshStatusElement) {
        refreshStatusElement.textContent = status;
    }
}
