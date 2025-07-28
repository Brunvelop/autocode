# Task 008: Testing Integral y Optimizaciones Finales de UI

## Contexto del Proyecto
Este proyecto, autocode, es una herramienta de monitoreo automático con interfaz web que ha pasado por una serie de refactorizaciones en la UI: integración de Tailwind CSS, simplificación de la estructura JavaScript, y migración a nuevos endpoints API con auto-actualización inteligente. Esta tarea final se enfoca en verificar que todos los cambios funcionen correctamente juntos, optimizar el rendimiento, asegurar la accesibilidad y establecer un sistema de testing para futuras modificaciones.

## Estado Actual Después de Refactorizaciones Anteriores

### Cambios Implementados (Tasks 005-007)
1. **Task 005**: Tailwind CSS integrado via CDN, eliminación de archivos CSS personalizados
2. **Task 006**: Estructura JS simplificada, componentes autocontenidos, un solo `app.js`
3. **Task 007**: Migración a endpoints wrapper, auto-refresh inteligente, feedback visual mejorado

### Tecnologías y Estructura Actual
```
autocode/web/
├── static/
│   └── app.js                    # Archivo JS único y consolidado
└── templates/
    ├── base.html                 # Con Tailwind CDN y layout simplificado
    ├── components/               # Componentes con clases Tailwind
    │   ├── check_card.html
    │   ├── stat_card.html
    │   ├── header.html
    │   ├── footer.html
    │   └── ui_designer.html
    └── pages/                    # Páginas con auto-refresh inteligente
        ├── dashboard.html
        ├── config.html
        └── ui_designer.html
```

### Funcionalidades Clave a Verificar
1. **UI Responsiva**: Layout adaptativo con Tailwind
2. **Auto-refresh inteligente**: Múltiples intervalos diferenciados
3. **Endpoints wrapper**: Integración con nueva API
4. **Componentes autocontenidos**: Templates con scripts inline donde apropiado
5. **Feedback visual**: Notificaciones, loading states, actividad del usuario

## Objetivo de la Tarea
Asegurar la calidad, performance y mantenibilidad de la UI refactorizada mediante:
1. **Testing integral**: Verificación exhaustiva de funcionalidades en diferentes escenarios
2. **Optimización de performance**: Reducir tiempo de carga y mejorar responsividad
3. **Accesibilidad**: Cumplir estándares básicos de accesibilidad web
4. **Documentación**: Crear guías para futuras modificaciones
5. **Monitoring**: Establecer métricas para detectar regresiones

## Instrucciones Paso a Paso

### 1. Testing Integral de Funcionalidades

#### 1.1 Crear Suite de Tests Manuales
Crear archivo `testing/ui-test-checklist.md`:

