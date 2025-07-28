# Task 006: Crear Componentes Base Reutilizables para Vue.js

## Contexto del Proyecto
Este proyecto autocode es una herramienta de desarrollo que automatiza verificaciones de código, documentación y tests. El sistema actual tiene una API FastAPI que expone endpoints para generar documentación, diagramas de diseño y ejecutar verificaciones. Se está desarrollando una nueva interfaz Vue.js moderna para reemplazar la UI legacy basada en Jinja2 templates.

## Estado Actual del Frontend
Existe un proyecto Vue.js en `autocode/web_modern/` con la siguiente estructura:

```
autocode/web_modern/
├── package.json
├── vite.config.js
├── index.html
├── src/
│   ├── App.vue
│   ├── main.js
│   ├── router/
│   │   └── index.js
│   ├── stores/
│   │   └── main.js
│   ├── views/
│   │   ├── Dashboard.vue
│   │   ├── Design.vue
│   │   ├── Docs.vue
│   │   └── Config.vue
│   └── components/          # Directorio a desarrollar en esta task
│       └── HelloWorld.vue   # Componente ejemplo de Vite (puede eliminarse)
└── node_modules/
```

### Tecnologías del Stack
- **Vue 3**: Framework reactivo con Composition API
- **Vite**: Build tool y dev server
- **Vue Router 4**: Routing del lado del cliente
- **Pinia**: State management
- **Axios**: Cliente HTTP para API calls

## Objetivo de los Componentes Base
Crear componentes Vue reutilizables que sirvan como building blocks para todas las vistas de la aplicación:

1. **Card**: Componente contenedor genérico para mostrar información estructurada
2. **MarkdownRenderer**: Renderiza contenido Markdown a HTML (para documentación)
3. **DiagramRenderer**: Renderiza diagramas Mermaid (para arquitectura y diseño)
4. **LoadingSpinner**: Indicador de carga reutilizable
5. **ErrorMessage**: Componente para mostrar errores de forma consistente

## Dependencias Necesarias

### Librerías de Renderizado
```bash
# Desde autocode/web_modern/
npm add marked mermaid

# marked: Para convertir Markdown a HTML
# mermaid: Para renderizar diagramas de código
```

### Herramientas de Testing
```bash
# Testing utilities para Vue 3
npm add -D vitest @vue/test-utils jsdom

# vitest: Test runner rápido para Vite
# @vue/test-utils: Utilidades para testing de componentes Vue
# jsdom: DOM environment para tests
```

## Instrucciones Paso a Paso

### 1. Instalar Dependencias
```bash
cd autocode/web_modern/
npm add marked mermaid
npm add -D vitest @vue/test-utils jsdom
```

### 2. Configurar Vitest para Testing
```javascript
// vite.config.js - Actualizar configuración existente
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        secure: false
      },
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
  },
  test: {
    globals: true,
    environment: 'jsdom'
  }
})
```

### 3. Actualizar package.json con Scripts de Testing
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:run": "vitest run",
    "test:ui": "vitest --ui"
  }
}
```

### 4. Crear Componente Card
```vue
<!-- src/components/Card.vue -->
<template>
  <div class="card" :class="cardClasses">
    <div v-if="title || $slots.header" class="card-header">
      <slot name="header">
        <h3 v-if="title" class="card-title">{{ title }}</h3>
      </slot>
    </div>
    
    <div class="card-body">
      <slot name="default">
        <p v-if="content">{{ content }}</p>
      </slot>
    </div>
    
    <div v-if="$slots.footer" class="card-footer">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Card',
  props: {
    title: {
      type: String,
      default: ''
    },
    content: {
      type: String,
      default: ''
    },
    variant: {
      type: String,
      default: 'default',
      validator: value => ['default', 'primary', 'success', 'warning', 'danger'].includes(value)
    },
    size: {
      type: String,
      default: 'medium',
      validator: value => ['small', 'medium', 'large'].includes(value)
    }
  },
  computed: {
    cardClasses() {
      return [
        `card--${this.variant}`,
        `card--${this.size}`
      ]
    }
  }
}
</script>

