# Task 011: Actualización y Verificación de la UI Funcional

## Contexto del Proyecto
Este proyecto, autocode, es una herramienta para automatizar tareas de calidad de código, documentación, tests y análisis Git. Después de las refactorizaciones de la API (migración a thin CLI layer) y del frontend (modularización de app.js), necesitamos asegurar que la interfaz de usuario siga funcionando completamente e integrar todos los cambios para que trabajen cohesivamente.

## Estado Actual Post-Refactorizaciones
Después de completar las Tasks 008, 009 y 010, el sistema debería tener:

### API Simplificada (Post-Task 008 y 009)
```python
# En autocode/api/server.py - Solo wrappers CLI y páginas:

# CLI Wrappers disponibles:
@app.post("/api/generate-docs")           # Invoca check_docs
@app.post("/api/generate-design")         # Invoca code_to_design  
@app.post("/api/analyze-git")             # Invoca git_changes
@app.get("/api/config/load")              # Invoca load_config
@app.post("/api/check-tests")             # Invoca check_tests
@app.post("/api/opencode")                # Invoca opencode
@app.post("/api/count-tokens")            # Invoca count_tokens

# Páginas (sin cambios):
@app.get("/")                             # Redirect a dashboard
@app.get("/dashboard")                    # Dashboard page
@app.get("/design")                       # Design page  
@app.get("/config")                       # Config page
@app.get("/health")                       # Health check

# Archivos estáticos (sin cambios):
app.mount("/static", StaticFiles(...))
app.mount("/design", StaticFiles(...))

# Endpoints ELIMINADOS (devuelven 404):
# /api/status, /api/daemon/status, /api/checks, /api/checks/{check_name}
# /api/config (PUT/GET), /api/tokens/count, /api/scheduler/tasks
# /api/architecture/diagram, /api/ui-designer/component-tree, etc.
```

### Frontend Modularizado (Post-Task 010)
```
autocode/web/static/
├── js/
│   ├── api/
│   │   ├── api-client.js          # Métodos HTTP base
│   │   └── api-wrappers.js        # Wrappers específicos
│   ├── components/
│   │   ├── dashboard.js           # Lógica del dashboard
│   │   ├── config-manager.js      # Manejo de configuración
│   │   ├── diagram-renderer.js    # Renderizado de diagramas
│   │   └── refresh-system.js      # Sistema de auto-refresh
│   ├── utils/
│   │   ├── formatters.js          # Funciones de formato
│   │   ├── notifications.js       # Sistema de notificaciones
│   │   ├── activity-detector.js   # Detección de actividad
│   │   └── dom-helpers.js         # Helpers para DOM
│   └── core/
│       └── app-manager.js         # Clase coordinadora principal
└── app.js                         # Entry point modular
```

### Templates HTML Actuales
```html
<!-- autocode/web/templates/base.html -->
<!-- Cabecera, navegación, scripts base -->

<!-- autocode/web/templates/pages/dashboard.html -->
<!-- Dashboard con tarjetas de checks, botones, stats -->

<!-- autocode/web/templates/pages/design.html -->  
<!-- Página de diseño con diagramas -->

<!-- autocode/web/templates/pages/config.html -->
<!-- Página de configuración con forms -->
```

## Problemas de Integración Esperados
Después de las refactorizaciones, estos problemas son probables:

### 1. Llamadas API Rotas en JavaScript
```javascript
// PROBLEMA: El frontend modular puede estar usando endpoints eliminados
// Ejemplo en el app.js anterior:
async refreshCheckResults() {
    const checks = ['doc_check', 'git_check', 'test_check'];
    const checkPromises = checks.map(checkName => this.getCheckResult(checkName));
    // ... donde getCheckResult podría llamar a /api/checks/{checkName} (ELIMINADO)
}

async fetchAndUpdateStatus() {
    const statusData = await this.apiGet('/api/status'); // ELIMINADO
    // ...
}
```

### 2. Referencias a Métodos No Existentes
```javascript
// PROBLEMA: HTML templates pueden referenciar funciones que no existen
// En dashboard.html:
<button onclick="runCheck('doc_check')">Run Doc Check</button>
<!-- Pero runCheck podría no estar definido en el nuevo app.js modular -->
```