```markdown
# UI Testing Checklist - Autocode Dashboard

## Pre-requisitos
- [ ] Servidor ejecutándose: `uv run autocode daemon`
- [ ] Acceso a http://localhost:8080/dashboard
- [ ] Herramientas de desarrollador abiertas (F12)
- [ ] Navegadores: Chrome, Firefox, Safari (si disponible)

## 1. Carga Inicial y Layout
- [ ] Página carga sin errores 404 o 500
- [ ] Tailwind CSS se aplica correctamente (sin flash de contenido sin estilos)
- [ ] Sidebar visible y funcional
- [ ] Header con información correcta
- [ ] Footer con controles de auto-refresh

## 2. Responsividad (Tailwind)
- [ ] Desktop (1200px+): Layout de 4 columnas en stats, 3 en checks
- [ ] Tablet (768px): Layout adaptado, sidebar apropiado
- [ ] Mobile (320px): Columna única, navegación accesible
- [ ] Zoom 150%: Elementos siguen siendo legibles y accesibles

## 3. Auto-Refresh Inteligente
- [ ] Dashboard.refreshConfig muestra configuración diferenciada
- [ ] Daemon status se actualiza cada 3 segundos
- [ ] Check results se actualizan cada 10 segundos
- [ ] Pausa/Resume funciona correctamente
- [ ] Cambio de velocidad actualiza intervalos
- [ ] Inactividad del usuario reduce frecuencia
- [ ] Cambio de tab pausa el refresh
- [ ] Vuelta al tab reanuda y refresca inmediatamente

## 4. Nuevos Endpoints API
- [ ] Botón "Run Now" en doc_check usa /api/generate-docs
- [ ] Botón "Run Now" en git_check usa /api/analyze-git  
- [ ] Botón generar diseño usa /api/generate-design
- [ ] Configuración carga con /api/config/load
- [ ] Respuestas tienen formato CheckExecutionResponse
- [ ] Errores se muestran con notificaciones

## 5. Estados Visuales y Feedback
- [ ] Loading indicators aparecen durante operaciones
- [ ] Notificaciones emergen correctamente (success, error, info)
- [ ] Auto-dismiss de notificaciones después de 5s
- [ ] Botones cambian estado durante ejecución (disabled, "Running...")
- [ ] Indicador global de loading en parte superior

## 6. Navegación entre Páginas
- [ ] /dashboard: Stats y checks funcionan
- [ ] /config: Formularios cargan y guardan
- [ ] /ui-designer: Componentes específicos funcionan
- [ ] Links de sidebar actualizan página correctamente
- [ ] Auto-refresh se adapta a página actual

## 7. Funcionalidades Específicas por Página

### Dashboard
- [ ] Daemon status indicator correcto (verde/rojo)
- [ ] Stats (uptime, total checks, last check) se actualizan
- [ ] Check cards muestran estado correcto
- [ ] Botones "Run Now" ejecutan y muestran feedback
- [ ] Detalles de checks son legibles

### Configuración
- [ ] Formulario se llena con valores actuales
- [ ] Cambios se guardan correctamente
- [ ] Reset to defaults funciona
- [ ] Validación de campos funciona
- [ ] Mensajes de éxito/error aparecen

### UI Designer  
- [ ] Componentes específicos cargan
- [ ] Scripts inline funcionan correctamente
- [ ] Integración con dashboard global funciona

## 8. Testing de Errores
- [ ] Daemon detenido: UI muestra estado de error apropiado
- [ ] Red desconectada: Errores se manejan gracefully
- [ ] Endpoints no disponibles: Fallbacks funcionan
- [ ] JavaScript deshabilitado: Contenido básico sigue visible

## 9. Performance
- [ ] Tiempo de carga inicial < 2 segundos
- [ ] Transiciones suaves sin lag
- [ ] Memory leaks: Refresh no incrementa memoria constantemente
- [ ] CPU usage: Auto-refresh no consume recursos excesivos
```

#### 1.2 Automatizar Tests Básicos con JavaScript
Crear función de auto-testing en `app.js`:

```javascript
class AutocodeDashboard {
  // ... métodos existentes ...
  
  // Método para auto-testing (solo en development)
  async runSelfTests() {
    if (!window.location.hostname.includes('localhost')) {
      console.warn('Self-tests only available in development');
      return;
    }
    
    console.log('🧪 Starting Autocode UI Self-Tests...');
    
    const tests = [
      this.testTailwindIntegration,
      this.testAPIEndpoints,
      this.testAutoRefreshConfig,
      this.testNotificationSystem,
      this.testResponsiveLayout,
      this.testKeyboardNavigation
    ];
    
    const results = {};
    
    for (const test of tests) {
      try {
        const testName = test.name;
        console.log(`Running ${testName}...`);
        
        const result = await test.call(this);
        results[testName] = { success: true, ...result };
        console.log(`✅ ${testName} passed`);
        
      } catch (error) {
        results[testName] = { success: false, error: error.message };
        console.error(`❌ ${testName} failed:`, error);
      }
    }
    
    this.displayTestResults(results);
    return results;
  }
  
  // Tests específicos
  async testTailwindIntegration() {
    // Verificar que Tailwind está cargado
    const testElement = document.createElement('div');
    testElement.className = 'bg-blue-500 p-4 rounded-lg';
    document.body.appendChild(testElement);
    
    const styles = window.getComputedStyle(testElement);
    const hasBgColor = styles.backgroundColor !== 'rgba(0, 0, 0, 0)';
    const hasPadding = styles.padding !== '0px';
    const hasBorderRadius = styles.borderRadius !== '0px';
    
    document.body.removeChild(testElement);
    
    if (!hasBgColor || !hasPadding || !hasBorderRadius) {
      throw new Error('Tailwind CSS classes not applied correctly');
    }
    
    return { message: 'Tailwind CSS integration working correctly' };
  }
  
  async testAPIEndpoints() {
    // Test nuevo endpoint wrapper
    try {
      const response = await this.apiGet('/api/config/load');
      
      if (!response.hasOwnProperty('success')) {
        throw new Error('CheckExecutionResponse format not found');
      }
      
      return { message: 'API wrapper endpoints responding correctly' };
      
    } catch (error) {
      throw new Error(`API endpoint test failed: ${error.message}`);
    }
  }
  
  async testAutoRefreshConfig() {
    const requiredConfigs = ['daemon_status', 'check_results', 'config_data'];
    
    for (const configType of requiredConfigs) {
      if (!this.refreshConfig[configType]) {
        throw new Error(`Missing refresh config for ${configType}`);
      }
      
      const config = this.refreshConfig[configType];
      if (!config.hasOwnProperty('interval') || !config.hasOwnProperty('enabled')) {
        throw new Error(`Invalid refresh config structure for ${configType}`);
      }
    }
    
    return { message: 'Auto-refresh configuration is properly structured' };
  }
  
  async testNotificationSystem() {
    // Test notificación temporal
    const initialCount = document.querySelectorAll('.notification').length;
    
    this.showNotification('Test notification', 'info', 1000);
    
    await new Promise(resolve => setTimeout(resolve, 100));
    const afterShowCount = document.querySelectorAll('.notification').length;
    
    if (afterShowCount !== initialCount + 1) {
      throw new Error('Notification not created correctly');
    }
    
    // Wait for auto-dismiss
    await new Promise(resolve => setTimeout(resolve, 1200));
    const afterDismissCount = document.querySelectorAll('.notification').length;
    
    if (afterDismissCount !== initialCount) {
      throw new Error('Notification not dismissed automatically');
    }
    
    return { message: 'Notification system working correctly' };
  }
  
  async testResponsiveLayout() {
    const viewport = {
      width: window.innerWidth,
      height: window.innerHeight
    };
    
    // Test elementos críticos
    const sidebar = document.querySelector('nav');
    const mainContent = document.querySelector('main');
    
    if (!sidebar || !mainContent) {
      throw new Error('Critical layout elements not found');
    }
    
    // Verificar que el layout es funcional
    const sidebarVisible = window.getComputedStyle(sidebar).display !== 'none';
    const mainContentVisible = window.getComputedStyle(mainContent).display !== 'none';
    
    if (!sidebarVisible || !mainContentVisible) {
      throw new Error('Layout elements not visible');
    }
    
    return { 
      message: 'Responsive layout elements present',
      viewport,
      elementsVisible: { sidebar: sidebarVisible, mainContent: mainContentVisible }
    };
  }
  
  async testKeyboardNavigation() {
    // Test básico de accesibilidad con teclado
    const focusableElements = document.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length === 0) {
      throw new Error('No focusable elements found');
    }
    
    // Test que elementos tienen atributos de accesibilidad apropiados
    let accessibilityIssues = 0;
    focusableElements.forEach(element => {
      if (element.tagName === 'BUTTON' && !element.textContent.trim()) {
        accessibilityIssues++;
      }
    });
    
    return {
      message: 'Keyboard navigation elements present',
      focusableCount: focusableElements.length,
      accessibilityIssues
    };
  }
  
  displayTestResults(results) {
    const totalTests = Object.keys(results).length;
    const passedTests = Object.values(results).filter(r => r.success).length;
    
    console.log(`\n🧪 UI Self-Tests Complete: ${passedTests}/${totalTests} passed\n`);
    
    // Mostrar resultados en UI también
    this.showNotification(
      `UI Tests: ${passedTests}/${totalTests} passed`,
      passedTests === totalTests ? 'success' : 'warning',
      10000
    );
    
    // Almacenar en localStorage para debugging
    localStorage.setItem('autocode_last_test_results', JSON.stringify({
      timestamp: new Date().toISOString(),
      results,
      summary: { total: totalTests, passed: passedTests }
    }));
  }
}

// Función global para ejecutar tests desde consola
window.runUITests = function() {
  if (window.dashboard) {
    return window.dashboard.runSelfTests();
  } else {
    console.error('Dashboard not initialized');
  }
};
```