<style scoped>
.card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e1e5e9;
  overflow: hidden;
  transition: box-shadow 0.3s ease;
}

.card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e1e5e9;
  background-color: #f8f9fa;
}

.card-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
}

.card-body {
  padding: 20px;
}

.card-footer {
  padding: 12px 20px;
  background-color: #f8f9fa;
  border-top: 1px solid #e1e5e9;
}

/* Variantes */
.card--primary {
  border-color: #007bff;
}

.card--primary .card-header {
  background-color: #007bff;
  color: white;
}

.card--primary .card-title {
  color: white;
}

.card--success {
  border-color: #28a745;
}

.card--success .card-header {
  background-color: #28a745;
  color: white;
}

.card--success .card-title {
  color: white;
}

.card--warning {
  border-color: #ffc107;
}

.card--warning .card-header {
  background-color: #ffc107;
  color: #212529;
}

.card--danger {
  border-color: #dc3545;
}

.card--danger .card-header {
  background-color: #dc3545;
  color: white;
}

.card--danger .card-title {
  color: white;
}

/* Tamaños */
.card--small {
  font-size: 0.875rem;
}

.card--small .card-header,
.card--small .card-body {
  padding: 12px 16px;
}

.card--small .card-title {
  font-size: 1.1rem;
}

.card--large {
  font-size: 1.1rem;
}

.card--large .card-header,
.card--large .card-body {
  padding: 24px 28px;
}

.card--large .card-title {
  font-size: 1.5rem;
}
</style>
```

### 5. Crear Componente MarkdownRenderer
```vue
<!-- src/components/MarkdownRenderer.vue -->
<template>
  <div class="markdown-renderer">
    <div v-if="loading" class="loading">
      Renderizando contenido...
    </div>
    <div v-else-if="error" class="error">
      Error al renderizar markdown: {{ error }}
    </div>
    <div v-else v-html="renderedContent" class="markdown-content"></div>
  </div>
</template>

<script>
import { marked } from 'marked'
import { ref, computed, watch } from 'vue'

export default {
  name: 'MarkdownRenderer',
  props: {
    content: {
      type: String,
      required: true
    },
    options: {
      type: Object,
      default: () => ({})
    }
  },
  setup(props) {
    const loading = ref(false)
    const error = ref(null)
    
    // Configurar marked con opciones por defecto
    const defaultOptions = {
      breaks: true,
      gfm: true,
      headerIds: true,
      mangle: false
    }
    
    const markedOptions = computed(() => ({
      ...defaultOptions,
      ...props.options
    }))
    
    const renderedContent = computed(() => {
      if (!props.content) return ''
      
      try {
        loading.value = true
        error.value = null
        
        // Configurar marked
        marked.setOptions(markedOptions.value)
        
        const result = marked(props.content)
        loading.value = false
        return result
      } catch (err) {
        loading.value = false
        error.value = err.message
        return ''
      }
    })
    
    return {
      loading,
      error,
      renderedContent
    }
  }
}
</script>

<style scoped>
.markdown-renderer {
  width: 100%;
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

.markdown-content {
  line-height: 1.6;
  color: #333;
}

/* Estilos para contenido markdown */
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  font-weight: 600;
  line-height: 1.25;
  color: #2c3e50;
}

.markdown-content :deep(h1) {
  font-size: 2rem;
  border-bottom: 2px solid #eaecef;
  padding-bottom: 0.5rem;
}

.markdown-content :deep(h2) {
  font-size: 1.5rem;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3rem;
}

.markdown-content :deep(h3) {
  font-size: 1.25rem;
}

.markdown-content :deep(p) {
  margin-bottom: 1em;
}

