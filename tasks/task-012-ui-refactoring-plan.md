# Plan de Refactorización UI - Sistema de Componentes Modular

## Resumen Ejecutivo

Este documento describe el plan completo para refactorizar la interfaz de usuario del proyecto Autocode, transformando el código actual (que mezcla lógica y presentación) en una arquitectura modular basada en componentes usando JavaScript puro (sin frameworks).

## Contexto del Proyecto

### Estado Actual

El proyecto Autocode es una herramienta de análisis y monitoreo de código que incluye:
- **Backend**: FastAPI (Python) con endpoints REST
- **Frontend**: JavaScript vanilla + Tailwind CSS + Jinja2 templates
- **Funcionalidades principales**:
  - Dashboard de monitoreo con "checks" (documentación, tests, git)
  - Visualización de diagramas de arquitectura
  - Configuración del sistema
  - Sistema de actualización automática (polling)

### Problemas Actuales

1. **Acoplamiento fuerte**: La lógica JavaScript está mezclada con la presentación HTML
2. **Funciones globales**: Se usan funciones en `window` para manejar eventos desde HTML
3. **Difícil mantenimiento**: Cambios requieren modificar múltiples archivos
4. **Poca reusabilidad**: Componentes no son verdaderamente modulares
5. **God objects**: Clases como `AppManager` y `DashboardCore` hacen demasiado

### Estructura Actual
```
autocode/web/
├── static/
│   ├── app.js              # Entry point con funciones globales
│   ├── app.js.backup       # Archivo de respaldo (eliminar)
│   └── js/
│       ├── api-client.js   # Cliente API
│       ├── app-manager.js  # Orquestador principal (god object)
│       ├── dashboard-core.js # Lógica UI mezclada
│       ├── refresh-system.js # Sistema de polling
│       └── utilities.js    # Utilidades DOM
└── templates/
    ├── base.html           # Layout principal
    ├── index.html          # Página legacy
    ├── components/         # Macros Jinja2 reutilizables
    │   ├── check_card.html
    │   ├── design.html
    │   ├── footer.html
    │   ├── header.html
    │   └── stat_card.html
    └── pages/              # Páginas completas
        ├── config.html
        ├── dashboard.html
        └── design.html
```

## Arquitectura Propuesta

### Principios de Diseño

1. **Separación de responsabilidades**: Vista (HTML/CSS) vs Lógica (JS)
2. **Componentes autónomos**: Cada componente maneja su propio estado y eventos
3. **Sin funciones globales**: Usar data attributes para vincular JS con HTML
4. **Comunicación desacoplada**: Event bus para comunicación entre componentes
5. **Servicios reutilizables**: Lógica de negocio en servicios independientes

### Nueva Estructura
```
autocode/web/
├── static/
│   ├── js/
│   │   ├── components/         # Lógica de componentes UI
│   │   │   ├── CheckCard.js
│   │   │   ├── DiagramViewer.js
│   │   │   ├── ConfigForm.js
│   │   │   └── RefreshControl.js
│   │   ├── core/              # Infraestructura base
│   │   │   ├── Component.js    # Clase base para componentes
│   │   │   ├── EventBus.js    # Sistema de eventos
│   │   │   └── Store.js       # Gestión de estado simple
│   │   ├── services/          # Lógica de negocio
│   │   │   ├── api-client.js  # Cliente HTTP
│   │   │   ├── check-service.js
│   │   │   ├── config-service.js
│   │   │   └── design-service.js
│   │   ├── pages/             # Controladores de página
│   │   │   ├── DashboardPage.js
│   │   │   ├── DesignPage.js
│   │   │   └── ConfigPage.js
│   │   └── utils/             # Utilidades puras
│   │       ├── dom.js         # Helpers DOM
│   │       ├── formatters.js  # Formateadores de datos
│   │       └── validators.js  # Validaciones
│   └── app.js                 # Entry point minimalista
└── templates/                 # Sin cambios estructurales
    ├── base.html
    ├── components/
    └── pages/
```

