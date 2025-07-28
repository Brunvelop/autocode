# Task 008: Implementar Polling Automático y Funcionalidad de Regeneración

## Contexto del Proyecto
Este proyecto autocode es una herramienta de desarrollo que automatiza verificaciones de código, documentación y tests. El sistema incluye un daemon de fondo que ejecuta verificaciones periódicas, un backend FastAPI que expone una API robusta, y un frontend Vue.js moderno que consume esta API para mostrar el estado del sistema en tiempo real.

## Estado Actual del Sistema

### Backend FastAPI (Puerto 8080)
El sistema cuenta con un backend FastAPI completo que expone los siguientes endpoints relevantes:

```python
# Endpoints de generación (procesamiento en background)
POST /api/generate-docs       # Generar documentación
POST /api/generate-design     # Generar diagramas de diseño

# Endpoints de estado y datos
GET  /api/status              # Estado general del daemon y checks
GET  /api/checks              # Resultados de todos los checks
GET  /api/daemon/status       # Estado específico del daemon

# Endpoints de archivos generados
GET  /design/{file_path}      # Servir archivos de diseño
GET  /docs/{file_path}        # Servir archivos de documentación
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

// POST /api/generate-design (Background Task)
{
  "status": "success",
  "message": "Design generation started in background",
  "task_id": "gen_design_1234567890",
  "files_generated": [
    "design/autocode/_index.md",
    "design/autocode/core/_module.md"
  ],
  "diagrams_created": 12
}

// POST /api/generate-docs (Background Task)
{
  "status": "success",
  "message": "Documentation generation started in background", 
  "task_id": "gen_docs_1234567890",
  "files_processed": 25,
  "docs_created": 18
}
```

### Frontend Vue.js Actual
El proyecto Vue.js está ubicado en `autocode/web_modern/` con la siguiente estructura:

```
autocode/web_modern/
├── package.json
├── vite.config.js              # Proxy configurado hacia localhost:8080
├── index.html
├── src/
│   ├── App.vue
│   ├── main.js
│   ├── router/
│   │   └── index.js            # Vue Router configurado
│   ├── stores/
│   │   └── main.js             # Pinia store principal
│   ├── views/
│   │   ├── Dashboard.vue       # Vista principal con estado del sistema
│   │   ├── Design.vue          # Vista de diagramas de diseño
│   │   ├── Docs.vue            # Vista de documentación
│   │   └── Config.vue          # Vista de configuración
│   └── components/
│       ├── Card.vue            # Contenedor con variants
│       ├── MarkdownRenderer.vue # Renderizado de Markdown
│       ├── DiagramRenderer.vue  # Renderizado de diagramas Mermaid
│       ├── LoadingSpinner.vue   # Indicador de carga
│       ├── ErrorMessage.vue     # Componente de error
│       └── index.js            # Exportación de componentes
```

### Store de Pinia Actual
```javascript
// src/stores/main.js (estructura actual básica)
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
    lastUpdated: null
  }),

  actions: {
    async fetchSystemStatus() {
      // Lógica básica de fetch
    },
    
    async generateDocs() {
      // Generación básica de documentación
    },
    
    async generateDesign() {
      // Generación básica de diseño  
    }
  }
})
```

### Configuración de Vite
```javascript
// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': 'http://localhost:8080',
      '/design': 'http://localhost:8080',
      '/docs': 'http://localhost:8080'
    }
  }
})
```

## Objetivos de Esta Tarea

Esta tarea implementa un sistema de polling automático y funcionalidad de regeneración para mantener la interfaz actualizada en tiempo real y permitir la regeneración manual de contenido. Los objetivos específicos son:

1. **Polling Automático**: Implementar actualizaciones periódicas automáticas cada 30 segundos
2. **Regeneración Manual**: Añadir botones para regenerar contenido bajo demanda
3. **Background Task Management**: Manejar tareas de larga duración en el backend
4. **Estado de Loading**: Mostrar indicadores de progreso durante operaciones
5. **Gestión de Memoria**: Prevenir memory leaks con limpieza adecuada de intervalos

## Instrucciones Paso a Paso