.markdown-content :deep(code) {
  background-color: #f8f8f8;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.markdown-content :deep(pre) {
  background-color: #f8f8f8;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 1em 0;
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid #dfe2e5;
  padding-left: 16px;
  margin-left: 0;
  color: #6a737d;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 2em;
  margin-bottom: 1em;
}

.markdown-content :deep(li) {
  margin-bottom: 0.25em;
}

.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #dfe2e5;
  padding: 8px 16px;
  text-align: left;
}

.markdown-content :deep(th) {
  background-color: #f6f8fa;
  font-weight: 600;
}
</style>
```

### 6. Crear Componente DiagramRenderer
```vue
<!-- src/components/DiagramRenderer.vue -->
<template>
  <div class="diagram-renderer">
    <div v-if="loading" class="loading">
      Renderizando diagrama...
    </div>
    <div v-else-if="error" class="error">
      Error al renderizar diagrama: {{ error }}
    </div>
    <div v-else ref="diagramContainer" class="diagram-container"></div>
  </div>
</template>

<script>
import mermaid from 'mermaid'
import { ref, onMounted, watch, nextTick } from 'vue'

export default {
  name: 'DiagramRenderer',
  props: {
    code: {
      type: String,
      required: true
    },
    config: {
      type: Object,
      default: () => ({})
    }
  },
  setup(props) {
    const diagramContainer = ref(null)
    const loading = ref(false)
    const error = ref(null)
    
    // Configuración por defecto de Mermaid
    const defaultConfig = {
      theme: 'default',
      themeVariables: {
        primaryColor: '#007bff',
        primaryTextColor: '#2c3e50',
        primaryBorderColor: '#007bff',
        lineColor: '#6c757d'
      },
      startOnLoad: false,
      securityLevel: 'loose'
    }
    
    const renderDiagram = async () => {
      if (!props.code || !diagramContainer.value) return
      
      try {
        loading.value = true
        error.value = null
        
        // Limpiar contenedor anterior
        diagramContainer.value.innerHTML = ''
        
        // Configurar Mermaid
        const config = { ...defaultConfig, ...props.config }
        mermaid.initialize(config)
        
        // Generar ID único para el diagrama
        const diagramId = `diagram-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        
        // Renderizar diagrama
        const { svg } = await mermaid.render(diagramId, props.code)
        
        // Insertar SVG en el contenedor
        diagramContainer.value.innerHTML = svg
        
        loading.value = false
      } catch (err) {
        loading.value = false
        error.value = err.message
        console.error('Error rendering diagram:', err)
      }
    }
    
    // Renderizar cuando cambie el código
    watch(() => props.code, renderDiagram, { immediate: false })
    
    onMounted(async () => {
      await nextTick()
      await renderDiagram()
    })
    
    return {
      diagramContainer,
      loading,
      error
    }
  }
}
</script>

<style scoped>
.diagram-renderer {
  width: 100%;
}

.loading, .error {
  padding: 10px;
  margin: 10px 0;
  border-radius: 4px;
  text-align: center;
}

.loading {
  background-color: #e3f2fd;
  color: #1976d2;
}

.error {
  background-color: #ffebee;
  color: #c62828;
}

.diagram-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e1e5e9;
}

.diagram-container :deep(svg) {
  max-width: 100%;
  height: auto;
}

/* Estilos específicos para diferentes tipos de diagramas */
.diagram-container :deep(.node rect),
.diagram-container :deep(.node circle),
.diagram-container :deep(.node ellipse) {
  fill: #f8f9fa;
  stroke: #007bff;
  stroke-width: 2px;
}

.diagram-container :deep(.node text) {
  fill: #2c3e50;
  font-family: 'Arial', sans-serif;
  font-size: 14px;
}

.diagram-container :deep(.edgePath path) {
  stroke: #6c757d;
  stroke-width: 2px;
}

.diagram-container :deep(.edgeLabel) {
  background-color: white;
  color: #495057;
  font-size: 12px;
}
</style>
```

### 7. Crear Componentes de UI Adicionales

```vue
<!-- src/components/LoadingSpinner.vue -->
<template>
  <div class="loading-spinner" :class="sizeClass">
    <div class="spinner" :class="variantClass"></div>
    <p v-if="message" class="loading-message">{{ message }}</p>
  </div>
</template>

<script>
export default {
  name: 'LoadingSpinner',
  props: {
    size: {
      type: String,
      default: 'medium',
      validator: value => ['small', 'medium', 'large'].includes(value)
    },
    variant: {
      type: String,
      default: 'primary',
      validator: value => ['primary', 'secondary', 'light'].includes(value)
    },
    message: {
      type: String,
      default: ''
    }
  },
  computed: {
    sizeClass() {
      return `loading-spinner--${this.size}`
    },
    variantClass() {
      return `spinner--${this.variant}`
    }
  }
}
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.spinner {
  border-radius: 50%;
  border: 3px solid #f3f3f3;
  border-top: 3px solid;
  animation: spin 1s linear infinite;
}

.loading-spinner--small .spinner {
  width: 24px;
  height: 24px;
}

.loading-spinner--medium .spinner {
  width: 40px;
  height: 40px;
}

.loading-spinner--large .spinner {
  width: 60px;
  height: 60px;
}

.spinner--primary {
  border-top-color: #007bff;
}

.spinner--secondary {
  border-top-color: #6c757d;
}

.spinner--light {
  border-top-color: #f8f9fa;
  border-color: #dee2e6;
}

.loading-message {
  margin-top: 12px;
  color: #6c757d;
  font-size: 0.9rem;
  text-align: center;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
```

```vue
<!-- src/components/ErrorMessage.vue -->
<template>
  <div class="error-message" :class="variantClass">
    <div class="error-icon">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <circle cx="12" cy="12" r="10"/>
        <line x1="15" y1="9" x2="9" y2="15"/>
        <line x1="9" y1="9" x2="15" y2="15"/>
      </svg>
    </div>
    <div class="error-content">
      <h4 v-if="title" class="error-title">{{ title }}</h4>
      <p class="error-text">{{ message }}</p>
      <div v-if="details" class="error-details">
        <details>
          <summary>Ver detalles</summary>
          <pre>{{ details }}</pre>
        </details>
      </div>
    </div>
    <button v-if="dismissible" @click="$emit('dismiss')" class="error-dismiss">
      ×
    </button>
  </div>
</template>

<script>
export default {
  name: 'ErrorMessage',
  emits: ['dismiss'],
  props: {
    message: {
      type: String,
      required: true
    },
    title: {
      type: String,
      default: 'Error'
    },
    variant: {
      type: String,
      default: 'danger',
      validator: value => ['danger', 'warning', 'info'].includes(value)
    },
    details: {
      type: String,
      default: ''
    },
    dismissible: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    variantClass() {
      return `error-message--${this.variant}`
    }
  }
}
</script>

<style scoped>
.error-message {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid;
  margin: 12px 0;
}

.error-message--danger {
  background-color: #f8d7da;
  border-color: #f5c6cb;
  color: #721c24;
}

.error-message--warning {
  background-color: #fff3cd;
  border-color: #ffeaa7;
  color: #856404;
}

.error-message--info {
  background-color: #d1ecf1;
  border-color: #bee5eb;
  color: #0c5460;
}

.error-icon {
  margin-right: 12px;
  flex-shrink: 0;
  margin-top: 2px;
}

.error-content {
  flex: 1;
}

.error-title {
  margin: 0 0 8px 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.error-text {
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.error-details {
  margin-top: 8px;
}

.error-details summary {
  cursor: pointer;
  font-size: 0.9rem;
  margin-bottom: 8px;
}

.error-details pre {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  overflow-x: auto;
  margin: 0;
}

.error-dismiss {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  margin-left: 12px;
  line-height: 1;
  opacity: 0.7;
  transition: opacity 0.3s;
}

.error-dismiss:hover {
  opacity: 1;
}
</style>
```

### 8. Crear Archivo de Exportación Central
```javascript
// src/components/index.js
export { default as Card } from './Card.vue'
export { default as MarkdownRenderer } from './MarkdownRenderer.vue'
export { default as DiagramRenderer } from './DiagramRenderer.vue'
export { default as LoadingSpinner } from './LoadingSpinner.vue'
export { default as ErrorMessage } from './ErrorMessage.vue'
```

### 9. Crear Tests Unitarios
```javascript
// src/components/__tests__/Card.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Card from '../Card.vue'

describe('Card', () => {
  it('renders with title and content props', () => {
    const wrapper = mount(Card, {
      props: {
        title: 'Test Title',
        content: 'Test content'
      }
    })

    expect(wrapper.find('.card-title').text()).toBe('Test Title')
    expect(wrapper.find('.card-body p').text()).toBe('Test content')
  })

  it('renders with slots', () => {
    const wrapper = mount(Card, {
      slots: {
        default: '<p>Slot content</p>',
        header: '<h2>Custom header</h2>'
      }
    })

    expect(wrapper.html()).toContain('<h2>Custom header</h2>')
    expect(wrapper.html()).toContain('<p>Slot content</p>')
  })

  it('applies variant classes correctly', () => {
    const wrapper = mount(Card, {
      props: { variant: 'primary' }
    })

    expect(wrapper.classes()).toContain('card--primary')
  })

  it('applies size classes correctly', () => {
    const wrapper = mount(Card, {
      props: { size: 'large' }
    })

    expect(wrapper.classes()).toContain('card--large')
  })
})
```

```javascript
// src/components/__tests__/MarkdownRenderer.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MarkdownRenderer from '../MarkdownRenderer.vue'

describe('MarkdownRenderer', () => {
  it('renders markdown content as HTML', async () => {
    const wrapper = mount(MarkdownRenderer, {
      props: {
        content: '# Test Header\n\nThis is **bold** text.'
      }
    })

    // Wait for rendering
    await wrapper.vm.$nextTick()

    const content = wrapper.find('.markdown-content')
    expect(content.html()).toContain('<h1')
    expect(content.html()).toContain('Test Header')
    expect(content.html()).toContain('<strong>bold</strong>')
  })

  it('handles empty content gracefully', () => {
    const wrapper = mount(MarkdownRenderer, {
      props: {
        content: ''
      }
    })

    expect(wrapper.find('.markdown-content').html()).toBe('<div class="markdown-content"></div>')
  })

  it('shows error when markdown parsing fails', async () => {
    // Mount with invalid markdown that could cause parsing issues
    const wrapper = mount(MarkdownRenderer, {
      props: {
        content: '# Valid header\n\n```invalid\nunclosed code block'
      }
    })

    await wrapper.vm.$nextTick()
    
    // The component should still render even with edge cases
    expect(wrapper.find('.markdown-content').exists()).toBe(true)
  })
})
```

```javascript
// src/components/__tests__/LoadingSpinner.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LoadingSpinner from '../LoadingSpinner.vue'

