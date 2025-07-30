# Button.html - Macro de Botón

## 🎯 Propósito
Este archivo define una macro de Jinja2 llamada `button`. Su propósito es generar un componente de UI reutilizable (un "botón") que muestra estilos consistentes y permite personalización a través de parámetros. La macro encapsula las clases CSS de Tailwind y la lógica de atributos HTML para crear botones uniformes en toda la aplicación.

## 🏗️ Arquitectura
```mermaid
graph LR
    A[button.html] --> B[Macro Definition]
    B --> C[Parameter Handling]
    B --> D[CSS Classes]
    B --> E[HTML Attributes]
    C --> F[text]
    C --> G[id (optional)]
    C --> H[classes (optional)]
    C --> I[onclick (optional)]
```

## 📋 Responsabilidades
- **Macro definition**: Define la macro `button()` reutilizable
- **Parameter handling**: Acepta y maneja parámetros opcionales y requeridos
- **CSS styling**: Aplica clases Tailwind para apariencia consistente
- **Event handling**: Soporte para event handlers via atributo onclick
- **Accessibility**: Incluye estados de focus y hover apropiados

## 🔗 Dependencias
### Internas
- Ninguna - Es un componente base

### Externas
- **Jinja2** - Sintaxis de macros `{% macro %}` y `{%- endmacro %}`
- **Tailwind CSS** - Clases de utilidad para styling y estados

## 📊 Interfaces Públicas
### Macro `button()`
```jinja2
{% macro button(text, id="", classes="", onclick="") -%}
```

### Parámetros
- **text** (requerido): Texto que se muestra en el botón
- **id** (opcional): ID HTML del elemento button
- **classes** (opcional): Clases CSS adicionales a las por defecto
- **onclick** (opcional): Handler JavaScript para el evento click

### HTML Generado
```html
<button 
    id="example-id"
    class="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 additional-classes"
    onclick="myFunction()"
>
    Button Text
</button>
```

## 🔧 Configuración
### Estilos Por Defecto
- **Padding**: `px-6 py-3` - Espaciado horizontal y vertical
- **Background**: `bg-blue-600` - Color azul primary
- **Text**: `text-white font-semibold` - Texto blanco y semi-bold
- **Border**: `rounded-lg` - Bordes redondeados
- **Hover**: `hover:bg-blue-700` - Color más oscuro en hover
- **Transition**: `transition-colors` - Animación suave de colores
- **Focus**: `focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2` - Ring de enfoque

### Lógica Condicional
```jinja2
{% if id %}id="{{ id }}"{% endif %}
{% if onclick %}onclick="{{ onclick }}"{% endif %}
```

## 💡 Patrones de Uso
### Uso Básico
```html
<!-- Import del macro -->
{% from "components/button.html" import button %}

<!-- Botón simple -->
{{ button("Click Me") }}

<!-- Botón con ID -->
{{ button("Submit", id="submit-btn") }}

<!-- Botón con event handler -->
{{ button("Check Docs", onclick="checkDocs()") }}

<!-- Botón con clases adicionales -->
{{ button("Cancel", classes="bg-gray-500 hover:bg-gray-600") }}
```

### Uso Completo
```html
{{ button(
    text="Verificar Documentación", 
    id="check-docs-btn", 
    onclick="checkDocs()",
    classes="w-full md:w-auto"
) }}
```

## ⚠️ Consideraciones
### Limitaciones
- **Styling override**: Las clases adicionales se añaden al final, pueden no override estilos base
- **JavaScript inline**: Usa onclick inline, no event listeners modernos
- **Single purpose**: Solo genera elementos `<button>`, no enlaces o otros elementos

### Efectos Secundarios
- **CSS specificity**: Las clases base pueden ser difíciles de sobrescribir
- **HTML injection**: No hay sanitización de parámetros (confianza en el desarrollador)

### Accesibilidad
- **Focus ring**: Incluye ring de enfoque para navegación por teclado
- **Semantic HTML**: Usa elemento `<button>` semánticamente correcto
- **Hover states**: Estados visuales claros para interacción

## 🧪 Testing
### Casos de Prueba
1. **Solo texto**: `{{ button("Test") }}` - Debe generar botón básico
2. **Con ID**: `{{ button("Test", id="test-btn") }}` - Debe incluir atributo id
3. **Con onclick**: `{{ button("Test", onclick="alert('hi')") }}` - Debe ejecutar JavaScript
4. **Con clases**: `{{ button("Test", classes="extra-class") }}` - Debe incluir clases adicionales

### Validación HTML
```html
<!-- Resultado esperado -->
<button class="px-6 py-3 bg-blue-600 text-white...">
    Button Text
</button>
```

## 🔄 Flujo de Renderizado
```mermaid
graph TB
    A[Template Page] --> B[Import Macro]
    B --> C[Call button()]
    C --> D[Process Parameters]
    D --> E[Generate HTML]
    E --> F[Apply CSS Classes]
    F --> G[Add Event Handlers]
    G --> H[Output Button Element]
```

## 🚀 Mejoras Futuras
- **Variant support**: Diferentes variantes (primary, secondary, danger)
- **Size options**: Diferentes tamaños (small, medium, large)
- **Icon support**: Soporte para iconos antes/después del texto
- **Loading state**: Estado de carga con spinner
- **Disabled state**: Soporte para botones deshabilitados
- **Better override**: Sistema más flexible para override de estilos