### 3. Configuración de Módulos ES6
```html
<!-- PROBLEMA: Templates pueden no cargar módulos correctamente -->
<script src="/static/app.js"></script>
<!-- Debería ser: -->
<script type="module" src="/static/app.js"></script>
```

### 4. Auto-refresh Roto
```javascript
// PROBLEMA: Sistema de refresh puede fallar sin endpoints de status
// El sistema espera poder obtener estado del daemon:
async refreshDaemonStatus() {
    await this.apiGet('/api/daemon/status'); // ELIMINADO
}
```

### 5. Datos Faltantes para UI
```javascript
// PROBLEMA: UI components esperan datos que ya no están disponibles
updateCheckCard(checkName, result) {
    // Espera result.status, result.message, result.timestamp
    // Pero los nuevos wrappers CLI solo devuelven {success: true/false, error: string}
}
```

## Objetivo de la Integración
Actualizar completamente la UI para que:
1. **Use solo los nuevos wrappers CLI**: Eliminar todas las llamadas a endpoints legacy
2. **Funcione con datos CLI**: Adaptar componentes para trabajar con salidas CLI reales
3. **Mantenga toda la funcionalidad**: Auto-refresh, notificaciones, diagramas, configuración
4. **Sea compatible con módulos ES6**: Imports/exports funcionando correctamente
5. **Proporcione experiencia de usuario equivalente**: Misma usabilidad que antes

## Instrucciones Paso a Paso

### 1. Actualizar Templates HTML para Módulos ES6

#### 1.1 Actualizar autocode/web/templates/base.html  
```html
<!-- Buscar la línea de carga de script y cambiar: -->
<!-- ANTES: -->
<script src="/static/app.js"></script>

<!-- DESPUÉS: -->
<script type="module" src="/static/app.js"></script>
```

#### 1.2 Verificar Compatibilidad de Navegadores
Añadir fallback para navegadores que no soportan módulos:
```html
<script type="module" src="/static/app.js"></script>
<script nomodule>
    alert('Este navegador no soporta módulos ES6. Por favor actualiza tu navegador.');
</script>
```

### 2. Implementar Adapter para Datos CLI en Frontend

#### 2.1 Crear js/utils/cli-adapter.js
```javascript
// Adapter para convertir salidas CLI en formato UI
export class CLIAdapter {
    // Convierte respuesta CLI wrapper en formato de check result
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
                message: `${checkName} completed successfully`,
                timestamp: new Date().toISOString(),
                details: cliResponse.result || null
            };
        } else {
            return {
                status: 'error', 
                message: cliResponse.error || 'Unknown error',
                timestamp: new Date().toISOString(),
                details: null
            };
        }
    }
    
    // Simula daemon status basado en health check
    static async getDaemonStatus(apiClient) {
        try {
            const health = await apiClient.get('/health');
            return {
                is_running: health.status === 'healthy',
                uptime_seconds: 0, // No disponible sin daemon real
                total_checks_run: 0, // No disponible
                last_check_run: null // No disponible
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
}
```

#### 2.2 Actualizar api/api-wrappers.js para usar adapter
```javascript
import { CLIAdapter } from '../utils/cli-adapter.js';

export class APIWrappers {
    // ... constructor existing
    
    async executeCheck(checkName) {
        try {
            let response;
            
            // Mapear check names a wrappers específicos
            switch (checkName) {
                case 'doc_check':
                    response = await this.generateDocumentation();
                    break;
                case 'git_check':
                    response = await this.analyzeGitChanges();
                    break;
                case 'test_check':
                    response = await this.checkTests();
                    break;
                default:
                    throw new Error(`Unknown check: ${checkName}`);
            }
            
            // Convertir respuesta CLI a formato UI
            return CLIAdapter.adaptCheckResult(response, checkName);
            
        } catch (error) {
            console.error(`Error executing check ${checkName}:`, error);
            return CLIAdapter.adaptCheckResult(null, checkName);
        }
    }
    
    async checkTests() {
        try {
            const response = await this.apiClient.post('/api/check-tests');
            
            if (response.success) {
                showNotification('Test check started', 'success');
            } else {
                showNotification(`Test check error: ${response.error}`, 'error');
            }
            
            return response;
        } catch (error) {
            console.error('Error checking tests:', error);
            throw error;
        }
    }
    
    async getDaemonStatus() {
        return await CLIAdapter.getDaemonStatus(this.apiClient);
    }
}
```

