# Task 010: Refactorización de app.js en Estructura Modular

## Contexto del Proyecto
Este proyecto, autocode, es una herramienta para automatizar tareas de calidad de código, documentación, tests y análisis Git. Incluye una interfaz web con un dashboard que permite monitorear el estado del sistema en tiempo real. El archivo JavaScript principal (`autocode/web/static/app.js`) ha crecido hasta convertirse en un archivo monolítico de ~500 líneas que maneja toda la lógica del frontend, desde llamadas API hasta manipulación del DOM.

## Estado Actual de app.js
El archivo `autocode/web/static/app.js` contiene una clase monolítica `AutocodeDashboard` que maneja múltiples responsabilidades:

### Estructura Actual del Archivo
```javascript
// Clase monolítica con múltiples responsabilidades
class AutocodeDashboard {
    constructor() {
        // Configuración de refresh, timers, estado
        this.refreshConfig = { ... };
        this.isLoading = {};
        this.lastUpdate = {};
        this.updatePaused = false;
        this.currentPage = this.getCurrentPage();
        // ... más propiedades
    }
    
    // === API METHODS (consolidated from APIClient) ===
    async apiGet(endpoint) { /* ~20 líneas */ }
    async apiPost(endpoint, data = null) { /* ~20 líneas */ }
    async apiPut(endpoint, data) { /* ~15 líneas */ }
    async apiDelete(endpoint) { /* ~10 líneas */ }
    
    // === NEW WRAPPER ENDPOINTS ===
    async generateDocumentation() { /* ~25 líneas */ }
    async generateDesign(options = {}) { /* ~30 líneas */ }
    async analyzeGitChanges(options = {}) { /* ~25 líneas */ }
    async loadConfigurationData() { /* ~15 líneas */ }
    
    // === INITIALIZATION ===
    init() { /* ~10 líneas */ }
    getCurrentPage() { /* ~10 líneas */ }
    setupNavigation() { /* ~10 líneas */ }
    async loadInitialData() { /* ~10 líneas */ }
    
    // === CONFIG PAGE METHODS ===
    async loadConfigPage() { /* ~10 líneas */ }
    populateConfigForm(config) { /* ~40 líneas */ }
    setCheckboxValue(id, value) { /* ~5 líneas */ }
    setInputValue(id, value) { /* ~5 líneas */ }
    setTextareaValue(id, value) { /* ~5 líneas */ }
    setupConfigFormHandlers() { /* ~20 líneas */ }
    async saveConfiguration() { /* ~30 líneas */ }
    async resetConfiguration() { /* ~50 líneas */ }
    getConfigFromForm() { /* ~60 líneas */ }
    validateConfigForm() { /* ~40 líneas */ }
    showConfigMessage(message, type) { /* ~15 líneas */ }
    
    // === INTELLIGENT AUTO-REFRESH SYSTEM ===
    startAutoRefresh() { /* ~10 líneas */ }
    startSpecificRefresh(dataType) { /* ~15 líneas */ }
    async refreshSpecificData(dataType) { /* ~20 líneas */ }
    async refreshDaemonStatus() { /* ~10 líneas */ }
    async refreshCheckResults() { /* ~20 líneas */ }
    async refreshConfigData() { /* ~10 líneas */ }
    async refreshDesignContent() { /* ~10 líneas */ }
    async getCheckResult(checkName) { /* ~10 líneas */ }
    pauseAutoRefresh() { /* ~10 líneas */ }
    resumeAutoRefresh() { /* ~5 líneas */ }
    stopAutoRefresh() { /* ~10 líneas */ }
    // ... más métodos de refresh (~15 métodos más)
    
    // === UI UPDATE METHODS ===
    async fetchAndUpdateStatus() { /* ~25 líneas */ }
    async fetchAndUpdateConfig() { /* ~10 líneas */ }
    updateUI(data) { /* ~15 líneas */ }
    updateDaemonStatus(daemon) { /* ~15 líneas */ }
    updateSystemStats(daemon) { /* ~25 líneas */ }
    updateCheckResults(checks) { /* ~10 líneas */ }
    updateCheckCard(checkName, result) { /* ~80 líneas */ }
    updateDocIndexInfo(details) { /* ~15 líneas */ }
    updateTokenInfo(details) { /* ~25 líneas */ }
    updateTestInfo(details) { /* ~20 líneas */ }
    formatTestDetails(details) { /* ~30 líneas */ }
    updateConfigUI(config) { /* ~35 líneas */ }
    
    // === UTILITY METHODS ===
    formatDuration(seconds) { /* ~10 líneas */ }
    formatTimestamp(timestamp) { /* ~5 líneas */ }
    formatGitDetails(details) { /* ~20 líneas */ }
    updateLastUpdated() { /* ~5 líneas */ }
    updateRefreshStatus(status) { /* ~5 líneas */ }
    handleError(error) { /* ~20 líneas */ }
    
    // === NOTIFICATION SYSTEM ===
    showNotification(message, type = 'info', duration = 5000) { /* ~25 líneas */ }
    getOrCreateNotificationContainer() { /* ~10 líneas */ }
    setLoadingState(isLoading, target = null) { /* ~15 líneas */ }
    updateLoadingIndicators() { /* ~5 líneas */ }
    
    // === ACTIVITY DETECTION SYSTEM ===
    setupActivityDetection() { /* ~15 líneas */ }
    handleUserActivity() { /* ~15 líneas */ }
    handleUserInactivity() { /* ~10 líneas */ }
    handlePageHidden() { /* ~5 líneas */ }
    handlePageVisible() { /* ~10 líneas */ }
    updateRefreshControls() { /* ~5 líneas */ }
    
    // === ARCHITECTURE DIAGRAM METHODS ===
    async loadArchitectureDiagram() { /* ~15 líneas */ }
    renderArchitectureDiagram(data) { /* ~40 líneas */ }
    handleArchitectureError(error) { /* ~20 líneas */ }
    renderComponentTree(data) { /* ~40 líneas */ }
    handleComponentTreeError(error) { /* ~20 líneas */ }
}

// === GLOBAL FUNCTIONS ===
async function refreshArchitecture() { /* ~20 líneas */ }
async function regenerateArchitecture() { /* ~25 líneas */ }
async function generateComponentTree() { /* ~25 líneas */ }
async function refreshComponentTree() { /* ~25 líneas */ }
async function runCheck(checkName) { /* ~40 líneas */ }
async function generateDesign() { /* ~20 líneas */ }
function toggleAutoRefresh() { /* ~15 líneas */ }
function changeRefreshSpeed(speed) { /* ~15 líneas */ }
async function updateConfig() { /* ~30 líneas */ }

// === INITIALIZATION ===
let dashboard;
document.addEventListener('DOMContentLoaded', function() { /* ~30 líneas */ });
window.addEventListener('beforeunload', function() { /* ~5 líneas */ });

// Total: ~500+ líneas en un solo archivo
```