## Implementación Detallada

### 1. Infraestructura Base

#### Component.js - Clase base para todos los componentes
```javascript
// static/js/core/Component.js

export class Component {
  constructor(element) {
    if (!element) {
      throw new Error('Component requires a DOM element');
    }
    
    this.element = element;
    this.state = {};
    this.elements = {};
    
    // Lifecycle hooks
    this.queryElements();
    this.bindActions();
    this.init();
  }
  
  // Busca elementos hijos con data-element
  queryElements() {
    this.element.querySelectorAll('[data-element]').forEach(el => {
      const name = el.dataset.element;
      this.elements[name] = el;
    });
  }
  
  // Vincula acciones a elementos con data-action
  bindActions() {
    this.element.querySelectorAll('[data-action]').forEach(el => {
      const action = el.dataset.action;
      const methodName = this.toCamelCase(action);
      
      if (typeof this[methodName] === 'function') {
        el.addEventListener('click', (e) => {
          e.preventDefault();
          this[methodName](e);
        });
      } else {
        console.warn(`Method ${methodName} not found in component`);
      }
    });
  }
  
  // Actualiza el estado y re-renderiza
  setState(newState) {
    const oldState = { ...this.state };
    this.state = { ...this.state, ...newState };
    this.stateChanged(oldState, this.state);
    this.render();
  }
  
  // Hook para cambios de estado
  stateChanged(oldState, newState) {
    // Override in subclasses if needed
  }
  
  // Actualiza un elemento específico
  updateElement(name, content = null, className = null, attributes = {}) {
    const element = this.elements[name];
    if (!element) return;
    
    if (content !== null) {
      element.textContent = content;
    }
    
    if (className !== null) {
      element.className = className;
    }
    
    Object.entries(attributes).forEach(([key, value]) => {
      element.setAttribute(key, value);
    });
  }
  
  // Muestra/oculta un elemento
  toggleElement(name, show) {
    const element = this.elements[name];
    if (!element) return;
    
    element.style.display = show ? '' : 'none';
  }
  
  // Utilities
  toCamelCase(str) {
    return str.replace(/-([a-z])/g, (g) => g[1].toUpperCase());
  }
  
  // Lifecycle methods (override in subclasses)
  init() {}
  render() {}
  destroy() {}
}
```

#### EventBus.js - Sistema de eventos global
```javascript
// static/js/core/EventBus.js

class EventBus {
  constructor() {
    this.events = {};
  }
  
  on(event, handler) {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(handler);
    
    // Return unsubscribe function
    return () => this.off(event, handler);
  }
  
  off(event, handler) {
    if (!this.events[event]) return;
    
    this.events[event] = this.events[event].filter(h => h !== handler);
  }
  
  emit(event, data = {}) {
    if (!this.events[event]) return;
    
    this.events[event].forEach(handler => {
      try {
        handler(data);
      } catch (error) {
        console.error(`Error in event handler for ${event}:`, error);
      }
    });
  }
  
  clear() {
    this.events = {};
  }
}

// Singleton instance
export const eventBus = new EventBus();
```

#### Store.js - Gestión de estado simple
```javascript
// static/js/core/Store.js

import { eventBus } from './EventBus.js';

class Store {
  constructor(initialState = {}) {
    this.state = initialState;
    this.subscribers = new Map();
  }
  
  getState() {
    return { ...this.state };
  }
  
  setState(updates) {
    const oldState = this.state;
    this.state = { ...this.state, ...updates };
    
    // Notify subscribers of changes
    Object.keys(updates).forEach(key => {
      if (this.subscribers.has(key)) {
        this.subscribers.get(key).forEach(callback => {
          callback(this.state[key], oldState[key]);
        });
      }
    });
    
    // Emit global state change event
    eventBus.emit('store:changed', {
      oldState,
      newState: this.state,
      changes: updates
    });
  }
  
  subscribe(key, callback) {
    if (!this.subscribers.has(key)) {
      this.subscribers.set(key, new Set());
    }
    
    this.subscribers.get(key).add(callback);
    
    // Return unsubscribe function
    return () => {
      this.subscribers.get(key).delete(callback);
    };
  }
}

// Create app store
export const store = new Store({
  checks: {},
  config: {},
  daemon: {
    isRunning: false,
    uptime: 0
  }
});
```