### 1. Expandir el Store de Pinia con Polling
```javascript
// src/stores/main.js - Versión expandida con polling
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
    
    // Polling state
    pollingIntervals: {
      status: null,
      design: null,
      docs: null
    },
    pollingEnabled: {
      status: false,
      design: false,
      docs: false
    },
    pollingConfig: {
      statusInterval: 30000,  // 30 segundos
      designInterval: 45000,  // 45 segundos
      docsInterval: 45000     // 45 segundos
    },
    
    // Background task tracking
    backgroundTasks: {
      generateDesign: {
        running: false,
        taskId: null,
        startTime: null,
        progress: null
      },
      generateDocs: {
        running: false,
        taskId: null,
        startTime: null,
        progress: null
      }
    }
  }),

  getters: {
    isDaemonRunning: (state) => state.daemonStatus?.running || false,
    hasErrors: (state) => state.error !== null,
    
    // Polling status getters
    isPollingActive: (state) => (type) => state.pollingEnabled[type] || false,
    getPollingInterval: (state) => (type) => state.pollingConfig[`${type}Interval`] || 30000,
    
    // Background task getters
    isGenerationRunning: (state) => (type) => state.backgroundTasks[type]?.running || false,
    getTaskProgress: (state) => (type) => state.backgroundTasks[type]?.progress,
    
    // Check status getters
    docCheckStatus: (state) => state.checksResults?.doc?.status || 'unknown',
    testCheckStatus: (state) => state.checksResults?.test?.status || 'unknown',
    gitCheckStatus: (state) => state.checksResults?.git?.status || 'unknown'
  },

  actions: {
    // Sistema general
    async fetchSystemStatus() {
      try {
        const response = await axios.get('/api/status')
        this.daemonStatus = response.data.daemon
        this.checksResults = response.data.checks
        this.systemConfig = response.data.config
        this.lastUpdated = new Date().toISOString()
        
        // Clear any errors on successful fetch
        if (this.error) {
          this.error = null
        }
        
        return response.data
      } catch (error) {
        this.error = 'Failed to fetch system status: ' + error.message
        console.error('Error fetching status:', error)
        throw error
      }
    },

    // Polling management
    startPolling(type = 'status') {
      if (this.pollingIntervals[type]) {
        this.stopPolling(type)
      }
      
      const intervalTime = this.getPollingInterval(type)
      const fetchFunction = this.getPollingFunction(type)
      
      this.pollingIntervals[type] = setInterval(async () => {
        try {
          await fetchFunction()
        } catch (error) {
          console.error(`Polling error for ${type}:`, error)
          // Don't stop polling on individual errors, just log them
        }
      }, intervalTime)
      
      this.pollingEnabled[type] = true
      console.log(`Polling started for ${type} (interval: ${intervalTime}ms)`)
    },

    stopPolling(type = 'status') {
      if (this.pollingIntervals[type]) {
        clearInterval(this.pollingIntervals[type])
        this.pollingIntervals[type] = null
        this.pollingEnabled[type] = false
        console.log(`Polling stopped for ${type}`)
      }
    },

    stopAllPolling() {
      Object.keys(this.pollingIntervals).forEach(type => {
        this.stopPolling(type)
      })
    },

    getPollingFunction(type) {
      switch (type) {
        case 'status':
          return this.fetchSystemStatus
        case 'design':
          return this.fetchDesignData
        case 'docs':
          return this.fetchDocsData
        default:
          return this.fetchSystemStatus
      }
    },

    // Design-specific polling and regeneration
    async fetchDesignData() {
      try {
        // Fetch design files list from status endpoint
        const statusResponse = await axios.get('/api/status')
        
        // Update design-related data if available
        if (statusResponse.data.design) {
          this.designFiles = statusResponse.data.design.files || []
          this.designGenerationStatus = statusResponse.data.design.status
        }
        
        // If we have a current design file, refresh its content
        if (this.currentDesignFile) {
          await this.fetchDesignFile(this.currentDesignFile)
        }
        
        return statusResponse.data
      } catch (error) {
        console.error('Error fetching design data:', error)
        throw error
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

    async regenerateDesign() {
      this.backgroundTasks.generateDesign.running = true
      this.backgroundTasks.generateDesign.startTime = new Date().toISOString()
      this.designGenerationStatus = 'generating'
      
      try {
        const response = await axios.post('/api/generate-design')
        
        // Track background task
        if (response.data.task_id) {
          this.backgroundTasks.generateDesign.taskId = response.data.task_id
        }
        
        // Update design files immediately if provided
        if (response.data.files_generated) {
          this.designFiles = response.data.files_generated
        }
        
        this.designGenerationStatus = 'success'
        
        // Force refresh of status to get updated data
        await this.fetchSystemStatus()
        await this.fetchDesignData()
        
        return response.data
      } catch (error) {
        this.designGenerationStatus = 'error'
        this.error = 'Failed to regenerate design: ' + error.message
        throw error
      } finally {
        this.backgroundTasks.generateDesign.running = false
        this.backgroundTasks.generateDesign.taskId = null
      }
    },

    // Docs-specific polling and regeneration
    async fetchDocsData() {
      try {
        // Fetch docs index
        const indexResponse = await axios.get('/api/docs/index')
        this.docsIndex = indexResponse.data
        
        // Fetch status for docs-related info
        const statusResponse = await axios.get('/api/status')
        if (statusResponse.data.docs) {
          this.docsStatus = statusResponse.data.docs
          this.docsGenerationStatus = statusResponse.data.docs.status
        }
        
        return { index: indexResponse.data, status: statusResponse.data }
      } catch (error) {
        console.error('Error fetching docs data:', error)
        // Don't throw for docs polling to avoid interrupting the process
      }
    },

    async regenerateDocumentation() {
      this.backgroundTasks.generateDocs.running = true
      this.backgroundTasks.generateDocs.startTime = new Date().toISOString()
      this.docsGenerationStatus = 'generating'
      
      try {
        const response = await axios.post('/api/generate-docs')
        
        // Track background task
        if (response.data.task_id) {
          this.backgroundTasks.generateDocs.taskId = response.data.task_id
        }
        
        this.docsStatus = response.data
        this.docsGenerationStatus = 'success'
        
        // Force refresh of data
        await this.fetchSystemStatus()
        await this.fetchDocsData()
        
        return response.data
      } catch (error) {
        this.docsGenerationStatus = 'error'
        this.error = 'Failed to regenerate documentation: ' + error.message
        throw error
      } finally {
        this.backgroundTasks.generateDocs.running = false
        this.backgroundTasks.generateDocs.taskId = null
      }
    },

    // Background task monitoring
    async checkBackgroundTask(type, taskId) {
      try {
        const response = await axios.get(`/api/tasks/${taskId}/status`)
        
        if (this.backgroundTasks[type]) {
          this.backgroundTasks[type].progress = response.data.progress
          
          if (response.data.status === 'completed') {
            this.backgroundTasks[type].running = false
            this.backgroundTasks[type].taskId = null
            
            // Refresh data after task completion
            if (type === 'generateDesign') {
              await this.fetchDesignData()
            } else if (type === 'generateDocs') {
              await this.fetchDocsData()
            }
          }
        }
        
        return response.data
      } catch (error) {
        console.error(`Error checking background task ${taskId}:`, error)
      }
    },

    // Utilidades
    clearError() {
      this.error = null
    },

    resetPollingState() {
      this.stopAllPolling()
      this.pollingEnabled = {
        status: false,
        design: false,
        docs: false
      }
    },

    // Configuration
    updatePollingInterval(type, interval) {
      this.pollingConfig[`${type}Interval`] = interval
      
      // Restart polling if it's currently active
      if (this.pollingEnabled[type]) {
        this.stopPolling(type)
        this.startPolling(type)
      }
    }
  }
})
```

