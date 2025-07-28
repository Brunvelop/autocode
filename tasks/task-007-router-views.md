# Task 007: Implementar Router y Vistas Principales con Integración de API

## Contexto del Proyecto
Este proyecto autocode es una herramienta de desarrollo que automatiza verificaciones de código, documentación y tests. El sistema cuenta con una API FastAPI robusta que expone múltiples endpoints para interactuar con el daemon de fondo, generar documentación, crear diagramas de diseño y ejecutar verificaciones.

## Estado Actual del Frontend
Existe un proyecto Vue.js en `autocode/web_modern/` con la siguiente estructura base:

```
autocode/web_modern/
├── package.json
├── vite.config.js
├── index.html
├── src/
│   ├── App.vue
│   ├── main.js
│   ├── router/
│   │   └── index.js           # Router básico a completar
│   ├── stores/
│   │   └── main.js            # Store básico a expandir
│   ├── views/
│   │   ├── Dashboard.vue      # Vista placeholder a implementar
│   │   ├── Design.vue         # Vista placeholder a implementar
│   │   ├── Docs.vue           # Vista placeholder a implementar
│   │   └── Config.vue         # Vista placeholder a implementar
│   └── components/            # Componentes base disponibles
│       ├── Card.vue
│       ├── MarkdownRenderer.vue 
│       ├── DiagramRenderer.vue
│       ├── LoadingSpinner.vue
│       ├── ErrorMessage.vue
│       └── index.js
└── node_modules/
```

### Tecnologías del Stack
- **Vue 3**: Framework con Composition API
- **Vue Router 4**: Para navegación del lado del cliente
- **Pinia**: State management moderno para Vue 3
- **Axios**: Cliente HTTP para comunicación con API
- **Vite**: Build tool con proxy configurado para desarrollo

### Componentes Base Disponibles
Los siguientes componentes están disponibles para uso en las vistas:

```javascript
// Importación desde src/components/index.js
import { 
  Card,                // Contenedor con variants y slots
  MarkdownRenderer,    // Renderiza Markdown con marked.js
  DiagramRenderer,     // Renderiza diagramas Mermaid
  LoadingSpinner,      // Indicador de carga configurable
  ErrorMessage         // Mensaje de error con variants
} from '@/components'
```

## API Endpoints Disponibles
El backend FastAPI (localhost:8080) expone los siguientes endpoints:

### Endpoints de Estado
```http
GET  /api/status              # Estado general del daemon y checks
GET  /api/daemon/status       # Estado específico del daemon
GET  /api/checks              # Resultados de todos los checks
```

### Endpoints de Generación
```http
POST /api/generate-docs       # Generar documentación
POST /api/generate-design     # Generar diagramas de diseño
POST /api/docs/check-sync     # Check síncrono de documentación
```

### Endpoints de Configuración
```http
GET  /api/config              # Configuración actual
POST /api/config/load         # Cargar configuración desde archivo
```

### Endpoints de Checks Individuales
```http
POST /api/checks/doc/run      # Ejecutar check de documentación
POST /api/checks/test/run     # Ejecutar check de tests
POST /api/checks/git/run      # Ejecutar check de git
```

### Estructura de Respuestas API
```javascript
// GET /api/status
{
  "daemon": {
    "running": true,
    "uptime": "00:15:23",
    "last_check": "2025-01-15T10:30:00Z"
  },
  "checks": {
    "doc": {
      "status": "success",
      "last_run": "2025-01-15T10:29:45Z",
      "files_checked": 15,
      "outdated": 2
    },
    "test": {
      "status": "warning", 
      "last_run": "2025-01-15T10:29:50Z",
      "tests_run": 45,
      "passed": 43,
      "failed": 2
    },
    "git": {
      "status": "info",
      "last_run": "2025-01-15T10:29:55Z", 
      "modified_files": 3,
      "staged_files": 1
    }
  },
  "config": {
    "project_name": "autocode",
    "scan_interval": 300
  }
}

// POST /api/generate-design
{
  "status": "success",
  "message": "Design documentation generated",
  "files_generated": [
    "design/autocode/_index.md",
    "design/autocode/core/_module.md"
  ],
  "diagrams_created": 12
}

// POST /api/generate-docs
{
  "status": "success", 
  "message": "Documentation generated successfully",
  "files_processed": 25,
  "docs_created": 18
}
```

## Instrucciones Paso a Paso

### 1. Configurar Router Completo
```javascript
// src/router/index.js - Configuración completa
import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Design from '../views/Design.vue'
import Docs from '../views/Docs.vue'
import Config from '../views/Config.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      title: 'Dashboard - Autocode',
      description: 'Vista principal con resumen del estado del sistema'
    }
  },
  {
    path: '/dashboard',
    name: 'DashboardAlias',
    redirect: '/'
  },
  {
    path: '/design',
    name: 'Design',
    component: Design,
    meta: {
      title: 'Design & Architecture - Autocode',
      description: 'Visualización de diagramas de arquitectura y diseño'
    }
  },
  {
    path: '/docs',
    name: 'Docs',
    component: Docs,
    meta: {
      title: 'Documentation - Autocode',
      description: 'Gestión y visualización de documentación'
    }
  },
  {
    path: '/config',
    name: 'Config',
    component: Config,
    meta: {
      title: 'Configuration - Autocode',
      description: 'Configuración del sistema'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guards para actualizar título de página
router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'Autocode'
  next()
})

export default router
```

