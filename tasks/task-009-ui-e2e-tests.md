# Task 009: Implementar Tests E2E Completos con Cypress

## Contexto General del Proyecto
Este proyecto es autocode, una herramienta de desarrollo que automatiza verificaciones de calidad del código, generación de documentación y validación de tests. El sistema tiene un backend FastAPI y una interfaz web moderna construida con Vue.js 3, Vite, Vue Router 4, y Pinia para el manejo de estado.

## Estado Actual del Codebase

### Estructura de Directorios del Frontend
```
autocode/web_vue/
├── src/
│   ├── main.js                 # Punto de entrada Vue
│   ├── App.vue                 # Componente raíz
│   ├── router/
│   │   └── index.js           # Configuración Vue Router
│   ├── stores/
│   │   └── main.js            # Store Pinia principal
│   ├── components/
│   │   ├── Card.vue           # Componente de tarjeta reutilizable
│   │   ├── MarkdownRenderer.vue  # Renderizador Markdown
│   │   ├── DiagramRenderer.vue   # Renderizador diagramas Mermaid
│   │   ├── LoadingSpinner.vue    # Indicador de carga
│   │   └── ErrorMessage.vue      # Componente de error
│   └── views/
│       ├── Dashboard.vue      # Vista dashboard principal
│       ├── Design.vue         # Vista documentación diseño
│       ├── Docs.vue          # Vista documentación general
│       └── Config.vue        # Vista configuración
├── package.json
├── vite.config.js
└── index.html
```

### Backend API Endpoints Existentes
```
GET /api/status          # Estado general del sistema
GET /api/status/doc      # Estado verificación documentación
GET /api/status/test     # Estado verificación tests
GET /api/status/git      # Estado análisis git
POST /api/generate/doc   # Generar documentación
POST /api/generate/test  # Generar tests
POST /api/generate/design # Generar diseño
GET /api/design/files    # Archivos de diseño disponibles
GET /api/design/content/{filename} # Contenido archivo diseño
```

### Componentes Vue Actuales

#### Store Pinia (src/stores/main.js)
```javascript
import { defineStore } from 'pinia'
import axios from 'axios'

export const useMainStore = defineStore('main', {
  state: () => ({
    systemStatus: null,
    docStatus: null,
    testStatus: null,
    gitStatus: null,
    loading: false,
    error: null,
    pollingEnabled: true,
    pollingInterval: 5000
  }),
  
  actions: {
    async fetchSystemStatus() {
      this.loading = true
      try {
        const response = await axios.get('/api/status')
        this.systemStatus = response.data
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },
    
    async generateDocumentation() {
      this.loading = true
      try {
        await axios.post('/api/generate/doc')
        await this.fetchSystemStatus()
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    }
  }
})
```

#### Componente Dashboard (src/views/Dashboard.vue)
```vue
<template>
  <div class="dashboard">
    <div class="header">
      <h1>Autocode Dashboard</h1>
      <div class="stats">
        <div class="stat">
          <span class="label">Estado:</span>
          <span class="value" :class="systemStatus?.status">
            {{ systemStatus?.status || 'Cargando...' }}
          </span>
        </div>
      </div>
    </div>
    
    <div class="checks-grid">
      <Card 
        title="Documentación"
        :status="docStatus?.status"
        :loading="loading"
        @regenerate="generateDoc"
      >
        <template #content>
          <p>{{ docStatus?.message || 'Sin información' }}</p>
        </template>
      </Card>
      
      <Card 
        title="Tests"
        :status="testStatus?.status"
        :loading="loading"
        @regenerate="generateTest"
      >
        <template #content>
          <p>{{ testStatus?.message || 'Sin información' }}</p>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useMainStore } from '@/stores/main'
import Card from '@/components/Card.vue'

const store = useMainStore()

const systemStatus = computed(() => store.systemStatus)
const docStatus = computed(() => store.docStatus)
const testStatus = computed(() => store.testStatus)
const loading = computed(() => store.loading)

const generateDoc = () => store.generateDocumentation()
const generateTest = () => store.generateTests()

onMounted(() => {
  store.fetchSystemStatus()
})
</script>
```

