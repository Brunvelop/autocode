// Autocode Monitoring Dashboard JavaScript

class AutocodeDashboard {
    constructor() {
        // Configuración de intervalos diferenciados
        this.refreshConfig = {
            daemon_status: { interval: 3000, timer: null, enabled: true },    // 3s - crítico
            check_results: { interval: 10000, timer: null, enabled: true },   // 10s - normal
            config_data: { interval: 30000, timer: null, enabled: true },     // 30s - lento
            design_data: { interval: 60000, timer: null, enabled: false }     // 60s - bajo demanda
        };
        
        this.isLoading = {};
        this.lastUpdate = {};
        this.updatePaused = false;
        this.currentPage = this.getCurrentPage();
        
        // Activity detection
        this.userActivityTimer = null;
        this.inactivityTimeout = 60000; // 1 minuto de inactividad
        this.wasActiveRefresh = true;
        
        this.init();
    }
    
    // === API METHODS (consolidated from APIClient) ===
    async apiGet(endpoint) {
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
    
    async apiPost(endpoint, data = null) {
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
    
    async apiPut(endpoint, data) {
        try {
            const response = await fetch(endpoint, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API PUT error for ${endpoint}:`, error);
            throw error;
        }
    }
    
    async apiDelete(endpoint) {
        try {
            const response = await fetch(endpoint, { method: 'DELETE' });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API DELETE error for ${endpoint}:`, error);
            throw error;
        }
    }
    
    // === NEW WRAPPER ENDPOINTS ===
    
    // Método para generar documentación usando nuevo wrapper
    async generateDocumentation() {
        try {
            console.log('Generating documentation...');
            
            const response = await this.apiPost('/api/generate-docs');
            
            if (response.success) {
                this.showNotification('Documentation generation started', 'success');
                
                // Auto-refresh después de un delay para capturar el resultado
                setTimeout(() => {
                    this.refreshSpecificData('check_results');
                }, 2000);
            } else {
                this.showNotification(`Documentation error: ${response.error}`, 'error');
            }
            
            return response;
            
        } catch (error) {
            console.error('Error generating documentation:', error);
            this.showNotification('Failed to start documentation generation', 'error');
            throw error;
        }
    }
    
    // Método para generar diseño usando nuevo wrapper
    async generateDesign(options = {}) {
        try {
            console.log('Generating design diagrams...');
            
            const params = new URLSearchParams();
            if (options.directory) params.append('directory', options.directory);
            if (options.output_dir) params.append('output_dir', options.output_dir);
            
            const endpoint = `/api/generate-design${params.toString() ? '?' + params.toString() : ''}`;
            const response = await this.apiPost(endpoint);
            
            if (response.success) {
                this.showNotification('Design generation started', 'success');
                
                // Refresh design-related UI after delay
                setTimeout(() => {
                    this.refreshSpecificData('design_data');
                }, 3000);
            } else {
                this.showNotification(`Design error: ${response.error}`, 'error');
            }
            
            return response;
            
        } catch (error) {
            console.error('Error generating design:', error);
            this.showNotification('Failed to start design generation', 'error');
            throw error;
        }
    }
    
    // Método para analizar git usando nuevo wrapper
    async analyzeGitChanges(options = {}) {
        try {
            console.log('Analyzing git changes...');
            
            const params = new URLSearchParams();
            if (options.output) params.append('output', options.output);
            if (options.verbose) params.append('verbose', options.verbose);
            
            const endpoint = `/api/analyze-git${params.toString() ? '?' + params.toString() : ''}`;
            const response = await this.apiPost(endpoint);
            
            if (response.success) {
                this.showNotification('Git analysis started', 'success');
                
                // Refresh git-related data
                setTimeout(() => {
                    this.refreshSpecificData('check_results');
                }, 1500);
            } else {
                this.showNotification(`Git analysis error: ${response.error}`, 'error');
            }
            
            return response;
            
        } catch (error) {
            console.error('Error analyzing git changes:', error);
            this.showNotification('Failed to start git analysis', 'error');
            throw error;
        }
    }
    
    // Método para cargar configuración usando nuevo wrapper
    async loadConfigurationData() {
        try {
            const response = await this.apiGet('/api/config/load');
            
            if (response.success) {
                return response.config;
            } else {
                throw new Error(response.error || 'Failed to load configuration');
            }
            
        } catch (error) {
            console.error('Error loading configuration:', error);
            throw error;
        }
    }
    
    init() {
        console.log('Initializing Autocode Dashboard');
        this.setupNavigation();
        this.setupActivityDetection();
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
            const config = await this.apiGet('/api/config');
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
            
            const result = await this.apiPut('/api/config', config);
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
            await this.apiPut('/api/config', defaultConfig);
            
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
    
    // === INTELLIGENT AUTO-REFRESH SYSTEM ===
    
    // Iniciar múltiples timers diferenciados
    startAutoRefresh() {
        Object.keys(this.refreshConfig).forEach(dataType => {
            this.startSpecificRefresh(dataType);
        });
        
        this.updateRefreshStatus('MULTI-ON');
    }
    
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
    
    // Método para refrescar tipos específicos de datos
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
    
    // Métodos específicos de refresh
    async refreshDaemonStatus() {
        const statusData = await this.apiGet('/api/status');
        this.updateDaemonStatus(statusData.daemon);
        this.updateSystemStats(statusData.daemon);
    }
    
    async refreshCheckResults() {
        const checks = ['doc_check', 'git_check', 'test_check'];
        const checkPromises = checks.map(checkName => this.getCheckResult(checkName));
        
        try {
            const results = await Promise.allSettled(checkPromises);
            
            results.forEach((result, index) => {
                const checkName = checks[index];
                if (result.status === 'fulfilled') {
                    this.updateCheckCard(checkName, result.value);
                } else {
                    console.error(`Failed to update ${checkName}:`, result.reason);
                }
            });
            
        } catch (error) {
            console.error('Error refreshing check results:', error);
        }
    }
    
    async refreshConfigData() {
        if (this.currentPage === 'config') {
            const configData = await this.loadConfigurationData();
            this.updateConfigUI(configData);
        }
    }
    
    async refreshDesignContent() {
        if (this.currentPage === 'design' || this.currentPage === 'ui-designer') {
            // Refresh design-related content
            await this.loadArchitectureDiagram();
        }
    }
    
    // Método para obtener resultado de check individual
    async getCheckResult(checkName) {
        // Para algunos checks, usar endpoints síncronos nuevos
        if (checkName === 'doc_check') {
            return await this.apiPost('/api/docs/check-sync');
        }
        
        // Para otros, seguir usando el endpoint de status general
        const statusData = await this.apiGet('/api/status');
        return statusData.checks[checkName];
    }
    
    // Pausar/reanudar refresh basado en actividad
    pauseAutoRefresh() {
        this.updatePaused = true;
        Object.keys(this.refreshConfig).forEach(dataType => {
            this.stopSpecificRefresh(dataType);
        });
        this.updateRefreshStatus('PAUSED');
    }
    
    resumeAutoRefresh() {
        this.updatePaused = false;
        this.startAutoRefresh();
    }
    
    stopAutoRefresh() {
        Object.keys(this.refreshConfig).forEach(dataType => {
            this.stopSpecificRefresh(dataType);
        });
        this.updateRefreshStatus('OFF');
    }
    
    stopSpecificRefresh(dataType) {
        const config = this.refreshConfig[dataType];
        if (config.timer) {
            clearInterval(config.timer);
            config.timer = null;
        }
    }
    
    // Toggle específico por tipo de datos
    toggleRefreshForDataType(dataType, enabled = null) {
        const config = this.refreshConfig[dataType];
        config.enabled = enabled !== null ? enabled : !config.enabled;
        
        if (config.enabled) {
            this.startSpecificRefresh(dataType);
        } else {
            this.stopSpecificRefresh(dataType);
        }
        
        this.updateRefreshControls();
    }
    
    // Cambiar intervalo dinámicamente
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
    
    // Backward compatibility
    async fetchAndUpdateStatus() {
        try {
            this.setLoadingState(true);
            
            // Usar endpoint de status existente para daemon info
            const statusData = await this.apiGet('/api/status');
            this.updateDaemonStatus(statusData.daemon);
            this.updateSystemStats(statusData.daemon);
            
            // Para checks individuales, usar nuevos endpoints wrapper cuando sea apropiado
            await this.refreshCheckResults();
            
            this.updateLastUpdated();
            
        } catch (error) {
            console.error('Error fetching status:', error);
            this.handleError(error);
        } finally {
            this.setLoadingState(false);
        }
    }
    
    async fetchAndUpdateConfig() {
        try {
            const config = await this.apiGet('/api/config');
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
        messageElement.textContent = result.message;
        
        // Update timestamp
        const timestampElement = card.querySelector('[id$="-check-timestamp"]');
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
            indexInfo.classList.remove('hidden');
            
            const stats = details.doc_index_stats;
            modulesElement.textContent = stats.total_modules || 0;
            filesElement.textContent = stats.total_files || 0;
            purposesElement.textContent = stats.total_purposes_found || 0;
        } else {
            indexInfo.classList.add('hidden');
        }
    }
    
    updateTokenInfo(details) {
        const tokenInfo = document.getElementById('git-check-tokens');
        const tokenCount = document.getElementById('git-token-count');
        const tokenThreshold = document.getElementById('git-token-threshold');
        const tokenWarning = document.getElementById('git-token-warning');
        
        if (details.token_info) {
            tokenInfo.classList.remove('hidden');
            tokenCount.textContent = details.token_info.token_count.toLocaleString();
            
            // Set threshold display
            const threshold = details.token_warning ? details.token_warning.threshold : 50000;
            tokenThreshold.textContent = `/ ${threshold.toLocaleString()}`;
            
            // Set warning status
            if (details.token_warning) {
                tokenWarning.textContent = '⚠️ Exceeds threshold!';
                tokenWarning.className = 'font-bold text-red-600 ml-2';
            } else {
                tokenWarning.textContent = '✅ Within limits';
                tokenWarning.className = 'font-medium text-green-600 ml-2';
            }
        } else {
            tokenInfo.classList.add('hidden');
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
            testInfo.classList.remove('hidden');
            
            missingCount.textContent = details.missing_count || 0;
            passingCount.textContent = details.passing_count || 0;
            failingCount.textContent = details.failing_count || 0;
            orphanedCount.textContent = details.orphaned_count || 0;
            unitCount.textContent = `${details.unit_tests || 0} Unit`;
            integrationCount.textContent = `${details.integration_tests || 0} Integration`;
        } else {
            testInfo.classList.add('hidden');
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
            indicator.className = 'w-3 h-3 rounded-full bg-red-500 shadow-lg transition-all';
            text.textContent = 'Connection Error';
            text.className = 'text-gray-700';
        }
        
        // Show error in system stats with null checks
        const uptimeElement = document.getElementById('uptime');
        const totalChecksElement = document.getElementById('total-checks');
        const lastCheckElement = document.getElementById('last-check');
        
        if (uptimeElement) uptimeElement.textContent = 'Error';
        if (totalChecksElement) totalChecksElement.textContent = 'Error';
        if (lastCheckElement) lastCheckElement.textContent = 'Error';
    }
    
    // === NOTIFICATION SYSTEM ===
    
    // Método para mostrar notificaciones temporales
    showNotification(message, type = 'info', duration = 5000) {
        const notificationContainer = this.getOrCreateNotificationContainer();
        
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
    
    getOrCreateNotificationContainer() {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(container);
        }
        return container;
    }
    
    // Estados de loading mejorados
    setLoadingState(isLoading, target = null) {
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
            // Global loading state
            this.isLoading.global = isLoading;
            this.updateLoadingIndicators();
        }
    }
    
    updateLoadingIndicators() {
        const indicator = document.getElementById('global-loading-indicator');
        if (indicator) {
            indicator.style.display = this.isLoading.global ? 'block' : 'none';
        }
    }
    
    // === ACTIVITY DETECTION SYSTEM ===
    
    setupActivityDetection() {
        // Eventos que indican actividad del usuario
        const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
        
        activityEvents.forEach(event => {
            document.addEventListener(event, () => {
                this.handleUserActivity();
            }, true);
        });
        
        // Detección de visibilidad de página
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
            this.resumeAutoRefresh();
            this.wasActiveRefresh = true;
        }
        
        // Set new inactivity timer
        this.userActivityTimer = setTimeout(() => {
            this.handleUserInactivity();
        }, this.inactivityTimeout);
    }
    
    handleUserInactivity() {
        console.log('User inactive, slowing down refresh...');
        
        // Slow down refresh instead of stopping completely
        this.setRefreshInterval('daemon_status', 10000); // 10s instead of 3s
        this.setRefreshInterval('check_results', 30000);  // 30s instead of 10s
        
        this.showNotification('Slowed refresh due to inactivity', 'info', 3000);
    }
    
    handlePageHidden() {
        console.log('Page hidden, pausing refresh...');
        this.pauseAutoRefresh();
        this.wasActiveRefresh = false;
    }
    
    handlePageVisible() {
        console.log('Page visible, resuming refresh...');
        this.resumeAutoRefresh();
        this.wasActiveRefresh = true;
        
        // Immediately refresh to get latest data
        this.fetchAndUpdateStatus();
    }
    
    updateRefreshControls() {
        // Placeholder for updating UI refresh controls
        console.log('Refresh controls updated');
    }
    
    async loadArchitectureDiagram() {
        try {
            console.log('Loading architecture diagram...');
            
            const data = await this.apiGet('/api/architecture/diagram');
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
    if (!dashboard) {
        console.error('Dashboard not initialized');
        return;
    }
    
    console.log('Regenerating architecture diagram...');
    
    // Disable button
    const button = event.target;
    button.disabled = true;
    button.textContent = 'Regenerating...';
    
    try {
        const result = await dashboard.apiPost('/api/architecture/regenerate');
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
    if (!dashboard) {
        console.error('Dashboard not initialized');
        return;
    }
    
    console.log('Generating component tree...');
    
    // Disable button
    const button = event.target;
    button.disabled = true;
    button.textContent = 'Generating...';
    
    try {
        const result = await dashboard.apiGet('/api/ui-designer/component-tree');
        
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
    if (!dashboard) {
        console.error('Dashboard not initialized');
        return;
    }
    
    console.log('Refreshing component tree...');
    
    // Disable button
    const button = event.target;
    button.disabled = true;
    button.textContent = 'Refreshing...';
    
    try {
        const result = await dashboard.apiGet('/api/ui-designer/component-tree');
        
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

// Global functions for button clicks - Updated to use new wrapper endpoints
async function runCheck(checkName) {
    if (!dashboard) {
        console.error('Dashboard not initialized');
        return;
    }
    
    console.log(`Running check: ${checkName}`);
    
    const button = event.target;
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Running...';
    
    try {
        let result;
        
        // Usar endpoint wrapper apropiado basado en el tipo de check
        switch (checkName) {
            case 'doc_check':
                result = await dashboard.generateDocumentation();
                break;
            case 'git_check':
                result = await dashboard.analyzeGitChanges();
                break;
            case 'test_check':
                // Usar endpoint refactorizado existente
                result = await dashboard.apiPost(`/api/checks/${checkName}/run`);
                break;
            default:
                result = await dashboard.apiPost(`/api/checks/${checkName}/run`);
        }
        
        if (result.success) {
            console.log(`Check ${checkName} executed successfully`);
            dashboard.showNotification(`${checkName} started successfully`, 'success');
        } else {
            console.error(`Check ${checkName} failed:`, result.error);
            dashboard.showNotification(`${checkName} failed: ${result.error}`, 'error');
        }
        
    } catch (error) {
        console.error(`Error running check ${checkName}:`, error);
        dashboard.showNotification(`Error running ${checkName}`, 'error');
        
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}

// Nueva función para generar diseño
async function generateDesign() {
    if (!dashboard) {
        console.error('Dashboard not initialized');
        return;
    }
    
    const button = event.target;
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Generating...';
    
    try {
        await dashboard.generateDesign({
            directory: 'autocode/',
            output_dir: 'design/'
        });
        
    } catch (error) {
        console.error('Error generating design:', error);
        
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}

// Controles para auto-refresh
function toggleAutoRefresh() {
    if (!dashboard) {
        console.error('Dashboard not initialized');
        return;
    }
    
    const button = document.getElementById('pause-refresh-btn');
    
    if (dashboard.updatePaused) {
        dashboard.resumeAutoRefresh();
        if (button) button.textContent = 'Pause';
    } else {
        dashboard.pauseAutoRefresh();
        if (button) button.textContent = 'Resume';
    }
}

function changeRefreshSpeed(speed) {
    if (!dashboard) {
        console.error('Dashboard not initialized');
        return;
    }
    
    const intervals = {
        'fast': { daemon_status: 2000, check_results: 5000 },
        'normal': { daemon_status: 3000, check_results: 10000 },
        'slow': { daemon_status: 5000, check_results: 20000 }
    };
    
    const config = intervals[speed];
    if (config) {
        Object.keys(config).forEach(dataType => {
            dashboard.setRefreshInterval(dataType, config[dataType]);
        });
        
        dashboard.showNotification(`Refresh speed changed to ${speed}`, 'info', 2000);
    }
}

async function updateConfig() {
    if (!dashboard) {
        console.error('Dashboard not initialized');
        return;
    }
    
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
        const result = await dashboard.apiPut('/api/config', config);
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