### 2. Actualizar Vista Design con Polling
```vue
<!-- src/views/Design.vue - Con polling y regeneración -->
<template>
  <div class="design">
    <!-- Header Section -->
    <div class="design-header">
      <h1>Diseño y Arquitectura</h1>
      <div class="design-actions">
        <button 
          @click="regenerateDesign" 
          :disabled="isRegenerating || loading"
          class="btn btn-primary"
        >
          <LoadingSpinner 
            v-if="isRegenerating" 
            size="small" 
            inline 
          />
          <span v-if="isRegenerating">Regenerando...</span>
          <span v-else>Regenerar Diagramas</span>
        </button>
        
        <button 
          @click="togglePolling" 
          :class="['btn', isPollingActive ? 'btn-success' : 'btn-outline-secondary']"
        >
          {{ isPollingActive ? 'Auto-actualización ON' : 'Auto-actualización OFF' }}
        </button>
        
        <button 
          @click="refreshDesignData" 
          :disabled="loading"
          class="btn btn-secondary"
        >
          Actualizar
        </button>
      </div>
    </div>

    <!-- Status Display -->
    <div class="status-bar">
      <div class="status-item">
        <span class="status-label">Estado de auto-actualización:</span>
        <span :class="['status-value', isPollingActive ? 'active' : 'inactive']">
          {{ isPollingActive ? 'Activa' : 'Inactiva' }}
        </span>
      </div>
      
      <div class="status-item" v-if="lastUpdated">
        <span class="status-label">Última actualización:</span>
        <span class="status-value">{{ formatTime(lastUpdated) }}</span>
      </div>
      
      <div class="status-item" v-if="isRegenerating">
        <span class="status-label">Regeneración:</span>
        <span class="status-value regenerating">En progreso...</span>
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
      title="Regenerando Diagramas"
    >
      <div class="generation-progress">
        <LoadingSpinner message="Analizando código y generando diagramas de arquitectura..." />
        <div v-if="backgroundTaskProgress" class="progress-info">
          <p>Progreso: {{ backgroundTaskProgress }}%</p>
        </div>
      </div>
    </Card>

    <!-- Success Message -->
    <Card 
      v-if="designGenerationStatus === 'success' && showSuccessMessage" 
      variant="success"
      title="Regeneración Completada"
    >
      <div class="success-content">
        <p>Los diagramas de diseño se han regenerado exitosamente.</p>
        <p><strong>Archivos creados:</strong> {{ designFiles.length }}</p>
        <button @click="showSuccessMessage = false" class="btn btn-sm btn-outline-success">
          Cerrar
        </button>
      </div>
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
                <p>Haz clic en "Regenerar Diagramas" para crear nuevos diagramas.</p>
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
    </div>
  </div>
</template>

<script>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
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
    const showSuccessMessage = ref(false)
    
    // Computed properties
    const loading = computed(() => store.loading)
    const error = computed(() => store.error)
    const designFiles = computed(() => store.designFiles)
    const currentDesignFile = computed({
      get: () => store.currentDesignFile,
      set: (value) => { store.currentDesignFile = value }
    })
    const designGenerationStatus = computed(() => store.designGenerationStatus)
    const lastUpdated = computed(() => store.lastUpdated)
    const isPollingActive = computed(() => store.isPollingActive('design'))
    const isRegenerating = computed(() => store.isGenerationRunning('generateDesign'))
    const backgroundTaskProgress = computed(() => store.getTaskProgress('generateDesign'))

    // Methods
    const regenerateDesign = async () => {
      try {
        showSuccessMessage.value = false
        await store.regenerateDesign()
        showSuccessMessage.value = true
        
        // Hide success message after 5 seconds
        setTimeout(() => {
          showSuccessMessage.value = false
        }, 5000)
      } catch (error) {
        console.error('Error regenerating design:', error)
      }
    }

    const togglePolling = () => {
      if (isPollingActive.value) {
        store.stopPolling('design')
      } else {
        store.startPolling('design')
      }
    }

    const refreshDesignData = async () => {
      try {
        await store.fetchDesignData()
      } catch (error) {
        console.error('Error refreshing design data:', error)
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

    const formatTime = (isoString) => {
      if (!isoString) return 'N/A'
      try {
        return new Date(isoString).toLocaleString()
      } catch {
        return 'Formato inválido'
      }
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
      // Initial data fetch
      await store.fetchSystemStatus()
      await store.fetchDesignData()
      
      // Start polling for design updates
      store.startPolling('design')
      
      // If there are design files, load the first one
      if (designFiles.value.length > 0) {
        selectDesignFile(designFiles.value[0])
      }
    })

    onUnmounted(() => {
      // Stop polling when component is unmounted
      store.stopPolling('design')
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
      lastUpdated,
      isPollingActive,
      isRegenerating,
      backgroundTaskProgress,
      showSuccessMessage,
      
      // Methods
      regenerateDesign,
      togglePolling,
      refreshDesignData,
      selectDesignFile,
      getFileName,
      formatTime,
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
  margin-bottom: 20px;
  padding-bottom: 15px;
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

.status-bar {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #007bff;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-label {
  font-weight: 500;
  color: #495057;
}

.status-value {
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.9rem;
}

.status-value.active {
  background-color: #d4edda;
  color: #155724;
}

.status-value.inactive {
  background-color: #f8d7da;
  color: #721c24;
}

.status-value.regenerating {
  background-color: #fff3cd;
  color: #856404;
  animation: pulse 1.5s infinite;
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

.no-selection,
.no-files {
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

.diagram-container {
  margin-bottom: 30px;
}

.generation-progress {
  text-align: center;
  padding: 20px;
}

.progress-info {
  margin-top: 15px;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.success-content {
  text-align: center;
}

.success-content button {
  margin-top: 15px;
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
  display: inline-flex;
  align-items: center;
  gap: 8px;
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

.btn-outline-secondary {
  background-color: transparent;
  border-color: #6c757d;
  color: #6c757d;
}

.btn-outline-secondary:hover:not(:disabled) {
  background-color: #6c757d;
  color: white;
}

.btn-outline-success {
  background-color: transparent;
  border-color: #28a745;
  color: #28a745;
}

.btn-outline-success:hover:not(:disabled) {
  background-color: #28a745;
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
  .design-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .explorer-layout {
    grid-template-columns: 1fr;
  }
  
  .status-bar {
    flex-direction: column;
    gap: 10px;
  }
}
</style>
```

