# Hoja de Estilos Principal

## 🎯 Propósito
Este archivo CSS define la apariencia visual y el layout de todos los componentes del dashboard de monitoreo de `autocode`. Su responsabilidad es tomar los valores del sistema de diseño (definidos en `design-tokens.css`) y aplicarlos para construir una interfaz de usuario cohesiva, profesional y responsiva.

## 🏗️ Arquitectura
La arquitectura de la hoja de estilos sigue un enfoque de **componentes**, donde el CSS se organiza en bloques que corresponden a los diferentes elementos de la UI.

1.  **Importación de Design Tokens**: La primera línea, `@import url('./design-tokens.css');`, importa todas las variables CSS, asegurando que estén disponibles para ser usadas en este archivo.
2.  **Reset y Estilos Base**: Se aplica un reseteo básico y se definen los estilos globales para el `<body>`, como la fuente y el color de fondo, utilizando las variables de los design tokens.
3.  **Estilos de Componentes**: El resto del archivo está dividido en secciones que estilizan componentes específicos de la UI:
    -   `.container`, `.header`, `.footer`: Estilos para el layout principal.
    -   `.card`, `.check-card`: Estilos para los contenedores de contenido.
    -   `.status-indicator`: Estilos para los indicadores de estado (éxito, error, etc.).
    -   `.btn-run`: Estilos para los botones.
    -   `.config-card`: Estilos para el formulario de configuración.
    -   `.ui-designer`: Estilos para la sección del diseñador de UI.
4.  **Diseño Responsivo**: Utiliza una **media query** (`@media (max-width: 768px)`) para aplicar estilos específicos en pantallas más pequeñas, asegurando que la interfaz sea usable en dispositivos móviles.
5.  **Estilos de Utilidad**: Incluye clases auxiliares como `.text-success` o `.hidden` para aplicar estilos comunes de forma rápida.
6.  **Estilos Mejorados para Mermaid**: Proporciona estilos personalizados para los diagramas generados por Mermaid.js, asegurando que su apariencia se integre con el resto del diseño del dashboard.

## 📋 Responsabilidades
- **Aplicar el Sistema de Diseño**: Utiliza las variables de `design-tokens.css` (ej. `var(--color-primary)`) para estilizar los elementos.
- **Definir el Layout**: Controla la disposición de los elementos en la página usando Flexbox y Grid.
- **Estilizar Componentes**: Proporciona los estilos visuales para cada componente de la UI (tarjetas, botones, inputs, etc.).
- **Asegurar la Responsividad**: Adapta el layout para diferentes tamaños de pantalla.
- **Proporcionar Feedback Visual**: Define los estilos para los diferentes estados (hover, active, disabled) y para los indicadores de estado.

## 🔗 Dependencias
### Internas
- `web/static/design-tokens.css`: Es una dependencia crítica, ya que este archivo consume las variables definidas allí.
- `web/templates/index.html`: Los selectores de este archivo CSS se corresponden directamente con las clases y los `id` definidos en la plantilla HTML.

## 💡 Patrones de Uso
Este archivo es cargado por el navegador a través de una etiqueta `<link>` en el `<head>` de `index.html`. No es utilizado directamente por ningún componente del backend.

## ⚠️ Consideraciones
- **Especificidad y Organización**: Mantener una buena organización y una especificidad de CSS controlada es clave para evitar conflictos de estilos a medida que la aplicación crece.
- **Acoplamiento con el HTML**: Al igual que `app.js`, este archivo está fuertemente acoplado a la estructura y las clases del HTML. Cambios en el HTML pueden requerir cambios aquí.

## 🧪 Testing
- El testing es principalmente visual. Se debe verificar en diferentes navegadores y tamaños de pantalla que:
    -   El layout no se rompe.
    -   Los colores, fuentes y espaciados son consistentes.
    -   Los estados de hover y otros feedbacks visuales funcionan correctamente.
- Se pueden usar herramientas de "snapshot testing" visual para detectar regresiones no deseadas en la UI.
