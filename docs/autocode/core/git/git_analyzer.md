# GitAnalyzer

## 🎯 Propósito
`GitAnalyzer` es un componente diseñado para analizar el estado de un repositorio de Git. Su función principal es obtener una lista detallada de todos los cambios en los archivos (modificados, añadidos, eliminados, etc.), incluyendo los diffs específicos, y estructurar esta información en un formato JSON. Este resultado es ideal para alimentar herramientas automáticas, como generadores de mensajes de commit basados en IA.

## 🏗️ Arquitectura
La clase `GitAnalyzer` interactúa directamente con la línea de comandos de Git a través del módulo `subprocess` de Python. No depende de ninguna biblioteca de Git de terceros, lo que la hace ligera y universal.

El flujo de trabajo es el siguiente:
1.  **Obtener Estado General**: Ejecuta `git status --porcelain` para obtener una lista rápida y fiable de todos los archivos que han cambiado.
2.  **Manejar Archivos Ignorados**: Carga los patrones del archivo `.gitignore` para filtrar los archivos que no deben ser analizados.
3.  **Obtener Diffs Detallados**: Para cada archivo modificado, ejecuta `git diff` para obtener el contenido exacto de los cambios (líneas añadidas/eliminadas).
4.  **Calcular Estadísticas**: Para cada diff, extrae el número de adiciones y eliminaciones.
5.  **Estructurar Datos**: Agrupa toda la información (nombre de archivo, estado, si está "staged", estadísticas y diff) en una lista de objetos `FileChange`.
6.  **Generar Resumen**: Procesa la lista de cambios para crear un resumen del estado del repositorio (`GitStatus`).
7.  **Exportar a JSON**: Combina toda la información en un único diccionario que puede ser fácilmente serializado a JSON.

## 📋 Responsabilidades
- **Ejecutar comandos de Git**: Proporciona un wrapper seguro para ejecutar comandos de Git y capturar su salida.
- **Analizar el estado de los archivos**: Determina si los archivos están modificados, añadidos, eliminados, renombrados o sin seguimiento.
- **Extraer diffs**: Obtiene el diff detallado tanto para cambios "staged" (en el índice) como "unstaged" (en el árbol de trabajo).
- **Respetar `.gitignore`**: Filtra los archivos que están explícitamente ignorados en el repositorio.
- **Estructurar la información**: Convierte la salida de texto plano de Git en objetos de Python bien definidos (`FileChange`, `GitStatus`).
- **Serializar a JSON**: Guarda el análisis completo en un archivo JSON para su uso por otras herramientas.

## 🔗 Dependencias
### Internas
- Ninguna.

### Externas
- `subprocess`: Para ejecutar comandos de Git.
- `json`: Para serializar los resultados.
- `fnmatch`: Para comparar nombres de archivo con los patrones de `.gitignore`.
- `pathlib`: Para la manipulación de rutas.

## 📊 Interfaces Públicas
### `class GitAnalyzer`
- `__init__(self, project_root: Path)`: Constructor.
- `analyze_changes(self) -> Dict`: Método principal que realiza el análisis completo y devuelve un diccionario con los resultados.
- `get_all_changes(self) -> List[FileChange]`: Devuelve una lista de todos los cambios en los archivos.
- `get_repository_status(self, changes: List[FileChange]) -> GitStatus`: Devuelve un resumen del estado del repositorio.
- `save_changes_to_file(self, output_path: Path) -> Dict`: Analiza los cambios y los guarda directamente en un archivo JSON.

### `FileChange(NamedTuple)` y `GitStatus(NamedTuple)`
- Clases de datos para representar la información de manera estructurada.

## 💡 Patrones de Uso
**Analizar un repositorio y mostrar un resumen de los cambios:**
```python
from pathlib import Path
from autocode.core.git.git_analyzer import GitAnalyzer

project_path = Path('.')
analyzer = GitAnalyzer(project_path)

analysis_result = analyzer.analyze_changes()

status = analysis_result['repository_status']
print(f"Resumen de cambios:")
print(f"- {status['modified']} modificados")
print(f"- {status['added']} añadidos")
print(f"- {status['deleted']} eliminados")

print("\nArchivos modificados:")
for file_change in analysis_result['changes']:
    print(f"- {file_change['file']} (+{file_change['additions']} / -{file_change['deletions']})")
```

## ⚠️ Consideraciones
- El analizador requiere que `git` esté instalado y accesible en el `PATH` del sistema.
- El rendimiento puede variar en repositorios con una cantidad muy grande de archivos modificados, ya que ejecuta `git diff` para cada uno.
- El manejo de archivos binarios es limitado; se detectan los cambios pero el `diff` puede no ser significativo.

## 🧪 Testing
- Probar en un repositorio con una mezcla de cambios: staged, unstaged, añadidos, eliminados y renombrados.
- Verificar que los archivos listados en `.gitignore` son correctamente ignorados.
- Comprobar que las estadísticas de adiciones/eliminaciones son correctas.
- Validar que el archivo JSON de salida es correcto y contiene toda la información esperada.