## Objetivo de Esta Tarea
Implementar una suite completa de tests E2E usando Cypress que cubra todos los flujos de usuario principales, interacciones con la API, navegación entre vistas, y funcionalidades de polling/regeneración. Los tests deben ser robustos, incluir mocking de API, y proporcionar cobertura completa de la aplicación.

## Instrucciones Paso a Paso

### 1. Instalación y Configuración de Cypress

#### Instalar Cypress
```bash
cd autocode/web_vue
npm install --save-dev cypress @cypress/vite-dev-server
```

#### Configurar Cypress (cypress.config.js)
```javascript
import { defineConfig } from 'cypress'
import vite from './vite.config.js'

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    supportFile: 'cypress/support/e2e.js',
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    video: true,
    screenshotOnRunFailure: true,
    viewportWidth: 1280,
    viewportHeight: 720,
    defaultCommandTimeout: 10000,
    requestTimeout: 10000,
    responseTimeout: 10000,
    setupNodeEvents(on, config) {
      // Plugin para integración con Vite
      on('dev-server:start', (options) => {
        return startDevServer({ options, viteConfig: vite })
      })
    }
  },
  
  component: {
    devServer: {
      framework: 'vue',
      bundler: 'vite',
      viteConfig: vite
    },
    supportFile: 'cypress/support/component.js',
    specPattern: 'src/**/*.cy.{js,jsx,ts,tsx}'
  }
})
```

#### Archivo de Soporte Principal (cypress/support/e2e.js)
```javascript
// Importar comandos personalizados
import './commands'

// Configuración global
Cypress.on('uncaught:exception', (err, runnable) => {
  // Evitar que errores de la aplicación fallen los tests
  if (err.message.includes('ResizeObserver loop limit exceeded')) {
    return false
  }
  return true
})

// Configurar viewport por defecto
beforeEach(() => {
  cy.viewport(1280, 720)
})
```

#### Comandos Personalizados (cypress/support/commands.js)
```javascript
// Comando para visitar dashboard y esperar carga
Cypress.Commands.add('visitDashboard', () => {
  cy.intercept('GET', '/api/status', { fixture: 'system-status.json' }).as('getStatus')
  cy.visit('/')
  cy.wait('@getStatus')
})

// Comando para mockear API completa
Cypress.Commands.add('mockAPI', () => {
  cy.intercept('GET', '/api/status', { fixture: 'system-status.json' }).as('getStatus')
  cy.intercept('GET', '/api/status/doc', { fixture: 'doc-status.json' }).as('getDocStatus')
  cy.intercept('GET', '/api/status/test', { fixture: 'test-status.json' }).as('getTestStatus')
  cy.intercept('GET', '/api/status/git', { fixture: 'git-status.json' }).as('getGitStatus')
  cy.intercept('POST', '/api/generate/doc', { statusCode: 200, body: { success: true } }).as('generateDoc')
  cy.intercept('POST', '/api/generate/test', { statusCode: 200, body: { success: true } }).as('generateTest')
  cy.intercept('POST', '/api/generate/design', { statusCode: 200, body: { success: true } }).as('generateDesign')
  cy.intercept('GET', '/api/design/files', { fixture: 'design-files.json' }).as('getDesignFiles')
})

// Comando para esperar que termine el loading
Cypress.Commands.add('waitForLoading', () => {
  cy.get('[data-testid="loading-spinner"]').should('not.exist')
})

// Comando para verificar estado de card
Cypress.Commands.add('checkCardStatus', (cardTitle, expectedStatus) => {
  cy.get(`[data-testid="card-${cardTitle.toLowerCase()}"]`)
    .should('be.visible')
    .within(() => {
      cy.get('[data-testid="card-status"]').should('contain', expectedStatus)
    })
})
```

### 2. Fixtures de Datos de Prueba

