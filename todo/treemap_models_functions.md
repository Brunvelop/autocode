# fix(frontend): treemap no muestra funciones de archivos models

## Descripción del problema

En el treemap del code-dashboard (`autocode/web/elements/code-dashboard/treemap-view.js`), las funciones definidas en archivos `models.py` (y posiblemente otros archivos de modelos) no aparecen visualizadas, aunque sí deberían hacerlo.

## Comportamiento esperado

Todos los archivos del proyecto, incluidos los `models.py`, deberían mostrar sus funciones/clases como nodos en el treemap.

## Comportamiento actual

Los archivos `models.py` aparecen en el treemap pero sin mostrar sus funciones/clases internas (o no aparecen en absoluto).

## Posibles causas a investigar

- El parser de Python (`python_parser.py`) puede no estar extrayendo correctamente las definiciones de clases/funciones de archivos que son principalmente modelos Pydantic (herencia, `Field`, etc.)
- El treemap puede estar filtrando nodos por algún criterio de tamaño o tipo que excluye estos archivos
- La API que alimenta el treemap puede no estar incluyendo los símbolos de `models.py` en su respuesta
- El componente `treemap-view.js` puede tener lógica de filtrado que descarta ciertos patrones de nombre de archivo

## Archivos relevantes

- `autocode/web/elements/code-dashboard/treemap-view.js` — componente de visualización
- `autocode/core/code/parsers/python_parser.py` — parser que extrae símbolos
- `autocode/core/code/structure.py` — construye la estructura del árbol
- `autocode/interfaces/api.py` — endpoint que sirve los datos al frontend
