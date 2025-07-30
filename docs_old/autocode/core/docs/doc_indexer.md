# DocIndexer

## 🎯 Propósito
`DocIndexer` es responsable de escanear la estructura de la documentación modular (`docs/`) y generar un índice JSON estructurado. Este índice actúa como un "mapa" de toda la documentación, extrayendo el propósito de cada archivo y módulo para facilitar la búsqueda, la navegación y el análisis programático del contenido documental.

## 🏗️ Arquitectura
La clase `DocIndexer` opera sobre el directorio `docs/` del proyecto. Su lógica principal es recursiva:
1.  **Escaneo Recursivo**: Recorre la estructura de directorios dentro de `docs/`, identificando tres tipos de archivos clave: `_index.md` (raíz), `_module.md` (módulo/directorio), y `archivo.md` (documentación de archivo).
2.  **Extracción de Propósito**: Para cada archivo de documentación encontrado, utiliza una expresión regular para buscar y extraer la sección "Propósito". Esto permite obtener un resumen conciso de cada documento.
3.  **Construcción de Árbol**: Ensambla una estructura de datos anidada (un diccionario de Python) que refleja la jerarquía de directorios y archivos de la documentación.
4.  **Cálculo de Estadísticas**: Una vez construido el árbol, lo recorre para calcular métricas como el número total de archivos, módulos y propósitos encontrados.
5.  **Generación de JSON**: Combina la estructura, las estadísticas y metadatos (como la fecha de generación) en un único objeto JSON y lo guarda en el archivo de salida especificado.

## 📋 Responsabilidades
- **Escanear la estructura de `docs/`**: Recorre directorios y subdirectorios para encontrar todos los archivos `.md`.
- **Extraer el propósito**: Lee el contenido de cada archivo `.md` para encontrar y extraer su propósito principal.
- **Construir un índice jerárquico**: Crea un diccionario que representa la estructura de la documentación.
- **Calcular estadísticas**: Cuenta el número de módulos, archivos y otros artefactos documentales.
- **Generar un archivo JSON**: Escribe el índice completo en un archivo de salida, típicamente `.clinerules/docs_index.json`.
- **Resolver la ruta de salida**: Determina dónde guardar el índice, dando prioridad a los argumentos de la CLI sobre la configuración del proyecto.

## 🔗 Dependencias
### Internas
- `autocode.api.models.DocIndexConfig`: Para la configuración tipada del indexador.

### Externas
- `json`: Para serializar el índice a formato JSON.
- `re`: Para la extracción del propósito mediante expresiones regulares.
- `datetime`: Para añadir marcas de tiempo al índice generado.
- `pathlib`: Para la manipulación de rutas del sistema de archivos.

## 📊 Interfaces Públicas
### `class DocIndexer`
- `__init__(self, project_root: Path, config: DocIndexConfig, output_override: Optional[str] = None)`: Constructor.
- `generate_index(self) -> Path`: Método principal que ejecuta el proceso de escaneo y genera el archivo de índice JSON. Devuelve la ruta al archivo generado.
- `extract_purpose(self, content: str) -> str`: Extrae la sección de propósito de un texto.
- `get_index_status(self) -> Dict[str, Any]`: Devuelve metadatos sobre el índice existente (si lo hay), como su fecha de última generación y estadísticas.

## 💡 Patrones de Uso
**Generar el índice de documentación desde un script:**
```python
from pathlib import Path
from autocode.core.docs.doc_indexer import DocIndexer
from autocode.api.models import DocIndexConfig

project_path = Path('.')
# Cargar o definir la configuración
config = DocIndexConfig(output_path=".clinerules/docs_index.json")

indexer = DocIndexer(project_path, config)
try:
    generated_file = indexer.generate_index()
    print(f"Índice de documentación generado en: {generated_file}")
except FileNotFoundError as e:
    print(f"Error: {e}")
```

## ⚠️ Consideraciones
- La calidad de la extracción del propósito depende de que los archivos de documentación sigan la plantilla esperada (una sección `## 🎯 Propósito`).
- El rendimiento puede verse afectado en proyectos con una cantidad masiva de archivos de documentación debido a las operaciones de lectura de archivos.
- El indexador no valida el contenido de la documentación más allá de buscar la sección de propósito.

## 🧪 Testing
- Probar con una estructura de `docs/` que incluya directorios anidados, `_index.md`, `_module.md` y archivos de documentación individuales.
- Verificar que la extracción de propósito funciona con diferentes formatos y espaciados.
- Probar el caso en que el directorio `docs/` no existe.
- Validar que el archivo JSON de salida es sintácticamente correcto y contiene la estructura y estadísticas esperadas.