### 2. Expandir Store de Pinia
```javascript
// src/stores/main.js - Store completo con acciones
import { defineStore } from 'pinia'
import axios from 'axios'

export const useMainStore = defineStore('main', {
  state: () => ({
    // Dashboard data
    daemonStatus: null,
    checksResults: {},
    systemConfig: null,
    
    // Design data
    designFiles: [],
    currentDesignFile: null,
    designGenerationStatus: null,
    
    // Docs data
    docsStatus: null,
    docsIndex: null,
    docsGenerationStatus: null,
    
    // UI state
    loading: false,
    error: null,
    lastUpdated: null,
    
    // Real-time updates
    autoRefresh: false,
    refreshInterval: null
  }),

  getters: {
    isDaemonRunning: (state) => state.daemonStatus?.running || false,
    hasErrors: (state) => state.error !== null,
    
    // Check status getters
    docCheckStatus: (state) => state.checksResults?.doc?.status || 'unknown',
    testCheckStatus: (state) => state.checksResults?.test?.status || 'unknown', 
    gitCheckStatus: (state) => state.checksResults?.git?.status || 'unknown',
    
    // Summary getters
    totalChecksRun: (state) => {
      const checks = state.checksResults
      let total = 0
      if (checks.doc?.files_checked) total += checks.doc.files_checked
      if (checks.test?.tests_run) total += checks.test.tests_run
      if (checks.git?.modified_files) total += checks.git.modified_files
      return total
    },
    
    hasWarnings: (state) => {
      const checks = state.checksResults
      return Object.values(checks).some(check => 
        check.status === 'warning' || check.status === 'error'
      )
    }
  },

  actions: {
    // Sistema general
    async fetchSystemStatus() {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get('/api/status')
        this.daemonStatus = response.data.daemon
        this.checksResults = response.data.checks
        this.systemConfig = response.data.config
        this.lastUpdated = new Date().toISOString()
      } catch (error) {
        this.error = 'Failed to fetch system status: ' + error.message
        console.error('Error fetching status:', error)
      } finally {
        this.loading = false
      }
    },

    // Documentación
    async generateDocs() {
      this.loading = true
      this.docsGenerationStatus = 'generating'
      
      try {
        const response = await axios.post('/api/generate-docs')
        this.docsGenerationStatus = 'success'
        this.docsStatus = response.data
        
        // Refrescar estado después de generar
        await this.fetchSystemStatus()
        
        return response.data
      } catch (error) {
        this.docsGenerationStatus = 'error'
        this.error = 'Failed to generate docs: ' + error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchDocsIndex() {
      try {
        const response = await axios.get('/api/docs/index')
        this.docsIndex = response.data
        return response.data
      } catch (error) {
        console.error('Error fetching docs index:', error)
        // No lanzar error para no interrumpir la UI
      }
    },

    // Diseño y arquitectura
    async generateDesign() {
      this.loading = true
      this.designGenerationStatus = 'generating'
      
      try {
        const response = await axios.post('/api/generate-design')
        this.designGenerationStatus = 'success'
        this.designFiles = response.data.files_generated || []
        
        // Refrescar estado después de generar
        await this.fetchSystemStatus()
        
        return response.data
      } catch (error) {
        this.designGenerationStatus = 'error'
        this.error = 'Failed to generate design: ' + error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchDesignFile(filePath) {
      try {
        const response = await axios.get(`/design/${filePath}`)
        return response.data
      } catch (error) {
        this.error = `Failed to fetch design file: ${filePath}`
        throw error
      }
    },

    // Configuración
    async loadConfig() {
      try {
        const response = await axios.get('/api/config/load')
        this.systemConfig = response.data.config
        return response.data
      } catch (error) {
        this.error = 'Failed to load configuration: ' + error.message
        throw error
      }
    },

    // Checks individuales
    async runCheck(checkType) {
      this.loading = true
      
      try {
        const response = await axios.post(`/api/checks/${checkType}/run`)
        
        // Actualizar el check específico
        if (this.checksResults[checkType]) {
          this.checksResults[checkType] = {
            ...this.checksResults[checkType],
            ...response.data
          }
        }
        
        return response.data
      } catch (error) {
        this.error = `Failed to run ${checkType} check: ` + error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    // Auto-refresh
    startAutoRefresh(interval = 30000) {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
      }
      
      this.autoRefresh = true
      this.refreshInterval = setInterval(() => {
        this.fetchSystemStatus()
      }, interval)
    },

    stopAutoRefresh() {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
        this.refreshInterval = null
      }
      this.autoRefresh = false
    },

    // Utilidades
    clearError() {
      this.error = null
    },

    resetState() {
      this.daemonStatus = null
      this.checksResults = {}
      this.systemConfig = null
      this.designFiles = []
      this.currentDesignFile = null
      this.docsStatus = null
      this.docsIndex = null
      this.error = null
      this.lastUpdated = null
    }
  }
})
```