### 3. Actualizar Vista Docs con Polling
```vue
<!-- src/views/Docs.vue - Con polling y regeneración -->
<template>
  <div class="docs">
    <!-- Header Section -->
    <div class="docs-header">
      <h1>Documentación</h1>
      <div class="docs-actions">
        <button 
          @click="regenerateDocumentation" 
          :disabled="isRegenerating || loading"
          class="btn btn-primary"
        >
          <LoadingSpinner 
            v-if="isRegenerating" 
            size="small" 
            inline 
          />
          <span v-if="isRegenerating">Regenerando...</span>
          <span v-else>Regenerar Documentación</span>
        </button>
        
        <button 
          @click="togglePolling" 
          :class="['btn', isPollingActive ? 'btn-success' : 'btn-outline-secondary']"
        >
          {{ isPollingActive ? 'Auto-actualización ON' : 'Auto-actualización OFF' }}
        </button>
        
        <button 
          @click="refreshDocsData" 
          :disabled="loading"
          class="btn btn-secondary"
        >
          Actualizar Índice
        </button>
      </div>
    </div>

    <!-- Status Display -->
    <div class="status-bar">
      <div class="status-item">
        <span class="status-label">Estado de auto-actualización:</span>
        <span :class="['status-value', isPollingActive ? 'active' : 'inactive']">
          {{ isPollingActive ? 'Activa' : 'Inactiva' }}
        </span>
      </div>
      
      <div class="status-item" v-if="lastUpdated">
        <span class="status-label">Última actualización:</span>
        <span class="status-value">{{ formatTime(lastUpdated) }}</span>
      </div>
      
      <div class="status-item" v-if="isRegenerating">
        <span class="status-label">Regeneración:</span>
        <span class="status-value regenerating">En progreso...</span>
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
      title="Regenerando Documentación"
    >
      <div class="generation-progress">
        <LoadingSpinner message="Analizando código fuente y generando documentación..." />
        <div v-if="backgroundTaskProgress" class="progress-info">
          <p>Progreso: {{ backgroundTaskProgress }}%</p>
        </div>
      </div>
    </Card>

    <!-- Success Message -->
    <Card 
      v-if="docsGenerationStatus === 'success' && showSuccessMessage" 
      variant="success"
      title="Regeneración Completada"
    >
      <div class="success-content">
        <p>La documentación se ha regenerado exitosamente.</p>
        <div v-if="docsStatus">
          <p><strong>Archivos procesados:</strong> {{ docsStatus.files_processed || 0 }}</p>
          <p><strong>Documentos creados:</strong> {{ docsStatus.docs_created || 0 }}</p>
        </div>
        <button @click="showSuccessMessage = false" class="btn btn-sm btn-outline-success">
          Cerrar
        </button>
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
            <p>Haz clic en "Regenerar Documentación" para crear la documentación del proyecto.</p>
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

              <Card variant="default" title="Última Actualización">
                <div class="stat-item">
                  <span class="stat-date">{{ formatTime(docsIndex.timestamp) }}</span>
                  <span class="stat-label">Índice actualizado</span>
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
import { computed, onMounted, onUnmounted, ref, reactive } from 'vue'
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
    const showSuccessMessage = ref(false)
    
    // Computed properties
    const loading = computed(() => store.loading)
    const error = computed(() => store.error)
    const docsIndex = computed(() => store.docsIndex)
    const docsStatus = computed(() => store.docsStatus)
    const docsGenerationStatus = computed(() => store.docsGenerationStatus)
    const lastUpdated = computed(() => store.lastUpdated)
    const isPollingActive = computed(() => store.isPollingActive('docs'))
    const isRegenerating = computed(() => store.isGenerationRunning('generateDocs'))
    const backgroundTaskProgress = computed(() => store.getTaskProgress('generateDocs'))

    // Methods
    const regenerateDocumentation = async () => {
      try {
        showSuccessMessage.value = false
        await store.regenerateDocumentation()
        showSuccessMessage.value = true
        
        // Hide success message after 5 seconds
        setTimeout(() => {
          showSuccessMessage.value = false
        }, 5000)
      } catch (error) {
        console.error('Error regenerating documentation:', error)
      }
    }

    const togglePolling = () => {
      if (isPollingActive.value) {
        store.stopPolling('docs')
      } else {
        store.startPolling('docs')
      }
    }

    const refreshDocsData = async () => {
      try {
        await store.fetchDocsData()
      } catch (error) {
        console.error('Error refreshing docs data:', error)
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

    const formatTime = (isoString) => {
      if (!isoString) return 'N/A'
      try {
        return new Date(isoString).toLocaleString()
      } catch {
        return 'Formato inválido'
      }
    }

    const clearError = () => {
      store.clearError()
    }

    // Lifecycle
    onMounted(async () => {
      // Initial data fetch
      await store.fetchSystemStatus()
      await store.fetchDocsData()
      
      // Start polling for docs updates
      store.startPolling('docs')
    })

    onUnmounted(() => {
      // Stop polling when component is unmounted
      store.stopPolling('docs')
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
      lastUpdated,
      isPollingActive,
      isRegenerating,
      backgroundTaskProgress,
      showSuccessMessage,
      
      // Methods
      regenerateDocumentation,
      togglePolling,
      refreshDocsData,
      toggleModule,
      loadDocFile,
      getModuleName,
      getFileName,
      formatTime,
      clearError
    }
  }
}
</script>

<style scoped>
/* Similar styles to Design.vue with docs-specific adaptations */
.docs {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.docs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
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

.status-bar {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #28a745;
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
  background-color: #28a745;
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

.module-files h4 {
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

/* Inherit button styles from Design component */
.btn {
  padding: 8px 16px;
  border: 1px solid;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
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

.btn-outline-secondary {
  background-color: transparent;
  border-color: #6c757d;
  color: #6c757d;
}

.btn-outline-secondary:hover:not(:disabled) {
  background-color: #6c757d;
  color: white;
}

.btn-outline-success {
  background-color: transparent;
  border-color: #28a745;
  color: #28a745;
}

.btn-outline-success:hover:not(:disabled) {
  background-color: #28a745;
  color: white;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 0.8rem;
}

/* Share animations and responsive styles */
@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.status-value.regenerating {
  animation: pulse 1.5s infinite;
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
  
  .status-bar {
    flex-direction: column;
    gap: 10px;
  }
}
</style>
```