### 2. Implementación de Componentes

#### CheckCard.js - Componente para mostrar estado de checks
```javascript
// static/js/components/CheckCard.js

import { Component } from '../core/Component.js';
import { eventBus } from '../core/EventBus.js';
import { checkService } from '../services/check-service.js';
import { formatTimestamp } from '../utils/formatters.js';

export class CheckCard extends Component {
  init() {
    this.checkName = this.element.dataset.checkName;
    this.state = {
      status: 'unknown',
      message: 'Not run yet',
      timestamp: null,
      loading: false,
      details: null
    };
    
    // Subscribe to updates for this check
    this.unsubscribe = eventBus.on(`check:${this.checkName}:updated`, (data) => {
      this.handleCheckUpdate(data);
    });
    
    // Initial render
    this.render();
  }
  
  async runCheck() {
    if (this.state.loading) return;
    
    this.setState({ loading: true });
    
    try {
      const result = await checkService.runCheck(this.checkName);
      this.handleCheckUpdate(result);
    } catch (error) {
      this.setState({
        status: 'error',
        message: `Failed to run check: ${error.message}`,
        loading: false
      });
    }
  }
  
  handleCheckUpdate(data) {
    this.setState({
      status: data.status,
      message: data.message,
      timestamp: data.timestamp,
      details: data.details,
      loading: false
    });
  }
  
  render() {
    const { status, message, timestamp, loading, details } = this.state;
    
    // Update status indicator
    const statusClasses = {
      success: 'bg-green-500',
      error: 'bg-red-500',
      warning: 'bg-yellow-500',
      unknown: 'bg-gray-300'
    };
    
    this.updateElement('statusIndicator', null, 
      `w-3 h-3 rounded-full ${statusClasses[status]} transition-all`
    );
    
    // Update status text
    this.updateElement('statusText', status, 
      `ml-2 text-sm font-medium capitalize ${
        status === 'success' ? 'text-green-700' :
        status === 'error' ? 'text-red-700' :
        status === 'warning' ? 'text-yellow-700' :
        'text-gray-600'
      }`
    );
    
    // Update message
    this.updateElement('message', message);
    
    // Update timestamp
    if (timestamp) {
      this.updateElement('timestamp', `Last run: ${formatTimestamp(timestamp)}`);
    }
    
    // Update button state
    const button = this.element.querySelector('[data-action="run-check"]');
    if (button) {
      button.disabled = loading;
      button.textContent = loading ? 'Running...' : 'Run Check';
      button.className = loading 
        ? 'bg-gray-400 text-white px-4 py-2 rounded cursor-not-allowed'
        : 'bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors';
    }
    
    // Update details if present
    if (details && this.elements.details) {
      this.renderDetails(details);
    }
  }
  
  renderDetails(details) {
    // Override in specific check card implementations
    this.updateElement('details', JSON.stringify(details, null, 2));
  }
  
  destroy() {
    if (this.unsubscribe) {
      this.unsubscribe();
    }
  }
}

// Auto-initialize all check cards when DOM is ready
export function initCheckCards() {
  document.querySelectorAll('[data-component="check-card"]').forEach(element => {
    new CheckCard(element);
  });
}
```