### 3. Actualizar Sistema de Refresh

#### 3.1 Modificar components/refresh-system.js
```javascript
import { CLIAdapter } from '../utils/cli-adapter.js';

export class RefreshSystem {
    constructor(apiWrappers, dashboard) {
        this.apiWrappers = apiWrappers;
        this.dashboard = dashboard;
        
        // Configuración de intervalos (sin daemon real, más lentos)
        this.refreshConfig = {
            daemon_status: { interval: 10000, timer: null, enabled: true },   // 10s
            check_results: { interval: 30000, timer: null, enabled: true },   // 30s  
            config_data: { interval: 60000, timer: null, enabled: false }     // 60s
        };
        
        this.isLoading = {};
        this.lastUpdate = {};
    }
    
    async refreshDaemonStatus() {
        try {
            const daemonStatus = await this.apiWrappers.getDaemonStatus();
            this.dashboard.updateDaemonStatus(daemonStatus);
            this.dashboard.updateSystemStats(daemonStatus);
        } catch (error) {
            console.error('Error refreshing daemon status:', error);
            this.dashboard.handleError(error);
        }
    }
    
    async refreshCheckResults() {
        const checks = ['doc_check', 'git_check', 'test_check'];
        
        for (const checkName of checks) {
            try {
                // Nota: No ejecutamos checks automáticamente, solo mostramos último estado conocido
                // El estado se actualiza cuando el usuario ejecuta checks manualmente
                const cachedResult = this.getCachedCheckResult(checkName);
                if (cachedResult) {
                    this.dashboard.updateCheckCard(checkName, cachedResult);
                }
            } catch (error) {
                console.error(`Failed to refresh ${checkName}:`, error);
            }
        }
    }
    
    // Cache simple para resultados de checks
    setCachedCheckResult(checkName, result) {
        const cacheKey = `check_result_${checkName}`;
        localStorage.setItem(cacheKey, JSON.stringify({
            result: result,
            timestamp: Date.now()
        }));
    }
    
    getCachedCheckResult(checkName) {
        const cacheKey = `check_result_${checkName}`;
        const cached = localStorage.getItem(cacheKey);
        
        if (!cached) return null;
        
        try {
            const data = JSON.parse(cached);
            // Cache válida por 5 minutos
            if (Date.now() - data.timestamp < 5 * 60 * 1000) {
                return data.result;
            }
        } catch (error) {
            console.error('Error parsing cached result:', error);
        }
        
        return null;
    }
    
    // ... resto de métodos de refresh
}
```

### 4. Actualizar Funciones Globales para Templates

