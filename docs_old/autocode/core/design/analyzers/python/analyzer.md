# PythonAnalyzer

## 🎯 Propósito
`PythonAnalyzer` es una implementación robusta de `BaseAnalyzer` para analizar código fuente de Python. A diferencia del analizador de JavaScript, este utiliza el módulo `ast` (Abstract Syntax Tree) de Python, lo que le permite realizar un análisis mucho más preciso y detallado de la estructura del código. Su objetivo es extraer información sobre clases, funciones, imports y atributos para la generación de documentación de diseño.

## 🏗️ Arquitectura
El núcleo de este analizador es el uso del módulo `ast` de Python.
1.  **Parseo a AST**: Lee el contenido de un archivo `.py` o `.pyi` y lo convierte en un Árbol de Sintaxis Abstracta (AST), que es una representación en árbol de la estructura del código.
2.  **Recorrido del Árbol**: Utiliza `ast.walk()` para recorrer todos los nodos del árbol.
3.  **Identificación de Nodos**: Busca nodos de tipos específicos que representan las estructuras del lenguaje:
    -   `ast.ClassDef`: Para clases.
    -   `ast.FunctionDef`: Para funciones y métodos.
    -   `ast.Import` y `ast.ImportFrom`: Para declaraciones de importación.
    -   `ast.Assign`: Para atributos de clase.
4.  **Extracción de Detalles**: Para cada nodo de interés, invoca a métodos auxiliares (`_extract_class_info`, `_extract_function_info`, etc.) que extraen metadatos detallados, como parámetros, tipos de retorno, decoradores, visibilidad y clases base.
5.  **Estructuración de Resultados**: Agrupa toda la información en un objeto `AnalysisResult`.

## 📋 Responsabilidades
- **Analizar Archivos Python**: Parsea archivos `.py` y `.pyi` para construir un AST.
- **Extraer Clases**: Identifica clases, sus clases base, decoradores, métodos y atributos.
- **Extraer Funciones**: Identifica funciones a nivel de módulo, sus parámetros, tipos de retorno y decoradores.
- **Extraer Imports**: Registra todas las declaraciones de importación.
- **Determinar Visibilidad**: Infiere la visibilidad (pública `+` o privada `-`) basándose en la convención de si el nombre comienza con un guion bajo (`_`).
- **Extraer Anotaciones de Tipo**: Parsea y extrae las anotaciones de tipo de los parámetros, retornos y atributos.
- **Calcular Métricas**: Proporciona recuentos de los elementos encontrados y las líneas de código.

## 🔗 Dependencias
### Internas
- `autocode.core.design.analyzers.base_analyzer.BaseAnalyzer`: La clase base de la que hereda.

### Externas
- `ast`: El módulo incorporado de Python para trabajar con Árboles de Sintaxis Abstracta.
- `pathlib`: Para la manipulación de rutas.

## 📊 Interfaces Públicas
### `class PythonAnalyzer(BaseAnalyzer)`
-   `get_supported_extensions(self) -> List[str]`: Devuelve `['.py', '.pyi']`.
-   `analyze_file(self, file_path: Path) -> AnalysisResult`: Implementación principal que analiza un archivo Python usando AST.

## 💡 Patrones de Uso
Este analizador es utilizado internamente por `CodeToDesign` a través de `AnalyzerFactory` cuando se encuentran archivos Python.

```python
# Uso a través de la factoría
from pathlib import Path
from autocode.core.design.analyzers.analyzer_factory import AnalyzerFactory

factory = AnalyzerFactory(Path('.'))
python_analyzer = factory.create_analyzer('python')

if python_analyzer:
    result = python_analyzer.analyze_file(Path('src/my_module.py'))
    if result.is_successful():
        print(f"Clases encontradas: {len(result.data['classes'])}")
        # La data contiene información muy detallada gracias al AST
        print(result.data['classes'][0]['methods'])
```

## ⚠️ Consideraciones
- **Precisión**: Al usar AST, este analizador es mucho más preciso y resistente a la sintaxis compleja que los analizadores basados en regex.
- **Errores de Sintaxis**: Si el archivo Python contiene un error de sintaxis, el parseo a AST fallará y el análisis de ese archivo se detendrá, devolviendo un error.
- **Análisis de Nivel Superior**: Por diseño, solo analiza funciones definidas en el nivel superior del módulo, ignorando las funciones anidadas dentro de otras funciones.

## 🧪 Testing
- Probar con archivos Python que contengan diferentes características del lenguaje: clases, herencia múltiple, decoradores, funciones con y sin anotaciones de tipo, etc.
- Verificar que la extracción de detalles (parámetros, visibilidad, etc.) es correcta.
- Probar con un archivo que contenga errores de sintaxis para asegurar que se maneja el error de forma controlada.
- Comprobar que los archivos `.pyi` (archivos de "stub" de tipos) también se pueden analizar.
