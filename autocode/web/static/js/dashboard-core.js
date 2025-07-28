// Dashboard Core - UI updates + Configuration + Diagrams
// Handles all dashboard UI logic, configuration forms, and diagram rendering

import { apiClient } from './api-client.js';
import { 
    formatDuration, 
    formatTimestamp, 
    formatGitDetails, 
    formatTestDetails,
    updateElement,
    toggleElementVisibility,
    setCheckboxValue,
    setInputValue,
    setTextareaValue,
    getCheckboxValue,
    getInputValue,
    getNumberValue,
    getTextareaArrayValue,
    setLoadingState
} from './utilities.js';

export class DashboardCore {
    constructor() {
        this.currentPage = this.getCurrentPage();
        this.setupEventListeners();
    }

    getCurrentPage() {
        const path = window.location.pathname;
        if (path === '/ui-designer') return 'ui-designer';
        if (path === '/design') return 'design';
        if (path === '/config') return 'config';
        return 'dashboard';
    }

    setupEventListeners() {
        // Listen for refresh system events
        window.addEventListener('daemonStatusUpdate', (event) => {
            this.updateDaemonStatus(event.detail);
            this.updateSystemStats(event.detail);
        });

        window.addEventListener('checkResultUpdate', (event) => {
            const { checkName, result } = event.detail;
            this.updateCheckCard(checkName, result);
        });

        window.addEventListener('configDataUpdate', (event) => {
            this.updateConfigUI(event.detail);
        });

        window.addEventListener('designContentUpdate', () => {
            this.loadArchitectureDiagram();
        });
    }

    // === DAEMON STATUS UPDATES ===
    
    updateDaemonStatus(daemon) {
        const indicator = document.getElementById('daemon-indicator');
        const text = document.getElementById('daemon-text');
        
        if (!indicator || !text) return;
        
        if (daemon.is_running) {
            indicator.className = 'w-3 h-3 rounded-full bg-green-500 shadow-lg transition-all';
            text.textContent = 'Running';
            text.className = 'text-gray-700';
        } else {
            indicator.className = 'w-3 h-3 rounded-full bg-red-500 shadow-lg transition-all';
            text.textContent = 'Stopped';
            text.className = 'text-gray-700';
        }
    }
    
    updateSystemStats(daemon) {
        // Update uptime
        const uptimeElement = document.getElementById('uptime');
        if (uptimeElement) {
            if (daemon.uptime_seconds) {
                uptimeElement.textContent = formatDuration(daemon.uptime_seconds);
            } else {
                uptimeElement.textContent = '--';
            }
        }
        
        // Update total checks
        const totalChecksElement = document.getElementById('total-checks');
        if (totalChecksElement) {
            totalChecksElement.textContent = daemon.total_checks_run || 0;
        }
        
        // Update last check
        const lastCheckElement = document.getElementById('last-check');
        if (lastCheckElement) {
            if (daemon.last_check_run) {
                lastCheckElement.textContent = formatTimestamp(daemon.last_check_run);
            } else {
                lastCheckElement.textContent = '--';
            }
        }
    }

    // === CHECK CARD UPDATES ===
    
