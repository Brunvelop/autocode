# Task 006: Simplificar Estructura JavaScript y Hacer Componentes Autocontenidos

## Contexto del Proyecto
Este proyecto, autocode, es una herramienta de monitoreo automático con interfaz web que utiliza FastAPI como backend y una interfaz JavaScript dinámica para el frontend. Actualmente, la aplicación tiene una estructura JavaScript modular con subcarpetas (`js/components/` y `js/utils/`) que puede resultar compleja de mantener. El objetivo es simplificar esta estructura manteniendo la funcionalidad, eliminando subcarpetas innecesarias y haciendo que los componentes sean más autocontenidos.

## Estado Actual de la Estructura JavaScript

### Estructura de Archivos JS Actuales
```
autocode/web/static/
├── app.js                      # Archivo principal con clase AutocodeDashboard
└── js/                         # Carpeta con módulos JS organizados
    ├── components/             # Scripts específicos de componentes
    │   └── ui-designer.js     # (Ejemplo) Manejo del visor de diagramas/UI designer
    └── utils/                 # Utilidades reutilizables
        └── api-fetch.js       # Cliente HTTP para interactuar con la API
```

### Contenido Actual de app.js (Archivo Principal)
El archivo `app.js` contiene una clase `AutocodeDashboard` que maneja:

#### Funcionalidades Core
- **Inicialización**: Setup de navegación, auto-refresh, carga inicial de datos
- **Auto-refresh**: Sistema de polling cada 5 segundos (`refreshInterval`)
- **API calls**: Fetches a endpoints como `/api/status`, `/api/config`
- **UI updates**: Actualización dinámica del DOM basada en respuestas de API
- **Navegación**: Detección de página actual y setup de links activos

#### Funcionalidades por Página
```javascript
// Dashboard principal
- fetchAndUpdateStatus(): Obtiene estado del daemon y checks
- updateDaemonStatus(): Actualiza indicadores de estado
- updateSystemStats(): Muestra uptime, total checks, last check
- updateCheckResults(): Actualiza tarjetas de verificación

// Página de configuración  
- loadConfigPage(): Carga formulario de configuración
- populateConfigForm(): Llena campos con valores actuales
- saveConfiguration(): Guarda cambios de configuración
- resetConfiguration(): Restaura configuración por defecto
- validateConfigForm(): Valida inputs del formulario

// Funciones utilitarias
- formatDuration(): Convierte segundos a formato legible
- formatTimestamp(): Formatea fechas
- handleError(): Manejo global de errores
```

#### Funciones Globales (Handlers de Botones)
```javascript
// Handlers llamados desde templates via onclick
async function runCheck(checkName)
async function updateConfig()
async function refreshArchitecture()
async function regenerateArchitecture()
async function generateComponentTree()
async function refreshComponentTree()
```

### Archivos en Subcarpetas (Estimados)

#### js/utils/api-fetch.js (Cliente API)
```javascript
// Clase para centralizar calls a la API
class APIClient {
  constructor(baseURL = '') {
    this.baseURL = baseURL;
  }
  
  async get(endpoint) {
    // Wrapper para fetch GET con manejo de errores
  }
  
  async post(endpoint, data) {
    // Wrapper para fetch POST con manejo de errores
  }
  
  async put(endpoint, data) {
    // Wrapper para fetch PUT con manejo de errores
  }
}
```

#### js/components/ui-designer.js (Estimado)
```javascript
// Funcionalidades específicas del UI Designer
class UIDesigner {
  constructor() {
    // Setup para componentes de diseño
  }
  
  loadDesignFiles() {
    // Carga archivos de diseño desde API
  }
  
  renderMermaidDiagram(content) {
    // Renderiza diagramas Mermaid
  }
  
  handleDesignErrors(error) {
    // Manejo específico de errores de diseño
  }
}
```