#### Datos del Sistema (cypress/fixtures/system-status.json)
```json
{
  "status": "ok",
  "timestamp": "2025-01-15T10:30:00Z",
  "version": "1.0.0",
  "checks": {
    "doc": {
      "status": "warning",
      "message": "3 archivos desactualizados",
      "last_check": "2025-01-15T10:25:00Z"
    },
    "test": {
      "status": "ok",
      "message": "Todos los tests pasan",
      "last_check": "2025-01-15T10:24:00Z"
    },
    "git": {
      "status": "ok",
      "message": "Repositorio limpio",
      "last_check": "2025-01-15T10:26:00Z"
    }
  }
}
```

#### Datos de Documentación (cypress/fixtures/doc-status.json)
```json
{
  "status": "warning",
  "message": "3 archivos desactualizados",
  "outdated_files": [
    "docs/autocode/core/design.md",
    "docs/autocode/api/models.md",
    "docs/autocode/cli.md"
  ],
  "total_files": 45,
  "up_to_date": 42,
  "last_check": "2025-01-15T10:25:00Z"
}
```

#### Datos de Tests (cypress/fixtures/test-status.json)
```json
{
  "status": "ok",
  "message": "Todos los tests pasan",
  "total_tests": 28,
  "passed": 28,
  "failed": 0,
  "coverage": 85.6,
  "last_run": "2025-01-15T10:24:00Z"
}
```

#### Archivos de Diseño (cypress/fixtures/design-files.json)
```json
{
  "files": [
    {
      "name": "_index.md",
      "path": "design/autocode/_index.md",
      "type": "overview"
    },
    {
      "name": "api_items.md",
      "path": "design/autocode/api/api_items.md",
      "type": "component"
    },
    {
      "name": "core_items.md",
      "path": "design/autocode/core/core_items.md",
      "type": "component"
    }
  ]
}
```

### 3. Tests E2E Principales

#### Test del Dashboard (cypress/e2e/dashboard.cy.js)
```javascript
describe('Dashboard', () => {
  beforeEach(() => {
    cy.mockAPI()
    cy.visitDashboard()
  })

  it('debería cargar el dashboard correctamente', () => {
    // Verificar título
    cy.get('[data-testid="page-title"]').should('contain', 'Autocode Dashboard')
    
    // Verificar estadísticas del header
    cy.get('[data-testid="system-status"]').should('contain', 'ok')
    cy.get('[data-testid="last-update"]').should('be.visible')
    
    // Verificar grid de checks
    cy.get('[data-testid="checks-grid"]').should('be.visible')
  })

  it('debería mostrar el estado de cada verificación', () => {
    // Verificar card de documentación
    cy.checkCardStatus('Documentación', 'warning')
    cy.get('[data-testid="card-documentacion"]')
      .should('contain', '3 archivos desactualizados')
    
    // Verificar card de tests
    cy.checkCardStatus('Tests', 'ok')
    cy.get('[data-testid="card-tests"]')
      .should('contain', 'Todos los tests pasan')
    
    // Verificar card de git
    cy.checkCardStatus('Git', 'ok')
    cy.get('[data-testid="card-git"]')
      .should('contain', 'Repositorio limpio')
  })

  it('debería permitir regenerar documentación', () => {
    cy.get('[data-testid="card-documentacion"]')
      .find('[data-testid="regenerate-button"]')
      .click()
    
    // Verificar que se muestra loading
    cy.get('[data-testid="loading-spinner"]').should('be.visible')
    
    // Verificar llamada a la API
    cy.wait('@generateDoc')
    
    // Verificar que desaparece el loading
    cy.waitForLoading()
    
    // Verificar que se actualiza el estado
    cy.wait('@getStatus')
  })

  it('debería manejar errores de API correctamente', () => {
    // Mockear error en la API
    cy.intercept('POST', '/api/generate/doc', {
      statusCode: 500,
      body: { error: 'Error interno del servidor' }
    }).as('generateDocError')
    
    cy.get('[data-testid="card-documentacion"]')
      .find('[data-testid="regenerate-button"]')
      .click()
    
    cy.wait('@generateDocError')
    
    // Verificar mensaje de error
    cy.get('[data-testid="error-message"]')
      .should('be.visible')
      .should('contain', 'Error interno del servidor')
  })

  it('debería actualizar datos automáticamente con polling', () => {
    // Cambiar mock para simular cambio de estado
    cy.intercept('GET', '/api/status', {
      ...require('../fixtures/system-status.json'),
      checks: {
        ...require('../fixtures/system-status.json').checks,
        doc: {
          status: 'ok',
          message: 'Documentación actualizada',
          last_check: new Date().toISOString()
        }
      }
    }).as('getStatusUpdated')
    
    // Esperar próximo polling (5 segundos)
    cy.wait('@getStatusUpdated', { timeout: 6000 })
    
    // Verificar actualización en UI
    cy.checkCardStatus('Documentación', 'ok')
    cy.get('[data-testid="card-documentacion"]')
      .should('contain', 'Documentación actualizada')
  })
})
```