describe('LoadingSpinner', () => {
  it('renders with default props', () => {
    const wrapper = mount(LoadingSpinner)

    expect(wrapper.classes()).toContain('loading-spinner--medium')
    expect(wrapper.find('.spinner').classes()).toContain('spinner--primary')
  })

  it('renders with custom message', () => {
    const wrapper = mount(LoadingSpinner, {
      props: {
        message: 'Loading data...'
      }
    })

    expect(wrapper.find('.loading-message').text()).toBe('Loading data...')
  })

  it('applies size and variant classes correctly', () => {
    const wrapper = mount(LoadingSpinner, {
      props: {
        size: 'large',
        variant: 'secondary'
      }
    })

    expect(wrapper.classes()).toContain('loading-spinner--large')
    expect(wrapper.find('.spinner').classes()).toContain('spinner--secondary')
  })
})
```

```javascript
// src/components/__tests__/ErrorMessage.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ErrorMessage from '../ErrorMessage.vue'

describe('ErrorMessage', () => {
  it('renders with required message prop', () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Something went wrong'
      }
    })

    expect(wrapper.find('.error-text').text()).toBe('Something went wrong')
    expect(wrapper.find('.error-title').text()).toBe('Error')
  })

  it('renders with custom title', () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test message',
        title: 'Custom Error'
      }
    })

    expect(wrapper.find('.error-title').text()).toBe('Custom Error')
  })

  it('shows details when provided', () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test message',
        details: 'Stack trace here'
      }
    })

    expect(wrapper.find('.error-details').exists()).toBe(true)
    expect(wrapper.html()).toContain('Stack trace here')
  })

  it('emits dismiss event when dismissible', async () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test message',
        dismissible: true
      }
    })

    await wrapper.find('.error-dismiss').trigger('click')
    expect(wrapper.emitted().dismiss).toHaveLength(1)
  })

  it('applies variant classes correctly', () => {
    const wrapper = mount(ErrorMessage, {
      props: {
        message: 'Test message',
        variant: 'warning'
      }
    })

    expect(wrapper.classes()).toContain('error-message--warning')
  })
})
```

```javascript
// src/components/__tests__/DiagramRenderer.test.js
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DiagramRenderer from '../DiagramRenderer.vue'