### Cómo se Cargan los Scripts Actualmente
En `base.html`:
```html
<script src="{{ url_for('static', path='app.js') }}"></script>
<!-- Posiblemente también: -->
<script src="{{ url_for('static', path='js/utils/api-fetch.js') }}"></script>
<script src="{{ url_for('static', path='js/components/ui-designer.js') }}"></script>
```

## Objetivo de la Refactorización
Simplificar la estructura JavaScript para:
1. **Reducir complejidad**: Eliminar subcarpetas y consolidar código
2. **Mejorar mantenibilidad**: Un solo archivo es más fácil de seguir
3. **Componentes autocontenidos**: Templates manejan su propia lógica específica cuando sea posible
4. **Preservar funcionalidad**: Mantener todas las características existentes

## Instrucciones Paso a Paso

### 1. Auditar y Consolidar Utilidades
#### 1.1 Revisar js/utils/api-fetch.js
Si existe, integrar su funcionalidad en `app.js`:

```javascript
// Añadir al final de la clase AutocodeDashboard
class AutocodeDashboard {
  // ... métodos existentes ...
  
  // Métodos de API consolidados
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
}
```

#### 1.2 Actualizar Métodos Existentes para Usar Nuevas Utilidades
```javascript
// Reemplazar calls directos de fetch con métodos consolidados
// ANTES:
async fetchAndUpdateStatus() {
  const response = await fetch('/api/status');
  const data = await response.json();
  // ...
}

// DESPUÉS:
async fetchAndUpdateStatus() {
  try {
    const data = await this.apiGet('/api/status');
    this.updateUI(data);
    this.updateLastUpdated();
  } catch (error) {
    this.handleError(error);
  }
}
```

### 2. Consolidar Componentes Específicos
#### 2.1 Integrar js/components/ui-designer.js (si existe)
Mover funcionalidad específica del UI Designer al final de `app.js`:

```javascript
// Añadir después de los métodos de API en AutocodeDashboard
class AutocodeDashboard {
  // ... métodos existentes ...
  
  // Métodos específicos del UI Designer
  async loadDesignDocumentation() {
    try {
      console.log('Loading design documentation...');
      
      const response = await this.apiGet('/api/design/files');
      this.renderDesignFiles(response);
      
    } catch (error) {
      console.error('Error loading design documentation:', error);
      this.handleDesignError(error);
    }
  }
  
  renderDesignFiles(files) {
    const container = document.getElementById('design-files-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    files.forEach(file => {
      const fileElement = this.createDesignFileElement(file);
      container.appendChild(fileElement);
    });
  }
  
  createDesignFileElement(file) {
    const div = document.createElement('div');
    div.className = 'design-file-item bg-white rounded-lg shadow-sm border p-4 mb-4';
    div.innerHTML = `
      <h3 class="text-lg font-semibold text-gray-900 mb-2">${file.name}</h3>
      <p class="text-gray-600 mb-3">${file.description || 'No description available'}</p>
      <button onclick="dashboard.loadDesignFile('${file.path}')" 
              class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-md text-sm">
        View Diagram
      </button>
    `;
    return div;
  }
  
  async loadDesignFile(filePath) {
    try {
      const response = await this.apiGet(`/api/design/file?path=${encodeURIComponent(filePath)}`);
      this.renderMermaidDiagram(response.content);
      
    } catch (error) {
      console.error('Error loading design file:', error);
      this.handleDesignError(error);
    }
  }
  
  renderMermaidDiagram(content) {
    const diagramContainer = document.getElementById('design-diagram-container');
    if (!diagramContainer) return;
    
    // Initialize Mermaid if not already done
    if (typeof mermaid === 'undefined') {
      console.error('Mermaid library not loaded');
      return;
    }
    
    // Configure Mermaid
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      securityLevel: 'loose'
    });
    
    // Clear previous diagram
    diagramContainer.innerHTML = '';
    
    // Create diagram element
    const diagramId = `design-diagram-${Date.now()}`;
    const diagramDiv = document.createElement('div');
    diagramDiv.id = diagramId;
    diagramDiv.className = 'mermaid';
    diagramDiv.textContent = content;
    
    diagramContainer.appendChild(diagramDiv);
    
    // Render the diagram
    mermaid.init(undefined, diagramDiv);
  }
  
  handleDesignError(error) {
    const diagramContainer = document.getElementById('design-diagram-container');
    if (diagramContainer) {
      diagramContainer.innerHTML = `
        <div class="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 class="text-red-800 font-semibold">Error Loading Design</h3>
          <p class="text-red-600 mt-2">${error.message}</p>
        </div>
      `;
    }
  }
}
```

