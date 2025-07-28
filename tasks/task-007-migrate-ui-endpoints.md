# Task 007: Migrar UI a Nuevos Endpoints API y Añadir Auto-Actualización

## Contexto del Proyecto
Este proyecto, autocode, es una herramienta de monitoreo automático con interfaz web que utiliza FastAPI como backend. En tareas anteriores se refactorizó la API para que actúe como "thin wrappers" sobre las funciones CLI, creando nuevos endpoints más consistentes y mantenibles. El objetivo es migrar la interfaz de usuario para utilizar estos nuevos endpoints en lugar de los antiguos, y mejorar el sistema de auto-actualización para hacer el dashboard más reactivo y eficiente.

## Estado Actual de la API y Endpoints

### Endpoints Antiguos (Actuales en UI)
```javascript
// Endpoints que la UI probablemente usa actualmente
GET  /api/status                    // Estado general del daemon y checks
GET  /api/checks                    // Resultados de todas las verificaciones
POST /api/checks/{check_name}/run   // Ejecutar verificación específica (refactorizado)
GET  /api/config                    // Obtener configuración actual
PUT  /api/config                    // Actualizar configuración
```

### Nuevos Endpoints Wrapper (Disponibles desde Task-003)
```javascript
// Nuevos endpoints que mapean directamente a funciones CLI
POST /api/generate-docs             // Wrapper sobre check_docs()
POST /api/generate-design           // Wrapper sobre code_to_design()
POST /api/analyze-git               // Wrapper sobre git_changes()
GET  /api/config/load               // Wrapper sobre load_config()
POST /api/docs/check-sync           // Check docs síncrono
```

### Estructura de Respuestas de Nuevos Endpoints
```json
// Respuesta estándar de endpoints wrapper (CheckExecutionResponse)
{
  "success": true|false,
  "result": "mensaje descriptivo o datos",
  "error": null|"descripción del error"
}

// Respuesta de config/load
{
  "success": true,
  "config": { /* objeto de configuración */ },
  "error": null
}
```

## Estado Actual del Sistema de Auto-Actualización

### Implementación Actual en app.js
```javascript
class AutocodeDashboard {
  constructor() {
    this.refreshInterval = 5000; // 5 segundos fijo
    this.refreshTimer = null;
    this.isLoading = false;
  }
  
  startAutoRefresh() {
    this.refreshTimer = setInterval(() => {
      if (!this.isLoading) {
        this.fetchAndUpdateStatus(); // Solo actualiza status
      }
    }, this.refreshInterval);
  }
  
  async fetchAndUpdateStatus() {
    // Hace fetch a /api/status únicamente
    // No actualiza otros datos automáticamente
  }
}
```

### Limitaciones del Sistema Actual
1. **Auto-refresh limitado**: Solo actualiza `/api/status`, no otros datos
2. **Intervalo fijo**: 5 segundos para todo, no diferenciado por tipo de datos
3. **Sin priorización**: Todos los updates tienen la misma frecuencia
4. **No adaptativo**: No se ajusta basado en actividad del usuario
5. **Sin feedback visual**: Usuario no sabe cuándo se está actualizando

## Objetivo de la Refactorización
Migrar la UI para usar los nuevos endpoints wrapper y mejorar el auto-refresh para:
1. **Endpoints consistentes**: Usar wrappers CLI para mayor consistencia
2. **Auto-refresh inteligente**: Diferentes intervalos para diferentes tipos de datos
3. **Feedback visual**: Indicadores de actualización y loading states
4. **Manejo de errores mejorado**: Responses estándar de los wrappers
5. **Reactivity adaptativa**: Pausar/acelerar refresh basado en actividad

## Instrucciones Paso a Paso

### 1. Migrar Métodos API a Nuevos Endpoints

#### 1.1 Actualizar fetchAndUpdateStatus para Usar Wrappers
```javascript
class AutocodeDashboard {
  // Método existente actualizado
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
  
  // Nuevo método para refrescar resultados de checks usando wrappers
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
}
```