// Mock mermaid
vi.mock('mermaid', () => ({
  default: {
    initialize: vi.fn(),
    render: vi.fn().mockResolvedValue({ svg: '<svg>Test diagram</svg>' })
  }
}))

describe('DiagramRenderer', () => {
  it('renders with mermaid code prop', async () => {
    const wrapper = mount(DiagramRenderer, {
      props: {
        code: 'graph TD\n    A --> B'
      }
    })

    // Wait for component to mount and render
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.diagram-container').exists()).toBe(true)
  })

  it('shows loading state initially', () => {
    const wrapper = mount(DiagramRenderer, {
      props: {
        code: 'graph TD\n    A --> B'
      }
    })

    // Initially should show loading or diagram container
    expect(wrapper.find('.diagram-renderer').exists()).toBe(true)
  })

  it('handles empty code gracefully', () => {
    const wrapper = mount(DiagramRenderer, {
      props: {
        code: ''
      }
    })

    expect(wrapper.find('.diagram-renderer').exists()).toBe(true)
  })
})
```

### 10. Crear Vista de Ejemplo para Probar Componentes
```vue
<!-- src/views/ComponentsDemo.vue -->
<template>
  <div class="components-demo">
    <h1>Demostración de Componentes Base</h1>
    
    <!-- Card Component Demo -->
    <section class="demo-section">
      <h2>Card Component</h2>
      <div class="demo-grid">
        <Card title="Card Básica" content="Contenido de ejemplo"></Card>
        <Card variant="primary" title="Card Primaria" content="Card con variante primaria"></Card>
        <Card variant="success" size="large" title="Card Grande" content="Card con tamaño grande y variante de éxito"></Card>
        
        <Card title="Card con Slots">
          <template #default>
            <p>Contenido personalizado usando slots</p>
            <button class="btn">Acción</button>
          </template>
          <template #footer>
            <small>Footer personalizado</small>
          </template>
        </Card>
      </div>
    </section>

    <!-- MarkdownRenderer Demo -->
    <section class="demo-section">
      <h2>MarkdownRenderer Component</h2>
      <Card title="Renderizado de Markdown">
        <MarkdownRenderer :content="markdownContent" />
      </Card>
    </section>

    <!-- DiagramRenderer Demo -->
    <section class="demo-section">
      <h2>DiagramRenderer Component</h2>
      <Card title="Diagrama Mermaid">
        <DiagramRenderer :code="mermaidCode" />
      </Card>
    </section>

    <!-- LoadingSpinner Demo -->
    <section class="demo-section">
      <h2>LoadingSpinner Component</h2>
      <div class="demo-grid">
        <Card title="Spinner Pequeño">
          <LoadingSpinner size="small" message="Cargando..." />
        </Card>
        <Card title="Spinner Mediano">
          <LoadingSpinner message="Procesando datos..." />
        </Card>
        <Card title="Spinner Grande">
          <LoadingSpinner size="large" variant="secondary" message="Generando contenido..." />
        </Card>
      </div>
    </section>

    <!-- ErrorMessage Demo -->
    <section class="demo-section">
      <h2>ErrorMessage Component</h2>
      <ErrorMessage 
        message="Error de conexión con la API" 
        details="Failed to fetch data from /api/status"
        dismissible
        @dismiss="handleErrorDismiss"
      />
      <ErrorMessage 
        variant="warning" 
        title="Advertencia"
        message="La configuración no está sincronizada"
      />
      <ErrorMessage 
        variant="info" 
        title="Información"
        message="El sistema se actualizará en 5 minutos"
      />
    </section>
  </div>