#### Test de Navegación (cypress/e2e/navigation.cy.js)
```javascript
describe('Navegación', () => {
  beforeEach(() => {
    cy.mockAPI()
  })

  it('debería navegar entre todas las vistas principales', () => {
    cy.visit('/')
    
    // Verificar dashboard
    cy.url().should('eq', Cypress.config().baseUrl + '/')
    cy.get('[data-testid="page-title"]').should('contain', 'Dashboard')
    
    // Navegar a Design
    cy.get('[data-testid="nav-design"]').click()
    cy.url().should('include', '/design')
    cy.get('[data-testid="page-title"]').should('contain', 'Documentación de Diseño')
    
    // Navegar a Docs
    cy.get('[data-testid="nav-docs"]').click()
    cy.url().should('include', '/docs')
    cy.get('[data-testid="page-title"]').should('contain', 'Documentación')
    
    // Navegar a Config
    cy.get('[data-testid="nav-config"]').click()
    cy.url().should('include', '/config')
    cy.get('[data-testid="page-title"]').should('contain', 'Configuración')
    
    // Volver al Dashboard
    cy.get('[data-testid="nav-dashboard"]').click()
    cy.url().should('eq', Cypress.config().baseUrl + '/')
  })

  it('debería mantener estado activo en navegación', () => {
    cy.visit('/design')
    
    cy.get('[data-testid="nav-design"]')
      .should('have.class', 'router-link-active')
    
    cy.get('[data-testid="nav-dashboard"]')
      .should('not.have.class', 'router-link-active')
  })

  it('debería manejar rutas no existentes', () => {
    cy.visit('/ruta-inexistente', { failOnStatusCode: false })
    
    // Debería redirigir al dashboard o mostrar 404
    cy.url().should('eq', Cypress.config().baseUrl + '/')
  })
})
```

#### Test de Vista Design (cypress/e2e/design.cy.js)
```javascript
describe('Vista Design', () => {
  beforeEach(() => {
    cy.mockAPI()
    cy.visit('/design')
    cy.wait('@getDesignFiles')
  })

  it('debería cargar lista de archivos de diseño', () => {
    cy.get('[data-testid="design-files-list"]').should('be.visible')
    
    cy.get('[data-testid="design-file-item"]').should('have.length.greaterThan', 0)
    
    // Verificar archivo overview
    cy.get('[data-testid="design-file-item"]')
      .contains('_index.md')
      .should('be.visible')
  })

  it('debería cargar contenido de archivo seleccionado', () => {
    cy.intercept('GET', '/api/design/content/_index.md', {
      fixture: 'design-content.md'
    }).as('getDesignContent')
    
    cy.get('[data-testid="design-file-item"]')
      .contains('_index.md')
      .click()
    
    cy.wait('@getDesignContent')
    
    // Verificar que se muestra el contenido
    cy.get('[data-testid="markdown-content"]').should('be.visible')
    cy.get('[data-testid="diagram-container"]').should('be.visible')
  })

  it('debería regenerar documentación de diseño', () => {
    cy.get('[data-testid="regenerate-design-button"]').click()
    
    cy.wait('@generateDesign')
    
    // Verificar recarga de archivos
    cy.wait('@getDesignFiles')
    
    // Verificar mensaje de éxito
    cy.get('[data-testid="success-message"]')
      .should('be.visible')
      .should('contain', 'Diseño regenerado correctamente')
  })

  it('debería renderizar diagramas Mermaid correctamente', () => {
    cy.intercept('GET', '/api/design/content/_index.md', {
      body: `# Diagrama de Prueba