### 4. Actualizar Dashboard con Polling Global
```javascript
// src/views/Dashboard.vue - Modificaciones para incluir polling
// En el script section, añadir esto al onMounted:

onMounted(async () => {
  // Initial data fetch
  await store.fetchSystemStatus()
  
  // Start global status polling for Dashboard
  store.startPolling('status')
})

onUnmounted(() => {
  // Stop status polling when leaving dashboard
  store.stopPolling('status')
})
```

### 5. Configurar Polling en App.vue (Global)
```vue
<!-- src/App.vue - Configuración global de polling -->
<script>
import { onMounted, onUnmounted, onBeforeUnmount } from 'vue'
import { useMainStore } from './stores/main'

export default {
  name: 'App',
  setup() {
    const store = useMainStore()

    // Global lifecycle management
    onMounted(() => {
      // Initialize system status
      store.fetchSystemStatus()
    })

    onBeforeUnmount(() => {
      // Clean up all polling when app is about to unmount
      store.stopAllPolling()
    })

    // Handle browser visibility changes
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page is hidden, optionally pause polling
        console.log('Page hidden - polling continues in background')
      } else {
        // Page is visible, ensure polling is active
        console.log('Page visible - refreshing data')
        store.fetchSystemStatus()
      }
    }

    onMounted(() => {
      document.addEventListener('visibilitychange', handleVisibilityChange)
    })

    onUnmounted(() => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    })

    return {}
  }
}
</script>
```