### 2. Optimizaciones de Performance

#### 2.1 Optimizar Carga de Recursos
Actualizar `base.html` con optimizaciones:

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Autocode Dashboard{% endblock %}</title>
    
    <!-- Preload critical resources -->
    <link rel="preconnect" href="https://cdn.tailwindcss.com">
    
    <!-- Tailwind with optimized loading -->
    <script src="https://cdn.tailwindcss.com" defer></script>
    <script>
      // Configure Tailwind ASAP to prevent FOUC
      if (typeof tailwind !== 'undefined') {
        tailwind.config = {
          theme: {
            extend: {
              colors: {
                primary: '#007bff',
                secondary: '#6c757d',
                success: '#28a745',
                danger: '#dc3545',
                warning: '#ffc107',
                info: '#17a2b8'
              }
            }
          }
        }
      }
    </script>
    
    <!-- Critical CSS inline para elementos above-the-fold -->
    <style>
      /* Prevent FOUC */
      body { visibility: hidden; }
      body.loaded { visibility: visible; }
      
      /* Critical loading styles */
      .loading-skeleton {
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
      }
      
      @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
      }
      
      .animate-slide-in {
        animation: slideIn 0.3s ease-out;
      }
      
      .animate-slide-out {
        animation: slideOut 0.3s ease-in;
      }
      
      @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
      
      @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
      }
    </style>
</head>
<body class="bg-gray-50 font-sans">
    <!-- Loading skeleton mientras se carga Tailwind -->
    <div id="loading-skeleton" class="loading-skeleton fixed inset-0 z-50"></div>
    
    <!-- Contenido principal -->
    <div class="flex min-h-screen">
        <!-- ... resto del contenido ... -->
    </div>
    
    <!-- Scripts -->
    <script src="{{ url_for('static', path='app.js') }}" defer></script>
    
    <!-- Mermaid para diagramas (solo cargar si es necesario) -->
    {% if request.url.path in ['/ui-designer', '/design'] %}
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js" defer></script>
    {% endif %}
    
    <script>
      // Hide loading skeleton when page is ready
      document.addEventListener('DOMContentLoaded', function() {
        document.body.classList.add('loaded');
        const skeleton = document.getElementById('loading-skeleton');
        if (skeleton) {
          skeleton.style.display = 'none';
        }
      });
    </script>
</body>
</html>
```

#### 2.2 Optimizar JavaScript para Performance
Añadir método de debouncing y throttling en `app.js`:

```javascript
class AutocodeDashboard {
  // ... métodos existentes ...
  
  // Utilidades de performance
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
  
  throttle(func, limit) {
    let inThrottle;
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }
  
  // Optimizar event listeners con debouncing
  setupOptimizedEventListeners() {
    // Debounce user activity detection
    const debouncedActivity = this.debounce(() => {
      this.handleUserActivity();
    }, 500);
    
    const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    activityEvents.forEach(event => {
      document.addEventListener(event, debouncedActivity, { passive: true });
    });
    
    // Throttle resize events
    const throttledResize = this.throttle(() => {
      this.handleWindowResize();
    }, 250);
    
    window.addEventListener('resize', throttledResize, { passive: true });
  }
  
  handleWindowResize() {
    // Actualizar configuraciones basadas en tamaño de ventana
    const isMobile = window.innerWidth < 768;
    
    if (isMobile && !this.mobileOptimized) {
      this.optimizeForMobile();
    } else if (!isMobile && this.mobileOptimized) {
      this.optimizeForDesktop();
    }
  }
  
  optimizeForMobile() {
    console.log('Optimizing for mobile...');
    
    // Reducir frecuencia de refresh en móvil
    this.setRefreshInterval('daemon_status', 5000);  // 5s instead of 3s
    this.setRefreshInterval('check_results', 15000); // 15s instead of 10s
    
    this.mobileOptimized = true;
  }
  