#### 4.1 Definir funciones globales en app.js
```javascript
// En el nuevo app.js modular:
import { AppManager } from './js/core/app-manager.js';

// Global app instance
let appManager;

// Funciones globales para HTML templates
window.runCheck = async function(checkName) {
    if (!appManager) {
        console.error('AppManager not initialized');
        return;
    }
    
    const button = event.target;
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Running...';
    
    try {
        const result = await appManager.apiWrappers.executeCheck(checkName);
        
        // Actualizar UI con resultado
        appManager.dashboard.updateCheckCard(checkName, result);
        
        // Guardar en cache para refresh system
        appManager.refreshSystem.setCachedCheckResult(checkName, result);
        
        console.log(`Check ${checkName} completed:`, result);
        
    } catch (error) {
        console.error(`Error running check ${checkName}:`, error);
        
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
};

window.generateDesign = async function() {
    if (!appManager) return;
    
    const button = event.target;
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Generating...';
    
    try {
        await appManager.apiWrappers.generateDesign({
            directory: 'autocode/',
            output_dir: 'design/'
        });
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
};

window.toggleAutoRefresh = function() {
    if (!appManager) return;
    appManager.refreshSystem.toggle();
};

window.refreshArchitecture = async function() {
    if (!appManager) return;
    
    const button = event.target;
    button.disabled = true;
    button.textContent = 'Loading...';
    
    try {
        await appManager.diagramRenderer.loadArchitectureDiagram();
    } finally {
        button.disabled = false;
        button.textContent = 'Refresh';
    }
};

window.regenerateArchitecture = async function() {
    if (!appManager) return;
    
    const button = event.target;
    button.disabled = true;
    button.textContent = 'Regenerating...';
    
    try {
        const result = await appManager.apiWrappers.generateDesign();
        
        // Wait for generation, then refresh
        setTimeout(async () => {
            await appManager.diagramRenderer.loadArchitectureDiagram();
        }, 3000);
        
    } finally {
        button.disabled = false;
        button.textContent = 'Regenerate';
    }
};

// ... más funciones globales según necesidad
```

### 5. Implementar Manejo de Configuración Sin Daemon

#### 5.1 Actualizar components/config-manager.js
```javascript
export class ConfigManager {
    constructor(apiWrappers) {
        this.apiWrappers = apiWrappers;
    }
    
    async loadConfigPage() {
        try {
            // Usar nuevo endpoint de carga de config
            const configData = await this.apiWrappers.loadConfigurationData();
            this.populateConfigForm(configData);
            this.setupConfigFormHandlers();
            
        } catch (error) {
            console.error('Error loading config page:', error);
            this.showConfigMessage('Error loading configuration', 'error');
        }
    }
    
    async saveConfiguration() {
        try {
            const saveButton = document.getElementById('save-config');
            const originalText = saveButton.textContent;
            
            saveButton.disabled = true;
            saveButton.textContent = 'Saving...';
            
            const config = this.getConfigFromForm();
            
            // Nota: Implementar endpoint /api/config/save si es necesario
            // O usar archivos de configuración directamente via CLI
            console.warn('Config save not implemented - requires new CLI wrapper');
            this.showConfigMessage('Configuration save not available (API migration)', 'warning');
            
        } catch (error) {
            console.error('Error saving configuration:', error);
            this.showConfigMessage(`Error: ${error.message}`, 'error');
            
        } finally {
            const saveButton = document.getElementById('save-config');
            saveButton.disabled = false;
            saveButton.textContent = 'Save Configuration';
        }
    }
    
    // ... resto de métodos existentes
}
```

### 6. Implementar Carga de Diagramas Sin Endpoints Legacy

#### 6.1 Actualizar components/diagram-renderer.js
```javascript
export class DiagramRenderer {
    constructor(apiWrappers) {
        this.apiWrappers = apiWrappers;
    }
    
    async loadArchitectureDiagram() {
        try {
            console.log('Loading architecture diagram...');
            
            // Usar archivos estáticos directamente en lugar de endpoint eliminado
            const response = await fetch('/design/_index.md');
            
            if (!response.ok) {
                throw new Error('Architecture diagram not found. Generate it first with code-to-design.');
            }
            
            const content = await response.text();
            this.renderArchitectureDiagram({ 
                mermaid_content: this.extractMermaidFromMarkdown(content),
                project_summary: this.extractSummaryFromMarkdown(content)
            });
            
        } catch (error) {
            console.error('Error loading architecture diagram:', error);
            this.handleArchitectureError(error);
        }
    }
    
    extractMermaidFromMarkdown(markdown) {
        const mermaidMatch = markdown.match(/```mermaid\n(.*?)\n```/s);
        return mermaidMatch ? mermaidMatch[1] : null;
    }
    
    extractSummaryFromMarkdown(markdown) {
        const summaryMatch = markdown.match(/\*\*Project Summary:\*\* (.+)/);
        return summaryMatch ? summaryMatch[1] : "Architecture diagram";
    }
    
    async generateComponentTree() {
        try {
            // En lugar del endpoint eliminado, generar usando CLI wrapper
            await this.apiWrappers.generateDesign({
                directory: 'autocode/web',
                diagrams: ['components']
            });
            
            // Luego cargar el resultado
            setTimeout(() => {
                this.loadComponentTreeFromFile();
            }, 2000);
            
        } catch (error) {
            console.error('Error generating component tree:', error);
            this.handleComponentTreeError(error);
        }
    }
    
    async loadComponentTreeFromFile() {
        try {
            // Intentar cargar desde archivo generado
            const response = await fetch('/design/autocode/web/_index.md');
            
            if (response.ok) {
                const content = await response.text();
                const mermaidContent = this.extractMermaidFromMarkdown(content);
                
                if (mermaidContent) {
                    this.renderComponentTree({
                        diagram: mermaidContent,
                        metrics: { total_components: 0, total_files: 0 } // Placeholder
                    });
                } else {
                    throw new Error('No component tree found in generated files');
                }
            } else {
                throw new Error('Component tree not found. Generate it first.');
            }
            
        } catch (error) {
            console.error('Error loading component tree:', error);
            this.handleComponentTreeError(error);
        }
    }
    
    // ... resto de métodos de renderizado
}
```