## Criterios de Verificación

### 1. Verificación del Polling
```bash
# Ejecutar ambos servidores
cd autocode/
uv run autocode daemon  # Terminal 1

cd autocode/web_modern/
npm run dev              # Terminal 2

# Verificar en el navegador:
# 1. Abrir DevTools > Network
# 2. Navegar a Design view (http://localhost:5173/design)
# 3. Verificar llamadas periódicas a /api/status cada 45 segundos
# 4. Navegar a Docs view (http://localhost:5173/docs)
# 5. Verificar llamadas a /api/docs/index cada 45 segundos
# 6. En Dashboard, verificar llamadas a /api/status cada 30 segundos
```

### 2. Verificación de Regeneración
```bash
# En la interfaz web:
# 1. Ir a Design view
# 2. Hacer clic en "Regenerar Diagramas"
# 3. Verificar en Network tab:
#    - POST a /api/generate-design
#    - Seguimiento de estado de la tarea
#    - Refresh automático de datos después
# 4. Repetir proceso en Docs view con "Regenerar Documentación"
```

### 3. Verificación de Estados UI
```javascript
// En Vue DevTools:
// 1. Store > main
// 2. Verificar que pollingEnabled cambia correctamente
// 3. Verificar que backgroundTasks se actualiza durante regeneración
// 4. Comprobar que lastUpdated se actualiza con cada poll
// 5. Verificar que polling se detiene al cambiar de vista
```