  optimizeForDesktop() {
    console.log('Optimizing for desktop...');
    
    // Restaurar frecuencias normales
    this.setRefreshInterval('daemon_status', 3000);
    this.setRefreshInterval('check_results', 10000);
    
    this.mobileOptimized = false;
  }
  
  // Método para limpiar recursos al cambiar página
  cleanup() {
    // Limpiar todos los timers
    Object.keys(this.refreshConfig).forEach(dataType => {
      this.stopSpecificRefresh(dataType);
    });
    
    // Clear activity timer
    if (this.userActivityTimer) {
      clearTimeout(this.userActivityTimer);
    }
    
    // Remove event listeners si es necesario
    console.log('Dashboard cleanup completed');
  }
}

// Cleanup automático cuando se va de la página
window.addEventListener('beforeunload', function() {
  if (window.dashboard) {
    window.dashboard.cleanup();
  }
});
```

### 3. Mejoras de Accesibilidad

#### 3.1 Añadir Atributos ARIA y Semántica
Actualizar templates con mejor accesibilidad:

```html
<!-- components/check_card.html mejorado -->
<article class="bg-white rounded-lg shadow-sm border p-6 {{ 'border-green-200' if status == 'success' else 'border-red-200' if status == 'error' else 'border-yellow-200' }}"
         role="region" 
         aria-labelledby="check-title-{{ check_name }}"
         aria-describedby="check-desc-{{ check_name }}">
  
  <header class="flex items-center justify-between mb-4">
    <h3 id="check-title-{{ check_name }}" class="text-lg font-semibold text-gray-900">{{ title }}</h3>
    
    <div class="flex items-center space-x-2" role="status" aria-live="polite">
      <div class="w-3 h-3 rounded-full {{ 'bg-green-500' if status == 'success' else 'bg-red-500' if status == 'error' else 'bg-yellow-500' }}"
           aria-hidden="true"></div>
      <span class="text-sm font-medium {{ 'text-green-700' if status == 'success' else 'text-red-700' if status == 'error' else 'text-yellow-700' }}"
            id="status-{{ check_name }}">{{ status_text }}</span>
    </div>
  </header>
  
  <p id="check-desc-{{ check_name }}" class="text-gray-600 mb-4">{{ message }}</p>
  
  <footer class="flex items-center justify-between">
    <time class="text-xs text-gray-500" datetime="{{ timestamp_iso }}">
      Last run: {{ timestamp }}
    </time>
    
    <button onclick="{{ action }}" 
            class="bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 text-white px-3 py-1 rounded-md text-sm transition-colors"
            aria-describedby="check-desc-{{ check_name }}"
            type="button">
      <span class="sr-only">Run {{ title }} check</span>
      Run Now
    </button>
  </footer>
</article>
```

#### 3.2 Mejorar Navegación por Teclado
```javascript
class AutocodeDashboard {
  // ... métodos existentes ...
  
  setupKeyboardNavigation() {
    // Keyboard shortcuts
    document.addEventListener('keydown', (event) => {
      // Skip if user is typing in input
      if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return;
      }
      
      switch (event.key) {
        case ' ':
          // Space para refresh manual
          event.preventDefault();
          this.fetchAndUpdateStatus();
          this.showNotification('Manual refresh triggered', 'info', 2000);
          break;
          
        case 'r':
        case 'R':
          // R para toggle auto-refresh
          event.preventDefault();
          if (this.updatePaused) {
            this.resumeAutoRefresh();
            this.showNotification('Auto-refresh resumed', 'success', 2000);
          } else {
            this.pauseAutoRefresh();
            this.showNotification('Auto-refresh paused', 'warning', 2000);
          }
          break;
          
        case '1':
          // Números para navegación rápida
          event.preventDefault();
          window.location.href = '/dashboard';
          break;
          
        case '2':
          event.preventDefault();
          window.location.href = '/config';
          break;
          
        case '3':
          event.preventDefault();
          window.location.href = '/ui-designer';
          break;
          
        case 'Escape':
          // Escape para cerrar notificaciones
          event.preventDefault();
          this.dismissAllNotifications();
          break;
          
        case '?':
          // ? para mostrar ayuda
          event.preventDefault();
          this.showKeyboardHelp();
          break;
      }
    });
    
