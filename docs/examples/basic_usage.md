# basic_usage.py

## 🎯 Propósito
Script de ejemplo que demuestra el uso programático de autocode, mostrando cómo utilizar las funcionalidades principales de DocChecker y GitAnalyzer desde código Python.

## 🏗️ Arquitectura
```mermaid
graph TD
    A[main()] --> B[DocChecker]
    A --> C[GitAnalyzer]
    B --> D[get_outdated_docs()]
    C --> E[get_repository_status()]
    C --> F[get_modified_files()]
    
    D --> G[Reporte de documentación]
    E --> H[Estado del repositorio]
    F --> I[Lista de archivos modificados]
```

## 📋 Responsabilidades
- **Demostrar DocChecker**: Verificar el estado de la documentación del proyecto
- **Demostrar GitAnalyzer**: Analizar cambios en el repositorio git
- **Proporcionar ejemplo de uso**: Mostrar cómo integrar autocode en scripts personalizados
- **Manejo de errores**: Demostrar manejo robusto de excepciones

## 🔗 Dependencias
### Internas
- `autocode.core.doc_checker.DocChecker` - Verificación de documentación
- `autocode.core.git_analyzer.GitAnalyzer` - Análisis de cambios git

### Externas
- `pathlib.Path` - Manipulación de rutas de archivo

## 📊 Interfaces Públicas
### Función Principal
```python
def main() -> None
```
- **Propósito**: Ejecutar demostración completa de funcionalidades autocode
- **Parámetros**: Ninguno
- **Retorno**: None
- **Efectos**: Imprime resultados en consola

## 🔧 Configuración
- **Directorio de trabajo**: Utiliza `Path.cwd()` para detectar automáticamente el directorio actual
- **Sin configuración externa**: No requiere archivos de configuración adicionales

## 💡 Patrones de Uso
### Ejecución como Script
```bash
# Ejecutar directamente
python examples/basic_usage.py

# Ejecutar con uv
uv run examples/basic_usage.py
```

### Integración en Código
```python
from examples.basic_usage import main

# Ejecutar demostración
main()
```

## ⚠️ Consideraciones
- **Manejo de errores**: Usa try/catch para manejar fallos graciosamente
- **Limitación de salida**: Muestra solo los primeros 5 archivos modificados para evitar salida excesiva
- **Dependencia de git**: Requiere repositorio git válido para funcionar completamente
- **Directorio de trabajo**: Debe ejecutarse desde directorio con estructura de proyecto autocode

## 🧪 Testing
- **Prueba manual**: Ejecutar el script desde diferentes directorios
- **Verificación de salida**: Confirmar que se muestran resultados apropiados
- **Manejo de errores**: Probar en repositorios sin git o con problemas

## 🔄 Flujo de Datos
1. **Inicialización**: Obtiene directorio de trabajo actual
2. **Verificación de documentación**: 
   - Crea instancia DocChecker
   - Obtiene lista de documentación desactualizada
   - Muestra resultados o mensaje de éxito
3. **Análisis de git**:
   - Crea instancia GitAnalyzer
   - Obtiene estado del repositorio
   - Lista archivos modificados (limitado a 5)
4. **Finalización**: Muestra consejos de uso adicional

## 📈 Salida Esperada
```
🚀 Autocode Basic Usage Example
========================================
📁 Project root: /path/to/project

📋 1. Checking documentation...
✅ All documentation is up to date!

🔍 2. Analyzing git changes...
📊 Repository status:
   Total files changed: 3
   Modified: 2
   Added: 1
   Deleted: 0

📄 Modified files:
   - autocode/core/doc_checker.py
   - examples/basic_usage.py

✨ Example completed!

💡 To run more examples:
   autocode check-docs
   autocode git-changes --verbose
   autocode daemon