### 3. Implementar Vista Dashboard
```vue
<!-- src/views/Dashboard.vue -->
<template>
  <div class="dashboard">
    <!-- Header Section -->
    <div class="dashboard-header">
      <h1>Dashboard de Monitoreo</h1>
      <div class="dashboard-actions">
        <button 
          @click="refreshData" 
          :disabled="loading"
          class="btn btn-secondary"
        >
          <span v-if="loading">Actualizando...</span>
          <span v-else>Actualizar</span>
        </button>
        
        <button 
          @click="toggleAutoRefresh" 
          :class="['btn', autoRefresh ? 'btn-success' : 'btn-outline-secondary']"
        >
          {{ autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF' }}
        </button>
      </div>
    </div>

    <!-- Error Display -->
    <ErrorMessage 
      v-if="error" 
      :message="error"
      dismissible
      @dismiss="clearError"
    />

    <!-- Loading State -->
    <LoadingSpinner 
      v-if="loading && !daemonStatus" 
      message="Cargando estado del sistema..."
      size="large"
    />

    <!-- Main Content -->
    <div v-else class="dashboard-content">
      
      <!-- System Status Summary -->
      <section class="status-overview">
        <div class="overview-grid">
          <Card 
            variant="primary" 
            size="large"
            title="Estado del Daemon"
          >
            <div class="status-content">
              <div class="status-indicator" :class="isDaemonRunning ? 'running' : 'stopped'">
                <span class="status-dot"></span>
                {{ isDaemonRunning ? 'Ejecutándose' : 'Detenido' }}
              </div>
              <div v-if="daemonStatus?.uptime" class="status-detail">
                Uptime: {{ daemonStatus.uptime }}
              </div>
              <div v-if="lastUpdated" class="status-detail">
                Última actualización: {{ formatTime(lastUpdated) }}
              </div>
            </div>
          </Card>

          <Card 
            :variant="hasWarnings ? 'warning' : 'success'"
            size="large"
            title="Estado de Checks"
          >
            <div class="checks-summary">
              <div class="check-item">
                <span class="check-label">Documentación:</span>
                <span :class="`check-status check-status--${docCheckStatus}`">
                  {{ docCheckStatus.toUpperCase() }}
                </span>
              </div>
              <div class="check-item">
                <span class="check-label">Tests:</span>
                <span :class="`check-status check-status--${testCheckStatus}`">
                  {{ testCheckStatus.toUpperCase() }}
                </span>
              </div>
              <div class="check-item">
                <span class="check-label">Git:</span>
                <span :class="`check-status check-status--${gitCheckStatus}`"> 
                  {{ gitCheckStatus.toUpperCase() }}
                </span>
              </div>
            </div>
          </Card>

          <Card 
            variant="default"
            size="large"
            title="Estadísticas"
          >
            <div class="stats-grid">
              <div class="stat-item">
                <span class="stat-number">{{ totalChecksRun }}</span>
                <span class="stat-label">Total de elementos verificados</span>
              </div>
              <div class="stat-item">
                <span class="stat-number">{{ Object.keys(checksResults).length }}</span>
                <span class="stat-label">Tipos de checks activos</span>
              </div>
            </div>
          </Card>
        </div>
      </section>

      <!-- Detailed Checks Section -->
      <section class="checks-detail">
        <h2>Detalle de Verificaciones</h2>
        <div class="checks-grid">
          
          <!-- Documentation Check -->
          <Card 
            title="Verificación de Documentación"
            :variant="getCheckVariant(docCheckStatus)"
          >
            <div v-if="checksResults.doc" class="check-details">
              <div class="check-metric">
                <span class="metric-label">Archivos verificados:</span>
                <span class="metric-value">{{ checksResults.doc.files_checked || 0 }}</span>
              </div>
              <div class="check-metric">
                <span class="metric-label">Desactualizados:</span>
                <span class="metric-value">{{ checksResults.doc.outdated || 0 }}</span>
              </div>
              <div v-if="checksResults.doc.last_run" class="check-metric">
                <span class="metric-label">Última ejecución:</span>
                <span class="metric-value">{{ formatTime(checksResults.doc.last_run) }}</span>
              </div>
            </div>
            <div v-else>
              <p>No hay datos de verificación de documentación disponibles.</p>
            </div>
            
            <template #footer>
              <div class="check-actions">
                <button @click="runDocCheck" class="btn btn-sm btn-primary">
                  Ejecutar Check
                </button>
                <router-link to="/docs" class="btn btn-sm btn-outline-primary">
                  Ver Documentación
                </router-link>
              </div>
            </template>
          </Card>

          <!-- Test Check -->
          <Card 
            title="Verificación de Tests"
            :variant="getCheckVariant(testCheckStatus)"
          >
            <div v-if="checksResults.test" class="check-details">
              <div class="check-metric">
                <span class="metric-label">Tests ejecutados:</span>
                <span class="metric-value">{{ checksResults.test.tests_run || 0 }}</span>
              </div>
              <div class="check-metric">
                <span class="metric-label">Exitosos:</span>
                <span class="metric-value text-success">{{ checksResults.test.passed || 0 }}</span>
              </div>
              <div class="check-metric">
                <span class="metric-label">Fallidos:</span>
                <span class="metric-value text-danger">{{ checksResults.test.failed || 0 }}</span>
              </div>
              <div v-if="checksResults.test.last_run" class="check-metric">
                <span class="metric-label">Última ejecución:</span>
                <span class="metric-value">{{ formatTime(checksResults.test.last_run) }}</span>
              </div>
            </div>
            <div v-else>
              <p>No hay datos de verificación de tests disponibles.</p>
            </div>
            
            <template #footer>
              <div class="check-actions">
                <button @click="runTestCheck" class="btn btn-sm btn-primary">
                  Ejecutar Tests
                </button>
              </div>
            </template>
          </Card>

          <!-- Git Check -->
          <Card 
            title="Estado de Git"
            :variant="getCheckVariant(gitCheckStatus)"
          >
            <div v-if="checksResults.git" class="check-details">
              <div class="check-metric">
                <span class="metric-label">Archivos modificados:</span>
                <span class="metric-value">{{ checksResults.git.modified_files || 0 }}</span>
              </div>
              <div class="check-metric">
                <span class="metric-label">Archivos en stage:</span>
                <span class="metric-value">{{ checksResults.git.staged_files || 0 }}</span>
              </div>
              <div v-if="checksResults.git.last_run" class="check-metric">
                <span class="metric-label">Última verificación:</span>
                <span class="metric-value">{{ formatTime(checksResults.git.last_run) }}</span>
              </div>
            </div>
            <div v-else>
              <p>No hay datos de estado de Git disponibles.</p>
            </div>
            
            <template #footer>
              <div class="check-actions">
                <button @click="runGitCheck" class="btn btn-sm btn-primary">
                  Verificar Git
                </button>
              </div>
            </template>
          </Card>
        </div>
      </section>

      <!-- Quick Actions -->
      <section class="quick-actions">
        <h2>Acciones Rápidas</h2>
        <div class="actions-grid">
          <Card title="Generar Documentación">
            <p>Genera automáticamente la documentación del proyecto basada en el código fuente.</p>
            <template #footer>
              <button @click="generateDocs" class="btn btn-primary" :disabled="loading">
                Generar Documentación
              </button>
            </template>
          </Card>

          <Card title="Generar Diagramas de Diseño">
            <p>Crea diagramas de arquitectura y diseño del sistema para mejor comprensión.</p>
            <template #footer>
              <button @click="generateDesign" class="btn btn-primary" :disabled="loading">
                Generar Diagramas
              </button>
            </template>
          </Card>

          <Card title="Explorar Diseño">
            <p>Navega por los diagramas de arquitectura y diseño del sistema.</p>
            <template #footer>
              <router-link to="/design" class="btn btn-outline-primary">
                Ver Diseño
              </router-link>
            </template>
          </Card>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, onUnmounted } from 'vue'
import { useMainStore } from '../stores/main'
import { Card, LoadingSpinner, ErrorMessage } from '../components'

export default {
  name: 'Dashboard',
  components: {
    Card,
    LoadingSpinner,
    ErrorMessage
  },
  setup() {
    const store = useMainStore()
    
    // Computed properties
    const loading = computed(() => store.loading)
    const error = computed(() => store.error)
    const daemonStatus = computed(() => store.daemonStatus)
    const checksResults = computed(() => store.checksResults)
    const isDaemonRunning = computed(() => store.isDaemonRunning)
    const hasWarnings = computed(() => store.hasWarnings)
    const docCheckStatus = computed(() => store.docCheckStatus)
    const testCheckStatus = computed(() => store.testCheckStatus)
    const gitCheckStatus = computed(() => store.gitCheckStatus)
    const totalChecksRun = computed(() => store.totalChecksRun)
    const lastUpdated = computed(() => store.lastUpdated)
    const autoRefresh = computed(() => store.autoRefresh)

    // Methods
    const refreshData = () => {
      store.fetchSystemStatus()
    }

    const toggleAutoRefresh = () => {
      if (autoRefresh.value) {
        store.stopAutoRefresh()
      } else {
        store.startAutoRefresh(30000) // 30 segundos
      }
    }

    const clearError = () => {
      store.clearError()
    }

    const runDocCheck = async () => {
      try {
        await store.runCheck('doc')
      } catch (error) {
        console.error('Error running doc check:', error)
      }
    }

    const runTestCheck = async () => {
      try {
        await store.runCheck('test')
      } catch (error) {
        console.error('Error running test check:', error)
      }
    }

    const runGitCheck = async () => {
      try {
        await store.runCheck('git')
      } catch (error) {
        console.error('Error running git check:', error)
      }
    }

    const generateDocs = async () => {
      try {
        await store.generateDocs()
        // Mostrar notificación de éxito (se podría agregar un sistema de notificaciones)
        alert('Documentación generada exitosamente')
      } catch (error) {
        console.error('Error generating docs:', error)
      }
    }

    const generateDesign = async () => {
      try {
        await store.generateDesign()
        alert('Diagramas de diseño generados exitosamente')
      } catch (error) {
        console.error('Error generating design:', error)
      }
    }

    const getCheckVariant = (status) => {
      switch (status) {
        case 'success': return 'success'
        case 'warning': return 'warning'
        case 'error': return 'danger'
        default: return 'default'
      }
    }

    const formatTime = (isoString) => {
      if (!isoString) return 'N/A'
      try {
        return new Date(isoString).toLocaleString()
      } catch {
        return 'Formato inválido'
      }
    }

    // Lifecycle
    onMounted(() => {
      store.fetchSystemStatus()
    })

    onUnmounted(() => {
      store.stopAutoRefresh()
    })

    return {
      // State
      loading,
      error,
      daemonStatus,
      checksResults,
      isDaemonRunning,
      hasWarnings,
      docCheckStatus,
      testCheckStatus,
      gitCheckStatus,
      totalChecksRun,
      lastUpdated,
      autoRefresh,
      
      // Methods
      refreshData,
      toggleAutoRefresh,
      clearError,
      runDocCheck,
      runTestCheck,
      runGitCheck,
      generateDocs,
      generateDesign,
      getCheckVariant,
      formatTime
    }
  }
}
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e1e5e9;
}

.dashboard-header h1 {
  color: #2c3e50;
  margin: 0;
}

.dashboard-actions {
  display: flex;
  gap: 10px;
}

.overview-grid,
.checks-grid,
.actions-grid {
  display: grid;
  gap: 20px;
  margin-bottom: 30px;
}

.overview-grid {
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
}

.checks-grid {
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
}

.actions-grid {
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

.status-content {
  text-align: center;
}

.status-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 10px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}

.status-indicator.running .status-dot {
  background-color: #28a745;
  animation: pulse 2s infinite;
}

.status-indicator.stopped .status-dot {
  background-color: #dc3545;
}

.status-detail {
  font-size: 0.9rem;
  color: #6c757d;
  margin-bottom: 5px;
}

.checks-summary {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.check-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.check-item:last-child {
  border-bottom: none;
}

.check-label {
  font-weight: 500;
}

.check-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
}

.check-status--success {
  background-color: #d4edda;
  color: #155724;
}

.check-status--warning {
  background-color: #fff3cd;
  color: #856404;
}

.check-status--error {
  background-color: #f8d7da;
  color: #721c24;
}

.check-status--unknown {
  background-color: #e2e3e5;
  color: #6c757d;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 2rem;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9rem;
  color: #6c757d;
}

.checks-detail,
.quick-actions {
  margin-bottom: 40px;
}

.checks-detail h2,
.quick-actions h2 {
  color: #2c3e50;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e1e5e9;
}

.check-details {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.check-metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
}

.metric-label {
  font-weight: 500;
  color: #495057;
}

.metric-value {
  font-weight: 600;
  color: #2c3e50;
}

.text-success {
  color: #28a745 !important;
}

.text-danger {
  color: #dc3545 !important;
}

.check-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* Buttons */
.btn {
  padding: 8px 16px;
  border: 1px solid;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-block;
  text-align: center;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #007bff;
  border-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
  border-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  border-color: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #545b62;
  border-color: #545b62;
}

.btn-success {
  background-color: #28a745;
  border-color: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background-color: #1e7e34;
  border-color: #1e7e34;
}

.btn-outline-primary {
  background-color: transparent;
  border-color: #007bff;
  color: #007bff;
}

.btn-outline-primary:hover:not(:disabled) {
  background-color: #007bff;
  color: white;
}

.btn-outline-secondary {
  background-color: transparent;
  border-color: #6c757d;
  color: #6c757d;
}

.btn-outline-secondary:hover:not(:disabled) {
  background-color: #6c757d;
  color: white;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 0.8rem;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .overview-grid,
  .checks-grid,
  .actions-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .check-actions {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
}
</style>
```

