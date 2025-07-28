# Task 005: Inicializar Proyecto Vue.js con Vite

## Contexto del Proyecto
Este proyecto autocode necesita una nueva interfaz de usuario moderna para reemplazar la actual basada en Jinja2 templates. El objetivo es crear un frontend Vue.js completamente separado que consuma la API FastAPI del backend, proporcionando una experiencia de usuario más dinámica e interactiva.

## Estado Actual del Sistema

### Backend API Existente
El proyecto tiene una API FastAPI corriendo en el puerto 8080 con endpoints como:

```python
# Endpoints principales disponibles:
# GET  /api/status              - Estado del daemon y checks
# GET  /api/daemon/status       - Estado específico del daemon
# GET  /api/checks              - Resultados de todos los checks
# POST /api/checks/{name}/run   - Ejecutar check específico
# GET  /api/config              - Configuración actual
# POST /api/generate-docs       - Generar documentación
# POST /api/generate-design     - Generar diagramas de diseño
# GET  /api/config/load         - Cargar configuración
# POST /api/docs/check-sync     - Check síncrono de documentación
```

### UI Legacy Actual
Existe una UI legacy en `autocode/web/` que usa:
- **Templates**: Jinja2 templates en `autocode/web/templates/`
- **Static files**: CSS y JS vanilla en `autocode/web/static/`
- **Server-side rendering**: Páginas renderizadas por FastAPI

```
autocode/web/
├── templates/
│   ├── base.html
│   ├── index.html
│   └── pages/
│       ├── dashboard.html
│       ├── design.html
│       └── config.html
└── static/
    ├── style.css
    ├── design-tokens.css
    ├── app.js
    └── js/
        ├── components/
        │   └── design.js
        └── utils/
            └── api-fetch.js
```

### Estructura del Proyecto
```
autocode/
├── cli.py                     # CLI con comandos Typer
├── api/
│   ├── server.py             # FastAPI app
│   └── models.py             # Modelos Pydantic
├── core/                     # Lógica de negocio
│   ├── docs/
│   ├── git/
│   ├── test/
│   └── design/
├── web/                      # UI legacy (mantener intacta)
└── orchestration/
    └── daemon.py
```

## Objetivo de la Nueva UI
Crear una interfaz Vue.js moderna que:
1. **Reemplace gradualmente** la UI legacy sin romper funcionalidad existente
2. **Consuma la API** de forma asíncrona para mejor UX
3. **Proporcione interactividad** en tiempo real
4. **Sea mantenible** con arquitectura de componentes
5. **Soporte futuras funcionalidades** con facilidad

## Dependencias y Requisitos

### Requisitos del Sistema
- **Node.js**: Versión 16+ (verificar con `node --version`)
- **npm**: Incluido con Node.js
- **Backend funcionando**: API en http://localhost:8080

### Tecnologías a Utilizar
- **Vue 3**: Framework progresivo para frontend
- **Vite**: Build tool rápido y dev server
- **Vue Router**: Routing del lado del cliente
- **Pinia**: State management para Vue 3
- **Axios**: Cliente HTTP para llamadas a API

## Instrucciones Paso a Paso

### 1. Crear Directorio del Nuevo Frontend
```bash
# Desde la raíz del proyecto autocode/
mkdir autocode/web_modern
cd autocode/web_modern
```

### 2. Inicializar Proyecto Vue con Vite
```bash
# Crear proyecto Vue.js con Vite (sin TypeScript por simplicidad)
npm create vite@latest . -- --template vue

# Esto creará la estructura base:
# ├── package.json
# ├── vite.config.js
# ├── index.html
# ├── public/
# └── src/
#     ├── App.vue
#     ├── main.js
#     ├── style.css
#     ├── assets/
#     └── components/
#         └── HelloWorld.vue
```

### 3. Instalar Dependencias Adicionales
```bash
# Instalar dependencias base
npm install

# Instalar dependencias adicionales para el proyecto
npm add vue-router@4 pinia axios

# vue-router@4: Routing para Vue 3
# pinia: State management oficial para Vue 3
# axios: Cliente HTTP para comunicación con API
```

### 4. Configurar Vue Router
```javascript
// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Design from '../views/Design.vue'
import Docs from '../views/Docs.vue'
import Config from '../views/Config.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/dashboard',
    name: 'DashboardAlias',
    component: Dashboard
  },
  {
    path: '/design',
    name: 'Design',
    component: Design
  },
  {
    path: '/docs',
    name: 'Docs',
    component: Docs
  },
  {
    path: '/config',
    name: 'Config',
    component: Config
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
```

