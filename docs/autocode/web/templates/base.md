# Base.html - Template Base

## 🎯 Propósito
Este archivo es la plantilla maestra o "layout" principal para toda la interfaz web de autocode. Su propósito es definir la estructura HTML común a todas las páginas, incluyendo la cabecera, el pie de página, la barra de navegación lateral y las áreas de contenido dinámico. Garantiza una apariencia y estructura consistentes en toda la aplicación.

## 🏗️ Arquitectura
```mermaid
graph TB
    A[base.html] --> B[HTML Structure]
    A --> C[Jinja2 Blocks]
    B --> D[Head Section]
    B --> E[Body Layout]
    C --> F[{% block title %}]
    C --> G[{% block content %}]
    C --> H[{% block scripts %}]
    E --> I[Navigation]
    E --> J[Main Content]
    E --> K[Footer]
```

## 📋 Responsabilidades
- **Estructura HTML**: Define la estructura básica de todas las páginas
- **Meta información**: Configuración de viewport, charset y título dinámico
- **Assets externos**: Carga de Tailwind CSS via CDN
- **Layout responsive**: Estructura flexible para desktop y móvil
- **Navegación común**: Inclusión de componente de navegación
- **Áreas extensibles**: Bloques de Jinja2 para contenido específico

## 🔗 Dependencias
### Internas
- `components/nav.html` - Componente de navegación principal

### Externas
- **Tailwind CSS** - Framework CSS via CDN (https://cdn.tailwindcss.com)
- **Jinja2** - Motor de plantillas para herencia y bloques

## 📊 Interfaces Públicas
### Bloques de Jinja2
- `{% block title %}` - Título específico de cada página
- `{% block content %}` - Contenido principal de cada página
- `{% block scripts %}` - Scripts específicos de cada página

### Estructura HTML
```html
<!DOCTYPE html>
<html lang="es">
  <head>
    <!-- Meta tags y assets -->
  </head>
  <body class="bg-gray-50 min-h-screen flex flex-col">
    <nav><!-- Navegación --></nav>
    <main><!-- Contenido dinámico --></main>
    <footer><!-- Pie de página --></footer>
  </body>
</html>
```

## 🔧 Configuración
### Meta Tags
- **charset**: UTF-8 para soporte completo de caracteres
- **viewport**: Configuración responsive para móviles
- **lang**: Español como idioma principal

### CSS Framework
- **Tailwind CSS**: Cargado via CDN para prototipado rápido
- **Layout classes**: Flexbox para estructura de página completa
- **Responsive**: Classes que se adaptan a diferentes tamaños

### Estructura de Layout
- **Header**: Barra de navegación fija
- **Main**: Área de contenido principal con padding y margin
- **Footer**: Pie de página con información de copyright

## 💡 Patrones de Uso
### Herencia de Template
```html
<!-- En páginas hijas -->
{% extends "base.html" %}

{% block title %}Mi Página{% endblock %}

{% block content %}
<div class="container mx-auto">
  <!-- Contenido específico -->
</div>
{% endblock %}

{% block scripts %}
<script src="/static/app.js"></script>
{% endblock %}
```

### Estructura de Clases CSS
```html
<!-- Layout principal -->
<body class="bg-gray-50 min-h-screen flex flex-col">
  <!-- Navegación -->
  <nav>{% include 'components/nav.html' %}</nav>
  
  <!-- Contenido principal -->
  <main class="flex-1 container mx-auto px-4 py-8">
    {% block content %}{% endblock %}
  </main>
  
  <!-- Footer pegado al bottom -->
  <footer class="bg-gray-100 py-4 mt-auto">
</body>
```

## ⚠️ Consideraciones
### Responsive Design
- **Mobile-first**: Clases base para móvil, responsive utilities para desktop
- **Flexbox layout**: Estructura flexible que se adapta al contenido
- **Container**: Contenedor responsive que se adapta al ancho de pantalla

### Performance
- **CDN loading**: Tailwind CSS cargado desde CDN para rapidez
- **Minimal HTML**: Estructura HTML mínima y semántica
- **Progressive enhancement**: Funciona sin JavaScript

### Accesibilidad
- **Lang attribute**: Especifica idioma para screen readers
- **Semantic structure**: nav, main, footer semánticamente correctos
- **Focus styles**: Tailwind incluye estilos de focus por defecto

## 🧪 Testing
### Validación HTML
- **DOCTYPE**: HTML5 válido
- **Meta tags**: Viewport y charset correctos
- **Semantic structure**: Elementos HTML semánticamente apropiados

### Responsive Testing
- **Mobile**: Verificar en dispositivos móviles
- **Desktop**: Comprobar en pantallas grandes
- **Tablet**: Validar en tamaños intermedios

## 🔄 Flujo de Herencia
```mermaid
graph TB
    A[base.html] --> B[home.html]
    A --> C[docs-check.html]
    B --> D[Renders with title "Inicio"]
    C --> E[Renders with title "Docs Check"]
    D --> F[Includes home content]
    E --> G[Includes docs-check content + scripts]
```

## 🚀 Mejoras Futuras
- **Dark mode**: Soporte para tema oscuro
- **Meta tags avanzados**: Open Graph, Twitter Cards
- **Critical CSS**: CSS inline para above-the-fold content
- **Service Worker**: PWA capabilities
- **Error boundaries**: Manejo de errores de renderizado