### 3. Hacer Componentes de Template Autocontenidos
#### 3.1 Mover Lógica Específica a Templates
Para componentes que tienen lógica muy específica, añadir scripts inline en los templates correspondientes.

**Ejemplo en `components/ui_designer.html`:**
```html
<div id="ui-designer-container" class="p-6">
  <div class="mb-6">
    <h2 class="text-2xl font-bold text-gray-900">UI Designer</h2>
    <p class="text-gray-600">Visualize and analyze UI components</p>
  </div>
  
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Component Tree Section -->
    <div class="bg-white rounded-lg shadow-sm border p-6">
      <h3 class="text-lg font-semibold mb-4">Component Tree</h3>
      <div id="component-tree-container">
        <div class="text-center py-8">
          <button onclick="generateComponentTree()" 
                  class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md">
            Generate Tree
          </button>
        </div>
      </div>
    </div>
    
    <!-- Design Files Section -->
    <div class="bg-white rounded-lg shadow-sm border p-6">
      <h3 class="text-lg font-semibold mb-4">Design Files</h3>
      <div id="design-files-container">
        <div class="text-center py-8">
          <button onclick="loadDesignFiles()" 
                  class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md">
            Load Files
          </button>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Diagram Display -->
  <div class="mt-6 bg-white rounded-lg shadow-sm border p-6">
    <h3 class="text-lg font-semibold mb-4">Diagram Viewer</h3>
    <div id="design-diagram-container" class="min-h-[400px] border border-gray-200 rounded-lg p-4">
      <div class="text-center text-gray-500 py-20">
        Select a component or design file to view diagram
      </div>
    </div>
  </div>
</div>

<!-- Script específico del componente (autocontenido) -->
<script>
// Funciones específicas del UI Designer que solo se usan en esta página
async function generateComponentTree() {
  if (!window.dashboard) {
    console.error('Dashboard not initialized');
    return;
  }
  
  const button = event.target;
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = 'Generating...';
  
  try {
    await dashboard.loadComponentTree();
  } catch (error) {
    console.error('Error generating component tree:', error);
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

async function loadDesignFiles() {
  if (!window.dashboard) {
    console.error('Dashboard not initialized');
    return;
  }
  
  const button = event.target;
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = 'Loading...';
  
  try {
    await dashboard.loadDesignDocumentation();
  } catch (error) {
    console.error('Error loading design files:', error);
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

// Auto-load cuando el componente está visible
document.addEventListener('DOMContentLoaded', function() {
  if (window.dashboard && window.dashboard.currentPage === 'ui-designer') {
    // Auto-cargar contenido si estamos en la página del UI Designer
    setTimeout(() => {
      loadDesignFiles();
    }, 500);
  }
});
</script>
```

### 4. Actualizar Referencias en base.html
#### 4.1 Simplificar Carga de Scripts
```html
<!-- ANTES (múltiples scripts): -->
<script src="{{ url_for('static', path='app.js') }}"></script>
<script src="{{ url_for('static', path='js/utils/api-fetch.js') }}"></script>
<script src="{{ url_for('static', path='js/components/ui-designer.js') }}"></script>

<!-- DESPUÉS (solo app.js): -->
<script src="{{ url_for('static', path='app.js') }}"></script>
```