### 5. Configurar Pinia Store
```javascript
// src/stores/main.js
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
    
    // Docs data
    docsStatus: null,
    docsIndex: null,
    
    // UI state
    loading: false,
    error: null
  }),

  getters: {
    isDaemonRunning: (state) => state.daemonStatus?.running || false,
    hasErrors: (state) => state.error !== null
  },

  actions: {
    async fetchSystemStatus() {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get('/api/status')
        this.daemonStatus = response.data.daemon
        this.checksResults = response.data.checks
        this.systemConfig = response.data.config
      } catch (error) {
        this.error = 'Failed to fetch system status'
        console.error('Error fetching status:', error)
      } finally {
        this.loading = false
      }
    },

    async generateDocs() {
      try {
        const response = await axios.post('/api/generate-docs')
        return response.data
      } catch (error) {
        this.error = 'Failed to generate docs'
        throw error
      }
    },

    async generateDesign() {
      try {
        const response = await axios.post('/api/generate-design')
        return response.data
      } catch (error) {
        this.error = 'Failed to generate design'
        throw error
      }
    },

    async loadConfig() {
      try {
        const response = await axios.get('/api/config/load')
        this.systemConfig = response.data.config
        return response.data
      } catch (error) {
        this.error = 'Failed to load configuration'
        throw error
      }
    }
  }
})
```

### 6. Configurar Vite para Development
```javascript
// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      // Proxy API calls al backend
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        secure: false
      },
      // Proxy para archivos de diseño
      '/design': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
})
```

### 7. Crear Vistas Base (Placeholders)
```vue
<!-- src/views/Dashboard.vue -->
<template>
  <div class="dashboard">
    <h1>Autocode Dashboard</h1>
    <div v-if="loading" class="loading">
      Cargando estado del sistema...
    </div>
    <div v-else-if="error" class="error">
      Error: {{ error }}
    </div>
    <div v-else class="dashboard-content">
      <div class="status-section">
        <h2>Estado del Daemon</h2>
        <p>Ejecutándose: {{ isDaemonRunning ? 'Sí' : 'No' }}</p>
      </div>
      <div class="checks-section">
        <h2>Checks</h2>
        <div v-for="(check, name) in checksResults" :key="name" class="check-item">
          <strong>{{ name }}:</strong> {{ check.status }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useMainStore } from '../stores/main'
import { computed, onMounted } from 'vue'

export default {
  name: 'Dashboard',
  setup() {
    const store = useMainStore()
    
    onMounted(() => {
      store.fetchSystemStatus()
    })

    return {
      loading: computed(() => store.loading),
      error: computed(() => store.error),
      checksResults: computed(() => store.checksResults),
      isDaemonRunning: computed(() => store.isDaemonRunning)
    }
  }
}
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.loading, .error {
  padding: 10px;
  margin: 10px 0;
  border-radius: 4px;
}

.loading {
  background-color: #e3f2fd;
  color: #1976d2;
}

.error {
  background-color: #ffebee;
  color: #c62828;
}

.status-section, .checks-section {
  margin: 20px 0;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.check-item {
  margin: 5px 0;
}
</style>
```

```vue
<!-- src/views/Design.vue -->
<template>
  <div class="design">
    <h1>Design & Architecture</h1>
    <button @click="generateDesign" :disabled="loading">
      {{ loading ? 'Generando...' : 'Generar Diagramas' }}
    </button>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="design-content">
      <p>Aquí se mostrarán los diagramas de arquitectura generados.</p>
    </div>
  </div>
</template>

<script>
import { useMainStore } from '../stores/main'
import { computed } from 'vue'

export default {
  name: 'Design',
  setup() {
    const store = useMainStore()

    const generateDesign = async () => {
      try {
        await store.generateDesign()
        alert('Generación de diseño iniciada')
      } catch (error) {
        console.error('Error generating design:', error)
      }
    }

    return {
      loading: computed(() => store.loading),
      error: computed(() => store.error),
      generateDesign
    }
  }
}
</script>
```

```vue
<!-- src/views/Docs.vue -->
<template>
  <div class="docs">
    <h1>Documentation</h1>
    <button @click="generateDocs" :disabled="loading">
      {{ loading ? 'Generando...' : 'Generar Documentación' }}
    </button>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="docs-content">
      <p>Aquí se mostrará la documentación del proyecto.</p>
    </div>
  </div>
</template>

<script>
import { useMainStore } from '../stores/main'
import { computed } from 'vue'

export default {
  name: 'Docs',
  setup() {
    const store = useMainStore()

    const generateDocs = async () => {
      try {
        await store.generateDocs()
        alert('Generación de documentación iniciada')
      } catch (error) {
        console.error('Error generating docs:', error)
      }
    }

    return {
      loading: computed(() => store.loading),
      error: computed(() => store.error),
      generateDocs
    }
  }
}
</script>
```

