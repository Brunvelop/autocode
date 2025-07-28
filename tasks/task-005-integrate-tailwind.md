# Task 005: Integrar Tailwind CSS via CDN y Simplificar Estilos

## Contexto del Proyecto
Este proyecto, autocode, es una herramienta de monitoreo automático con interfaz web que utiliza FastAPI como backend y Jinja2/CSS personalizado para el frontend. La aplicación incluye un dashboard de monitoreo en tiempo real con componentes de UI modulares. El objetivo es simplificar el sistema de estilos reemplazando archivos CSS personalizados con Tailwind CSS via CDN, manteniendo la funcionalidad visual actual pero reduciendo la complejidad del código.

## Estado Actual del Sistema de Estilos

### Estructura de Archivos CSS Actuales
```
autocode/web/static/
├── design-tokens.css      # Variables CSS personalizadas (colores, espaciado, tipografía)
├── style.css             # Estilos principales de la aplicación
└── css/                  # Carpeta para componentes CSS (puede estar vacía o con subcarpetas mínimas)
    └── components/       # Subcarpeta para estilos de componentes específicos
```

### Archivos CSS Existentes

#### design-tokens.css (Variables del Sistema de Diseño)
```css
:root {
  /* Colors */
  --primary-color: #007bff;
  --secondary-color: #6c757d;
  --success-color: #28a745;
  --danger-color: #dc3545;
  --warning-color: #ffc107;
  --info-color: #17a2b8;
  --light-color: #f8f9fa;
  --dark-color: #343a40;
  
  /* Typography */
  --font-family-base: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-size-base: 1rem;
  --line-height-base: 1.5;
  
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 3rem;
  
  /* Border radius */
  --border-radius-sm: 0.25rem;
  --border-radius-md: 0.375rem;
  --border-radius-lg: 0.5rem;
}
```

#### style.css (Estilos Principales)
Contiene estilos para:
- Layout general (.container, .header, .sidebar, .main-content)
- Componentes de UI (.check-card, .stat-card, .status-indicator)
- Navegación (.nav-link, .active)
- Formularios (inputs, buttons, textareas)
- Estados de componentes (.success, .error, .warning)
- Utilidades (.loading-message, .save-status)

### Estructura de Templates HTML Actuales
```
autocode/web/templates/
├── base.html                    # Template base con <head>, navegación y estructura general
├── index.html                   # Dashboard principal (deprecated, usa pages/dashboard.html)
├── components/                  # Componentes reutilizables (macros Jinja2)
│   ├── check_card.html         # Tarjeta para mostrar estado de verificaciones
│   ├── stat_card.html          # Tarjeta simple para estadísticas
│   ├── header.html             # Cabecera de la aplicación
│   ├── footer.html             # Pie de página
│   └── design.html             # Componente para el visor de diagramas
└── pages/                      # Páginas completas
    ├── dashboard.html          # Dashboard principal
    ├── config.html             # Página de configuración
    └── design.html             # Página del UI Designer
```

### Cómo se Cargan los Estilos Actualmente
En `base.html`:
```html
<head>
    <link rel="stylesheet" href="{{ url_for('static', path='design-tokens.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', path='style.css') }}">
</head>
```

## Objetivo de la Refactorización
Reemplazar el sistema de CSS personalizado con Tailwind CSS via CDN para:
1. **Simplicidad**: Eliminar archivos CSS personalizados y usar utility classes
2. **Consistencia**: Aprovechar el sistema de diseño cohesivo de Tailwind
3. **Mantenibilidad**: Reducir código CSS personalizado y usar clases estándar
4. **Sin build process**: Usar CDN para evitar configuración adicional

## Instrucciones Paso a Paso

### 1. Integrar Tailwind CSS via CDN
Modificar `autocode/web/templates/base.html` para incluir Tailwind:

```html
<!-- Reemplazar las líneas de CSS existentes -->
<!-- ANTES: -->
<link rel="stylesheet" href="{{ url_for('static', path='design-tokens.css') }}">
<link rel="stylesheet" href="{{ url_for('static', path='style.css') }}">

<!-- DESPUÉS: -->
<script src="https://cdn.tailwindcss.com"></script>
<script>
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
</script>
```

### 2. Mapear Estilos Actuales a Clases Tailwind

#### Layout y Estructura
```css
/* CSS Actual → Clases Tailwind */
.container → max-w-7xl mx-auto px-4
.header → bg-white shadow-sm border-b
.sidebar → bg-gray-50 border-r min-h-screen w-64
.main-content → flex-1 p-6
```