### 4. Implementar Vista Design
```vue
<!-- src/views/Design.vue -->
<template>
  <div class="design">
    <!-- Header Section -->
    <div class="design-header">
      <h1>Diseño y Arquitectura</h1>
      <div class="design-actions">
        <button 
          @click="generateDesignDiagrams" 
          :disabled="loading"
          class="btn btn-primary"
        >
          <span v-if="designGenerationStatus === 'generating'">Generando...</span>
          <span v-else>Generar Diagramas</span>
        </button>
        
        <button 
          @click="refreshDesignFiles" 
          :disabled="loading"
          class="btn btn-secondary"
        >
          Actualizar Lista
        </button>
      </div>
    </div>

    <!-- Error Display -->
    <ErrorMessage 
      v-if="error" 
      :message="error"
      dismissible
      @dismiss="clearError"
    />

    <!-- Generation Status -->
    <Card 
      v-if="designGenerationStatus === 'generating'" 
      variant="primary"
      title="Generando Diagramas"
    >
      <LoadingSpinner message="Analizando código y generando diagramas de arquitectura..." />
    </Card>

    <!-- Success Message -->
    <Card 
      v-if="designGenerationStatus === 'success'" 
      variant="success"
      title="Generación Completada"
    >
      <p>Los diagramas de diseño se han generado exitosamente.</p>
      <p><strong>Archivos creados:</strong> {{ designFiles.length }}</p>
    </Card>

    <!-- Main Content -->
    <div class="design-content">
      
      <!-- Design Files Explorer -->
      <section class="design-explorer">
        <div class="explorer-layout">
          
          <!-- File List Sidebar -->
          <div class="file-list">
            <Card title="Archivos de Diseño">
              <div v-if="designFiles.length === 0" class="no-files">
                <p>No hay archivos de diseño disponibles.</p>
                <p>Haz clic en "Generar Diagramas" para crear nuevos diagramas.</p>
              </div>
              
              <div v-else class="files-tree">
                <div 
                  v-for="file in designFiles" 
                  :key="file"
                  class="file-item"
                  :class="{ active: currentDesignFile === file }"
                  @click="selectDesignFile(file)"
                >
                  <span class="file-icon">📄</span>
                  <span class="file-name">{{ getFileName(file) }}</span>
                </div>
              </div>
            </Card>
          </div>

          <!-- Content Viewer -->
          <div class="content-viewer">
            <Card 
              v-if="!currentDesignFile" 
              title="Selecciona un Archivo"
            >
              <div class="no-selection">
                <p>Selecciona un archivo de diseño de la lista para visualizarlo.</p>
              </div>
            </Card>

            <Card 
              v-else
              :title="getFileName(currentDesignFile)"
            >
              <LoadingSpinner 
                v-if="loadingFile" 
                message="Cargando archivo de diseño..."
              />
              
              <div v-else-if="fileContent" class="file-content">
                <!-- Render markdown content -->
                <MarkdownRenderer :content="fileContent" />
                
                <!-- Extract and render mermaid diagrams if any -->
                <div v-if="extractedDiagrams.length > 0" class="diagrams-section">
                  <h3>Diagramas</h3>
                  <div 
                    v-for="(diagram, index) in extractedDiagrams" 
                    :key="index"
                    class="diagram-container"
                  >
                    <h4>{{ diagram.title || `Diagrama ${index + 1}` }}</h4>
                    <DiagramRenderer :code="diagram.code" />
                  </div>
                </div>
              </div>
              
              <div v-else class="error-content">
                <p>No se pudo cargar el contenido del archivo.</p>
              </div>
            </Card>
          </div>
        </div>
      </section>

      <!-- Design Overview -->
      <section class="design-overview">
        <h2>Resumen de Arquitectura</h2>
        <div class="overview-grid">
          
          <Card title="Módulos Analizados">
            <div class="overview-stats">
              <div class="stat-item">
                <span class="stat-number">{{ designStats.modulesCount }}</span>
                <span class="stat-label">Módulos identificados</span>
              </div>
            </div>
          </Card>

          <Card title="Diagramas Generados">
            <div class="overview-stats">
              <div class="stat-item">
                <span class="stat-number">{{ designStats.diagramsCount }}</span>
                <span class="stat-label">Diagramas creados</span>
              </div>
            </div>
          </Card>

          <Card title="Última Generación">
            <div class="overview-stats">
              <div class="stat-item">
                <span class="stat-date">{{ designStats.lastGenerated }}</span>
                <span class="stat-label">Fecha de generación</span>
              </div>
            </div>
          </Card>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, ref, watch } from 'vue'
import { useMainStore } from '../stores/main'
import { Card, LoadingSpinner, ErrorMessage, MarkdownRenderer, DiagramRenderer } from '../components'

export default {
  name: 'Design',
  components: {
    Card,
    LoadingSpinner,
    ErrorMessage,
    MarkdownRenderer,
    DiagramRenderer
  },
  setup() {
    const store = useMainStore()
    const loadingFile = ref(false)
    const fileContent = ref('')
    const extractedDiagrams = ref([])
    
    // Computed properties
    const loading = computed(() => store.loading)
    const error = computed(() => store.error)
    const designFiles = computed(() => store.designFiles)
    const currentDesignFile = computed({
      get: () => store.currentDesignFile,
      set: (value) => { store.currentDesignFile = value }
    })
    const designGenerationStatus = computed(() => store.designGenerationStatus)

    // Design statistics
    const designStats = computed(() => {
      return {
        modulesCount: designFiles.value.length,
        diagramsCount: extractedDiagrams.value.length,
        lastGenerated: store.lastUpdated ? 
          new Date(store.lastUpdated).toLocaleString() : 
          'No disponible'
      }
    })

    // Methods
    const generateDesignDiagrams = async () => {
      try {
        await store.generateDesign()
        // Auto-refresh files list after generation
        await refreshDesignFiles()
      } catch (error) {
        console.error('Error generating design:', error)
      }
    }

    const refreshDesignFiles = async () => {
      try {
        // Fetch updated list from backend
        await store.fetchSystemStatus()
      } catch (error) {
        console.error('Error refreshing files:', error)
      }
    }

    const selectDesignFile = async (file) => {
      if (currentDesignFile.value === file) return
      
      currentDesignFile.value = file
      await loadDesignFile(file)
    }

    const loadDesignFile = async (file) => {
      if (!file) return
      
      loadingFile.value = true
      fileContent.value = ''
      extractedDiagrams.value = []
      
      try {
        const content = await store.fetchDesignFile(file)
        fileContent.value = content
        
        // Extract mermaid diagrams from markdown
        extractDiagrams(content)
      } catch (error) {
        console.error('Error loading design file:', error)
      } finally {
        loadingFile.value = false
      }
    }

    const extractDiagrams = (content) => {
      const diagrams = []
      const mermaidRegex = /```mermaid\n([\s\S]*?)\n```/g
      let match
      
      while ((match = mermaidRegex.exec(content)) !== null) {
        diagrams.push({
          code: match[1].trim(),
          title: `Diagrama ${diagrams.length + 1}`
        })
      }
      
      extractedDiagrams.value = diagrams
    }

    const getFileName = (filePath) => {
      if (!filePath) return ''
      return filePath.split('/').pop().replace('.md', '')
    }

    const clearError = () => {
      store.clearError()
    }

    // Watch for design files changes
    watch(designFiles, (newFiles) => {
      if (newFiles.length > 0 && !currentDesignFile.value) {
        // Auto-select first file
        selectDesignFile(newFiles[0])
      }
    })

    // Lifecycle
    onMounted(async () => {
      await store.fetchSystemStatus()
      
      // If there are design files, load the first one
      if (designFiles.value.length > 0) {
        selectDesignFile(designFiles.value[0])
      }
    })

    return {
      // State
      loading,
      error,
      loadingFile,
      fileContent,
      extractedDiagrams,
      designFiles,
      currentDesignFile,
      designGenerationStatus,
      designStats,
      
      // Methods
      generateDesignDiagrams,
      refreshDesignFiles,
      selectDesignFile,
      getFileName,
      clearError
    }
  }
}
</script>

<style scoped>
.design {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.design-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e1e5e9;
}

.design-header h1 {
  color: #2c3e50;
  margin: 0;
}

.design-actions {
  display: flex;
  gap: 10px;
}

.explorer-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.file-list {
  height: fit-content;
}

.no-files {
  text-align: center;
  padding: 20px;
  color: #6c757d;
}

.files-tree {
  max-height: 600px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.file-item:hover {
  background-color: #f8f9fa;
}

.file-item.active {
  background-color: #007bff;
  color: white;
}

.file-icon {
  font-size: 16px;
}

.file-name {
  font-size: 0.9rem;
  font-weight: 500;
}

.content-viewer {
  min-height: 600px;
}

.no-selection {
  text-align: center;
  padding: 40px;
  color: #6c757d;
}

.file-content {
  max-height: 800px;
  overflow-y: auto;
}

.diagrams-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 2px solid #e1e5e9;
}

.diagrams-section h3 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.diagram-container {
  margin-bottom: 30px;
}

.diagram-container h4 {
  color: #495057;
  margin-bottom: 15px;
  font-size: 1.1rem;
}

.design-overview {
  margin-top: 40px;
}

.design-overview h2 {
  color: #2c3e50;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e1e5e9;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.overview-stats {
  text-align: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-number {
  font-size: 2rem;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 5px;
}

.stat-date {
  font-size: 1rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9rem;
  color: #6c757d;
}

.error-content {
  text-align: center;
  padding: 40px;
  color: #dc3545;
}

/* Buttons */
.btn {
  padding: 8px 16px;
  border: 1px solid;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-block;
  text-align: center;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #007bff;
  border-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
  border-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  border-color: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #545b62;
  border-color: #545b62;
}

/* Responsive */
@media (max-width: 768px) {
  .design-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .explorer-layout {
    grid-template-columns: 1fr;
  }
  
  .overview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
```