```vue
<!-- src/views/Config.vue -->
<template>
  <div class="config">
    <h1>Configuration</h1>
    <button @click="loadConfig" :disabled="loading">
      {{ loading ? 'Cargando...' : 'Cargar Configuración' }}
    </button>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="systemConfig" class="config-content">
      <pre>{{ JSON.stringify(systemConfig, null, 2) }}</pre>
    </div>
  </div>
</template>

<script>
import { useMainStore } from '../stores/main'
import { computed } from 'vue'

export default {
  name: 'Config',
  setup() {
    const store = useMainStore()

    const loadConfig = async () => {
      try {
        await store.loadConfig()
      } catch (error) {
        console.error('Error loading config:', error)
      }
    }

    return {
      loading: computed(() => store.loading),
      error: computed(() => store.error),
      systemConfig: computed(() => store.systemConfig),
      loadConfig
    }
  }
}
</script>
</style>
```

### 8. Actualizar App.vue Principal
```vue
<!-- src/App.vue -->
<template>
  <div id="app">
    <nav class="navbar">
      <div class="nav-brand">
        <router-link to="/">Autocode</router-link>
      </div>
      <div class="nav-links">
        <router-link to="/dashboard">Dashboard</router-link>
        <router-link to="/design">Design</router-link>
        <router-link to="/docs">Docs</router-link>
        <router-link to="/config">Config</router-link>
      </div>
    </nav>
    
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background-color: #2c3e50;
  color: white;
}

.nav-brand a {
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  text-decoration: none;
}

.nav-links {
  display: flex;
  gap: 1rem;
}

.nav-links a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  background-color: #34495e;
}

.main-content {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.error {
  background-color: #ffebee;
  color: #c62828;
  padding: 10px;
  margin: 10px 0;
  border-radius: 4px;
  border: 1px solid #ffcdd2;
}
</style>
```

### 9. Actualizar main.js
```javascript
// src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
```

### 10. Crear Directorio de Vistas
```bash
# Crear directorio de vistas
mkdir src/views

# Después de crear los archivos Vue arriba, la estructura quedará:
# src/
# ├── views/
# │   ├── Dashboard.vue
# │   ├── Design.vue
# │   ├── Docs.vue
# │   └── Config.vue
# ├── stores/
# │   └── main.js
# └── router/
#     └── index.js
```

## Criterios de Verificación

### 1. Desarrollo Local
```bash
# Desde autocode/web_modern/
npm run dev

# Debería mostrar:
# ➜  Local:   http://localhost:5173/
# ➜  Network: use --host to expose
# ➜  press h to show help
```

### 2. Verificaciones en Navegador
1. **Carga inicial**: Ir a http://localhost:5173/ - debe mostrar la aplicación
2. **Navegación**: Probar links Dashboard, Design, Docs, Config
3. **Routing**: URLs deben cambiar correctamente (/dashboard, /design, etc.)
4. **Proxy API**: Abrir DevTools > Network y verificar que llamadas a /api van al backend

### 3. Test de Funcionalidad Básica
```bash
# En otra terminal, asegurar que el backend esté corriendo
cd autocode/
uv run autocode daemon

# Volver al frontend y probar:
# 1. Dashboard debería cargar estado del daemon
# 2. Botones de generar deberían hacer requests a /api
# 3. No debería haber errores de CORS en consola
```

### 4. Verificaciones Técnicas
- **Vue DevTools**: Instalar extensión y verificar que detecta Vue 3, Pinia, Router
- **Console errors**: No debe haber errores en la consola del navegador
- **Network requests**: Peticiones a API deben llegar al backend (localhost:8080)

### 5. Estructura de Archivos Final
```
autocode/web_modern/
├── package.json
├── vite.config.js
├── index.html
├── src/
│   ├── App.vue
│   ├── main.js
│   ├── style.css
│   ├── router/
│   │   └── index.js
│   ├── stores/
│   │   └── main.js
│   ├── views/
│   │   ├── Dashboard.vue
│   │   ├── Design.vue
│   │   ├── Docs.vue
│   │   └── Config.vue
│   └── components/
│       └── HelloWorld.vue (puede eliminarse)
└── node_modules/
```

## Template de Commit Message
```
feat(ui): initialize Vue.js frontend with Vite and essential setup

- Created new Vue 3 project in autocode/web_modern/ using Vite
- Configured Vue Router with routes for Dashboard, Design, Docs, Config
- Set up Pinia store for state management with API integration
- Added Axios for HTTP requests with API proxy configuration
- Created placeholder views with basic functionality
- Configured development server proxy to backend API (localhost:8080)
- Added navigation and basic styling for modern UI foundation
- Maintained separation from legacy UI in autocode/web/
```