### Problemas del Estado Actual
1. **Monolítico**: Una sola clase con >20 responsabilidades diferentes
2. **Difícil mantenimiento**: Cambios pequeños requieren tocar un archivo enorme
3. **Acoplamiento alto**: Métodos API mezclados con lógica de UI y refresh
4. **Testing difícil**: Imposible testear componentes individuales
5. **Reutilización limitada**: Funciones útiles encapsuladas en la clase monolítica
6. **Navegación compleja**: Encontrar código específico en 500+ líneas es difícil

## Objetivo de la Refactorización
Dividir `app.js` en una estructura modular organizada por responsabilidades, manteniendo toda la funcionalidad existente pero con mejor separación de concerns.

### Estructura de Carpetas Propuesta
```
autocode/web/static/js/
├── api/
│   ├── api-client.js          # Métodos HTTP base (GET, POST, PUT, DELETE)
│   └── api-wrappers.js        # Wrappers específicos (generateDocumentation, etc.)
├── components/
│   ├── dashboard.js           # Lógica específica del dashboard
│   ├── config-manager.js      # Manejo de configuración y forms
│   ├── diagram-renderer.js    # Renderizado de diagramas (Mermaid)
│   └── refresh-system.js      # Sistema de auto-refresh inteligente
├── utils/
│   ├── formatters.js          # Funciones de formato (duration, timestamp, etc.)
│   ├── notifications.js       # Sistema de notificaciones
│   ├── activity-detector.js   # Detección de actividad del usuario
│   └── dom-helpers.js         # Helpers para manipulación del DOM
├── core/
│   └── app-manager.js         # Clase principal coordinadora
└── app.js                     # Entry point (importa y inicializa todo)
```

### Distribución de Responsabilidades

#### api/api-client.js (~50 líneas)
- Métodos HTTP base: `apiGet`, `apiPost`, `apiPut`, `apiDelete`
- Manejo de errores de red
- Configuración base de fetch

#### api/api-wrappers.js (~80 líneas)
- Wrappers específicos: `generateDocumentation`, `generateDesign`, `analyzeGitChanges`
- `loadConfigurationData`
- Lógica específica de cada endpoint

#### components/dashboard.js (~100 líneas)
- `updateDaemonStatus`, `updateSystemStats`
- `updateCheckCard`, `updateCheckResults`
- `updateDocIndexInfo`, `updateTokenInfo`, `updateTestInfo`
- Lógica específica del dashboard

