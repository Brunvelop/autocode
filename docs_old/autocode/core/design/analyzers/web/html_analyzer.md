# HTMLAnalyzer

## 🎯 Propósito
`HTMLAnalyzer` es una implementación de `BaseAnalyzer` para analizar archivos HTML. Su objetivo es parsear la estructura del DOM (Document Object Model) para extraer información sobre los elementos, componentes personalizados (custom elements), formularios, scripts y enlaces. Esto es fundamental para entender la estructura de una interfaz de usuario.

## 🏗️ Arquitectura
A diferencia de otros analizadores basados en regex, `HTMLAnalyzer` utiliza la biblioteca **BeautifulSoup** para parsear el HTML en un árbol de objetos, lo que permite un análisis mucho más robusto y preciso de la estructura del documento.

El flujo de análisis es el siguiente:
1.  **Parseo con BeautifulSoup**: Lee el contenido del archivo y lo convierte en un objeto `soup` que representa el DOM.
2.  **Extracción de Elementos**: Recorre el árbol del DOM para extraer diferentes tipos de elementos de interés:
    -   Todos los elementos HTML con sus atributos.
    -   Elementos personalizados (aquellos con un guion en el nombre, ej. `<my-component>`).
    -   Elementos de formulario (`<form>`, `<input>`, etc.).
    -   Etiquetas `<script>` y `<link>`.
3.  **Análisis de Relaciones**: Recorre el árbol de forma recursiva para extraer las relaciones padre-hijo entre los elementos.
4.  **Cálculo de Métricas**: Realiza recuentos de los elementos extraídos y calcula la profundidad máxima del DOM.
5.  **Estructuración de Resultados**: Organiza toda la información en un objeto `AnalysisResult`.

## 📋 Responsabilidades
- **Analizar la Estructura del DOM**: Parsea un archivo HTML y extrae todos los elementos y sus atributos.
- **Identificar Componentes Personalizados**: Detecta el uso de Web Components o componentes de frameworks que se renderizan como etiquetas personalizadas.
- **Extraer Formularios**: Identifica todos los elementos relacionados con formularios.
- **Analizar Recursos Externos**: Extrae información sobre los scripts y hojas de estilo enlazados.
- **Mapear Relaciones Jerárquicas**: Documenta la estructura anidada de los elementos del DOM.
- **Calcular Métricas del DOM**: Proporciona datos como la profundidad del árbol y el número total de elementos.

## 🔗 Dependencias
### Internas
- `autocode.core.design.analyzers.base_analyzer.BaseAnalyzer`: La clase base de la que hereda.

### Externas
- `beautifulsoup4`: La biblioteca principal para parsear HTML.
- `pathlib`: Para la manipulación de rutas.

## 📊 Interfaces Públicas
### `class HTMLAnalyzer(BaseAnalyzer)`
-   `get_supported_extensions(self) -> List[str]`: Devuelve `['.html', '.htm']`.
-   `analyze_file(self, file_path: Path) -> AnalysisResult`: Implementación principal que analiza un archivo HTML.

## 💡 Patrones de Uso
Este analizador es utilizado por `CodeToDesign` cuando se encuentran archivos HTML en el proyecto. Sus resultados son especialmente útiles cuando se combinan con los de `CSSAnalyzer` y `JavaScriptAnalyzer` para obtener una visión completa de un componente de frontend.

```python
# Uso a través de la factoría
from pathlib import Path
from autocode.core.design.analyzers.analyzer_factory import AnalyzerFactory

factory = AnalyzerFactory(Path('.'))
html_analyzer = factory.create_analyzer('html')

if html_analyzer:
    result = html_analyzer.analyze_file(Path('src/index.html'))
    if result.is_successful():
        print(f"Total de elementos: {result.data['metrics']['total_elements']}")
        print(f"Componentes personalizados: {result.data['metrics']['custom_elements']}")
```

## ⚠️ Consideraciones
- **Dependencia de BeautifulSoup**: Requiere que la biblioteca `beautifulsoup4` (y un parser como `html.parser` o `lxml`) esté instalada.
- **HTML Mal Formado**: Aunque BeautifulSoup es muy tolerante con el HTML mal formado, errores graves de sintaxis podrían llevar a un árbol DOM incorrecto y, por tanto, a un análisis impreciso.

## 🧪 Testing
- Probar con archivos HTML simples y complejos.
- Verificar que se extraen correctamente los elementos anidados.
- Probar con un archivo que contenga componentes personalizados, formularios, scripts y enlaces.
- Asegurarse de que el análisis no falla con HTML que no esté perfectamente formado.