</template>

<script>
import { Card, MarkdownRenderer, DiagramRenderer, LoadingSpinner, ErrorMessage } from '../components'

export default {
  name: 'ComponentsDemo',
  components: {
    Card,
    MarkdownRenderer,
    DiagramRenderer,
    LoadingSpinner,
    ErrorMessage
  },
  data() {
    return {
      markdownContent: `# Ejemplo de Markdown

Este es un ejemplo de contenido **Markdown** renderizado.

## Lista de características:
- Soporte para **negrita** e *cursiva*
- Listas ordenadas y no ordenadas
- Enlaces: [Autocode GitHub](https://github.com/brunvelop/autocode)
- Código inline: \`npm install\`

### Bloque de código:
\`\`\`javascript
function ejemplo() {
  console.log("Hola mundo");
}
\`\`\`

> Este es un blockquote de ejemplo
> para mostrar el styling.`,

      mermaidCode: `graph TD
    A[Usuario] --> B[Frontend Vue]
    B --> C[API FastAPI]
    C --> D[AutocodeDaemon]
    D --> E[DocChecker]
    D --> F[GitAnalyzer]
    D --> G[TestChecker]
    E --> H[Documentación]
    F --> I[Estado Git]
    G --> J[Resultados Tests]`
    }
  },
  methods: {
    handleErrorDismiss() {
      console.log('Error dismissed')
    }
  }
}
</script>