### 7. Verificar y Corregir Event Handlers en Templates

#### 7.1 Verificar dashboard.html
Buscar y verificar que todas las funciones referenciadas existan:
```html
<!-- Verificar que estas funciones estén definidas en window: -->
<button onclick="runCheck('doc_check')">Run Doc Check</button>
<button onclick="runCheck('git_check')">Run Git Check</button>
<button onclick="runCheck('test_check')">Run Test Check</button>
<button onclick="generateDesign()">Generate Design</button>
<button onclick="toggleAutoRefresh()">Toggle Refresh</button>
```

#### 7.2 Verificar design.html
```html
<button onclick="refreshArchitecture()">Refresh</button>
<button onclick="regenerateArchitecture()">Regenerate</button>
<button onclick="generateComponentTree()">Generate Tree</button>
```

#### 7.3 Verificar config.html
```html
<!-- Verificar que estos elementos y funciones existan: -->
<button onclick="appManager.configManager.saveConfiguration()">Save</button>
<button onclick="appManager.configManager.resetConfiguration()">Reset</button>
```

### 8. Implementar Fallbacks para Funcionalidad Faltante

#### 8.1 Crear js/utils/fallbacks.js
```javascript
// Fallbacks para funcionalidad que dependía del daemon
export class UIFallbacks {
    static getDefaultDaemonStatus() {
        return {
            is_running: true, // Asumimos que está running si la página carga
            uptime_seconds: 0,
            total_checks_run: 0,
            last_check_run: null
        };
    }
    
    static getDefaultCheckResult(checkName) {
        return {
            status: 'unknown',
            message: `${checkName} not run yet. Click 'Run Check' to execute.`,
            timestamp: new Date().toISOString(),
            details: null
        };
    }
    
    static simulateSystemStats() {
        return {
            uptime: '--',
            total_checks: '--',
            last_check: '--'
        };
    }
}
```

## Criterios de Verificación

### 1. Daemon Debe Arrancar Sin Errores
```bash
cd /path/to/autocode
uv run autocode daemon
# Debe arrancar y mostrar:
# 🚀 Starting Autocode Monitoring Daemon
# 🌐 Web Interface: http://127.0.0.1:8080
# Sin errores en logs
```

### 2. Todas las Páginas Deben Cargar
```bash
# Verificar en navegador (preferiblemente Chrome/Firefox):
# http://127.0.0.1:8080/           -> Debe redirigir a dashboard
# http://127.0.0.1:8080/dashboard  -> Dashboard funcional
# http://127.0.0.1:8080/design     -> Página de diseño
# http://127.0.0.1:8080/config     -> Página de configuración

# Verificar en Developer Tools (F12) que NO hay:
# - Errores de módulos ES6
# - Referencias a funciones undefined
# - Errores de fetch a endpoints eliminados
```