### 5. Implementar Vista Docs
```vue
<!-- src/views/Docs.vue -->
<template>
  <div class="docs">
    <!-- Header Section -->
    <div class="docs-header">
      <h1>Documentación</h1>
      <div class="docs-actions">
        <button 
          @click="generateDocumentation" 
          :disabled="loading"
          class="btn btn-primary"
        >
          <span v-if="docsGenerationStatus === 'generating'">Generando...</span>
          <span v-else>Generar Documentación</span>
        </button>
        
        <button 
          @click="refreshDocsIndex" 
          :disabled="loading"
          class="btn btn-secondary"
        >
          Actualizar Índice
        </button>
      </div>
    </div>

    <!-- Error Display -->
    <ErrorMessage 
      v-if="error" 
      :message="error"
      dismissible
      @dismiss="clearError"
    />

    <!-- Generation Status -->
    <Card 
      v-if="docsGenerationStatus === 'generating'" 
      variant="primary"
      title="Generando Documentación"
    >
      <LoadingSpinner message="Analizando código fuente y generando documentación..." />
    </Card>

    <!-- Success Message -->
    <Card 
      v-if="docsGenerationStatus === 'success'" 
      variant="success"
      title="Documentación Generada"
    >
      <p>La documentación se ha generado exitosamente.</p>
      <div v-if="docsStatus">
        <p><strong>Archivos procesados:</strong> {{ docsStatus.files_processed || 0 }}</p>
        <p><strong>Documentos creados:</strong> {{ docsStatus.docs_created || 0 }}</p>
      </div>
    </Card>

    <!-- Main Content -->
    <div class="docs-content">
      
      <!-- Documentation Index -->
      <section class="docs-index">
        <h2>Índice de Documentación</h2>
        
        <LoadingSpinner 
          v-if="loading && !docsIndex" 
          message="Cargando índice de documentación..."
        />
        
        <Card v-else-if="!docsIndex" title="Sin Documentación">
          <div class="no-docs">
            <p>No se encontró documentación disponible.</p>
            <p>Haz clic en "Generar Documentación" para crear la documentación del proyecto.</p>
          </div>
        </Card>

        <div v-else class="docs-tree">
          <!-- Documentation Statistics -->
          <div class="docs-stats">
            <div class="stats-grid">
              <Card variant="primary" title="Estadísticas">
                <div class="stat-item">
                  <span class="stat-number">{{ docsIndex.documentation_stats?.total_files || 0 }}</span>
                  <span class="stat-label">Archivos documentados</span>
                </div>
              </Card>

              <Card variant="success" title="Módulos">
                <div class="stat-item">
                  <span class="stat-number">{{ docsIndex.documentation_stats?.total_modules || 0 }}</span>
                  <span class="stat-label">Módulos identificados</span>
                </div>
              </Card>

              <Card variant="default" title="Directorios">
                <div class="stat-item">
                  <span class="stat-number">{{ docsIndex.documentation_stats?.total_directories || 0 }}</span>
                  <span class="stat-label">Directorios analizados</span>
                </div>
              </Card>
            </div>
          </div>

          <!-- Documentation Tree Structure -->
          <Card title="Estructura de Documentación">
            <div class="tree-structure">
              <div 
                v-for="(module, path) in docsIndex.structure" 
                :key="path"
                class="module-item"
              >
                <div class="module-header" @click="toggleModule(path)">
                  <span class="toggle-icon" :class="{ expanded: expandedModules[path] }">▶</span>
                  <span class="module-icon">📁</span>
                  <span class="module-name">{{ getModuleName(path) }}</span>
                  <span class="module-type">{{ module.type }}</span>
                </div>
                
                <div v-if="expandedModules[path]" class="module-content">
                  <div v-if="module.purpose" class="module-purpose">
                    <strong>Propósito:</strong> {{ module.purpose }}
                  </div>
                  
                  <!-- Module files -->
                  <div v-if="module.files" class="module-files">
                    <h4>Archivos:</h4>
                    <div 
                      v-for="(file, filePath) in module.files" 
                      :key="filePath"
                      class="file-item"
                      @click="loadDocFile(filePath)"
                    >
                      <span class="file-icon">📄</span>
                      <span class="file-name">{{ getFileName(filePath) }}</span>
                    </div>
                  </div>

                  <!-- Subdirectories -->
                  <div v-if="module.subdirectories" class="subdirectories">
                    <h4>Subdirectorios:</h4>
                    <div 
                      v-for="(submodule, subPath) in module.subdirectories" 
                      :key="subPath"
                      class="submodule-item"
                    >
                      <span class="submodule-icon">📁</span>
                      <span class="submodule-name">{{ getModuleName(subPath) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </section>

      <!-- Document Viewer -->
      <section class="doc-viewer" v-if="selectedDocFile">
        <Card :title="`Documentación: ${getFileName(selectedDocFile)}`">
          <LoadingSpinner 
            v-if="loadingDoc" 
            message="Cargando documento..."
          />
          
          <div v-else-if="docContent" class="doc-content">
            <MarkdownRenderer :content="docContent" />
          </div>
          
          <div v-else class="error-doc">
            <p>No se pudo cargar el contenido del documento.</p>
          </div>
        </Card>
      </section>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, ref, reactive } from 'vue'
import { useMainStore } from '../stores/main'
import { Card, LoadingSpinner, ErrorMessage, MarkdownRenderer } from '../components'

export default {
  name: 'Docs',
  components: {
    Card,
    LoadingSpinner,
    ErrorMessage,
    MarkdownRenderer
  },
  setup() {
    const store = useMainStore()
    const loadingDoc = ref(false)
    const docContent = ref('')
    const selectedDocFile = ref('')
    const expandedModules = reactive({})
    
    // Computed properties
    const loading = computed(() => store.loading)
    const error = computed(() => store.error)
    const docsIndex = computed(() => store.docsIndex)
    const docsStatus = computed(() => store.docsStatus)
    const docsGenerationStatus = computed(() => store.docsGenerationStatus)

    // Methods
    const generateDocumentation = async () => {
      try {
        await store.generateDocs()
        // Refresh index after generation
        await refreshDocsIndex()
      } catch (error) {
        console.error('Error generating documentation:', error)
      }
    }

    const refreshDocsIndex = async () => {
      try {
        await store.fetchDocsIndex()
      } catch (error) {
        console.error('Error refreshing docs index:', error)
      }
    }

    const toggleModule = (path) => {
      expandedModules[path] = !expandedModules[path]
    }

    const loadDocFile = async (filePath) => {
      if (selectedDocFile.value === filePath) return
      
      selectedDocFile.value = filePath
      loadingDoc.value = true
      docContent.value = ''
      
      try {
        // Construct full path for documentation file
        const fullPath = filePath.replace('docs\\', '').replace(/\\/g, '/')
        const response = await fetch(`/docs/${fullPath}`)
        
        if (response.ok) {
          docContent.value = await response.text()
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
      } catch (error) {
        console.error('Error loading doc file:', error)
        store.error = `Error cargando archivo: ${error.message}`
      } finally {
        loadingDoc.value = false
      }
    }

    const getModuleName = (path) => {
      if (!path) return ''
      return path.split('\\').pop().split('/').pop()
    }

    const getFileName = (filePath) => {
      if (!filePath) return ''
      return filePath.split('\\').pop().split('/').pop().replace('.md', '')
    }

    const clearError = () => {
      store.clearError()
    }

    // Lifecycle
    onMounted(async () => {
      await store.fetchSystemStatus()
      await refreshDocsIndex()
    })

    return {
      // State
      loading,
      error,
      loadingDoc,
      docContent,
      selectedDocFile,
      expandedModules,
      docsIndex,
      docsStatus,
      docsGenerationStatus,
      
      // Methods
      generateDocumentation,
      refreshDocsIndex,
      toggleModule,
      loadDocFile,
      getModuleName,
      getFileName,
      clearError
    }
  }
}
</script>

<style scoped>
.docs {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.docs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e1e5e9;
}

.docs-header h1 {
  color: #2c3e50;
  margin: 0;
}

.docs-actions {
  display: flex;
  gap: 10px;
}

.no-docs {
  text-align: center;
  padding: 40px;
  color: #6c757d;
}

.docs-stats {
  margin-bottom: 30px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 2rem;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9rem;
  color: #6c757d;
}

.tree-structure {
  max-height: 600px;
  overflow-y: auto;
}

.module-item {
  margin-bottom: 10px;
  border: 1px solid #e1e5e9;
  border-radius: 4px;
}

.module-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  cursor: pointer;
  background-color: #f8f9fa;
  border-radius: 4px 4px 0 0;
  transition: background-color 0.3s;
}

.module-header:hover {
  background-color: #e9ecef;
}

.toggle-icon {
  font-size: 12px;
  transition: transform 0.3s;
}

.toggle-icon.expanded {
  transform: rotate(90deg);
}

.module-icon {
  font-size: 16px;
}

.module-name {
  font-weight: 600;
  color: #2c3e50;
  flex: 1;
}

.module-type {
  background-color: #007bff;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.module-content {
  padding: 15px;
  background-color: white;
}

.module-purpose {
  margin-bottom: 15px;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
  font-size: 0.9rem;
  line-height: 1.4;
}

.module-files h4,
.subdirectories h4 {
  color: #495057;
  margin-bottom: 10px;
  font-size: 1rem;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.3s;
  margin-bottom: 5px;
}

.file-item:hover {
  background-color: #e3f2fd;
}

.file-icon {
  font-size: 14px;
}

.file-name {
  font-size: 0.9rem;
  color: #007bff;
  font-weight: 500;
}

.submodule-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  margin-bottom: 5px;
}

.submodule-icon {
  font-size: 14px;
}

.submodule-name {
  font-size: 0.9rem;
  color: #6c757d;
}

.doc-viewer {
  margin-top: 30px;
}

.doc-content {
  max-height: 600px;
  overflow-y: auto;
}

.error-doc {
  text-align: center;
  padding: 40px;
  color: #dc3545;
}

/* Buttons */
.btn {
  padding: 8px 16px;
  border: 1px solid;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-block;
  text-align: center;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #007bff;
  border-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
  border-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  border-color: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #545b62;
  border-color: #545b62;
}

/* Responsive */
@media (max-width: 768px) {
  .docs-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
```

