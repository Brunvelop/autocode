# Página: UI Designer (ui_designer.html)

## 🎯 Propósito
Este archivo define la página del "UI Designer" o "Visor de Documentación de Diseño". Su propósito principal es actuar como un contenedor o "cáscara" que hereda el layout general de la aplicación y carga el componente específico del visor de diseño y su script asociado.

## 🏗️ Arquitectura
Esta plantilla es un ejemplo claro de una "página contenedora". Extiende `base.html` y su única función es incluir el componente `components/ui_designer.html` dentro del bloque de contenido y cargar el script `js/components/ui-designer.js` en el bloque de JavaScript extra.

```mermaid
graph TD
    A[base.html] <|-- B(pages/ui_designer.html);
    
    subgraph "Contenido de la Página"
        B -- Incluye --> C[components/ui_designer.html];
        B -- Carga --> D[js/components/ui-designer.js];
    end
    
    C -- Es controlado por --> D;
```

## 📋 Responsabilidades
- **Heredar el layout base**: Asegura que la página del visor de diseño mantenga la consistencia visual con el resto de la aplicación.
- **Establecer el título de la página**: Define el título como "UI Designer".
- **Incluir el componente del visor**: Utiliza `{% include %}` para insertar la estructura HTML del visor de diseño.
- **Cargar el script específico**: Utiliza el bloque `{% block extra_js %}` para cargar el archivo JavaScript `ui-designer.js`, que es el que dota de funcionalidad al componente.

## 🔗 Dependencias
### Internas (Plantillas y Assets)
- `base.html`: Hereda la estructura principal de esta plantilla.
- `components/ui_designer.html`: Incluye el componente que define la UI del visor.
- `/static/js/components/ui-designer.js`: Carga el script que controla la lógica del visor.

### Externas
- Ninguna directamente, pero hereda las dependencias de `base.html` (como `mermaid.js`).

## 💡 Patrones de Uso
Esta plantilla es renderizada por el servidor de FastAPI cuando un usuario navega a la ruta `/ui-designer`. Su rol es ensamblar las piezas necesarias (layout, componente y script) para presentar una página funcional.

## ⚠️ Consideraciones
- **Separación de incumbencias**: Este archivo demuestra una buena práctica al mantener la plantilla de la página separada del componente que contiene. La página se preocupa del "dónde" y el "cómo se carga", mientras que el componente se preocupa del "qué se muestra".
- **Carga de Script con `defer`**: El script se carga con el atributo `defer` (heredado de la definición en el componente), lo que asegura que no bloqueará el renderizado del HTML.

## 🧪 Testing
Para verificar esta página:
1. Navegar a la ruta `/ui-designer` en la aplicación.
2. Verificar que el título de la pestaña del navegador es "UI Designer".
3. Comprobar que la página tiene la cabecera, pie de página y barra lateral de `base.html`.
4. Confirmar que el contenido principal de la página es el definido en `components/ui_designer.html`.
5. Usar las herramientas de desarrollador para asegurarse de que el script `/static/js/components/ui-designer.js` se ha cargado correctamente.