#### Template correspondiente (Jinja2)
```html
<!-- templates/components/check_card.html -->
{% macro check_card(check_name, title, description) %}
<div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-gray-300 hover:shadow-lg transition-all"
     data-component="check-card"
     data-check-name="{{ check_name }}">
  
  <!-- Header -->
  <div class="flex justify-between items-start mb-4">
    <div>
      <h3 class="text-lg font-semibold text-gray-800">{{ title }}</h3>
      <p class="text-sm text-gray-600">{{ description }}</p>
    </div>
    
    <!-- Status indicator -->
    <div data-element="status" class="flex items-center">
      <div data-element="statusIndicator" class="w-3 h-3 rounded-full bg-gray-300"></div>
      <span data-element="statusText" class="ml-2 text-sm text-gray-600">unknown</span>
    </div>
  </div>
  
  <!-- Message -->
  <div class="mb-4">
    <p data-element="message" class="text-gray-700">
      Waiting for first run...
    </p>
    <p data-element="timestamp" class="text-xs text-gray-500 mt-1"></p>
  </div>
  
  <!-- Actions -->
  <div class="flex justify-between items-center">
    <button data-action="run-check" 
            class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors">
      Run Check
    </button>
    
    <button data-action="toggle-details"
            class="text-sm text-blue-600 hover:text-blue-800">
      Show Details
    </button>
  </div>
  
  <!-- Details (hidden by default) -->
  <div data-element="detailsContainer" class="mt-4 hidden">
    <pre data-element="details" class="bg-gray-100 p-3 rounded text-xs overflow-x-auto"></pre>
  </div>
</div>
{% endmacro %}
```

### 3. Servicios

#### check-service.js - Lógica de negocio para checks
```javascript
// static/js/services/check-service.js

import { apiClient } from './api-client.js';
import { eventBus } from '../core/EventBus.js';
import { store } from '../core/Store.js';

class CheckService {
  constructor() {
    this.cache = new Map();
    this.pendingRequests = new Map();
  }
  
  async runCheck(checkName) {
    // Prevent duplicate requests
    if (this.pendingRequests.has(checkName)) {
      return this.pendingRequests.get(checkName);
    }
    
    const request = this._executeCheck(checkName);
    this.pendingRequests.set(checkName, request);
    
    try {
      const result = await request;
      return result;
    } finally {
      this.pendingRequests.delete(checkName);
    }
  }
  
  async _executeCheck(checkName) {
    try {
      // Call API
      const response = await apiClient.post(`/api/${checkName.replace('_', '-')}`, {});
      
      if (!response.success) {
        throw new Error(response.error || 'Check failed');
      }
      
      // Wait a bit for the check to complete, then fetch results
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Get updated results
      const result = await this.getCheckResult(checkName);
      
      // Update store
      store.setState({
        checks: {
          ...store.getState().checks,
          [checkName]: result
        }
      });
      
      // Emit event
      eventBus.emit(`check:${checkName}:updated`, result);
      
      return result;
      
    } catch (error) {
      console.error(`Error running check ${checkName}:`, error);
      
      const errorResult = {
        status: 'error',
        message: error.message,
        timestamp: new Date().toISOString()
      };
      
      eventBus.emit(`check:${checkName}:updated`, errorResult);
      throw error;
    }
  }
  
  async getCheckResult(checkName) {
    // This would normally fetch from an endpoint, 
    // but since we're using the wrapper pattern, we'll simulate
    return {
      status: 'success',
      message: `${checkName} completed successfully`,
      timestamp: new Date().toISOString(),
      details: {}
    };
  }
  
  async getAllCheckResults() {
    const checks = ['doc_check', 'git_check', 'test_check'];
    const results = {};
    
    for (const check of checks) {
      try {
        results[check] = await this.getCheckResult(check);
      } catch (error) {
        results[check] = {
          status: 'error',
          message: 'Failed to fetch result',
          timestamp: new Date().toISOString()
        };
      }
    }
    
    return results;
  }
}

export const checkService = new CheckService();
```

### 4. Controladores de Página

