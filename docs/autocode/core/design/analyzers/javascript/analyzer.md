# JavaScriptAnalyzer

## 🎯 Propósito
`JavaScriptAnalyzer` es una implementación de `BaseAnalyzer` diseñada para analizar código fuente de JavaScript y TypeScript. Su objetivo es extraer información estructural clave, como clases, funciones, imports y exports, para alimentar el sistema de generación de documentación de diseño.

## 🏗️ Arquitectura
Este analizador se basa principalmente en **expresiones regulares (regex)** para identificar las estructuras del código. No utiliza un Analizador Sintáctico Abstracto (AST) completo, lo que lo hace más rápido y simple, aunque potencialmente menos robusto ante sintaxis muy complejas o no estándar.

El flujo de trabajo para analizar un archivo es el siguiente:
1.  **Leer Contenido**: Carga el contenido del archivo de código.
2.  **Aplicar Patrones**: Ejecuta una serie de expresiones regulares predefinidas para encontrar todas las coincidencias de clases, funciones (normales y de flecha), imports y exports.
3.  **Extraer Detalles**: Para cada coincidencia, extrae información específica, como el nombre de la clase, los métodos, los parámetros de la función, etc.
4.  **Calcular Métricas**: Cuenta los elementos encontrados y calcula métricas básicas como el total de líneas de código.
5.  **Estructurar Resultados**: Empaqueta toda la información extraída en un objeto `AnalysisResult` estandarizado.

## 📋 Responsabilidades
- **Soportar Múltiples Extensiones**: Reconoce y analiza archivos `.js`, `.ts`, `.jsx` y `.tsx`.
- **Extraer Clases**: Identifica definiciones de clases, su herencia y sus métodos internos.
- **Extraer Funciones**: Detecta tanto funciones declaradas con `function` como funciones de flecha (`=>`) asignadas a variables.
- **Extraer Módulos ES6**: Analiza las declaraciones `import` y `export` para entender las dependencias y la interfaz pública del archivo.
- **Calcular Métricas de Código**: Proporciona recuentos de los elementos encontrados y las líneas de código.

## 🔗 Dependencias
### Internas
- `autocode.core.design.analyzers.base_analyzer.BaseAnalyzer`: La clase base de la que hereda.
- `autocode.core.design.analyzers.base_analyzer.AnalysisResult`: Para empaquetar los resultados.

### Externas
- `re`: El módulo de expresiones regulares de Python, que es el núcleo de este analizador.
- `pathlib`: Para la manipulación de rutas.

## 📊 Interfaces Públicas
### `class JavaScriptAnalyzer(BaseAnalyzer)`
-   `get_supported_extensions(self) -> List[str]`: Devuelve `['.js', '.ts', '.jsx', '.tsx']`.
-   `analyze_file(self, file_path: Path) -> AnalysisResult`: Implementación principal que analiza un archivo JS/TS.

## 💡 Patrones de Uso
Este analizador es utilizado internamente por `CodeToDesign` a través de `AnalyzerFactory` cuando se encuentran archivos con las extensiones soportadas.

```python
# Uso a través de la factoría
from pathlib import Path
from autocode.core.design.analyzers.analyzer_factory import AnalyzerFactory

factory = AnalyzerFactory(Path('.'))
js_analyzer = factory.create_analyzer('javascript')

if js_analyzer:
    result = js_analyzer.analyze_file(Path('src/my_component.jsx'))
    if result.is_successful():
        print(f"Clases encontradas: {len(result.data['classes'])}")
```

## ⚠️ Consideraciones
- **Basado en Regex**: Al no usar un AST, puede fallar o dar resultados imprecisos con código que use sintaxis muy moderna o inusual que no coincida con los patrones.
- **Extracción de Cuerpo de Clase**: La lógica para encontrar el cuerpo de una clase se basa en el balanceo de llaves (`{...}`), lo que puede ser frágil si hay llaves en comentarios o cadenas de texto dentro de la definición de la clase.
- **Visibilidad de Métodos**: La visibilidad se infiere de manera simple: si un método comienza con `_`, se considera privado (`-`); de lo contrario, público (`+`). No reconoce los modificadores `public`, `private` de TypeScript.

## 🧪 Testing
- Probar con archivos JS y TS que contengan una mezcla de clases, funciones, imports y exports.
- Verificar que se extraen correctamente los métodos de las clases.
- Probar con sintaxis de ES6 y TypeScript común.
- Probar casos límite, como archivos vacíos o archivos con errores de sintaxis, para asegurar que el analizador no falla catastróficamente.