#### components/config-manager.js (~120 líneas)
- `populateConfigForm`, `setupConfigFormHandlers`
- `saveConfiguration`, `resetConfiguration`
- `getConfigFromForm`, `validateConfigForm`
- Todo el manejo de configuración

#### components/diagram-renderer.js (~80 líneas)
- `renderArchitectureDiagram`, `renderComponentTree`
- `loadArchitectureDiagram`
- `handleArchitectureError`, `handleComponentTreeError`
- Integración con Mermaid

#### components/refresh-system.js (~100 líneas)
- `startAutoRefresh`, `startSpecificRefresh`
- `refreshSpecificData`, `pauseAutoRefresh`
- Todo el sistema de refresh inteligente
- Configuración de intervalos

#### utils/formatters.js (~40 líneas)
- `formatDuration`, `formatTimestamp`
- `formatGitDetails`, `formatTestDetails`
- Funciones puras de formato

#### utils/notifications.js (~30 líneas)
- `showNotification`, `getOrCreateNotificationContainer`
- Sistema de notificaciones temporales

#### utils/activity-detector.js (~40 líneas)
- `setupActivityDetection`, `handleUserActivity`
- `handleUserInactivity`, `handlePageHidden`, `handlePageVisible`
- Detección de actividad

#### utils/dom-helpers.js (~30 líneas)
- `setLoadingState`, `updateLoadingIndicators`
- Helpers para manipulación del DOM

#### core/app-manager.js (~60 líneas)
- Clase principal que coordina todos los módulos
- `init`, `getCurrentPage`, `setupNavigation`
- Gestión del estado global

#### app.js (~40 líneas)
- Entry point simple
- Imports de todos los módulos
- Inicialización y event listeners globales

## Instrucciones Paso a Paso

### 1. Crear Estructura de Carpetas
```bash
cd autocode/web/static
mkdir -p js/api js/components js/utils js/core
```

### 2. Crear api/api-client.js
```javascript
// Extraer métodos HTTP base
export class APIClient {
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
                headers: { 'Content-Type': 'application/json' }
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
    
    async put(endpoint, data) {
        try {
            const response = await fetch(endpoint, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
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
    
    async delete(endpoint) {
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
}
```

### 3. Crear api/api-wrappers.js
```javascript
// Importar APIClient
import { APIClient } from './api-client.js';
import { showNotification } from '../utils/notifications.js';

export class APIWrappers {
    constructor() {
        this.apiClient = new APIClient();
    }
    
    async generateDocumentation() {
        try {
            console.log('Generating documentation...');
            const response = await this.apiClient.post('/api/generate-docs');
            
            if (response.success) {
                showNotification('Documentation generation started', 'success');
                // Auto-refresh logic here
            } else {
                showNotification(`Documentation error: ${response.error}`, 'error');
            }
            
            return response;
        } catch (error) {
            console.error('Error generating documentation:', error);
            showNotification('Failed to start documentation generation', 'error');
            throw error;
        }
    }
    
    async generateDesign(options = {}) {
        // Similar structure
    }
    
    async analyzeGitChanges(options = {}) {
        // Similar structure
    }
    
    async loadConfigurationData() {
        // Similar structure
    }
}
```

### 4. Crear utils/formatters.js
```javascript
// Funciones puras de formato
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
    
    return output;
}
```

### 5. Crear utils/notifications.js
```javascript
// Sistema de notificaciones
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
```

### 6. Crear core/app-manager.js
```javascript
// Clase principal coordinadora
import { APIWrappers } from '../api/api-wrappers.js';
import { DashboardComponents } from '../components/dashboard.js';
import { ConfigManager } from '../components/config-manager.js';
import { RefreshSystem } from '../components/refresh-system.js';
import { ActivityDetector } from '../utils/activity-detector.js';

export class AppManager {
    constructor() {
        this.apiWrappers = new APIWrappers();
        this.dashboard = new DashboardComponents();
        this.configManager = new ConfigManager();
        this.refreshSystem = new RefreshSystem();
        this.activityDetector = new ActivityDetector();
        
        this.currentPage = this.getCurrentPage();
        this.updatePaused = false;
    }
    
    getCurrentPage() {
        const path = window.location.pathname;
        if (path === '/ui-designer') return 'ui-designer';
        if (path === '/design') return 'design';
        if (path === '/config') return 'config';
        return 'dashboard';
    }
    
    init() {
        console.log('Initializing Autocode Dashboard');
        this.setupNavigation();
        this.activityDetector.setup();
        this.refreshSystem.start();
        this.loadInitialData();
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
            await this.dashboard.loadDashboardData();
        } else if (this.currentPage === 'config') {
            await this.configManager.loadConfigPage();
        }
    }
}
```

