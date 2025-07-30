# GeneratorFactory

## 🎯 Propósito
`GeneratorFactory` es una factoría, análoga a `AnalyzerFactory`, responsable de crear dinámicamente instancias de generadores de diagramas. Su función es desacoplar el sistema de las implementaciones concretas de los generadores (como `ClassDiagramGenerator`), permitiendo una fácil extensión para soportar nuevos formatos de diagramas (ej. PlantUML, D2) en el futuro.

## 🏗️ Arquitectura
La arquitectura es paralela a la de `AnalyzerFactory`, utilizando un **Registro (Registry)** y el patrón de diseño **Factory**.
1.  **`GeneratorRegistry`**: Un registro global que mapea nombres de generadores (ej. "mermaid") a sus clases (`ClassDiagramGenerator`) y a los formatos que soportan (`md`, `mermaid`).
2.  **`GeneratorFactory`**: Utiliza el registro para instanciar los generadores. Puede crear un generador por su nombre, por el formato de salida deseado, o auto-detectar los generadores necesarios para una lista de tipos de diagramas solicitados.

El flujo de trabajo es:
1.  Al iniciar, los generadores de diagramas incorporados (`ClassDiagramGenerator`, `ComponentTreeGenerator`) se registran en el `GeneratorRegistry`.
2.  `CodeToDesign` solicita a la factoría que cree los generadores necesarios según la configuración del proyecto (ej. los tipos de diagramas a generar).
3.  La factoría consulta el registro, instancia las clases de generador correspondientes y las devuelve.

## 📋 Responsabilidades
- **Registrar Generadores**: Mantiene un registro de todos los generadores de diagramas disponibles.
- **Crear Instancias de Generadores**: Instancia un generador específico a petición.
- **Auto-detección**: Determina qué generadores se necesitan para crear una lista de tipos de diagramas (ej. "classes", "components").
- **Desacoplar Componentes**: Abstrae la lógica de creación de generadores, permitiendo que el sistema principal trabaje con la interfaz `BaseGenerator`.
- **Proporcionar Información**: Ofrece métodos para consultar los generadores disponibles y los formatos que soportan.

## 🔗 Dependencias
### Internas
- `autocode.core.design.diagrams.base_generator.BaseGenerator`: La clase base de la que todos los generadores deben heredar.
- Generadores concretos (ej. `ClassDiagramGenerator`) para el registro.

### Externas
- `logging`: Para registrar advertencias si un generador no está disponible.

## 📊 Interfaces Públicas
### `class GeneratorFactory`
-   `__init__(self, config: Dict[str, Any] = None)`: Constructor.
-   `create_generator(self, generator_type: str) -> Optional[BaseGenerator]`: Crea un generador por su nombre (ej. "mermaid").
-   `auto_detect_generators(self, diagram_types: List[str]) -> Dict[str, BaseGenerator]`: Auto-detecta y crea los generadores necesarios para una lista de tipos de diagramas.
-   `get_available_generators(self) -> List[str]`: Devuelve los nombres de todos los generadores registrados.
-   `get_supported_formats(self) -> List[str]`: Devuelve una lista de todos los formatos de salida soportados.
-   `get_generator_info(self) -> Dict[str, Any]`: Proporciona metadatos detallados sobre todos los generadores disponibles.

### `GeneratorRegistry` y funciones de registro
-   `register_generator(...)`: Función para añadir un nuevo generador al sistema.

## 💡 Patrones de Uso
**Crear un generador de Mermaid:**
```python
from autocode.core.design.diagrams.generator_factory import GeneratorFactory

factory = GeneratorFactory()
mermaid_generator = factory.create_generator('mermaid')

if mermaid_generator:
    # Usar el generador para crear un diagrama
    diagram_code = mermaid_generator.generate_class_diagram(...)
```

**Auto-detectar los generadores necesarios para la configuración:**
```python
config_diagrams = ['classes', 'components']
factory = GeneratorFactory()
needed_generators = factory.auto_detect_generators(config_diagrams)

# needed_generators contendrá instancias de ClassDiagramGenerator y ComponentTreeGenerator
for name, instance in needed_generators.items():
    print(f"Generador necesario: {name}")
```

## ⚠️ Consideraciones
- El sistema depende de que los generadores se registren correctamente al inicio.
- La lógica de `auto_detect_generators` actualmente tiene un mapeo simple de tipo de diagrama a generador (ej. "classes" -> "mermaid"). Esto podría expandirse en el futuro para ser más flexible.

## 🧪 Testing
- Verificar que los generadores incorporados se registran correctamente.
- Probar la creación de generadores por nombre.
- Probar la función de auto-detección con diferentes listas de tipos de diagramas.
- Asegurarse de que la factoría maneja correctamente las solicitudes de generadores no existentes.