#### 1.2 Añadir Métodos para Nuevos Endpoints Wrapper
```javascript
class AutocodeDashboard {
  // Método para generar documentación usando nuevo wrapper
  async generateDocumentation() {
    try {
      console.log('Generating documentation...');
      
      const response = await this.apiPost('/api/generate-docs');
      
      if (response.success) {
        this.showNotification('Documentation generation started', 'success');
        
        // Auto-refresh después de un delay para capturar el resultado
        setTimeout(() => {
          this.fetchAndUpdateStatus();
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
          this.refreshDesignContent();
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
          this.fetchAndUpdateStatus();
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
}
```

### 2. Implementar Sistema de Auto-Actualización Inteligente

#### 2.1 Crear Configuración de Refresh Diferenciado
```javascript
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
  }
  
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
  
  async refreshConfigData() {
    if (this.currentPage === 'config') {
      const configData = await this.loadConfigurationData();
      this.updateConfigUI(configData);
    }
  }
  
  async refreshDesignContent() {
    if (this.currentPage === 'design' || this.currentPage === 'ui-designer') {
      // Refresh design-related content
      await this.loadDesignDocumentation();
    }
  }
}
```

#### 2.2 Añadir Controles de Auto-Refresh
```javascript
class AutocodeDashboard {
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
}
```

### 3. Añadir Feedback Visual y Estados de Loading

#### 3.1 Crear Sistema de Notificaciones
```javascript
class AutocodeDashboard {
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
}
```

#### 3.2 Actualizar Templates con Indicadores Visuales
```html
<!-- Añadir a base.html -->
<div id="global-loading-indicator" class="fixed top-2 left-1/2 transform -translate-x-1/2 z-50 hidden">
  <div class="bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-2">
    <div class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
    <span class="text-sm">Updating...</span>
  </div>
</div>

<!-- Controles de refresh mejorados en el footer -->
<div class="flex items-center space-x-4">
  <span class="text-sm text-gray-500">Auto-refresh:</span>
  
  <div class="flex items-center space-x-2">
    <button id="pause-refresh-btn" onclick="toggleAutoRefresh()" 
            class="text-sm bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded">
      Pause
    </button>
    
    <select id="refresh-speed" onchange="changeRefreshSpeed(this.value)"
            class="text-sm border border-gray-300 rounded px-2 py-1">
      <option value="fast">Fast (3s)</option>
      <option value="normal" selected>Normal (5s)</option>
      <option value="slow">Slow (10s)</option>
    </select>
  </div>
  
  <div class="text-xs text-gray-400">
    <span>Last: </span>
    <span id="last-updated">--</span>
  </div>
</div>
```

### 4. Actualizar Handlers de Botones para Usar Nuevos Endpoints

#### 4.1 Modificar Funciones Globales
```javascript
// Actualizar función global para usar nuevos wrappers
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
  const button = document.getElementById('pause-refresh-btn');
  
  if (dashboard.updatePaused) {
    dashboard.resumeAutoRefresh();
    button.textContent = 'Pause';
  } else {
    dashboard.pauseAutoRefresh();
    button.textContent = 'Resume';
  }
}

function changeRefreshSpeed(speed) {
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
```

### 5. Añadir Detección de Actividad del Usuario

#### 5.1 Sistema de Pausa Automática
```javascript
class AutocodeDashboard {
  constructor() {
    // ... configuración existente ...
    
    this.userActivityTimer = null;
    this.inactivityTimeout = 60000; // 1 minuto de inactividad
    this.wasActiveRefresh = true;
  }
  
  init() {
    // ... inicialización existente ...
    
    this.setupActivityDetection();
  }
  
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
}
```

## Criterios de Verificación

### Verificación de Migración a Nuevos Endpoints
1. **Documentación**: Botón de docs debe usar `/api/generate-docs`
2. **Diseño**: Funciones de diseño deben usar `/api/generate-design`
3. **Git**: Análisis de git debe usar `/api/analyze-git`
4. **Configuración**: Carga de config debe usar `/api/config/load`
5. **Responses consistentes**: Todos los wrappers deben retornar formato estándar