### 6. Implementar Vista Config (Básica)
```vue
<!-- src/views/Config.vue -->
<template>
  <div class="config">
    <!-- Header Section -->
    <div class="config-header">
      <h1>Configuración del Sistema</h1>
      <div class="config-actions">
        <button 
          @click="loadConfiguration" 
          :disabled="loading"
          class="btn btn-primary"
        >
          <span v-if="loading">Cargando...</span>
          <span v-else>Cargar Configuración</span>
        </button>
      </div>
    </div>

    <!-- Error Display -->
    <ErrorMessage 
      v-if="error" 
      :message="error"
      dismissible
      @dismiss="clearError"
    />

    <!-- Loading State -->
    <LoadingSpinner 
      v-if="loading && !systemConfig" 
      message="Cargando configuración del sistema..."
    />

    <!-- Configuration Display -->
    <div v-else-if="systemConfig" class="config-content">
      <Card title="Configuración Actual">
        <div class="config-display">
          <pre>{{ JSON.stringify(systemConfig, null, 2) }}</pre>
        </div>
      </Card>
    </div>

    <!-- No Configuration -->
    <Card v-else title="Sin Configuración">
      <div class="no-config">
        <p>No se ha cargado ninguna configuración.</p>
        <p>Haz clic en "Cargar Configuración" para obtener la configuración actual del sistema.</p>
      </div>
    </Card>
  </div>
</template>

<script>
import { computed, onMounted } from 'vue'
import { useMainStore } from '../stores/main'
import { Card, LoadingSpinner, ErrorMessage } from '../components'

export default {
  name: 'Config',
  components: {
    Card,
    LoadingSpinner,
    ErrorMessage
  },
  setup() {
    const store = useMainStore()
    
    // Computed properties
    const loading = computed(() => store.loading)
    const error = computed(() => store.error)
    const systemConfig = computed(() => store.systemConfig)

    // Methods
    const loadConfiguration = async () => {
      try {
        await store.loadConfig()
      } catch (error) {
        console.error('Error loading config:', error)
      }
    }

    const clearError = () => {
      store.clearError()
    }

    // Lifecycle
    onMounted(() => {
      store.fetchSystemStatus()
    })

    return {
      // State
      loading,
      error,
      systemConfig,
      
      // Methods
      loadConfiguration,
      clearError
    }
  }
}
</script>

<style scoped>
.config {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e1e5e9;
}

.config-header h1 {
  color: #2c3e50;
  margin: 0;
}

.config-actions {
  display: flex;
  gap: 10px;
}

.config-display {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 4px;
  overflow-x: auto;
}

.config-display pre {
  margin: 0;
  color: #2c3e50;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  line-height: 1.4;
}

.no-config {
  text-align: center;
  padding: 40px;
  color: #6c757d;
}

/* Buttons */
.btn {
  padding: 8px 16px;
  border: 1px solid;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #007bff;
  border-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
  border-color: #0056b3;
}

/* Responsive */
@media (max-width: 768px) {
  .config-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
}
</style>
```