### 3. Botones de Checks Deben Funcionar
```bash
# En dashboard (http://127.0.0.1:8080/dashboard):
# 1. Click "Run Doc Check" -> Debe ejecutar sin errores
# 2. Click "Run Git Check" -> Debe ejecutar sin errores  
# 3. Click "Run Test Check" -> Debe ejecutar sin errores
# 4. Los botones deben mostrar "Running..." y luego volver al texto original
# 5. Las tarjetas de checks deben actualizarse con resultados
```

### 4. Auto-refresh Debe Funcionar (Simplificado)
```bash
# En dashboard:
# 1. Auto-refresh debe estar activo (ver footer del dashboard)
# 2. Timestamps deben actualizarse periódicamente
# 3. Estado del daemon debe mantenerse
# 4. No debe haber errores en consola por endpoints faltantes
```

### 5. Navegación Entre Páginas
```bash
# Verificar en sidebar navigation:
# 1. Click "Dashboard" -> Va a /dashboard
# 2. Click "Design" -> Va a /design  
# 3. Click "Config" -> Va a /config
# 4. La navegación activa debe resaltarse correctamente
```

### 6. Página de Diseño Funcional
```bash
# En /design:
# 1. Click "Refresh" -> Debe cargar diagrama si existe
# 2. Click "Regenerate" -> Debe iniciar generación
# 3. Diagramas Mermaid deben renderizarse correctamente
# 4. Si no hay archivos, debe mostrar error descriptivo
```

### 7. Página de Configuración
```bash
# En /config:
# 1. Formulario debe cargarse con valores actuales
# 2. Click "Save Configuration" -> Debe mostrar mensaje apropiado
# 3. Click "Reset to Defaults" -> Debe resetear formulario
# 4. Validación de campos debe funcionar
```

### 8. Sistema de Notificaciones
```bash
# Verificar que aparezcan notificaciones:
# 1. Al ejecutar checks exitosamente -> Notificación verde
# 2. Al fallar operaciones -> Notificación roja
# 3. Notificaciones deben auto-desaparecer después de 5 segundos
# 4. Deben aparecer en esquina superior derecha
```

### 9. Compatibilidad con Navegadores
```bash
# Probar en al menos 2 navegadores:
# - Chrome/Chromium (versión reciente)
# - Firefox (versión reciente)

# Verificar que NO hay:
# - Errores de "module not supported"
# - Referencias a funciones undefined
# - Problemas de CORS o fetch
```

### 10. Performance y Memory
```bash
# En Developer Tools -> Performance/Memory:
# 1. Carga inicial debe ser <3 segundos
# 2. Auto-refresh no debe causar memory leaks evidentes
# 3. Interacciones deben ser responsivas (<500ms)
```

### 11. Fallback para Navegadores Sin Módulos
```bash
# En navegador antiguo (ej. IE11 si está disponible):
# Debe mostrar mensaje: "Este navegador no soporta módulos ES6"
```

### 12. Logs Limpios
```bash
# En terminal del daemon Y en browser console:
# NO debe haber:
# - Errores de import/export
# - Referencias a endpoints eliminados (/api/status, etc.)
# - Warnings sobre funciones faltantes
# - Errors de Mermaid rendering (si hay diagramas)
```

## Template de Commit Message
```
feat(ui): integrate API migration with modular frontend

- Updated HTML templates to load ES6 modules with type="module"
- Created CLIAdapter to convert CLI responses to UI-compatible format
- Updated APIWrappers to use new CLI endpoints exclusively
- Modified RefreshSystem to work without daemon status endpoints
- Implemented caching for check results using localStorage
- Updated global functions (runCheck, generateDesign, etc.) for HTML templates
- Added fallbacks for missing daemon functionality
- Fixed diagram loading to use static files instead of eliminated endpoints
- Added browser compatibility checks for ES6 modules
- Maintained all user-facing functionality while using simplified backend

Integration complete:
- API: Thin CLI wrappers only (Tasks 008-009)
- Frontend: Modular ES6 structure (Task 010)  
- UI: Fully functional with new architecture (Task 011)
- All pages working: /dashboard, /design, /config
- Auto-refresh, notifications, and interactions preserved