#### 4.2 Mantener Funciones Globales para Interoperabilidad
Asegurar que las funciones globales siguen disponibles en `app.js`:
```javascript
// Al final de app.js, mantener funciones globales para onclick handlers
let dashboard;

// Funciones globales para handlers de botones (llamadas desde templates)
async function runCheck(checkName) {
  if (!dashboard) {
    console.error('Dashboard not initialized');
    return;
  }
  
  console.log(`Running check: ${checkName}`);
  
  const button = event.target;
  button.disabled = true;
  button.textContent = 'Running...';
  
  try {
    const result = await dashboard.apiPost(`/api/checks/${checkName}/run`);
    
    if (result.success) {
      console.log(`Check ${checkName} executed successfully`);
    } else {
      console.error(`Check ${checkName} failed:`, result.error);
    }
    
  } catch (error) {
    console.error(`Error running check ${checkName}:`, error);
    
  } finally {
    button.disabled = false;
    button.textContent = 'Run Now';
    
    // Refresh status immediately
    dashboard.fetchAndUpdateStatus();
  }
}

async function updateConfig() {
  if (!dashboard) {
    console.error('Dashboard not initialized');
    return;
  }
  
  // Usar método consolidado del dashboard
  await dashboard.saveConfiguration();
}

// Otras funciones globales necesarias...
async function refreshArchitecture() { /* ... */ }
async function regenerateArchitecture() { /* ... */ }
async function generateComponentTree() { /* ... */ }
async function refreshComponentTree() { /* ... */ }

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
  dashboard = new AutocodeDashboard();
  
  // Eventos globales
  document.addEventListener('keydown', function(event) {
    if (event.code === 'Space' && event.target.tagName !== 'INPUT') {
      event.preventDefault();
      dashboard.fetchAndUpdateStatus();
    }
  });
});
```

### 5. Eliminar Archivos y Carpetas Obsoletas
```bash
# Eliminar archivos JS modulares después de consolidar
rm -rf autocode/web/static/js/utils/
rm -rf autocode/web/static/js/components/
rm -rf autocode/web/static/js/  # Solo si está completamente vacía

# Alternativamente, si hay archivos que no se pueden consolidar fácilmente:
# Mantener solo los archivos esenciales y eliminar los redundantes
```

### 6. Optimizar app.js para Legibilidad
#### 6.1 Organizar Métodos por Funcionalidad
```javascript
class AutocodeDashboard {
  constructor() { /* ... */ }
  
  // === CORE METHODS ===
  init() { /* ... */ }
  getCurrentPage() { /* ... */ }
  setupNavigation() { /* ... */ }
  
  // === API METHODS ===
  async apiGet(endpoint) { /* ... */ }
  async apiPost(endpoint, data) { /* ... */ }
  async apiPut(endpoint, data) { /* ... */ }
  
  // === DATA LOADING ===
  async loadInitialData() { /* ... */ }
  async fetchAndUpdateStatus() { /* ... */ }
  async fetchAndUpdateConfig() { /* ... */ }
  
  // === UI UPDATES ===
  updateUI(data) { /* ... */ }
  updateDaemonStatus(daemon) { /* ... */ }
  updateSystemStats(daemon) { /* ... */ }
  updateCheckResults(checks) { /* ... */ }
  
  // === CONFIG MANAGEMENT ===
  async loadConfigPage() { /* ... */ }
  async saveConfiguration() { /* ... */ }
  async resetConfiguration() { /* ... */ }
  
  // === AUTO-REFRESH ===
  startAutoRefresh() { /* ... */ }
  stopAutoRefresh() { /* ... */ }
  
  // === DESIGN/UI DESIGNER ===
  async loadDesignDocumentation() { /* ... */ }
  renderMermaidDiagram(content) { /* ... */ }
  
  // === UTILITIES ===
  formatDuration(seconds) { /* ... */ }
  formatTimestamp(timestamp) { /* ... */ }
  handleError(error) { /* ... */ }
}
```