\`\`\`mermaid
graph TD
    A[Inicio] --> B[Proceso]
    B --> C[Fin]
\`\`\`
`
    }).as('getDiagramContent')
    
    cy.get('[data-testid="design-file-item"]')
      .first()
      .click()
    
    cy.wait('@getDiagramContent')
    
    // Verificar que se renderiza el diagrama
    cy.get('.mermaid').should('be.visible')
    cy.get('.mermaid svg').should('exist')
  })
})
```

#### Test de Configuración (cypress/e2e/config.cy.js)
```javascript
describe('Vista Config', () => {
  beforeEach(() => {
    cy.mockAPI()
    cy.visit('/config')
  })

  it('debería mostrar configuración de polling', () => {
    cy.get('[data-testid="polling-config"]').should('be.visible')
    
    // Verificar toggle de polling
    cy.get('[data-testid="polling-enabled-toggle"]')
      .should('be.visible')
      .should('be.checked')
    
    // Verificar input de intervalo
    cy.get('[data-testid="polling-interval-input"]')
      .should('be.visible')
      .should('have.value', '5000')
  })

  it('debería permitir cambiar configuración de polling', () => {
    // Deshabilitar polling
    cy.get('[data-testid="polling-enabled-toggle"]').click()
    
    // Verificar que se actualiza el estado
    cy.get('[data-testid="polling-status"]')
      .should('contain', 'Deshabilitado')
    
    // Cambiar intervalo
    cy.get('[data-testid="polling-interval-input"]')
      .clear()
      .type('10000')
    
    // Guardar configuración
    cy.get('[data-testid="save-config-button"]').click()
    
    // Verificar mensaje de éxito
    cy.get('[data-testid="success-message"]')
      .should('contain', 'Configuración guardada')
  })

  it('debería validar valores de configuración', () => {
    // Intentar intervalo inválido
    cy.get('[data-testid="polling-interval-input"]')
      .clear()
      .type('invalid')
    
    cy.get('[data-testid="save-config-button"]').click()
    
    // Verificar mensaje de error
    cy.get('[data-testid="error-message"]')
      .should('contain', 'Intervalo debe ser un número válido')
  })
})
```

### 4. Tests de Componentes

#### Test del Componente Card (cypress/component/Card.cy.js)
```javascript
import Card from '../../src/components/Card.vue'

describe('Card Component', () => {
  it('debería renderizar correctamente', () => {
    cy.mount(Card, {
      props: {
        title: 'Test Card',
        status: 'ok',
        loading: false
      },
      slots: {
        content: '<p>Contenido de prueba</p>'
      }
    })
    
    cy.get('[data-testid="card-title"]').should('contain', 'Test Card')
    cy.get('[data-testid="card-status"]').should('contain', 'ok')
    cy.get('[data-testid="card-content"]').should('contain', 'Contenido de prueba')
  })

  it('debería mostrar loading spinner cuando está cargando', () => {
    cy.mount(Card, {
      props: {
        title: 'Test Card',
        status: 'ok',
        loading: true
      }
    })
    
    cy.get('[data-testid="loading-spinner"]').should('be.visible')
    cy.get('[data-testid="regenerate-button"]').should('be.disabled')
  })

  it('debería emitir evento regenerate al hacer click', () => {
    const onRegenerate = cy.stub()
    
    cy.mount(Card, {
      props: {
        title: 'Test Card',
        status: 'ok',
        loading: false,
        onRegenerate
      }
    })
    
    cy.get('[data-testid="regenerate-button"]').click()
    cy.wrap(onRegenerate).should('have.been.called')
  })
})
```

### 5. Configuración de Scripts y CI/CD

#### Actualizar package.json
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test:e2e": "cypress run",
    "test:e2e:dev": "cypress open",
    "test:component": "cypress run --component",
    "test:component:dev": "cypress open --component",
    "test:all": "npm run test:component && npm run test:e2e"
  }
}
```

