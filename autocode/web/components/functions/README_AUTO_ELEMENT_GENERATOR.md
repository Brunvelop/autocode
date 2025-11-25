# Auto Element Generator

Generador automático de Custom Elements para funciones del registry, adaptado al concepto de elementos autocontenidos con HTML, Tailwind CSS y JavaScript funcional.

## 🎯 Concepto

El **auto-element-generator.js** transforma automáticamente las funciones registradas en el `FUNCTION_REGISTRY` en Custom Web Components listos para usar en cualquier frontend. Cada función se convierte en un elemento `<auto-{nombre}>` con:

- **UI básica con Tailwind**: Interfaz funcional sin estilos temáticos complejos
- **Autocontenido**: Funcional sin configuración adicional
- **Extensible**: Slots, atributos, eventos y métodos públicos para personalización
- **Genérico**: Lógica JavaScript automática sin código específico por función

## 🚀 Inicio Rápido

### 1. Incluir el Script

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <!-- Incluir el generador -->
    <script src="/components/functions/js/auto-element-generator.js"></script>
</body>
</html>
```

### 2. Usar los Elementos

```html
<!-- Elemento básico -->
<auto-add></auto-add>

<!-- Con auto-ejecución -->
<auto-hello_world auto-execute="true"></auto-hello_world>

<!-- Con slots personalizados -->
<auto-multiply>
    <div slot="header" class="bg-blue-500 text-white p-4">
        <h3>Calculadora Custom</h3>
    </div>
</auto-multiply>
```

## 📋 Características

### Generación Automática

Al cargar el script:
1. Fetch a `/functions/details` para obtener el registry
2. Por cada función, crea un Custom Element `<auto-{nombre}>`
3. Genera UI automática con:
   - Form para parámetros (inputs/selects según tipo)
   - Botón de ejecución
   - Área de resultado
   - Indicador de estado

### UI con Tailwind

Los elementos usan clases Tailwind básicas:

```html
<div class="flex flex-col gap-4 p-4 border border-gray-200 rounded-lg bg-white shadow-sm">
    <!-- Header con título y descripción -->
    <h3 class="text-xl font-semibold text-gray-800">...</h3>
    
    <!-- Form de parámetros -->
    <input class="p-2 border border-gray-300 rounded-lg...">
    
    <!-- Botón de ejecución -->
    <button class="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600...">
        Ejecutar
    </button>
    
    <!-- Resultado -->
    <div class="p-3 bg-green-100 border border-green-300 rounded-lg...">
        Resultado aquí
    </div>
</div>
```

### Validación Automática

- **Campos requeridos**: Validados antes de ejecutar
- **Tipos**: Inputs adaptados al tipo (number para int/float, text para string)
- **Choices**: Generados como `<select>` con opciones
- **Feedback visual**: Bordes rojos en campos inválidos

## 🔌 Extensibilidad

### Slots Disponibles

Personaliza partes del elemento sin perder funcionalidad:

```html
<auto-subtract>
    <!-- Header completo -->
    <div slot="header">
        <h2>Mi Header Custom</h2>
    </div>
    
    <!-- Solo título -->
    <h3 slot="title">Título Custom</h3>
    
    <!-- Botones extra en toolbar -->
    <button slot="toolbar">Info</button>
    
    <!-- UI de parámetros custom -->
    <div slot="params-ui">
        <input type="number" name="x" />
        <input type="number" name="y" />
    </div>
    
    <!-- Botón de ejecución custom -->
    <button slot="execute-button" onclick="this.closest('auto-subtract').execute()">
        Ejecutar Custom
    </button>
    
    <!-- Resultado custom -->
    <div slot="result-ui" id="myResult"></div>
    
    <!-- Status custom -->
    <div slot="status">Estado: Listo</div>
    
    <!-- Footer -->
    <div slot="footer">
        <small>© 2024</small>
    </div>
</auto-subtract>
```

### Atributos Observados

Controla el comportamiento del elemento:

```html
<!-- Auto-ejecutar al cargar -->
<auto-add auto-execute="true"></auto-add>

<!-- Ocultar resultado -->
<auto-multiply show-result="false"></auto-multiply>

<!-- Ocultar parámetros -->
<auto-divide show-params="false"></auto-divide>

<!-- Modo solo lectura -->
<auto-subtract readonly="true"></auto-subtract>
```

### Eventos Custom

Escucha eventos para lógica externa:

```javascript
const elem = document.querySelector('auto-add');

// Cuando se conecta al DOM
elem.addEventListener('function-connected', (e) => {
    console.log('Conectado:', e.detail.funcName);
});

// Antes de ejecutar (cancelable)
elem.addEventListener('before-execute', (e) => {
    console.log('Params:', e.detail.params);
    // e.preventDefault() para cancelar
});

// Después de ejecutar
elem.addEventListener('after-execute', (e) => {
    console.log('Resultado:', e.detail.result);
});

// Error en ejecución
elem.addEventListener('execute-error', (e) => {
    console.error('Error:', e.detail.error);
});

// Cambio en parámetros
elem.addEventListener('params-changed', (e) => {
    console.log('Nuevos params:', e.detail.params);
});
```

### Métodos Públicos

Control programático del elemento:

```javascript
const elem = document.querySelector('auto-multiply');

// Ejecutar la función
await elem.execute();

// Establecer parámetro
elem.setParam('x', 10);
elem.setParam('y', 5);

// Obtener parámetro
const x = elem.getParam('x'); // 10

