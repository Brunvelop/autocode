// Autocode Monitoring Dashboard JavaScript

class AutocodeDashboard {
    constructor() {
        this.refreshInterval = 5000; // 5 seconds
        this.refreshTimer = null;
        this.isLoading = false;
        this.currentPage = this.getCurrentPage();
        
        this.init();
    }
    
    init() {
        console.log('Initializing Autocode Dashboard');
        this.setupNavigation();
        this.startAutoRefresh();
        this.loadInitialData();
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
        if (this.currentPage === 'dashboard') {
            await this.fetchAndUpdateStatus();
            await this.fetchAndUpdateConfig();
        } else if (this.currentPage === 'config') {
            await this.loadConfigPage();
        }
    }
    
    async loadConfigPage() {
        try {
            const response = await fetch('/api/config');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const config = await response.json();
            this.populateConfigForm(config);
            this.setupConfigFormHandlers();
            
        } catch (error) {
            console.error('Error loading config page:', error);
            this.showConfigMessage('Error loading configuration', 'error');
        }
    }
    
    populateConfigForm(config) {
        // Daemon settings
        this.setCheckboxValue('daemon.doc_check.enabled', config.daemon.doc_check.enabled);
        this.setInputValue('daemon.doc_check.interval_minutes', config.daemon.doc_check.interval_minutes);
        
        this.setCheckboxValue('daemon.git_check.enabled', config.daemon.git_check.enabled);
        this.setInputValue('daemon.git_check.interval_minutes', config.daemon.git_check.interval_minutes);
        
        this.setCheckboxValue('daemon.test_check.enabled', config.daemon.test_check.enabled);
        this.setInputValue('daemon.test_check.interval_minutes', config.daemon.test_check.interval_minutes);
        
        this.setCheckboxValue('daemon.token_alerts.enabled', config.daemon.token_alerts.enabled);
        this.setInputValue('daemon.token_alerts.threshold', config.daemon.token_alerts.threshold);
        this.setInputValue('daemon.token_alerts.model', config.daemon.token_alerts.model);
        
        // API settings
        this.setInputValue('api.host', config.api.host);
        this.setInputValue('api.port', config.api.port);
        
        // OpenCode settings
        this.setCheckboxValue('opencode.enabled', config.opencode.enabled);
        this.setInputValue('opencode.model', config.opencode.model);
        this.setInputValue('opencode.max_tokens', config.opencode.max_tokens);
        this.setCheckboxValue('opencode.debug', config.opencode.debug);
        this.setCheckboxValue('opencode.quiet_mode', config.opencode.quiet_mode);
        this.setCheckboxValue('opencode.json_output', config.opencode.json_output);
        this.setInputValue('opencode.config_path', config.opencode.config_path);
        
        // Doc index settings
        this.setCheckboxValue('doc_index.enabled', config.doc_index.enabled);
        this.setCheckboxValue('doc_index.auto_generate', config.doc_index.auto_generate);
        this.setCheckboxValue('doc_index.update_on_docs_change', config.doc_index.update_on_docs_change);
        this.setInputValue('doc_index.output_path', config.doc_index.output_path);
        
        // Documentation settings
        this.setCheckboxValue('docs.enabled', config.docs.enabled);
        this.setTextareaValue('docs.directories', config.docs.directories);
        this.setTextareaValue('docs.file_extensions', config.docs.file_extensions);
        this.setTextareaValue('docs.exclude', config.docs.exclude);
        
        // Test settings
        this.setCheckboxValue('tests.enabled', config.tests.enabled);
        this.setCheckboxValue('tests.auto_execute', config.tests.auto_execute);
        this.setTextareaValue('tests.directories', config.tests.directories);
        this.setTextareaValue('tests.exclude', config.tests.exclude);
        this.setTextareaValue('tests.test_frameworks', config.tests.test_frameworks);
        
        // Code to design settings
        this.setCheckboxValue('code_to_design.enabled', config.code_to_design.enabled);
        this.setInputValue('code_to_design.output_dir', config.code_to_design.output_dir);
        this.setTextareaValue('code_to_design.languages', config.code_to_design.languages);
        this.setTextareaValue('code_to_design.diagrams', config.code_to_design.diagrams);
        this.setTextareaValue('code_to_design.directories', config.code_to_design.directories);
    }
    