### 4. Verificación de Memory Leaks
```javascript
// En DevTools > Performance:
// 1. Grabar performance profile
// 2. Navegar entre vistas múltiples veces
// 3. Verificar que no hay intervalos huérfanos
// 4. Comprobar que memory usage se mantiene estable
// 5. Confirmar que setInterval se limpia correctamente
```

### 5. Verificación de Estados de Error
```bash
# Simular errores:
# 1. Detener backend (Ctrl+C en daemon terminal)
# 2. Verificar que polling continúa y maneja errores
# 3. Verificar que UI muestra estados de error apropiados
# 4. Reiniciar backend
# 5. Confirmar que polling recupera automáticamente
```

### 6. Verificación de Background Tasks
```bash
# Para verificar manejo de tareas de larga duración:
# 1. Simular generación lenta modificando backend
# 2. Iniciar regeneración desde UI
# 3. Verificar que UI muestra progreso correctamente
# 4. Confirmar que botones se deshabilitan durante la operación
# 5. Verificar que el estado se actualiza al completarse
```

### 7. Verificación de Toggles de Polling
```bash
# En cada vista (Design, Docs):
# 1. Verificar que el botón "Auto-actualización" funciona
# 2. Comprobar cambio visual del botón (ON/OFF)
# 3. Verificar en console logs que polling se inicia/detiene
# 4. Confirmar que status bar refleja el estado correcto
# 5. Probar navegación entre vistas con polling activo
```

### 8. Verificación de Visibilidad del Browser
```bash
# Prueba de visibility API:
# 1. Iniciar polling en cualquier vista
# 2. Cambiar a otra pestaña del navegador (minimize)
# 3. Verificar en DevTools que polling continúa
# 4. Volver a la pestaña de autocode
# 5. Verificar que se ejecuta refresh inmediato
```