#### Configuración para GitHub Actions (.github/workflows/e2e.yml)
```yaml
name: E2E Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  e2e:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: autocode/web_vue/package-lock.json
    
    - name: Install dependencies
      working-directory: autocode/web_vue
      run: npm ci
    
    - name: Build application
      working-directory: autocode/web_vue
      run: npm run build
    
    - name: Start backend server
      working-directory: autocode
      run: |
        pip install -e .
        uvicorn autocode.api.server:app --host 0.0.0.0 --port 8000 &
        sleep 5
    
    - name: Run Cypress tests
      working-directory: autocode/web_vue
      uses: cypress-io/github-action@v5
      with:
        start: npm run preview
        wait-on: 'http://localhost:3000'
        browser: chrome
        record: true
      env:
        CYPRESS_RECORD_KEY: ${{ secrets.CYPRESS_RECORD_KEY }}
```

## Verificación y Criterios de Éxito

### 1. Verificación de Instalación
```bash
cd autocode/web_vue
npm install --save-dev cypress @cypress/vite-dev-server
npx cypress verify
```

### 2. Verificación de Configuración
```bash
# Abrir Cypress en modo desarrollo
npx cypress open

# Ejecutar tests en modo headless
npm run test:e2e

# Ejecutar tests de componentes
npm run test:component
```

### 3. Verificación de Cobertura
Los tests deben cubrir:
- ✅ Navegación entre todas las vistas
- ✅ Carga inicial de datos desde API
- ✅ Funcionalidad de regeneración de cada módulo
- ✅ Manejo de errores de API
- ✅ Polling automático y actualización de datos
- ✅ Configuración de sistema
- ✅ Renderizado de componentes individuales
- ✅ Validación de formularios
- ✅ Estados de loading y error

### 4. Verificación de Performance
```bash
# Los tests deben ejecutarse en menos de 5 minutos
npm run test:e2e
# Verificar que no hay memory leaks en polling
# Verificar que los diagramas se renderizan correctamente
```

### 5. Verificación Visual
```bash
# Abrir Cypress UI para verificación visual
npx cypress open
# Ejecutar tests y verificar screenshots
# Validar que todos los componentes se ven correctamente
```

## Estructura Final de Tests
```
cypress/
├── e2e/
│   ├── dashboard.cy.js      # Tests principales del dashboard
│   ├── navigation.cy.js     # Tests de navegación
│   ├── design.cy.js         # Tests de vista de diseño
│   ├── docs.cy.js          # Tests de documentación
│   └── config.cy.js        # Tests de configuración
├── component/
│   ├── Card.cy.js          # Tests del componente Card
│   ├── MarkdownRenderer.cy.js
│   └── DiagramRenderer.cy.js
├── fixtures/
│   ├── system-status.json
│   ├── doc-status.json
│   ├── test-status.json
│   ├── design-files.json
│   └── design-content.md
└── support/
    ├── e2e.js              # Configuración E2E
    ├── component.js        # Configuración componentes
    └── commands.js         # Comandos personalizados
```

## Template de Commit Message
```
test(ui): implement comprehensive E2E testing with Cypress

- Added Cypress with full E2E and component testing setup
- Created comprehensive test suites for all main user flows
- Implemented API mocking strategies for reliable testing
- Added custom commands and fixtures for maintainable tests
- Configured CI/CD integration with GitHub Actions
- Achieved 100% coverage of critical user interactions
- Included performance and visual regression testing

Tests cover:
- Dashboard functionality and status displays
- Navigation between all application views  
- Document and design generation workflows
- Polling and real-time updates
- Configuration management
- Error handling and edge cases
- Component isolation and behavior
```

## Notas Importantes

### Consideraciones de Mantenimiento
1. **Actualizar fixtures**: Mantener datos de prueba sincronizados con cambios de API
2. **Selectores estables**: Usar `data-testid` en lugar de clases CSS para mayor estabilidad
3. **Tests independientes**: Cada test debe poder ejecutarse de forma aislada
4. **Limpieza de estado**: Resetear estado entre tests para evitar interferencias

### Mejores Prácticas Implementadas
1. **Page Object Pattern**: Comandos personalizados para operaciones comunes
2. **API Mocking**: Intercepción de todas las llamadas para tests determinísticos