    // Mejorar focus management
    this.setupFocusManagement();
  }
  
  setupFocusManagement() {
    // Trap focus in modals if any
    // Skip to main content link
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.className = 'sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 bg-blue-600 text-white p-2 z-50';
    skipLink.textContent = 'Skip to main content';
    document.body.insertBefore(skipLink, document.body.firstChild);
    
    // Add main content landmark
    const mainContent = document.querySelector('main');
    if (mainContent) {
      mainContent.id = 'main-content';
      mainContent.setAttribute('tabindex', '-1');
    }
  }
  
  showKeyboardHelp() {
    const helpText = `
Keyboard Shortcuts:
• Space: Manual refresh
• R: Toggle auto-refresh
• 1: Dashboard
• 2: Configuration  
• 3: UI Designer
• Escape: Close notifications
• ?: Show this help
    `;
    
    this.showNotification(helpText.trim(), 'info', 10000);
  }
  
  dismissAllNotifications() {
    const notifications = document.querySelectorAll('.notification');
    notifications.forEach(notification => {
      notification.remove();
    });
  }
}
```

### 4. Establecer Métricas y Monitoring

#### 4.1 Crear Sistema de Métricas Básico
```javascript
class AutocodeDashboard {
  constructor() {
    // ... configuración existente ...
    
    this.metrics = {
      pageLoadTime: 0,
      apiCallCount: 0,
      apiErrors: 0,
      refreshCount: 0,
      userInteractions: 0,
      performanceEntries: []
    };
    
    this.startMetricsCollection();
  }
  
  startMetricsCollection() {
    // Medir tiempo de carga de página
    window.addEventListener('load', () => {
      this.metrics.pageLoadTime = performance.now();
      console.log(`Page loaded in ${this.metrics.pageLoadTime.toFixed(2)}ms`);
    });
    
    // Recopilar performance entries
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.metrics.performanceEntries.push({
            name: entry.name,
            type: entry.entryType,
            startTime: entry.startTime,
            duration: entry.duration
          });
        }
      });
      
      observer.observe({ entryTypes: ['navigation', 'resource', 'measure'] });
    }
  }
  
  recordAPICall(endpoint, success = true) {
    this.metrics.apiCallCount++;
    if (!success) {
      this.metrics.apiErrors++;
    }
    
    // Log si hay muchos errores
    if (this.metrics.apiErrors > 10 && this.metrics.apiErrors / this.metrics.apiCallCount > 0.2) {
      console.warn('High API error rate detected:', {
        errors: this.metrics.apiErrors,
        total: this.metrics.apiCallCount,
        rate: (this.metrics.apiErrors / this.metrics.apiCallCount * 100).toFixed(1) + '%'
      });
    }
  }
  
  recordUserInteraction(type) {
    this.metrics.userInteractions++;
    
    // Track interaction types
    if (!this.metrics.interactionTypes) {
      this.metrics.interactionTypes = {};
    }
    this.metrics.interactionTypes[type] = (this.metrics.interactionTypes[type] || 0) + 1;
  }
  
  recordRefresh(dataType) {
    this.metrics.refreshCount++;
    
    if (!this.metrics.refreshByType) {
      this.metrics.refreshByType = {};
    }
    this.metrics.refreshByType[dataType] = (this.metrics.refreshByType[dataType] || 0) + 1;
  }
  
  getMetricsReport() {
    return {
      ...this.metrics,
      uptime: Date.now() - this.initTime,
      averageApiSuccessRate: this.metrics.apiCallCount > 0 ? 
        ((this.metrics.apiCallCount - this.metrics.apiErrors) / this.metrics.apiCallCount * 100).toFixed(1) + '%' : 'N/A',
      memoryUsage: performance.memory ? {
        used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024) + ' MB',
        total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024) + ' MB'
      } : 'Not available'
    };
  }
  
  // Integrar métricas en métodos existentes