### 7. Crear Archivo app.js Principal (Nuevo)
```javascript
// Entry point principal - solo imports e inicialización
import { AppManager } from './js/core/app-manager.js';

// Global app instance
let appManager;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    appManager = new AppManager();
    appManager.init();
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Space bar to refresh
        if (event.code === 'Space' && event.target.tagName !== 'INPUT') {
            event.preventDefault();
            appManager.refreshSystem.refreshAll();
        }
        
        // 'R' to toggle auto-refresh
        if (event.code === 'KeyR' && event.target.tagName !== 'INPUT') {
            event.preventDefault();
            appManager.refreshSystem.toggle();
        }
    });
    
    // Handle visibility changes
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            appManager.refreshSystem.pause();
        } else {
            appManager.refreshSystem.resume();
        }
    });
});

// Handle page unload
window.addEventListener('beforeunload', function() {
    if (appManager) {
        appManager.refreshSystem.stop();
    }
});

// Export global functions needed by HTML templates
window.runCheck = async function(checkName) {
    return await appManager.apiWrappers.executeCheck(checkName);
};

window.generateDesign = async function() {
    return await appManager.apiWrappers.generateDesign();
};

window.toggleAutoRefresh = function() {
    appManager.refreshSystem.toggle();
};

// ... más funciones globales según sea necesario
```

### 8. Actualizar Templates HTML
En los templates HTML (como `autocode/web/templates/base.html` o `index.html`), actualizar la carga del script:

```html
<!-- Cambiar de: -->
<script src="/static/app.js"></script>

<!-- A: -->
<script type="module" src="/static/app.js"></script>
```

### 9. Verificar que No Hay Referencias Rotas
Buscar todas las referencias a `dashboard` en templates HTML y asegurar que las funciones globales estén disponibles.

## Criterios de Verificación

### 1. Estructura de Archivos Creada
```bash
# Verificar que existan todos los archivos
ls -la autocode/web/static/js/api/
ls -la autocode/web/static/js/components/
ls -la autocode/web/static/js/utils/
ls -la autocode/web/static/js/core/
ls -la autocode/web/static/app.js
```

### 2. Archivos Deben Tener Tamaño Apropiado
```bash
# Ningún archivo debe superar las 150 líneas
wc -l autocode/web/static/js/**/*.js
wc -l autocode/web/static/app.js

# app.js debe ser <50 líneas
# Archivos individuales deben ser <150 líneas cada uno
```

### 3. Sin Errores de Sintaxis JavaScript
```bash
# Si tienes Node.js instalado, verificar sintaxis
node -c autocode/web/static/app.js
node -c autocode/web/static/js/api/api-client.js
# ... para cada archivo
```

### 4. Imports/Exports Funcionan
```bash
# Ejecutar el daemon y verificar que no hay errores de imports en consola
uv run autocode daemon
# Abrir http://127.0.0.1:8080/dashboard en navegador
# Verificar en Developer Tools que no hay errores de módulos
```

### 5. Funcionalidad Completa Mantenida
Probar todas las funcionalidades principales:

```bash
# En navegador (http://127.0.0.1:8080/dashboard):
# 1. Auto-refresh debe funcionar (ver timestamps actualizándose)
# 2. Botones "Run Check" deben funcionar
# 3. Navegación entre páginas (/dashboard, /design, /config)
# 4. Configuración debe cargarse y guardarse
# 5. Notificaciones deben aparecer
# 6. Diagramas deben renderizarse
# 7. Detección de actividad debe funcionar
```

### 6. Compatibilidad con Navegadores
Probar en al menos Chrome/Firefox que:
- Los módulos ES6 cargan correctamente
- No hay errores en consola
- Todas las funciones siguen funcionando

### 7. Performance No Debe Degradarse
- El tiempo de carga inicial debe ser similar o mejor
- Auto-refresh debe mantener su comportamiento
- No debe haber memory leaks evidentes

### 8. Código Debe Ser Más Mantenible
```bash
# Verificar que es más fácil encontrar código específico:
# - API calls están en js/api/
# - UI updates están en js/components/
# - Utilities están en js/utils/
# - Lógica principal está en js/core/
```

## Template de Commit Message
```
refactor(frontend): modularize app.js into organized component structure

- Split monolithic 500+ line app.js into focused modules
- Created api/, components/, utils/, core/ directories under js/
- Extracted API client and wrappers into separate files
- Separated dashboard, config, and diagram components
- Moved utilities (formatters, notifications, activity detection) to utils/
- Created AppManager as central coordinator
- Reduced main app.js to <50 lines (entry point only)
- Maintained 100% functionality while improving maintainability
- Added ES6 modules with proper imports/exports
- All files now <150 lines for better readability

Files changed:
- Split: app.js -> 10+ focused modules
- Updated: HTML templates to use type="module"
- Maintained: All existing functionality and APIs