// Obtener todos los parámetros
const params = elem.getParams(); // { x: 10, y: 5 }

// Obtener resultado
const result = elem.getResult(); // 50

// Validar
const isValid = elem.validate(); // true/false
```

## 📚 Ejemplos Completos

### Ejemplo 1: Integración Básica

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <h1>Mis Funciones</h1>
    
    <!-- Los elementos se generan automáticamente -->
    <auto-add></auto-add>
    <auto-subtract></auto-subtract>
    
    <script src="/components/functions/js/auto-element-generator.js"></script>
</body>
</html>
```

### Ejemplo 2: Control Programático

```html
<auto-multiply id="calc"></auto-multiply>

<script>
const calc = document.getElementById('calc');

// Establecer valores
calc.setParam('x', 7);
calc.setParam('y', 6);

// Ejecutar
await calc.execute();

// Obtener resultado
console.log(calc.getResult()); // 42
</script>
```

### Ejemplo 3: Workflow con Eventos

```html
<auto-divide id="workflow"></auto-divide>

<script>
const workflow = document.getElementById('workflow');

// Validar antes de ejecutar
workflow.addEventListener('before-execute', async (e) => {
    const params = e.detail.params;
    
    // Prevenir división por cero
    if (params.y === 0) {
        e.preventDefault();
        alert('No se puede dividir por cero');
    }
});

// Procesar resultado
workflow.addEventListener('after-execute', (e) => {
    const result = e.detail.result;
    console.log(`Resultado: ${result}`);
    
    // Lógica adicional
    if (result > 100) {
        alert('Resultado muy grande!');
    }
});

// Manejar errores
workflow.addEventListener('execute-error', (e) => {
    console.error('Error:', e.detail.error);
    // Mostrar notificación custom
});
</script>
```

### Ejemplo 4: UI Completamente Personalizada

```html
<auto-add>
    <!-- Header personalizado -->
    <div slot="header" class="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-6 rounded-t-lg">
        <h2 class="text-2xl font-bold">Calculadora Suma</h2>
        <p class="text-sm opacity-90">Suma dos números con estilo</p>
    </div>
    
    <!-- Parámetros personalizados -->
    <div slot="params-ui" class="space-y-4 p-4">
        <div>
            <label class="block text-sm font-bold mb-2">Primer Número</label>
            <input type="number" name="x" class="w-full p-3 border-2 border-blue-300 rounded-lg" />
        </div>
        <div>
            <label class="block text-sm font-bold mb-2">Segundo Número</label>
            <input type="number" name="y" class="w-full p-3 border-2 border-blue-300 rounded-lg" />
        </div>
    </div>
    
    <!-- Botón personalizado -->
    <button slot="execute-button" 
            class="w-full py-4 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700"
            onclick="this.closest('auto-add').execute()">
        🚀 CALCULAR SUMA
    </button>
    
    <!-- Resultado personalizado -->
    <div slot="result-ui" class="mt-4"></div>
    
    <!-- Footer personalizado -->
    <div slot="footer" class="text-center text-xs text-gray-500 mt-4">
        Calculadora v1.0
    </div>
</auto-add>
```

## 🔄 Diferencias con auto-function-generator.js

| Característica | auto-function-generator | auto-element-generator |
|----------------|------------------------|------------------------|
| **Estilos** | CSS inline con themes | Tailwind classes básicas |
| **Themes** | Soporte light/dark | No (extensión manual) |
| **DOM** | Shadow DOM | Light DOM |
| **Slots** | Menos slots | Más slots (header, title, toolbar, footer, etc.) |
| **Eventos** | Básicos | Extendidos (params-changed, etc.) |
| **Métodos** | Básicos | Más métodos (validate, getParams) |
| **Enfoque** | Funcionalidad + estética | Solo funcionalidad |

## 🎨 Personalización de Estilos

Los cambios estéticos se hacen mediante extensión, no en el código base:

### Opción 1: Clases Tailwind Custom

```html
<style>
    auto-add {
        display: block;
        /* Tus estilos custom */
    }
</style>

<auto-add class="shadow-2xl border-4 border-purple-500"></auto-add>
```

### Opción 2: Slots Personalizados

```html
<auto-add>
    <div slot="header" class="[tus-clases-tailwind]">
        <!-- Tu UI -->
    </div>
</auto-add>
```

### Opción 3: JavaScript

```javascript
const elem = document.querySelector('auto-add');

// Escuchar evento y modificar
elem.addEventListener('after-execute', (e) => {
    const container = elem.querySelector('[data-part="container"]');
    container.classList.add('bg-green-50');
});
```

## 🧪 Testing

Ver página de demostración en `/demo` para ejemplos interactivos de:

- Elementos básicos
- Auto-execute
- Readonly
- Slots personalizados
- Control programático
- Eventos custom
- Métodos públicos

## 📝 Notas

- **Tailwind requerido**: Los elementos asumen que Tailwind CSS está cargado en la página
- **Registry dinámico**: Los elementos se generan automáticamente del registry actual
- **Sin nuevos endpoints**: Usa solo `/functions/details` existente
- **Extensibilidad primero**: Diseñado para ser extendido, no modificado
- **Funcionalidad genérica**: Sin lógica específica por tipo de función

## 🔗 Ver También

- [auto-function-generator.js](./auto-function-generator.js) - Generador original con themes
- [Demo interactiva](/demo) - Ejemplos en vivo
- [Registry documentation](../../../interfaces/registry.py) - Cómo registrar funciones