## Criterios de Verificación

### Verificación de Funcionalidad
1. **Dashboard principal**: Auto-refresh, botones de checks, estadísticas deben funcionar
2. **Página de configuración**: Formularios de config deben cargar y guardar correctamente
3. **UI Designer**: Componentes específicos deben funcionar (si existen)
4. **Navegación**: Cambio entre páginas debe mantener funcionalidad
5. **Handlers globales**: Funciones onclick desde templates deben ejecutarse

### Verificación de Carga de Scripts
```bash
# Iniciar servidor
uv run autocode daemon

# Verificar en navegador
# 1. Abrir herramientas de desarrollador
# 2. Tab Network → Recargar página
# 3. Verificar que solo se carga app.js (no subcarpetas js/)
# 4. No debe haber errores 404 para archivos JS eliminados
```

### Tests de Consola JavaScript
```javascript
// En consola del navegador, verificar que dashboard está disponible
window.dashboard instanceof AutocodeDashboard  // debe retornar true

// Verificar métodos API consolidados
dashboard.apiGet('/api/status')  // debe ejecutar sin errores

// Verificar funciones globales
typeof runCheck === 'function'  // debe retornar true
typeof updateConfig === 'function'  // debe retornar true
```

### Verificación de Templates Autocontenidos
1. **Componentes inline**: Scripts en templates específicos deben ejecutarse
2. **Event handlers**: onclick y otros eventos deben funcionar correctamente
3. **Inicialización**: Componentes deben auto-inicializarse cuando sea apropiado

### Verificación de Mantenibilidad
1. **Un solo archivo JS**: Solo `app.js` debe existir (sin subcarpetas js/)
2. **Organización clara**: Métodos organizados por funcionalidad
3. **Sin duplicación**: No debe haber código repetido entre templates y app.js
4. **Funciones utilitarias**: Métodos API consolidados deben ser reutilizables

## Consideraciones Importantes

### Preservar Funcionalidad Existente
- Todas las funciones actuales deben seguir funcionando
- Auto-refresh debe mantener mismo comportamiento
- Handlers de botones deben preservar funcionalidad
- Formularios de configuración deben funcionar igual

### Balance Simplicidad vs Funcionalidad
- Priorizar un solo archivo JS principal
- Usar scripts inline solo para lógica muy específica de componentes
- Mantener separación clara entre lógica global y específica

### Interoperabilidad con Templates
- Funciones globales deben permanecer disponibles para onclick
- Variables globales como `dashboard` deben ser accesibles
- Event listeners deben funcionar correctamente

## Template de Commit Message
```
refactor(js): simplify JavaScript structure and make components self-contained

- Consolidated js/utils/api-fetch.js functionality into AutocodeDashboard class
- Integrated js/components/ui-designer.js methods into main app.js
- Added consolidated API methods (apiGet, apiPost, apiPut) for consistent error handling
- Moved component-specific logic to inline scripts in templates where appropriate
- Removed js/utils/ and js/components/ subdirectories
- Organized AutocodeDashboard methods by functionality for better maintainability
- Preserved all existing functionality including auto-refresh, config management, and UI updates
- Maintained global functions for template onclick handlers
- Simplified script loading to single app.js file
- Made templates more self-contained while keeping shared logic centralized
```

## Notas para el Programador

### Debugging
Si algo no funciona después de la consolidación:
1. Verificar que no hay referencias a archivos JS eliminados en templates
2. Comprobar que funciones globales están definidas correctamente
3. Verificar que métodos consolidados mantienen la misma funcionalidad
4. Revisar consola del navegador para errores de JavaScript

### Extensibilidad
Para añadir nueva funcionalidad:
1. Añadir métodos a la clase `AutocodeDashboard` para lógica compartida
2. Usar scripts inline en templates para lógica muy específica
3. Mantener funciones globales para handlers de botones si es necesario
4. Seguir organización por funcionalidad en `app.js`
