# DocChecker

## 🎯 Propósito
`DocChecker` es el componente central para verificar el estado de la documentación modular en un proyecto. Su responsabilidad principal es comparar las fechas de modificación entre los archivos de código fuente y sus correspondientes archivos de documentación, siguiendo una estructura jerárquica (`_index.md`, `_module.md`, `archivo.md`).

## 🏗️ Arquitectura
El sistema opera mediante la clase `DocChecker`, que escanea el proyecto para encontrar archivos de código y de documentación. Utiliza un sistema de mapeo para relacionar cada archivo de código con su respectivo documento.

El flujo de trabajo es el siguiente:
1.  **Descubrimiento**: Encuentra todos los directorios y archivos de código relevantes basándose en una configuración (o auto-descubrimiento) y extensiones de archivo.
2.  **Mapeo**: Asocia cada archivo de código (`.py`, `.js`, etc.) a su archivo de documentación (`.md`) y cada directorio de código a su `_module.md`.
3.  **Comparación**: Compara la fecha de última modificación del archivo de código con la de su documentación. Si el código es más reciente, la documentación se considera desactualizada.
4.  **Verificación de Estado**: Determina el estado de cada par:
    *   `up_to_date`: La documentación está actualizada.
    *   `outdated`: El código ha sido modificado después que la documentación.
    *   `missing`: No existe el archivo de documentación correspondiente.
    *   `orphaned`: Existe un archivo de documentación pero su archivo de código ha sido eliminado.
5.  **Reporte**: Genera una lista formateada de todos los archivos que requieren atención.

## 📋 Responsabilidades
- **Auto-descubrir directorios de código**: Identifica las carpetas que contienen código fuente.
- **Mapear código a documentación**: Implementa la lógica para encontrar el archivo `.md` que corresponde a un archivo de código, y viceversa.
- **Verificar fechas de modificación**: Compara las marcas de tiempo de los archivos para detectar documentación desactualizada.
- **Detectar documentación faltante**: Identifica archivos de código que no tienen su contraparte en la documentación.
- **Detectar documentación huérfana**: Encuentra archivos de documentación cuyos archivos de código ya no existen.
- **Formatear resultados**: Presenta un informe claro y legible de los problemas encontrados.

## 🔗 Dependencias
### Internas
- Ninguna.

### Externas
- `pathlib`: Para una gestión robusta y orientada a objetos de las rutas del sistema de archivos.
- `typing`: Para anotaciones de tipo (`List`, `NamedTuple`, `Set`, `Optional`).

## 📊 Interfaces Públicas
### `class DocChecker`
- `__init__(self, project_root: Path, config: Optional['DocsConfig'] = None)`: Constructor.
- `check_all_docs(self) -> List[DocStatus]`: Realiza una verificación completa de toda la documentación del proyecto.
- `get_outdated_docs(self) -> List[DocStatus]`: Devuelve solo los elementos que necesitan atención.
- `find_orphaned_docs(self) -> List[DocStatus]`: Busca específicamente documentación huérfana.
- `format_results(self, results: List[DocStatus]) -> str`: Formatea los resultados de la verificación para ser mostrados al usuario.

### `class DocStatus(NamedTuple)`
- Una estructura de datos para almacenar el resultado de la verificación de un par código-documentación.

## 💡 Patrones de Uso
**Ejecutar una verificación completa y mostrar los resultados:**
```python
from pathlib import Path
from autocode.core.docs.doc_checker import DocChecker

project_path = Path('.')
checker = DocChecker(project_path)

# Obtener solo los documentos que necesitan trabajo
pending_docs = checker.get_outdated_docs()

# Formatear y mostrar el informe
report = checker.format_results(pending_docs)
print(report)
```

## ⚠️ Consideraciones
- El sistema se basa en las fechas de modificación del sistema de archivos. Operaciones como `git checkout` pueden alterar estas fechas y afectar los resultados.
- La configuración (`DocsConfig`) es opcional pero permite personalizar los directorios a incluir/excluir y las extensiones de archivo a considerar.
- No documenta archivos `__init__.py` de Python, ya que se consideran archivos de inicialización de módulos y no de contenido.

## 🧪 Testing
- Las pruebas deben simular diferentes estados: archivos actualizados, desactualizados, faltantes y huérfanos.
- Probar con diferentes estructuras de directorios, incluyendo subdirectorios anidados.
- Verificar que el mapeo entre código y documentación funciona para diferentes extensiones de archivo.
- Asegurarse de que los patrones de exclusión de la configuración se aplican correctamente.