    updateCheckCard(checkName, result) {
        const card = document.getElementById(checkName.replace('_', '-'));
        if (!card) return;
        
        // Update status indicator
        const statusElement = card.querySelector('[id$="-check-status"]');
        const indicator = statusElement.querySelector('div');
        const statusText = statusElement.querySelector('span');
        
        // Update indicator with Tailwind classes
        let indicatorClasses = 'w-3 h-3 rounded-full shadow-lg transition-all';
        let textClasses = 'text-sm font-medium capitalize';
        let borderClasses = 'bg-white rounded-lg shadow-sm border border-l-4 p-6 mb-4 transition-all hover:shadow-md hover:-translate-y-0.5 relative overflow-hidden';
        
        if (result.status === 'success') {
            indicatorClasses += ' bg-green-500';
            textClasses += ' text-green-700';
            borderClasses += ' border-l-green-500';
        } else if (result.status === 'error') {
            indicatorClasses += ' bg-red-500';
            textClasses += ' text-red-700';
            borderClasses += ' border-l-red-500';
        } else if (result.status === 'warning') {
            indicatorClasses += ' bg-yellow-500';
            textClasses += ' text-yellow-700';
            borderClasses += ' border-l-yellow-500';
        } else {
            indicatorClasses += ' bg-gray-500';
            textClasses += ' text-gray-600';
            borderClasses += ' border-l-gray-300';
        }
        
        indicator.className = indicatorClasses;
        statusText.className = textClasses;
        statusText.textContent = result.status;
        
        // Update card border
        card.className = borderClasses;
        
        // Update message
        const messageElement = card.querySelector('[id$="-check-message"]');
        if (messageElement) {
            messageElement.textContent = result.message;
        }
        
        // Update timestamp
        const timestampElement = card.querySelector('[id$="-check-timestamp"]');
        if (timestampElement) {
            timestampElement.textContent = `Last run: ${formatTimestamp(result.timestamp)}`;
        }
        
        // Update specific details based on check type
        if (checkName === 'doc_check' && result.details && result.details.doc_index_stats) {
            this.updateDocIndexInfo(result.details);
        }
        
        if (checkName === 'git_check' && result.details && result.details.token_info) {
            this.updateTokenInfo(result.details);
        }
        
        if (checkName === 'test_check' && result.details) {
            this.updateTestInfo(result.details);
        }
        
        // Update details content
        const detailsElement = card.querySelector('.check-details-content');
        if (detailsElement && result.details) {
            if (checkName === 'doc_check' && result.details.formatted_output) {
                detailsElement.textContent = result.details.formatted_output;
            } else if (checkName === 'git_check' && result.details.repository_status) {
                detailsElement.textContent = formatGitDetails(result.details);
            } else if (checkName === 'test_check') {
                detailsElement.textContent = formatTestDetails(result.details);
            } else {
                detailsElement.textContent = JSON.stringify(result.details, null, 2);
            }
        } else if (detailsElement) {
            detailsElement.textContent = 'No details available';
        }
    }
    
    updateDocIndexInfo(details) {
        const indexInfo = document.getElementById('doc-index-info');
        const modulesElement = document.getElementById('doc-index-modules');
        const filesElement = document.getElementById('doc-index-files');
        const purposesElement = document.getElementById('doc-index-purposes');
        
        if (details.doc_index_stats && details.doc_index_status === 'generated') {
            toggleElementVisibility('doc-index-info', true);
            
            const stats = details.doc_index_stats;
            updateElement('doc-index-modules', stats.total_modules || 0);
            updateElement('doc-index-files', stats.total_files || 0);
            updateElement('doc-index-purposes', stats.total_purposes_found || 0);
        } else {
            toggleElementVisibility('doc-index-info', false);
        }
    }
    
    updateTokenInfo(details) {
        const tokenInfo = document.getElementById('git-check-tokens');
        const tokenCount = document.getElementById('git-token-count');
        const tokenThreshold = document.getElementById('git-token-threshold');
        const tokenWarning = document.getElementById('git-token-warning');
        
        if (details.token_info) {
            toggleElementVisibility('git-check-tokens', true);
            updateElement('git-token-count', details.token_info.token_count.toLocaleString());
            
            // Set threshold display
            const threshold = details.token_warning ? details.token_warning.threshold : 50000;
            updateElement('git-token-threshold', `/ ${threshold.toLocaleString()}`);
            
            // Set warning status
            if (details.token_warning) {
                updateElement('git-token-warning', '⚠️ Exceeds threshold!');
                updateElement('git-token-warning', 'font-bold text-red-600 ml-2', 'className');
            } else {
                updateElement('git-token-warning', '✅ Within limits');
                updateElement('git-token-warning', 'font-medium text-green-600 ml-2', 'className');
            }
        } else {
            toggleElementVisibility('git-check-tokens', false);
        }
    }
    