## Criterios de Verificación

### 1. Verificación del Router
```bash
# Ejecutar servidor de desarrollo
cd autocode/web_modern/
npm run dev

# Navegar entre rutas:
# http://localhost:5173/ (Dashboard)
# http://localhost:5173/design (Design)
# http://localhost:5173/docs (Docs)
# http://localhost:5173/config (Config)

# Verificar que:
# - No hay errores de consola
# - Las rutas cambian correctamente
# - Los títulos de página se actualizan
# - Los componentes se cargan sin errores
```

### 2. Verificación de la API Integration
```bash
# Asegurar que el backend esté ejecutándose
cd autocode/
uv run autocode daemon

# En el frontend, verificar en DevTools > Network:
# - Llamadas a /api/status se ejecutan correctamente
# - Responses tienen la estructura esperada
# - Errores de red se manejan apropiadamente
```

### 3. Verificación del Store
```javascript
// En Vue DevTools, verificar que:
// - Pinia store se inicializa correctamente
// - Actions se ejecutan y actualizan el state
// - Getters devuelven valores correctos
// - Estado es reactivo en las vistas
```

### 4. Verificaciones Funcionales por Vista

**Dashboard:**
- Estado del daemon se muestra correctamente
- Cards muestran información de checks
- Botones ejecutan acciones (generar docs, design)
- Auto-refresh funciona
- Navegación a otras vistas funciona