#### DashboardPage.js - Controlador para la página del dashboard
```javascript
// static/js/pages/DashboardPage.js

import { eventBus } from '../core/EventBus.js';
import { store } from '../core/Store.js';
import { checkService } from '../services/check-service.js';
import { initCheckCards } from '../components/CheckCard.js';
import { RefreshControl } from '../components/RefreshControl.js';

export class DashboardPage {
  constructor() {
    this.refreshInterval = null;
    this.components = [];
  }
  
  async init() {
    console.log('Initializing Dashboard Page');
    
    // Initialize components
    this.initComponents();
    
    // Load initial data
    await this.loadInitialData();
    
    // Setup auto-refresh
    this.setupAutoRefresh();
    
    // Listen for global events
    this.setupEventListeners();
  }
  
  initComponents() {
    // Initialize check cards
    initCheckCards();
    
    // Initialize refresh control
    const refreshElement = document.querySelector('[data-component="refresh-control"]');
    if (refreshElement) {
      this.refreshControl = new RefreshControl(refreshElement);
      this.components.push(this.refreshControl);
    }
    
    // Initialize other dashboard components...
  }
  
  async loadInitialData() {
    try {
      // Load all check results
      const results = await checkService.getAllCheckResults();
      
      // Update store
      store.setState({ checks: results });
      
      // Emit events for each check
      Object.entries(results).forEach(([checkName, result]) => {
        eventBus.emit(`check:${checkName}:updated`, result);
      });
      
    } catch (error) {
      console.error('Error loading initial data:', error);
    }
  }
  
  setupAutoRefresh() {
    // Default: refresh every 10 seconds
    this.startAutoRefresh(10000);
    
    // Listen for refresh control changes
    eventBus.on('refresh:interval:changed', ({ interval }) => {
      this.startAutoRefresh(interval);
    });
    
    eventBus.on('refresh:paused', () => {
      this.stopAutoRefresh();
    });
    
    eventBus.on('refresh:resumed', () => {
      this.startAutoRefresh();
    });
  }
  
  startAutoRefresh(interval = 10000) {
    this.stopAutoRefresh();
    
    this.refreshInterval = setInterval(() => {
      this.loadInitialData();
    }, interval);
  }
  
  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }
  
  setupEventListeners() {
    // Handle visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.stopAutoRefresh();
      } else {
        this.startAutoRefresh();
      }
    });
  }
  
  destroy() {
    this.stopAutoRefresh();
    
    // Destroy all components
    this.components.forEach(component => {
      if (component.destroy) {
        component.destroy();
      }
    });
  }
}
```

### 5. Entry Point Minimalista

#### app.js - Punto de entrada simplificado
```javascript
// static/app.js

import { DashboardPage } from './js/pages/DashboardPage.js';
import { DesignPage } from './js/pages/DesignPage.js';
import { ConfigPage } from './js/pages/ConfigPage.js';

class App {
  constructor() {
    this.currentPage = null;
  }
  
  init() {
    // Determine current page from URL
    const path = window.location.pathname;
    
    let PageClass;
    if (path === '/dashboard' || path === '/') {
      PageClass = DashboardPage;
    } else if (path === '/design') {
      PageClass = DesignPage;
    } else if (path === '/config') {
      PageClass = ConfigPage;
    } else {
      console.warn('Unknown page:', path);
      return;
    }
    
    // Initialize page
    this.currentPage = new PageClass();
    this.currentPage.init();
    
    // Handle page cleanup on unload
    window.addEventListener('beforeunload', () => {
      if (this.currentPage && this.currentPage.destroy) {
        this.currentPage.destroy();
      }
    });
  }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.init();
  });
} else {
  const app = new App();
  app.init();
}
```

## Plan de Migración

### Fase 1: Preparación (1-2 días)
1. **Crear la infraestructura base**:
   - Implementar `Component.js`, `EventBus.js`, `Store.js`
   - Crear estructura de carpetas
   - Configurar imports/exports

2. **Limpiar código actual**:
   - Eliminar `app.js.backup`
   - Mover utilidades a `utils/`
   - Documentar funciones globales a eliminar

### Fase 2: Migración de Componentes (3-4 días)
1. **Empezar con CheckCard**:
   - Crear `CheckCard.js`
   - Actualizar template `check_card.html`
   - Testear en una página

2. **Migrar componentes uno por uno**:
   - DiagramViewer
   - ConfigForm
   - RefreshControl
   - Otros componentes menores

