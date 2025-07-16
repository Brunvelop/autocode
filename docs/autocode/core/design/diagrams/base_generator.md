# BaseGenerator

## 🎯 Propósito
`BaseGenerator` es una **clase base abstracta** que establece el contrato para todos los generadores de diagramas del sistema. Su función es asegurar que cualquier generador (ya sea para Mermaid, PlantUML, etc.) se integre de manera consistente en el flujo de trabajo de `CodeToDesign`, proporcionando una interfaz común para la creación de diagramas.

## 🏗️ Arquitectura
Al igual que `BaseAnalyzer`, este módulo utiliza una clase abstracta (`ABC`) para definir una interfaz.

-   **`BaseGenerator` (Clase Abstracta)**:
    -   Define un método abstracto, `get_diagram_format`, que obliga a las clases hijas a declarar el formato de diagrama que producen (ej. "mermaid").
    -   Proporciona implementaciones por defecto (virtuales) para métodos como `generate_class_diagram` y `generate_diagram`. Estas implementaciones devuelven un mensaje de "no soportado", permitiendo que las clases hijas solo implementen los tipos de diagrama que les interesan. Esto sigue el **Principio de Segregación de Interfaces**, ya que las clases no están forzadas a implementar métodos que no utilizan.

## 📋 Responsabilidades
- **Definir el Contrato del Generador**: Especifica los métodos que un generador de diagramas debe o puede implementar.
- **Estandarizar la Creación de Diagramas**: Proporciona una firma de método común para generar diagramas a partir de datos estructurados.
- **Permitir la Extensibilidad**: Facilita la adición de nuevos tipos de generadores de diagramas (para otras tecnologías como PlantUML, D2, etc.) sin tener que modificar el núcleo del sistema.

## 🔗 Dependencias
### Externas
- `abc` (Abstract Base Classes): Para la definición de la clase abstracta.

## 📊 Interfaces Públicas
### `class BaseGenerator(ABC)`
-   `__init__(self, config: Dict[str, Any] = None)`: Constructor base.
-   `get_diagram_format(self) -> str`: **Método abstracto**. Debe devolver el nombre del formato del diagrama (ej. "mermaid").
-   `generate_class_diagram(self, class_info: Dict) -> str`: Método opcional para generar un diagrama de una sola clase. Las clases hijas lo sobreescriben si soportan este tipo de diagrama.
-   `generate_diagram(self, data: Dict[str, Any], diagram_type: str = "default") -> str`: Método genérico para generar diferentes tipos de diagramas.
-   `supports_diagram_type(self, diagram_type: str) -> bool`: Comprueba si el generador soporta un tipo de diagrama específico.

## 💡 Patrones de Uso
`BaseGenerator` no se instancia directamente. Sirve como plantilla para crear generadores concretos.

**Ejemplo de implementación de un nuevo generador:**
```python
from .base_generator import BaseGenerator

class MermaidGenerator(BaseGenerator):
    def get_diagram_format(self) -> str:
        return 'mermaid'

    def generate_class_diagram(self, class_info: Dict) -> str:
        # Lógica para generar un diagrama de clase en formato Mermaid
        diagram = "classDiagram\n"
        diagram += f"    class {class_info['name']}\n"
        # ... añadir métodos y atributos ...
        return diagram

    def supports_diagram_type(self, diagram_type: str) -> bool:
        # Este generador soporta diagramas de clase
        return diagram_type == "class"
```

## ⚠️ Consideraciones
- Las clases hijas deben implementar `get_diagram_format`.
- Si una clase hija no sobreescribe un método de generación como `generate_class_diagram`, se utilizará la implementación base, que indica que la operación no es soportada.

## 🧪 Testing
- Las pruebas se realizan sobre las implementaciones concretas de esta clase.
- Se debe verificar que cada generador concreto implementa `get_diagram_format` y que los métodos de generación producen una sintaxis de diagrama válida para su formato específico.