#### Componentes de Estado
```css
/* Estados de verificación */
.status-indicator.success → w-3 h-3 bg-green-500 rounded-full
.status-indicator.error → w-3 h-3 bg-red-500 rounded-full
.status-indicator.warning → w-3 h-3 bg-yellow-500 rounded-full

/* Tarjetas */
.check-card → bg-white rounded-lg shadow-sm border p-6
.check-card.success → border-green-200
.check-card.error → border-red-200
.stat-card → bg-white rounded-lg shadow-sm border p-4
```

#### Botones y Formularios
```css
/* Botones */
.btn-primary → bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md
.btn-secondary → bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md
.btn-success → bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md

/* Inputs */
input[type="text"] → border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500
```

### 3. Actualizar Templates con Clases Tailwind

#### 3.1 Actualizar base.html (Layout Principal)
```html
<!-- Estructura del layout -->
<body class="bg-gray-50 font-sans">
  <div class="flex min-h-screen">
    <!-- Sidebar -->
    <nav class="bg-white shadow-sm border-r w-64 fixed h-full">
      <div class="p-6">
        <h1 class="text-xl font-bold text-gray-900">Autocode</h1>
      </div>
      <ul class="mt-6">
        <li><a href="/dashboard" class="block px-6 py-3 text-gray-700 hover:bg-gray-50 hover:text-blue-600">Dashboard</a></li>
        <li><a href="/config" class="block px-6 py-3 text-gray-700 hover:bg-gray-50 hover:text-blue-600">Configuration</a></li>
        <li><a href="/design" class="block px-6 py-3 text-gray-700 hover:bg-gray-50 hover:text-blue-600">UI Designer</a></li>
      </ul>
    </nav>
    
    <!-- Main Content -->
    <main class="flex-1 ml-64">
      {% block content %}{% endblock %}
    </main>
  </div>
</body>
```

#### 3.2 Actualizar components/check_card.html
```html
<div class="bg-white rounded-lg shadow-sm border p-6 {{ 'border-green-200' if status == 'success' else 'border-red-200' if status == 'error' else 'border-yellow-200' }}">
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold text-gray-900">{{ title }}</h3>
    <div class="flex items-center space-x-2">
      <div class="w-3 h-3 rounded-full {{ 'bg-green-500' if status == 'success' else 'bg-red-500' if status == 'error' else 'bg-yellow-500' }}"></div>
      <span class="text-sm font-medium {{ 'text-green-700' if status == 'success' else 'text-red-700' if status == 'error' else 'text-yellow-700' }}">{{ status_text }}</span>
    </div>
  </div>
  
  <p class="text-gray-600 mb-4">{{ message }}</p>
  
  <div class="flex items-center justify-between">
    <span class="text-xs text-gray-500">{{ timestamp }}</span>
    <button onclick="{{ action }}" class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-md text-sm">
      Run Now
    </button>
  </div>
</div>
```

#### 3.3 Actualizar components/stat_card.html
```html
<div class="bg-white rounded-lg shadow-sm border p-4">
  <div class="text-center">
    <div class="text-2xl font-bold text-gray-900">{{ value }}</div>
    <div class="text-sm text-gray-500">{{ label }}</div>
  </div>
</div>
```

#### 3.4 Actualizar pages/dashboard.html
```html
{% extends "base.html" %}

{% block content %}
<div class="p-6">
  <!-- Header -->
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-900">Autocode Dashboard</h1>
    <p class="mt-2 text-gray-600">Monitor your code quality and automation tasks</p>
  </div>
  
  <!-- Stats Grid -->
  <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
    <div class="bg-white rounded-lg shadow-sm border p-4">
      <div class="flex items-center">
        <div class="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
        <span class="text-sm font-medium text-gray-900">Daemon Status</span>
      </div>
      <div class="mt-2 text-lg font-semibold" id="daemon-text">Running</div>
    </div>
    
    <div class="bg-white rounded-lg shadow-sm border p-4">
      <div class="text-center">
        <div class="text-2xl font-bold text-gray-900" id="uptime">--</div>
        <div class="text-sm text-gray-500">Uptime</div>
      </div>
    </div>
    
    <div class="bg-white rounded-lg shadow-sm border p-4">
      <div class="text-center">
        <div class="text-2xl font-bold text-gray-900" id="total-checks">--</div>
        <div class="text-sm text-gray-500">Total Checks</div>
      </div>
    </div>
    
    <div class="bg-white rounded-lg shadow-sm border p-4">
      <div class="text-center">
        <div class="text-lg font-semibold text-gray-900" id="last-check">--</div>
        <div class="text-sm text-gray-500">Last Check</div>
      </div>
    </div>
  </div>
  
  <!-- Checks Grid -->
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    {% for check_name, check_data in checks.items() %}
      {% include "components/check_card.html" %}
    {% endfor %}
  </div>
</div>
{% endblock %}
```