**Design:**
- Botón "Generar Diagramas" funciona
- Lista de archivos se carga y muestra
- Selección de archivos carga contenido
- Diagramas Mermaid se renderizan
- Markdown se procesa correctamente

**Docs:**
- Botón "Generar Documentación" funciona
- Índice de documentación se carga
- Árbol de módulos es interactivo
- Archivos de documentación se cargan
- Contenido Markdown se renderiza

**Config:**
- Configuración se carga y muestra
- JSON se formatea correctamente
- Estado de loading se maneja

### 5. Verificación de Responsividad
```css
/* Probar en diferentes tamaños de pantalla: */
/* - Desktop (>1200px) */
/* - Tablet (768px-1200px) */  
/* - Mobile (<768px) */

/* Verificar que: */
/* - Grids se adaptan correctamente */
/* - Navegación funciona en móvil */
/* - Contenido es legible */
/* - Botones son accesibles */
```

### 6. Verificación de Estados de Error
```javascript
// Simular errores para verificar manejo:
// 1. Desconectar backend
// 2. Verificar que ErrorMessage se muestra
// 3. Verificar que LoadingSpinner funciona
// 4. Probar dismiss de errores
```

### 7. Verificación de Performance
```bash
# En DevTools > Performance:
# - Tiempo de carga inicial <3s
# - Navegación entre rutas <500ms
# - API calls con loading states apropiados
# - No memory leaks en navegación
```

## Estructura Final de Archivos
```
autocode/web_modern/src/
├── router/
│   └── index.js                 # Router completo con guards
├── stores/
│   └── main.js                  # Store con todas las acciones
├── views/
│   ├── Dashboard.vue           # Vista principal completa
│   ├── Design.vue              # Vista de diagramas completa
│   ├── Docs.vue                # Vista de documentación completa
│   └── Config.vue              # Vista de configuración básica
└── components/                 # Componentes base (disponibles)
```

## Template de Commit Message
```
feat(ui): implement complete router and views with API integration

- Configured Vue Router with meta fields and navigation guards
- Expanded Pinia store with comprehensive actions for all API endpoints
- Implemented Dashboard view with real-time monitoring and auto-refresh
- Created Design view with file explorer and diagram rendering
- Built Docs view with documentation tree and markdown viewer
- Added Config view for system configuration display
- Integrated all components with API endpoints using Axios
- Added proper error handling and loading states
- Implemented responsive design for all views
- Added navigation between views and proper state management
- All views consume API data reactively through Pinia store
- Error states and loading indicators provide good UX
- Auto-refresh functionality for real-time updates
```
