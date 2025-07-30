# Design Tokens

## 🎯 Propósito
Este archivo CSS establece el **sistema de diseño** para la interfaz de usuario de Autocode. Centraliza todas las decisiones de diseño fundamentales (colores, tipografía, espaciado, etc.) en forma de **CSS Custom Properties** (variables CSS). Su propósito es garantizar una apariencia visual consistente, facilitar el mantenimiento y permitir la tematización (como el modo oscuro).

## 🏗️ Arquitectura
La arquitectura se basa en el uso de variables CSS definidas dentro del pseudo-selector `:root`, lo que las hace disponibles globalmente en toda la aplicación.

La estructura del archivo se divide en secciones lógicas:
1.  **Colores**: Define la paleta de colores principal, incluyendo colores primarios, de estado (éxito, error) y una escala de grises (neutrales).
2.  **Tipografía**: Establece las familias de fuentes, una escala de tamaños de fuente, grosores y alturas de línea.
3.  **Espaciado**: Proporciona una escala de espaciado consistente para márgenes, paddings, etc.
4.  **Bordes y Sombras**: Define los radios de borde y diferentes niveles de sombras para la profundidad de la UI.
5.  **Transiciones y Z-index**: Estandariza las animaciones y el apilamiento de capas.
6.  **Componentes Específicos**: Define variables compuestas para componentes comunes como tarjetas (`--card-*`), botones (`--button-*`) e inputs (`--input-*`), utilizando los tokens base.
7.  **Layout**: Define variables para la estructura principal de la página, como el ancho del contenedor y de la barra lateral.
8.  **Soporte para Modo Oscuro**: Utiliza una media query `(prefers-color-scheme: dark)` para sobreescribir las variables de color y adaptar la UI a un tema oscuro.
9.  **Clases de Utilidad**: Incluye algunas clases de utilidad, como `.visually-hidden` para accesibilidad.

## 📋 Responsabilidades
- **Centralizar las Variables de Diseño**: Actúa como la única fuente de verdad para todos los valores de estilo.
- **Garantizar Consistencia Visual**: Asegura que todos los componentes de la UI utilicen los mismos valores de color, espaciado, etc.
- **Facilitar la Tematización**: Permite cambiar la apariencia de toda la aplicación (ej. a modo oscuro) simplemente sobreescribiendo un conjunto de variables.
- **Mejorar la Mantenibilidad**: Permite que un cambio de diseño (ej. cambiar el color primario) se realice en un solo lugar.

## 🔗 Dependencias
- Este archivo es una dependencia fundamental para `style.css` y cualquier otro archivo CSS del proyecto, ya que estos utilizarán las variables aquí definidas.

## 💡 Patrones de Uso
Las variables definidas en este archivo se utilizan en otros archivos CSS a través de la función `var()`.

**Ejemplo de uso en `style.css`:**
```css
.my-button {
  background-color: var(--color-primary);
  padding: var(--button-padding-y) var(--button-padding-x);
  border-radius: var(--button-radius);
  font-size: var(--font-size-base);
  transition: background-color var(--transition-fast);
}

.my-button:hover {
  background-color: var(--color-primary-hover);
}
```

## ⚠️ Consideraciones
- **Compatibilidad de Navegadores**: El uso de CSS Custom Properties es ampliamente soportado por los navegadores modernos, pero podría no funcionar en versiones muy antiguas (ej. Internet Explorer 11).
- **Organización**: Mantener una nomenclatura clara y una buena organización es clave para la escalabilidad del sistema de diseño.

## 🧪 Testing
- La "prueba" de este archivo es visual. Se debe verificar que todos los componentes de la UI se renderizan correctamente y que el cambio entre modo claro y oscuro funciona como se espera.
- Se pueden usar herramientas de "linting" de CSS para asegurar que no hay variables duplicadas o mal definidas.