    updateTestInfo(details) {
        if (details && typeof details.missing_count !== 'undefined') {
            toggleElementVisibility('test-check-stats', true);
            
            updateElement('test-missing-count', details.missing_count || 0);
            updateElement('test-passing-count', details.passing_count || 0);
            updateElement('test-failing-count', details.failing_count || 0);
            updateElement('test-orphaned-count', details.orphaned_count || 0);
            updateElement('test-unit-count', `${details.unit_tests || 0} Unit`);
            updateElement('test-integration-count', `${details.integration_tests || 0} Integration`);
        } else {
            toggleElementVisibility('test-check-stats', false);
        }
    }

    // === CONFIGURATION MANAGEMENT ===
    
    async loadConfigPage() {
        try {
            const config = await apiClient.getConfig();
            this.populateConfigForm(config);
            this.setupConfigFormHandlers();
            
        } catch (error) {
            console.error('Error loading config page:', error);
            this.showConfigMessage('Error loading configuration', 'error');
        }
    }
    
    populateConfigForm(config) {
        // Daemon settings
        setCheckboxValue('daemon.doc_check.enabled', config.daemon.doc_check.enabled);
        setInputValue('daemon.doc_check.interval_minutes', config.daemon.doc_check.interval_minutes);
        
        setCheckboxValue('daemon.git_check.enabled', config.daemon.git_check.enabled);
        setInputValue('daemon.git_check.interval_minutes', config.daemon.git_check.interval_minutes);
        
        setCheckboxValue('daemon.test_check.enabled', config.daemon.test_check.enabled);
        setInputValue('daemon.test_check.interval_minutes', config.daemon.test_check.interval_minutes);
        
        setCheckboxValue('daemon.token_alerts.enabled', config.daemon.token_alerts.enabled);
        setInputValue('daemon.token_alerts.threshold', config.daemon.token_alerts.threshold);
        setInputValue('daemon.token_alerts.model', config.daemon.token_alerts.model);
        
        // API settings
        setInputValue('api.host', config.api.host);
        setInputValue('api.port', config.api.port);
        
        // ... Continue with other config sections
    }
    
    setupConfigFormHandlers() {
        const saveButton = document.getElementById('save-config');
        const resetButton = document.getElementById('reset-config');
        const form = document.getElementById('config-form');
        
        if (saveButton) {
            saveButton.addEventListener('click', async (e) => {
                e.preventDefault();
                await this.saveConfiguration();
            });
        }
        
        if (resetButton) {
            resetButton.addEventListener('click', async (e) => {
                e.preventDefault();
                await this.resetConfiguration();
            });
        }
        
        if (form) {
            form.addEventListener('change', () => {
                this.validateConfigForm();
            });
        }
    }
    
    async saveConfiguration() {
        try {
            const saveButton = document.getElementById('save-config');
            const originalText = saveButton.textContent;
            
            saveButton.disabled = true;
            saveButton.textContent = 'Saving...';
            
            const config = this.getConfigFromForm();
            const result = await apiClient.updateConfig(config);
            
            this.showConfigMessage('Configuration saved successfully!', 'success');
            
        } catch (error) {
            console.error('Error saving configuration:', error);
            this.showConfigMessage(`Error saving configuration: ${error.message}`, 'error');
            
        } finally {
            const saveButton = document.getElementById('save-config');
            saveButton.disabled = false;
            saveButton.textContent = 'Save Configuration';
        }
    }
    