### 4. Eliminar Archivos CSS Obsoletos
Después de aplicar Tailwind a todos los templates:

```bash
# Eliminar archivos CSS personalizados
rm autocode/web/static/design-tokens.css
rm autocode/web/static/style.css
rm -rf autocode/web/static/css/  # Si existe y está vacía o con archivos obsoletos
```

### 5. Actualizar Referencias de Modo Oscuro (Opcional)
Si se desea soporte para modo oscuro, añadir al config de Tailwind:
```javascript
tailwind.config = {
  darkMode: 'class',
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
```

Y usar clases como `dark:bg-gray-900` en los templates.

## Criterios de Verificación

### Verificación Visual
1. **Iniciación del servidor**: `uv run autocode daemon`
2. **Acceso al dashboard**: Navegar a `http://localhost:8080/dashboard`
3. **Comparación visual**: La UI debe verse **idéntica o mejor** que la versión anterior
4. **Responsive**: Verificar que funciona en mobile y desktop
5. **Estados**: Probar diferentes estados de checks (success, error, warning)

### Verificación de Funcionalidad
```bash
# Verificar que no hay errores 404 en archivos CSS
# Abrir herramientas de desarrollador → Network → Recargar página
# No debe haber errores de carga de design-tokens.css o style.css

# Verificar que Tailwind se carga correctamente
# En consola del navegador:
# document.querySelector('script[src*="tailwindcss"]') 
# Debe retornar el elemento script
```

### Tests de Navegación
1. **Dashboard** (`/dashboard`): Tarjetas de estado, estadísticas, botones funcionales
2. **Configuración** (`/config`): Formularios con estilos correctos
3. **UI Designer** (`/design`): Componentes de visualización
4. **Navegación**: Links del sidebar deben resaltar correctamente

### Verificación de Responsividad
```css
/* Probar en diferentes tamaños */
- Desktop (1200px+): Grid de 4 columnas para stats, 3 para checks
- Tablet (768px-1200px): Grid adaptable
- Mobile (<768px): Columna única, sidebar colapsable
```

### Verificación de Performance
- **Tiempo de carga**: Tailwind CDN debe cargar rápido
- **Sin flash de contenido sin estilos**: Los estilos deben aplicarse inmediatamente
- **Tamaño**: El bundle de Tailwind CDN es más grande que CSS personalizado, pero aceptable para simplicidad

## Consideraciones Importantes

### Mantenimiento del CSS Personalizado Mínimo
Si algunos estilos específicos no se pueden replicar fácilmente con Tailwind, mantener un pequeño `<style>` inline en `base.html`:
```html
<style>
  /* Solo estilos muy específicos que no tienen equivalente directo en Tailwind */
  .custom-animation {
    animation: spin 1s linear infinite;
  }
</style>
```

### Colores y Branding
Los colores definidos en el config de Tailwind deben coincidir con los actuales:
- Primary: #007bff (azul)
- Success: #28a745 (verde)
- Danger: #dc3545 (rojo)
- Warning: #ffc107 (amarillo)

### Accesibilidad
Mantener contraste y accesibilidad:
- Usar `focus:outline-none focus:ring-2 focus:ring-blue-500` para elementos interactivos
- Mantener colores con contraste adecuado
- Preservar estructura semántica HTML

## Template de Commit Message
```
feat(ui): integrate Tailwind CSS via CDN and remove custom styles

- Added Tailwind CSS via CDN to base.html with custom color configuration
- Converted all templates to use Tailwind utility classes
- Updated layout components (header, sidebar, main content) with Tailwind classes
- Replaced custom CSS components (.check-card, .stat-card, etc.) with Tailwind equivalents
- Updated form elements and buttons to use Tailwind styling
- Removed design-tokens.css and style.css files
- Eliminated css/ directory and all custom stylesheets
- Maintained visual consistency and functionality
- Preserved responsive design and component states
- Added proper focus states and accessibility features
```

## Notas para el Programador

### Debugging
Si algo no se ve correctamente:
1. Verificar que el script de Tailwind se carga en herramientas de desarrollador
2. Comprobar que las clases Tailwind están siendo aplicadas (inspeccionar elemento)
3. Verificar que no hay conflictos con CSS residual

### Extensibilidad
Para añadir nuevos componentes:
1. Usar clases de Tailwind estándar
2. Seguir el patrón de colores definido en el config
3. Mantener consistencia con el spacing (p-4, p-6, etc.)
4. Usar el sistema de grid de Tailwind para layouts
