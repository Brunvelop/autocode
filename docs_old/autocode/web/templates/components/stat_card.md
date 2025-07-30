# Componente: Stat Card (stat_card.html)

## 🎯 Propósito
Este archivo define una macro de Jinja2, `stat_card`, extremadamente simple y reutilizable. Su único propósito es generar un pequeño componente de UI para mostrar una estadística individual, que consiste en una etiqueta (label) y un valor.

## 🏗️ Arquitectura
El componente es una macro de Jinja2 que toma un objeto de configuración para renderizar un `<div>` con dos `<span>`. Uno para la etiqueta estática y otro para el valor dinámico, que tiene un ID para ser actualizado por JavaScript.

```mermaid
graph TD
    A[Plantilla Padre] -- Llama a la macro --> B(stat_card macro);
    B -- Recibe parámetro --> C{config: {label, id, default_value}};
    B -- Genera HTML --> D[div.stat];
    D --> E[span.stat-label];
    D --> F[span.stat-value];
    G[app.js] -- Actualiza el contenido de --> F;
```

## 📋 Responsabilidades
- **Generar un par etiqueta-valor**: Crea la estructura HTML para una estadística.
- **Ser configurable**: Permite definir la etiqueta, el ID del valor y un valor por defecto a través de un diccionario de configuración.
- **Proporcionar un hook para JavaScript**: Asigna un ID al `<span>` del valor para que pueda ser actualizado dinámicamente.

## 🔗 Dependencias
### Internas
- Ninguna. Es una macro autocontenida.

### Externas
- **JavaScript (`app.js` o similar)**: El componente depende de JavaScript para actualizar el valor de la estadística después de la carga inicial.

## 📊 Interfaces Públicas (Parámetros de la Macro)
- `config` (dict): Un diccionario de Python que debe contener las siguientes claves:
    - `label` (string): El texto que se mostrará como etiqueta de la estadística.
    - `id` (string): El ID que se asignará al `<span>` del valor para su manipulación con JS.
    - `default_value` (string, opcional): El valor inicial que se mostrará. Por defecto es `"--"`.

## 💡 Patrones de Uso
Esta macro es ideal para construir listas o rejillas de estadísticas en un dashboard.

```jinja
{# 1. Importar la macro #}
{% from 'components/stat_card.html' import stat_card %}

{# 2. Definir la configuración en la lógica del backend (Python/FastAPI) #}
stats_config = [
    {'label': 'Archivos Analizados', 'id': 'files-analyzed-stat', 'default_value': '0'},
    {'label': 'Errores Encontrados', 'id': 'errors-found-stat', 'default_value': '0'}
]

{# 3. Iterar y renderizar en la plantilla #}
<div class="stats-grid">
    {% for stat_conf in stats_config %}
        {{ stat_card(stat_conf) }}
    {% endfor %}
</div>
```

## ⚠️ Consideraciones
- **Atomicidad**: Este es un componente atómico, diseñado para ser una pieza de construcción de componentes más grandes.
- **Dependencia de JS**: Al igual que otros componentes de este proyecto, su valor real proviene de las actualizaciones dinámicas realizadas por JavaScript.

## 🧪 Testing
Para verificar este componente:
1. Cargar una página que lo utilice.
2. Verificar que la etiqueta se renderiza correctamente con el texto proporcionado.
3. Comprobar que el valor inicial (o el por defecto `"--"`) se muestra.
4. Inspeccionar el DOM para asegurarse de que el `<span>` del valor tiene el ID correcto.
5. Observar si el JavaScript correspondiente actualiza el valor correctamente después de obtener datos de la API.