### Verificación de Auto-Actualización Inteligente
```bash
# Iniciar servidor
uv run autocode daemon

# Verificar en consola del navegador:
# 1. dashboard.refreshConfig debe mostrar configuración diferenciada
# 2. Múltiples timers activos con diferentes intervalos
# 3. Pausa/resume debe funcionar correctamente
# 4. Cambio de velocidad debe actualizar intervalos
```

### Tests de Funcionalidad
1. **Multi-refresh**: Diferentes tipos de datos se actualizan a diferentes velocidades
2. **Controles**: Botones de pausa/resume y selector de velocidad funcionan
3. **Notificaciones**: Mensajes aparecen correctamente para acciones
4. **Estados de loading**: Indicadores visuales durante updates
5. **Detección de actividad**: Refresh se adapta a actividad del usuario

### Verificación de Nuevos Endpoints
```bash
# Test de endpoints wrapper
curl -X POST http://localhost:8080/api/generate-docs
curl -X POST http://localhost:8080/api/generate-design
curl -X POST http://localhost:8080/api/analyze-git
curl http://localhost:8080/api/config/load

# Todos deben retornar formato CheckExecutionResponse
```

### Verificación de Performance
1. **Reducción de calls**: Menos requests simultáneos gracias a refresh diferenciado
2. **Actividad adaptativa**: Refresh más lento cuando usuario inactivo
3. **Page visibility**: Pausa automática cuando tab no está visible
4. **Error resilience**: Fallos en un tipo de datos no afectan otros

## Consideraciones Importantes

### Compatibilidad con Endpoints Existentes
- Mantener endpoints antiguos funcionando para gradual migration
- `/api/status` sigue siendo necesario para daemon status
- `/api/config` PUT sigue siendo necesario para guardar configuración

### Manejo de Errores Mejorado
- Nuevos endpoints wrapper tienen formato de error consistente
- Notificaciones visuales para errores y éxitos
- Graceful degradation si algunos endpoints fallan

### Performance y UX
- Refresh diferenciado reduce carga del servidor
- Feedback visual mejora experiencia del usuario
- Detección de actividad optimiza recursos

## Template de Commit Message
```
feat(ui): migrate to new API wrapper endpoints and enhance auto-refresh

- Migrated UI to use new wrapper endpoints (/api/generate-docs, /api/generate-design, /api/analyze-git)
- Implemented intelligent auto-refresh with differentiated intervals per data type
- Added visual loading indicators and notification system for better UX
- Enhanced button handlers to use appropriate wrapper endpoints
- Implemented user activity detection for adaptive refresh behavior
- Added refresh controls (pause/resume, speed adjustment) in UI
- Integrated CheckExecutionResponse format handling throughout frontend
- Added page visibility detection to pause refresh when tab hidden
- Implemented graceful error handling with visual feedback
- Maintained backward compatibility with existing daemon status endpoints
```

## Notas para el Programador

### Debugging
Si los nuevos endpoints no funcionan:
1. Verificar que los wrappers están implementados en el backend (Task-003)
2. Comprobar formato de respuesta en Network tab de DevTools
3. Verificar que funciones CLI están disponibles para importar
4. Revisar logs del servidor para errores en endpoints wrapper

### Testing
Para verificar el refresh diferenciado:
1. Abrir consola del navegador
2. Ejecutar `dashboard.refreshConfig` para ver configuración
3. Usar `dashboard.setRefreshInterval('daemon_status', 1000)` para test rápido
4. Verificar múltiples timers con `dashboard.refreshConfig.daemon_status.timer`

### Extensibilidad
Para añadir nuevos tipos de refresh:
1. Añadir entrada en `refreshConfig`
2. Crear método `refreshNewDataType()`
3. Añadir case en `refreshSpecificData()`
4. Añadir controles UI si es necesario