### 9. Verificación de Estados de Success/Error
```bash
# Estados de éxito:
# 1. Regenerar contenido exitosamente
# 2. Verificar mensaje de éxito aparece
# 3. Confirmar que desaparece automáticamente después de 5s
# 4. Verificar que botón "Cerrar" funciona

# Estados de error:
# 1. Simular error de API (desconectar backend durante regeneración)
# 2. Verificar que error se muestra correctamente
# 3. Confirmar que botones vuelven a estado normal
# 4. Verificar que error es dismissible
```

### 10. Verificación de Responsive Design
```bash
# Probar en diferentes tamaños:
# 1. Desktop: Verificar que status-bar se muestra horizontalmente
# 2. Mobile: Confirmar que status-bar se adapta verticalmente
# 3. Tablet: Verificar que botones son accesibles
# 4. Confirmar que polling funciona en todos los tamaños
```

## Notas Importantes para la Implementación

### Gestión de Memoria
- **Crítico**: Todos los `setInterval` deben limpiarse en `onUnmounted`
- **Importante**: `stopAllPolling()` debe llamarse en App.vue antes del unmount
- **Recomendado**: Usar `console.log` para debug de inicio/parada de polling

### Manejo de Errores
- Los errores de polling no deben detener el interval automáticamente
- Mostrar errores en UI pero continuar con próximo poll
- Recuperación automática cuando el backend vuelve a estar disponible

### UX Considerations
- Indicadores visuales claros del estado de polling
- Botones deshabilitados durante operaciones de regeneración
- Timeouts apropiados para evitar spam de requests
- Feedback inmediato al usuario en todas las acciones

### Performance
- Intervalos diferenciados por tipo de contenido (30s status, 45s design/docs)
- Usar `document.hidden` para optimización de resources
- Evitar polls simultáneos innecesarios

## Estructura Final de Archivos

```
autocode/web_modern/src/
├── stores/
│   └── main.js                  # Store expandido con polling completo
├── views/
│   ├── Dashboard.vue            # Con polling de status
│   ├── Design.vue              # Con polling y regeneración de design
│   ├── Docs.vue                # Con polling y regeneración de docs
│   └── Config.vue              # Sin cambios
├── App.vue                     # Con gestión global de polling
└── components/                 # Componentes base (sin cambios)
```

## Template de Commit Message
```
feat(ui): implement polling and regeneration functionality

- Added comprehensive polling system to Pinia store with configurable intervals
- Implemented automatic background updates for Design and Docs views every 45s
- Added Dashboard status polling every 30s for real-time monitoring
- Created regeneration buttons with loading states and progress tracking
- Implemented background task management with proper state tracking
- Added status bars showing polling state and last update time
- Implemented proper cleanup of intervals to prevent memory leaks
- Added error handling for polling with automatic recovery
- Created responsive design for polling controls and status displays
- Added browser visibility API integration for optimized resource usage
- Implemented toggle functionality for enabling/disabling auto-updates
- Added success/error states with auto-dismiss and manual close options
- Enhanced UX with disabled states during regeneration operations
- All polling intervals are properly cleaned up on component unmount
- Store provides centralized polling management across all views
- Background tasks show progress indicators and status updates
- Polling continues gracefully even during temporary API errors
- Visual feedback for all user actions with appropriate loading states
```

## Consideraciones de Desarrollo

### Orden de Implementación Recomendado
1. **Store**: Expandir Pinia store con toda la lógica de polling
2. **Design View**: Implementar polling y regeneración en vista de diseño  
3. **Docs View**: Implementar polling y regeneración en vista de documentación
4. **Dashboard**: Añadir polling de status global
5. **App.vue**: Configurar gestión global y cleanup
6. **Testing**: Verificar todos los criterios paso a paso

### Puntos Críticos a Verificar
- **Memory Leaks**: Usar DevTools para confirmar limpieza de intervals
- **Error Recovery**: Probar desconexión/reconexión de backend
- **UI States**: Verificar todos los estados visuales (loading, success, error)
- **Cross-View Navigation**: Polling debe manejarse correctamente al cambiar vistas
- **Performance**: No debe haber degradación notable con polling activo

### Debug y Troubleshooting
- Activar console logs para seguimiento de polling
- Usar Vue DevTools para monitorear cambios de estado
- Network tab para verificar timing de requests
- Performance tab para detectar memory leaks
- Application tab para verificar que no hay timers huérfanos
