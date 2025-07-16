# ClassDiagramGenerator

## 🎯 Propósito
`ClassDiagramGenerator` es una implementación concreta de `BaseGenerator` especializada en crear **diagramas de clases** utilizando la sintaxis de **Mermaid**. Su única responsabilidad es tomar una estructura de datos que representa una clase de Python y traducirla a un diagrama de texto que puede ser renderizado por Mermaid.

## 🏗️ Arquitectura
Esta clase hereda de `BaseGenerator` y sobreescribe los métodos necesarios para proporcionar su funcionalidad específica:
-   `get_diagram_format()`: Devuelve la cadena "mermaid".
-   `supports_diagram_type()`: Indica que solo soporta diagramas de tipo "class".
-   `generate_class_diagram()`: Contiene la lógica principal para construir el diagrama.

El método `generate_class_diagram` procesa la información de la clase (nombre, atributos, métodos, herencia) y la formatea línea por línea para cumplir con la sintaxis de `classDiagram` de Mermaid.

## 📋 Responsabilidades
- **Generar Diagramas de Clases**: Convierte la representación de una clase en un diagrama de Mermaid.
- **Formatear Atributos**: Muestra los atributos de la clase, incluyendo su visibilidad (pública, protegida, privada) y tipo.
- **Formatear Métodos**: Muestra los métodos, su visibilidad, parámetros (con tipos) y tipo de retorno.
- **Representar Herencia**: Añade las relaciones de herencia (`<|--`) con las clases base.
- **Añadir Estereotipos**: Utiliza estereotipos de Mermaid (`<<property>>`, `<<static>>`) para representar decoradores comunes de Python.

## 🔗 Dependencias
### Internas
- `autocode.core.design.diagrams.base_generator.BaseGenerator`: La clase base de la que hereda.

### Externas
- Ninguna.

## 📊 Interfaces Públicas
### `class ClassDiagramGenerator(BaseGenerator)`
-   `get_diagram_format(self) -> str`: Devuelve "mermaid".
-   `supports_diagram_type(self, diagram_type: str) -> bool`: Devuelve `True` si `diagram_type` es "class".
-   `generate_class_diagram(self, class_info: Dict) -> str`: El método principal que genera el diagrama de clase.

## 💡 Patrones de Uso
Este generador es utilizado internamente por `CodeToDesign` cuando la configuración solicita la generación de diagramas de clases. No está pensado para ser usado directamente, pero podría serlo:

**Generar un diagrama para una estructura de clase simple:**
```python
from autocode.core.design.diagrams.class_diagram_generator import ClassDiagramGenerator

# Datos de ejemplo que un analizador podría producir
class_data = {
    "name": "MyClass",
    "bases": ["BaseClass"],
    "attributes": [
        {"name": "my_attribute", "type": "str", "visibility": "+"}
    ],
    "methods": [
        {
            "name": "my_method",
            "parameters": [{"name": "param1", "type": "int"}],
            "return_type": "bool",
            "visibility": "+",
            "is_property": False,
            "is_static": False,
            "is_class": False
        }
    ]
}

generator = ClassDiagramGenerator()
mermaid_code = generator.generate_class_diagram(class_data)
print(mermaid_code)
```

## ⚠️ Consideraciones
- La calidad del diagrama depende enteramente de la riqueza y precisión de los datos proporcionados por el analizador en `class_info`.
- El generador omite el parámetro `self` de los métodos para mejorar la legibilidad del diagrama, una convención común en diagramas de clases.

## 🧪 Testing
- Probar con diferentes tipos de clases: clases simples, clases con herencia, clases con atributos y métodos de diferente visibilidad.
- Verificar que los tipos de datos de atributos, parámetros y retornos se renderizan correctamente.
- Comprobar que los decoradores (`@property`, `@staticmethod`) se traducen a los estereotipos de Mermaid correctos.
- Asegurarse de que la sintaxis de Mermaid generada es siempre válida.