### Fase 3: Servicios y Lógica (2-3 días)
1. **Extraer servicios**:
   - Mover lógica de API a servicios
   - Crear servicios específicos por dominio
   - Implementar caché y gestión de errores

2. **Refactorizar api-client.js**:
   - Mantener como capa HTTP pura
   - Añadir interceptores si es necesario

### Fase 4: Páginas y Limpieza (2-3 días)
1. **Implementar controladores de página**:
   - DashboardPage
   - DesignPage
   - ConfigPage

2. **Eliminar código legacy**:
   - Quitar funciones globales de `app.js`
   - Eliminar `app-manager.js` y `dashboard-core.js`
   - Actualizar templates para no usar `onclick`

### Fase 5: Testing y Documentación (1-2 días)
1. **Testing manual completo**
2. **Documentar nuevos patrones**
3. **Crear guía de contribución**

## Consideraciones Importantes

### Compatibilidad con Backend
- Los endpoints de la API no cambian
- Se mantiene la misma estructura de respuestas
- Solo cambia cómo el frontend consume los datos

### Gestión de Estado
- El `Store` es simple y suficiente para esta aplicación
- No necesita ser reactivo como Redux/Vuex
- Los componentes se suscriben solo a lo que necesitan

### Performance
- Lazy loading de componentes pesados (ej: Mermaid para diagramas)
- Debouncing en actualizaciones frecuentes
- Cache de resultados de API cuando sea apropiado

### Debugging
- Usar `console.group()` para agrupar logs por componente
- EventBus puede tener modo debug para trazar eventos
- Store puede tener DevTools simples

## Ejemplo de Migración Completa

Veamos cómo migrar el componente de estadísticas del daemon:

### Antes (código actual entrelazado):
```javascript
// En dashboard-core.js
updateSystemStats(daemon) {
    const uptimeElement = document.getElementById('uptime');
    if (uptimeElement) {
        uptimeElement.textContent = formatDuration(daemon.uptime_seconds);
    }
    // ... más manipulación DOM directa
}
```

### Después (componente modular):
```javascript
// components/DaemonStats.js
export class DaemonStats extends Component {
  init() {
    // Subscribe to daemon updates
    store.subscribe('daemon', (daemon) => {
      this.setState(daemon);
    });
    
    this.render();
  }
  
  render() {
    const { isRunning, uptime, totalChecks } = this.state;
    
    this.updateElement('status', isRunning ? 'Running' : 'Stopped',
      `font-medium ${isRunning ? 'text-green-600' : 'text-red-600'}`
    );
    
    this.updateElement('uptime', formatDuration(uptime));
    this.updateElement('totalChecks', totalChecks || 0);
  }
}
```

```html
<!-- Template -->
<div data-component="daemon-stats" class="bg-white rounded-lg shadow p-4">
  <h3 class="text-lg font-semibold mb-2">System Status</h3>
  <div class="space-y-2">
    <div class="flex justify-between">
      <span>Status:</span>
      <span data-element="status">Unknown</span>
    </div>
    <div class="flex justify-between">
      <span>Uptime:</span>
      <span data-element="uptime">--</span>
    </div>
    <div class="flex justify-between">
      <span>Total Checks:</span>
      <span data-element="totalChecks">0</span>
    </div>
  </div>
</div>
```

## Conclusión

Esta refactorización transformará el código en una arquitectura mantenible y extensible, manteniendo la simplicidad de JavaScript vanilla. Los beneficios principales son:

1. **Modularidad real**: Componentes independientes y reutilizables
2. **Mejor separación**: Vista (HTML) y lógica (JS) claramente separadas
3. **Fácil extensión**: Añadir nuevos componentes es trivial
4. **Mantenibilidad**: Cambios localizados, sin efectos secundarios
5. **Testabilidad**: Componentes y servicios pueden testearse aisladamente

El proceso de migración es gradual y puede hacerse sin romper la funcionalidad existente.