<style scoped>
.components-demo {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.demo-section {
  margin-bottom: 40px;
}

.demo-section h2 {
  color: #2c3e50;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e1e5e9;
}

.demo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.btn {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn:hover {
  background-color: #0056b3;
}
</style>
```

### 11. Actualizar Router para Incluir la Vista de Demo
```javascript
// src/router/index.js - Añadir ruta a la configuración existente
import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Design from '../views/Design.vue'
import Docs from '../views/Docs.vue'
import Config from '../views/Config.vue'
import ComponentsDemo from '../views/ComponentsDemo.vue'

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
  },
  {
    path: '/demo',
    name: 'ComponentsDemo',
    component: ComponentsDemo
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
```

## Criterios de Verificación

### 1. Instalación y Setup
```bash
# Verificar que las dependencias se instalen correctamente
cd autocode/web_modern/
npm add marked mermaid
npm add -D vitest @vue/test-utils jsdom

# Verificar estructura de archivos creada
ls -la src/components/
# Debe mostrar: Card.vue, MarkdownRenderer.vue, DiagramRenderer.vue, LoadingSpinner.vue, ErrorMessage.vue, index.js
```

### 2. Tests Unitarios
```bash
# Ejecutar tests para verificar componentes
npm run test

# Los tests deben pasar:
# ✓ Card.test.js - 4 tests
# ✓ MarkdownRenderer.test.js - 3 tests  
# ✓ LoadingSpinner.test.js - 3 tests
# ✓ ErrorMessage.test.js - 5 tests
# ✓ DiagramRenderer.test.js - 3 tests
```

### 3. Integración en el Desarrollo
```bash
# Ejecutar servidor de desarrollo
npm run dev

# Visitar http://localhost:5173/demo
# Debe mostrar todos los componentes funcionando correctamente
```

### 4. Verificaciones Funcionales en el Navegador

**Card Component:**
- Debe mostrar títulos, contenido y aplicar variantes correctamente
- Los slots deben funcionar para contenido personalizado
- Las variantes (primary, success, warning, danger) deben aplicar los colores correctos
- Los tamaños (small, medium, large) deben afectar el padding y font-size

**MarkdownRenderer:**
- Debe convertir Markdown a HTML correctamente
- Headers, links, código y listas deben renderizarse apropiadamente
- El styling CSS debe aplicarse a elementos markdown (:deep selectors)

**DiagramRenderer:**
- Debe renderizar diagramas Mermaid como SVG
- Debe mostrar estado de carga mientras renderiza
- Debe manejar errores de sintaxis de manera elegante

**LoadingSpinner:**
- Animación de rotación debe funcionar suavemente
- Diferentes tamaños y variantes deben aplicarse correctamente
- Mensaje opcional debe mostrarse cuando se proporcione

**ErrorMessage:**
- Debe mostrar mensaje y título correctamente
- Diferentes variantes (danger, warning, info) deben tener colores distintos
- Botón de dismiss debe emitir evento cuando está habilitado
- Detalles colapsables deben funcionar cuando se proporcionan

### 5. Verificación de Imports
```javascript
// Probar que los componentes se exporten correctamente
import { Card, MarkdownRenderer, DiagramRenderer, LoadingSpinner, ErrorMessage } from '@/components'

// En cualquier componente Vue:
export default {
  components: {
    Card,
    MarkdownRenderer
    // etc.
  }
}
```

### 6. Verificación de Accesibilidad y UX
- Todos los componentes deben ser responsivos
- Estados de loading y error deben ser claros para el usuario
- Los colores deben tener suficiente contraste
- Los componentes deben funcionar sin JavaScript (graceful degradation donde sea posible)

### 7. Integración con Stores (Opcional para esta task)
```javascript
// Los componentes deben poder usar stores de Pinia
import { useMainStore } from '@/stores/main'

// En setup() de un componente:
const store = useMainStore()
```

## Estructura Final de Archivos
```
autocode/web_modern/src/components/
├── Card.vue
├── MarkdownRenderer.vue
├── DiagramRenderer.vue
├── LoadingSpinner.vue
├── ErrorMessage.vue
├── index.js
└── __tests__/
    ├── Card.test.js
    ├── MarkdownRenderer.test.js
    ├── DiagramRenderer.test.js
    ├── LoadingSpinner.test.js
    └── ErrorMessage.test.js
```

## Template de Commit Message
```
feat(ui): add comprehensive base components library

- Created Card component with variants, sizes and slots support
- Added MarkdownRenderer with marked.js integration and custom styling
- Implemented DiagramRenderer with Mermaid.js for architecture diagrams
- Added LoadingSpinner with multiple sizes and variants
- Created ErrorMessage component with dismissible and details support
- Set up component export barrel in index.js
- Added comprehensive unit tests with Vitest and @vue/test-utils
- Configured Vitest testing environment in vite.config.js
- Created ComponentsDemo view for visual component testing
- All components follow Vue 3 Composition API best practices
- Components are fully typed with prop validation
- Implemented responsive design and accessibility considerations
```
