# CSSAnalyzer

## 🎯 Propósito
`CSSAnalyzer` es una implementación de `BaseAnalyzer` para analizar archivos de hojas de estilo (CSS, SCSS, etc.). Su objetivo es extraer información detallada sobre las reglas de estilo, selectores, propiedades, media queries y variables (custom properties) para proporcionar una visión completa del sistema de diseño de un proyecto.

## 🏗️ Arquitectura
Al igual que el analizador de JavaScript, `CSSAnalyzer` se basa en **expresiones regulares (regex)** para parsear el contenido de los archivos CSS.

El flujo de análisis es el siguiente:
1.  **Limpieza**: Elimina los comentarios del contenido para simplificar el parseo.
2.  **Extracción de Reglas**: Utiliza una expresión regular para identificar bloques de reglas completas (selector y cuerpo con propiedades).
3.  **Extracción de Componentes**: Para cada regla o para el archivo completo, aplica patrones específicos para extraer:
    -   **Selectores**: Identifica y clasifica los selectores (clase, id, elemento, etc.).
    -   **Propiedades**: Lista todas las propiedades y sus valores.
    -   **Media Queries**: Detecta bloques `@media`.
    -   **Imports**: Encuentra declaraciones `@import`.
    -   **Variables**: Extrae las "custom properties" (`--variable-name`).
4.  **Cálculo de Métricas**: Realiza recuentos de los elementos extraídos y calcula la especificidad de los selectores.
5.  **Estructuración de Resultados**: Organiza toda la información en un objeto `AnalysisResult`.

## 📋 Responsabilidades
- **Soportar Preprocesadores**: Analiza no solo CSS estándar, sino también extensiones comunes como `.scss`, `.sass` y `.less`.
- **Extraer Reglas de Estilo**: Identifica cada regla CSS y las propiedades que contiene.
- **Clasificar Selectores**: Determina si un selector es de tipo clase, id, elemento, atributo o pseudo-clase.
- **Calcular Especificidad**: Proporciona una puntuación de especificidad simplificada para cada selector.
- **Categorizar Propiedades**: Agrupa las propiedades CSS en categorías lógicas (layout, tipografía, color, etc.).
- **Analizar Media Queries y Variables**: Extrae información sobre diseño responsivo y el sistema de variables CSS.

## 🔗 Dependencias
### Internas
- `autocode.core.design.analyzers.base_analyzer.BaseAnalyzer`: La clase base de la que hereda.

### Externas
- `re`: El módulo de expresiones regulares de Python.
- `pathlib`: Para la manipulación de rutas.

## 📊 Interfaces Públicas
### `class CSSAnalyzer(BaseAnalyzer)`
-   `get_supported_extensions(self) -> List[str]`: Devuelve `['.css', '.scss', '.sass', '.less']`.
-   `analyze_file(self, file_path: Path) -> AnalysisResult`: Implementación principal que analiza un archivo de hoja de estilos.

## 💡 Patrones de Uso
Este analizador es utilizado por `CodeToDesign` cuando se encuentran archivos de hojas de estilo en el proyecto.

```python
# Uso a través de la factoría
from pathlib import Path
from autocode.core.design.analyzers.analyzer_factory import AnalyzerFactory

factory = AnalyzerFactory(Path('.'))
css_analyzer = factory.create_analyzer('css')

if css_analyzer:
    result = css_analyzer.analyze_file(Path('src/styles/main.css'))
    if result.is_successful():
        print(f"Reglas encontradas: {result.data['metrics']['total_rules']}")
        print(f"Variables CSS: {result.data['metrics']['variables']}")
```

## ⚠️ Consideraciones
- **Basado en Regex**: Al no ser un parser de CSS completo, puede tener dificultades con sintaxis muy complejas o anidaciones profundas típicas de SCSS/SASS. Trata estos archivos como CSS plano.
- **Especificidad Simplificada**: El cálculo de la especificidad es una aproximación y puede no ser 100% preciso en casos muy complejos, pero es útil para una evaluación general.

## 🧪 Testing
- Probar con archivos CSS que contengan diferentes tipos de selectores, propiedades y media queries.
- Verificar que los comentarios se eliminan correctamente antes del análisis.
- Probar con archivos SCSS/SASS para asegurar que el análisis no falla, aunque no interprete la anidación.
- Comprobar que las métricas (recuentos, especificidad) se calculan correctamente.