    getConfigFromForm() {
        return {
            daemon: {
                doc_check: {
                    enabled: getCheckboxValue('daemon.doc_check.enabled'),
                    interval_minutes: getNumberValue('daemon.doc_check.interval_minutes')
                },
                git_check: {
                    enabled: getCheckboxValue('daemon.git_check.enabled'),
                    interval_minutes: getNumberValue('daemon.git_check.interval_minutes')
                },
                test_check: {
                    enabled: getCheckboxValue('daemon.test_check.enabled'),
                    interval_minutes: getNumberValue('daemon.test_check.interval_minutes')
                },
                token_alerts: {
                    enabled: getCheckboxValue('daemon.token_alerts.enabled'),
                    threshold: getNumberValue('daemon.token_alerts.threshold'),
                    model: getInputValue('daemon.token_alerts.model')
                }
            },
            api: {
                host: getInputValue('api.host'),
                port: getNumberValue('api.port')
            }
        };
    }
    
    validateConfigForm() {
        // Basic validation logic
        const errors = [];
        
        // Validate intervals
        const intervals = ['daemon.doc_check.interval_minutes', 'daemon.git_check.interval_minutes', 'daemon.test_check.interval_minutes'];
        intervals.forEach(id => {
            const value = getNumberValue(id);
            if (value < 1 || value > 1440) {
                errors.push(`${id.replace(/\./g, ' ')} must be between 1 and 1440 minutes`);
            }
        });
        
        return errors.length === 0;
    }
    
    showConfigMessage(message, type) {
        const statusElement = document.getElementById('save-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `save-status ${type}`;
            
            setTimeout(() => {
                statusElement.textContent = '';
                statusElement.className = 'save-status';
            }, 5000);
        }
    }
    
    updateConfigUI(config) {
        if (this.currentPage !== 'dashboard' && this.currentPage !== 'config') {
            return;
        }
        
        // Update dashboard config elements
        setCheckboxValue('doc-check-enabled', config.daemon.doc_check.enabled);
        setInputValue('doc-check-interval', config.daemon.doc_check.interval_minutes);
        
        setCheckboxValue('git-check-enabled', config.daemon.git_check.enabled);
        setInputValue('git-check-interval', config.daemon.git_check.interval_minutes);
        
        setCheckboxValue('test-check-enabled', config.daemon.test_check.enabled);
        setInputValue('test-check-interval', config.daemon.test_check.interval_minutes);
    }

    // === DIAGRAM RENDERING ===
    
    async loadArchitectureDiagram() {
        try {
            console.log('Loading architecture diagram...');
            const data = await apiClient.getArchitectureDiagram();
            
            if (data.mermaid_content) {
                this.renderArchitectureDiagram(data);
            } else {
                throw new Error('No Mermaid content found in architecture diagram');
            }
            
        } catch (error) {
            console.error('Error loading architecture diagram:', error);
            this.handleArchitectureError(error);
        }
    }
    
    renderArchitectureDiagram(data) {
        const titleElement = document.getElementById('architecture-title');
        const summaryElement = document.getElementById('architecture-summary');
        const diagramElement = document.getElementById('architecture-diagram');
        
        if (!diagramElement) return;
        
        // Update title and summary
        if (titleElement) titleElement.textContent = 'Autocode Architecture Overview';
        if (summaryElement) summaryElement.textContent = data.project_summary;
        
        // Initialize Mermaid if available
        if (typeof mermaid === 'undefined') {
            console.error('Mermaid is not loaded');
            this.handleArchitectureError(new Error('Mermaid library not loaded'));
            return;
        }
        
        // Configure Mermaid
        mermaid.initialize({
            startOnLoad: false,
            theme: 'default',
            themeVariables: {
                primaryColor: '#fff',
                primaryTextColor: '#333',
                primaryBorderColor: '#333',
                lineColor: '#6c757d',
                secondaryColor: '#f8f9fa',
                tertiaryColor: '#e9ecef'
            },
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true
            },
            securityLevel: 'loose'
        });
        
        // Clear previous diagram
        diagramElement.innerHTML = '';
        