    setCheckboxValue(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.checked = value;
        }
    }
    
    setInputValue(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.value = value;
        }
    }
    
    setTextareaValue(id, value) {
        const element = document.getElementById(id);
        if (element && Array.isArray(value)) {
            element.value = value.join('\n');
        }
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
        
        // Add form change handler for validation
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
            console.log('Configuration saved:', result);
            
            this.showConfigMessage('Configuration saved successfully! Changes will take effect immediately.', 'success');
            
        } catch (error) {
            console.error('Error saving configuration:', error);
            this.showConfigMessage(`Error saving configuration: ${error.message}`, 'error');
            
        } finally {
            const saveButton = document.getElementById('save-config');
            saveButton.disabled = false;
            saveButton.textContent = 'Save Configuration';
        }
    }
    
    async resetConfiguration() {
        if (!confirm('Are you sure you want to reset to default configuration? This will overwrite all current settings.')) {
            return;
        }
        
        try {
            const resetButton = document.getElementById('reset-config');
            const originalText = resetButton.textContent;
            
            resetButton.disabled = true;
            resetButton.textContent = 'Resetting...';
            
            // Create default config (matches the defaults in models.py)
            const defaultConfig = {
                daemon: {
                    doc_check: { enabled: true, interval_minutes: 10 },
                    git_check: { enabled: true, interval_minutes: 5 },
                    test_check: { enabled: true, interval_minutes: 5 },
                    token_alerts: { enabled: true, threshold: 50000, model: "gpt-4" }
                },
                api: { port: 8080, host: "127.0.0.1" },
                opencode: {
                    enabled: true,
                    model: "claude-4-sonnet",
                    max_tokens: 64000,
                    debug: true,
                    config_path: ".opencode.json",
                    quiet_mode: true,
                    json_output: true
                },
                doc_index: {
                    enabled: true,
                    output_path: ".clinerules/docs_index.json",
                    auto_generate: true,
                    update_on_docs_change: true
                },
                docs: {
                    enabled: true,
                    directories: ["vidi/", "autocode/"],
                    file_extensions: [".py", ".js", ".html", ".css", ".ts", ".jsx", ".tsx"],
                    exclude: ["__pycache__/", "*.pyc", "__init__.py"]
                },
                tests: {
                    enabled: true,
                    directories: ["vidi/", "autocode/", "tools/"],
                    exclude: ["__pycache__/", "*.pyc", "__init__.py"],
                    test_frameworks: ["pytest"],
                    auto_execute: true
                },
                code_to_design: {
                    enabled: true,
                    output_dir: "design",
                    language: "python",
                    languages: ["python", "javascript", "html", "css"],
                    diagrams: ["classes", "components"],
                    directories: ["autocode/"]
                }
            };
            
            // Save default config
            const response = await fetch('/api/config', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(defaultConfig)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            // Reload the form with defaults
            this.populateConfigForm(defaultConfig);
            this.showConfigMessage('Configuration reset to defaults successfully!', 'success');
            
        } catch (error) {
            console.error('Error resetting configuration:', error);
            this.showConfigMessage(`Error resetting configuration: ${error.message}`, 'error');
            
        } finally {
            const resetButton = document.getElementById('reset-config');
            resetButton.disabled = false;
            resetButton.textContent = 'Reset to Defaults';
        }
    }
    
    getConfigFromForm() {
        return {
            daemon: {
                doc_check: {
                    enabled: this.getCheckboxValue('daemon.doc_check.enabled'),
                    interval_minutes: this.getNumberValue('daemon.doc_check.interval_minutes')
                },
                git_check: {
                    enabled: this.getCheckboxValue('daemon.git_check.enabled'),
                    interval_minutes: this.getNumberValue('daemon.git_check.interval_minutes')
                },
                test_check: {
                    enabled: this.getCheckboxValue('daemon.test_check.enabled'),
                    interval_minutes: this.getNumberValue('daemon.test_check.interval_minutes')
                },
                token_alerts: {
                    enabled: this.getCheckboxValue('daemon.token_alerts.enabled'),
                    threshold: this.getNumberValue('daemon.token_alerts.threshold'),
                    model: this.getInputValue('daemon.token_alerts.model')
                }
            },
            api: {
                host: this.getInputValue('api.host'),
                port: this.getNumberValue('api.port')
            },
            opencode: {
                enabled: this.getCheckboxValue('opencode.enabled'),
                model: this.getInputValue('opencode.model'),
                max_tokens: this.getNumberValue('opencode.max_tokens'),
                debug: this.getCheckboxValue('opencode.debug'),
                config_path: this.getInputValue('opencode.config_path'),
                quiet_mode: this.getCheckboxValue('opencode.quiet_mode'),
                json_output: this.getCheckboxValue('opencode.json_output')
            },
            doc_index: {
                enabled: this.getCheckboxValue('doc_index.enabled'),
                output_path: this.getInputValue('doc_index.output_path'),
                auto_generate: this.getCheckboxValue('doc_index.auto_generate'),
                update_on_docs_change: this.getCheckboxValue('doc_index.update_on_docs_change')
            },
            docs: {
                enabled: this.getCheckboxValue('docs.enabled'),
                directories: this.getTextareaArrayValue('docs.directories'),
                file_extensions: this.getTextareaArrayValue('docs.file_extensions'),
                exclude: this.getTextareaArrayValue('docs.exclude')
            },
            tests: {
                enabled: this.getCheckboxValue('tests.enabled'),
                directories: this.getTextareaArrayValue('tests.directories'),
                exclude: this.getTextareaArrayValue('tests.exclude'),
                test_frameworks: this.getTextareaArrayValue('tests.test_frameworks'),
                auto_execute: this.getCheckboxValue('tests.auto_execute')
            },
            code_to_design: {
                enabled: this.getCheckboxValue('code_to_design.enabled'),
                output_dir: this.getInputValue('code_to_design.output_dir'),
                language: "python", // Keep for backward compatibility
                languages: this.getTextareaArrayValue('code_to_design.languages'),
                diagrams: this.getTextareaArrayValue('code_to_design.diagrams'),
                directories: this.getTextareaArrayValue('code_to_design.directories')
            }
        };
    }
    
    getCheckboxValue(id) {
        const element = document.getElementById(id);
        return element ? element.checked : false;
    }
    
    getInputValue(id) {
        const element = document.getElementById(id);
        return element ? element.value : '';
    }
    
    getNumberValue(id) {
        const element = document.getElementById(id);
        return element ? parseInt(element.value) || 0 : 0;
    }
    
    getTextareaArrayValue(id) {
        const element = document.getElementById(id);
        if (!element) return [];
        return element.value.split('\n').filter(line => line.trim() !== '');
    }
    
    validateConfigForm() {
        // Add basic validation
        const errors = [];
        
        // Validate intervals
        const intervals = ['daemon.doc_check.interval_minutes', 'daemon.git_check.interval_minutes', 'daemon.test_check.interval_minutes'];
        intervals.forEach(id => {
            const value = this.getNumberValue(id);
            if (value < 1 || value > 1440) {
                errors.push(`${id.replace(/\./g, ' ')} must be between 1 and 1440 minutes`);
            }
        });
        
        // Validate token threshold
        const threshold = this.getNumberValue('daemon.token_alerts.threshold');
        if (threshold < 1000 || threshold > 1000000) {
            errors.push('Token threshold must be between 1,000 and 1,000,000');
        }
        
        // Validate port
        const port = this.getNumberValue('api.port');
        if (port < 1 || port > 65535) {
            errors.push('API port must be between 1 and 65535');
        }
        
        // Validate max tokens
        const maxTokens = this.getNumberValue('opencode.max_tokens');
        if (maxTokens < 1000 || maxTokens > 200000) {
            errors.push('OpenCode max tokens must be between 1,000 and 200,000');
        }
        
        // Show validation errors
        if (errors.length > 0) {
            this.showConfigMessage(`Validation errors: ${errors.join(', ')}`, 'error');
            return false;
        }
        
        return true;
    }
    
    showConfigMessage(message, type) {
        const statusElement = document.getElementById('save-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `save-status ${type}`;
            
            // Clear message after 5 seconds
            setTimeout(() => {
                statusElement.textContent = '';
                statusElement.className = 'save-status';
            }, 5000);
        }
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
        if (uptimeElement) {
            if (daemon.uptime_seconds) {
                uptimeElement.textContent = this.formatDuration(daemon.uptime_seconds);
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
                lastCheckElement.textContent = this.formatTimestamp(daemon.last_check_run);
            } else {
                lastCheckElement.textContent = '--';
            }
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
        
        // Update documentation index information for doc_check
        if (checkName === 'doc_check' && result.details && result.details.doc_index_stats) {
            this.updateDocIndexInfo(result.details);
        } else if (checkName === 'doc_check') {
            // Hide index info if not available
            const indexInfo = document.getElementById('doc-index-info');
            if (indexInfo) {
                indexInfo.style.display = 'none';
            }
        }
        
        // Update token information for git_check
        if (checkName === 'git_check' && result.details && result.details.token_info) {
            this.updateTokenInfo(result.details);
        }
        
        // Update test information for test_check
        if (checkName === 'test_check' && result.details) {
            this.updateTestInfo(result.details);
        }
        
        // Update details
        const detailsElement = card.querySelector('.check-details-content');
        if (result.details) {
            if (checkName === 'doc_check' && result.details.formatted_output) {
                detailsElement.textContent = result.details.formatted_output;
            } else if (checkName === 'git_check' && result.details.repository_status) {
                detailsElement.textContent = this.formatGitDetails(result.details);
            } else if (checkName === 'test_check') {
                detailsElement.textContent = this.formatTestDetails(result.details);
            } else {
                detailsElement.textContent = JSON.stringify(result.details, null, 2);
            }
        } else {
            detailsElement.textContent = 'No details available';
        }
    }
    
    updateDocIndexInfo(details) {
        const indexInfo = document.getElementById('doc-index-info');
        const modulesElement = document.getElementById('doc-index-modules');
        const filesElement = document.getElementById('doc-index-files');
        const purposesElement = document.getElementById('doc-index-purposes');
        
        if (details.doc_index_stats && details.doc_index_status === 'generated') {
            indexInfo.style.display = 'block';
            
            const stats = details.doc_index_stats;
            modulesElement.textContent = stats.total_modules || 0;
            filesElement.textContent = stats.total_files || 0;
            purposesElement.textContent = stats.total_purposes_found || 0;
        } else {
            indexInfo.style.display = 'none';
        }
    }
    
    updateTokenInfo(details) {
        const tokenInfo = document.getElementById('git-check-tokens');
        const tokenCount = document.getElementById('git-token-count');
        const tokenThreshold = document.getElementById('git-token-threshold');
        const tokenWarning = document.getElementById('git-token-warning');
        
        if (details.token_info) {
            tokenInfo.style.display = 'block';
            tokenCount.textContent = details.token_info.token_count.toLocaleString();
            
            // Set threshold display
            const threshold = details.token_warning ? details.token_warning.threshold : 50000;
            tokenThreshold.textContent = `/ ${threshold.toLocaleString()}`;
            
            // Set warning status
            if (details.token_warning) {
                tokenWarning.textContent = '⚠️ Exceeds threshold!';
                tokenWarning.className = 'token-warning error';
                tokenWarning.style.color = '#dc3545';
                tokenWarning.style.fontWeight = 'bold';
            } else {
                tokenWarning.textContent = '✅ Within limits';
                tokenWarning.className = 'token-warning success';
                tokenWarning.style.color = '#28a745';
                tokenWarning.style.fontWeight = 'normal';
            }
        } else {
            tokenInfo.style.display = 'none';
        }
    }
    
    updateTestInfo(details) {
        const testInfo = document.getElementById('test-check-stats');
        const missingCount = document.getElementById('test-missing-count');
        const passingCount = document.getElementById('test-passing-count');
        const failingCount = document.getElementById('test-failing-count');
        const orphanedCount = document.getElementById('test-orphaned-count');
        const unitCount = document.getElementById('test-unit-count');
        const integrationCount = document.getElementById('test-integration-count');
        
        if (details && typeof details.missing_count !== 'undefined') {
            testInfo.style.display = 'block';
            
            missingCount.textContent = details.missing_count || 0;
            passingCount.textContent = details.passing_count || 0;
            failingCount.textContent = details.failing_count || 0;
            orphanedCount.textContent = details.orphaned_count || 0;
            unitCount.textContent = `${details.unit_tests || 0} Unit`;
            integrationCount.textContent = `${details.integration_tests || 0} Integration`;
        } else {
            testInfo.style.display = 'none';
        }
    }
    
    formatTestDetails(details) {
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
    
    updateConfigUI(config) {
        // Only update config UI if we're on a page that has these elements
        if (this.currentPage !== 'dashboard' && this.currentPage !== 'config') {
            return;
        }
        
        // Update doc check config
        const docCheckEnabled = document.getElementById('doc-check-enabled');
        const docCheckInterval = document.getElementById('doc-check-interval');
        
        if (docCheckEnabled && docCheckInterval) {
            docCheckEnabled.checked = config.daemon.doc_check.enabled;
            docCheckInterval.value = config.daemon.doc_check.interval_minutes;
        }
        
        // Update git check config
        const gitCheckEnabled = document.getElementById('git-check-enabled');
        const gitCheckInterval = document.getElementById('git-check-interval');
        
        if (gitCheckEnabled && gitCheckInterval) {
            gitCheckEnabled.checked = config.daemon.git_check.enabled;
            gitCheckInterval.value = config.daemon.git_check.interval_minutes;
        }
        
        // Update test check config
        const testCheckEnabled = document.getElementById('test-check-enabled');
        const testCheckInterval = document.getElementById('test-check-interval');
        
        if (testCheckEnabled && testCheckInterval) {
            testCheckEnabled.checked = config.daemon.test_check.enabled;
            testCheckInterval.value = config.daemon.test_check.interval_minutes;
        }
        
        // Update token alerts config
        const tokenAlertsEnabled = document.getElementById('token-alerts-enabled');
        const tokenThreshold = document.getElementById('token-threshold');
        const tokenModel = document.getElementById('token-model');
        
        if (tokenAlertsEnabled && tokenThreshold && tokenModel && config.daemon.token_alerts) {
            tokenAlertsEnabled.checked = config.daemon.token_alerts.enabled;
            tokenThreshold.value = config.daemon.token_alerts.threshold;
            tokenModel.value = config.daemon.token_alerts.model;
        }
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
        if (lastUpdatedElement) {
            lastUpdatedElement.textContent = new Date().toLocaleTimeString();
        }
    }
    
    updateRefreshStatus(status) {
        const refreshStatusElement = document.getElementById('auto-refresh-status');
        if (refreshStatusElement) {
            refreshStatusElement.textContent = status;
        }
    }
    
    handleError(error) {
        console.error('Dashboard error:', error);
        
        // Update daemon status to error
        const indicator = document.getElementById('daemon-indicator');
        const text = document.getElementById('daemon-text');
        
        if (indicator && text) {
            indicator.className = 'status-indicator error';
            text.textContent = 'Connection Error';
        }
        
        // Show error in system stats with null checks
        const uptimeElement = document.getElementById('uptime');
        const totalChecksElement = document.getElementById('total-checks');
        const lastCheckElement = document.getElementById('last-check');
        
        if (uptimeElement) uptimeElement.textContent = 'Error';
        if (totalChecksElement) totalChecksElement.textContent = 'Error';
        if (lastCheckElement) lastCheckElement.textContent = 'Error';
    }
    
    async loadArchitectureDiagram() {
        try {
            console.log('Loading architecture diagram...');
            
            const response = await fetch('/api/architecture/diagram');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.renderArchitectureDiagram(data);
            
        } catch (error) {
            console.error('Error loading architecture diagram:', error);
            this.handleArchitectureError(error);
        }
    }
    
    renderArchitectureDiagram(data) {
        const titleElement = document.getElementById('architecture-title');
        const summaryElement = document.getElementById('architecture-summary');
        const diagramElement = document.getElementById('architecture-diagram');
        
        // Update title and summary
        titleElement.textContent = 'Autocode Architecture Overview';
        summaryElement.textContent = data.project_summary;
        
        // Initialize Mermaid if not already done
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
    
    handleArchitectureError(error) {
        console.error('Architecture diagram error:', error);
        
        const titleElement = document.getElementById('architecture-title');
        const summaryElement = document.getElementById('architecture-summary');
        const diagramElement = document.getElementById('architecture-diagram');
        
        titleElement.textContent = 'Architecture Diagram Error';
        summaryElement.textContent = error.message;
        
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
    
    renderComponentTree(data) {
        const titleElement = document.getElementById('ui-designer-title');
        const summaryElement = document.getElementById('ui-designer-summary');
        const diagramElement = document.getElementById('component-tree-diagram');
        
        // Update title and summary
        titleElement.textContent = 'Component Tree Visualization';
        summaryElement.textContent = `Found ${data.metrics.total_components} components in ${data.metrics.total_files} files`;
        
        // Initialize Mermaid if not already done
        if (typeof mermaid === 'undefined') {
            console.error('Mermaid is not loaded');
            this.handleComponentTreeError(new Error('Mermaid library not loaded'));
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
        
        // Clear previous diagram
        diagramElement.innerHTML = '';
        
        // Generate unique ID for the diagram
        const diagramId = `component-tree-diagram-${Date.now()}`;
        
        // Create a div for the diagram
        const diagramDiv = document.createElement('div');
        diagramDiv.id = diagramId;
        diagramDiv.className = 'mermaid';
        diagramDiv.textContent = data.diagram;
        
        diagramElement.appendChild(diagramDiv);
        
        // Render the diagram
        mermaid.init(undefined, diagramDiv);
        
        console.log('Component tree rendered successfully');
    }
    
    handleComponentTreeError(error) {
        console.error('Component tree error:', error);
        
        const titleElement = document.getElementById('ui-designer-title');
        const summaryElement = document.getElementById('ui-designer-summary');
        const diagramElement = document.getElementById('component-tree-diagram');
        
        titleElement.textContent = 'Component Tree Error';
        summaryElement.textContent = error.message;
        
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

// Global functions for architecture diagram
async function refreshArchitecture() {
    console.log('Refreshing architecture diagram...');
    
    // Disable button
    const button = event.target;
    button.disabled = true;
    button.textContent = 'Loading...';
    
    try {
        await dashboard.loadArchitectureDiagram();
        console.log('Architecture diagram refreshed successfully');
        
    } catch (error) {
        console.error('Error refreshing architecture diagram:', error);
        
    } finally {
        // Re-enable button
        button.disabled = false;
        button.textContent = 'Refresh';
    }
}

async function regenerateArchitecture() {
    console.log('Regenerating architecture diagram...');
    
    // Disable button
    const button = event.target;
    button.disabled = true;
    button.textContent = 'Regenerating...';
    
    try {
        const response = await fetch('/api/architecture/regenerate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('Architecture regeneration started:', result);
        
        // Wait a bit for regeneration to complete, then refresh
        setTimeout(async () => {
            await dashboard.loadArchitectureDiagram();
        }, 3000);
        
    } catch (error) {
        console.error('Error regenerating architecture diagram:', error);
        
    } finally {
        // Re-enable button
        button.disabled = false;
        button.textContent = 'Regenerate';
    }
}

// Global functions for UI Designer
async function generateComponentTree() {
    console.log('Generating component tree...');
    
    // Disable button
    const button = event.target;
    button.disabled = true;
    button.textContent = 'Generating...';
    
    try {
        const response = await fetch('/api/ui-designer/component-tree');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.status === 'success') {
            dashboard.renderComponentTree(result);
            console.log('Component tree generated successfully');
        } else {
            throw new Error(result.error || 'Unknown error generating component tree');
        }
        
    } catch (error) {
        console.error('Error generating component tree:', error);
        dashboard.handleComponentTreeError(error);
        
    } finally {
        // Re-enable button
        button.disabled = false;
        button.textContent = 'Generate Tree';
    }
}

async function refreshComponentTree() {
    console.log('Refreshing component tree...');
    
    // Disable button
    const button = event.target;
    button.disabled = true;
    button.textContent = 'Refreshing...';
    
    try {
        const response = await fetch('/api/ui-designer/component-tree');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.status === 'success') {
            dashboard.renderComponentTree(result);
            console.log('Component tree refreshed successfully');
        } else {
            throw new Error(result.error || 'Unknown error refreshing component tree');
        }
        
    } catch (error) {
        console.error('Error refreshing component tree:', error);
        dashboard.handleComponentTreeError(error);
        
    } finally {
        // Re-enable button
        button.disabled = false;
        button.textContent = 'Refresh';
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
            },
            test_check: {
                enabled: document.getElementById('test-check-enabled').checked,
                interval_minutes: parseInt(document.getElementById('test-check-interval').value)
            },
            token_alerts: {
                enabled: document.getElementById('token-alerts-enabled').checked,
                threshold: parseInt(document.getElementById('token-threshold').value),
                model: document.getElementById('token-model').value
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