        // Generate unique ID for the diagram
        const diagramId = `architecture-diagram-${Date.now()}`;
        
        // Create a div for the diagram
        const diagramDiv = document.createElement('div');
        diagramDiv.id = diagramId;
        diagramDiv.className = 'mermaid';
        diagramDiv.textContent = data.mermaid_content;
        
        diagramElement.appendChild(diagramDiv);
        
        // Render the diagram
        mermaid.init(undefined, diagramDiv);
        
        console.log('Architecture diagram rendered successfully');
    }
    
    renderComponentTree(data) {
        const titleElement = document.getElementById('ui-designer-title');
        const summaryElement = document.getElementById('ui-designer-summary');
        const diagramElement = document.getElementById('component-tree-diagram');
        
        if (!diagramElement) return;
        
        // Update title and summary
        if (titleElement) titleElement.textContent = 'Component Tree Visualization';
        if (summaryElement) summaryElement.textContent = `Found ${data.metrics.total_components} components in ${data.metrics.total_files} files`;
        
        // Similar Mermaid rendering logic as architecture diagram
        if (typeof mermaid !== 'undefined') {
            diagramElement.innerHTML = '';
            const diagramId = `component-tree-diagram-${Date.now()}`;
            const diagramDiv = document.createElement('div');
            diagramDiv.id = diagramId;
            diagramDiv.className = 'mermaid';
            diagramDiv.textContent = data.diagram;
            diagramElement.appendChild(diagramDiv);
            mermaid.init(undefined, diagramDiv);
        }
    }
    
    handleArchitectureError(error) {
        console.error('Architecture diagram error:', error);
        
        const titleElement = document.getElementById('architecture-title');
        const summaryElement = document.getElementById('architecture-summary');
        const diagramElement = document.getElementById('architecture-diagram');
        
        if (titleElement) titleElement.textContent = 'Architecture Diagram Error';
        if (summaryElement) summaryElement.textContent = error.message;
        
        if (diagramElement) {
            diagramElement.innerHTML = `
                <div class="loading-message">
                    <p>❌ Error loading architecture diagram</p>
                    <p style="color: #dc3545; font-size: 0.9rem; margin-top: 10px;">${error.message}</p>
                    <p style="color: #6c757d; font-size: 0.85rem; margin-top: 10px;">
                        Try running <code>autocode code-to-design</code> first, then use the Regenerate button.
                    </p>
                </div>
            `;
        }
    }
    
    handleComponentTreeError(error) {
        console.error('Component tree error:', error);
        
        const titleElement = document.getElementById('ui-designer-title');
        const summaryElement = document.getElementById('ui-designer-summary');
        const diagramElement = document.getElementById('component-tree-diagram');
        
        if (titleElement) titleElement.textContent = 'Component Tree Error';
        if (summaryElement) summaryElement.textContent = error.message;
        
        if (diagramElement) {
            diagramElement.innerHTML = `
                <div class="loading-message">
                    <p>❌ Error generating component tree</p>
                    <p style="color: #dc3545; font-size: 0.9rem; margin-top: 10px;">${error.message}</p>
                    <p style="color: #6c757d; font-size: 0.85rem; margin-top: 10px;">
                        Make sure the autocode/web directory contains HTML, JavaScript, or CSS files to analyze.
                    </p>
                </div>
            `;
        }
    }
    
    handleError(error) {
        console.error('Dashboard error:', error);
        
        // Update daemon status to error
        const indicator = document.getElementById('daemon-indicator');
        const text = document.getElementById('daemon-text');
        
        if (indicator && text) {
            indicator.className = 'w-3 h-3 rounded-full bg-red-500 shadow-lg transition-all';
            text.textContent = 'Connection Error';
            text.className = 'text-gray-700';
        }
        
        // Show error in system stats
        updateElement('uptime', 'Error');
        updateElement('total-checks', 'Error');
        updateElement('last-check', 'Error');
    }
}
