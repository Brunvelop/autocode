# TokenCounter

## 🎯 Propósito
Proporciona una herramienta para contar la cantidad de tokens en textos y archivos, utilizando las codificaciones de modelos de lenguaje grandes (LLM) a través de la biblioteca `tiktoken`. Es esencial para estimar costos de API, validar límites de contexto y analizar el uso de tokens en aplicaciones de IA.

## 🏗️ Arquitectura
El módulo se basa en la clase `TokenCounter`, que se inicializa con un modelo de LLM específico (por ejemplo, "gpt-4") para cargar la codificación de tokens correcta. Si el modelo no es reconocido, utiliza una codificación de fallback (`cl100k_base`). Las funciones del módulo permiten contar tokens en cadenas de texto, en archivos individuales y en múltiples archivos, además de proporcionar utilidades para estimar costos y verificar umbrales.

## 📋 Responsabilidades
- **Contar Tokens en Texto**: Calcula el número de tokens para una cadena de texto dada.
- **Contar Tokens en Archivos**: Lee el contenido de un archivo y cuenta sus tokens.
- **Generar Estadísticas**: Proporciona estadísticas detalladas para un archivo, incluyendo el recuento de tokens, el tamaño del archivo y la densidad de tokens.
- **Estimar Costos**: Calcula el costo estimado de una operación de LLM basándose en el número de tokens y precios configurables por cada 1000 tokens.
- **Verificar Umbrales**: Comprueba si un recuento de tokens excede un límite predefinido, devolviendo información sobre el uso del contexto.
- **Procesamiento por Lotes**: Ofrece una función para agregar estadísticas de tokens de múltiples archivos.

## 🔗 Dependencias
### Externas
- `tiktoken`: Biblioteca de OpenAI para la tokenización de texto según los modelos de LLM.
- `pathlib`: Para la gestión de rutas de archivos de manera orientada a objetos.

## 📊 Interfaces Públicas
### `class TokenCounter`
- `__init__(self, model: str = "gpt-4")`: Constructor que inicializa el tokenizador para un modelo específico.
- `count_tokens_in_text(self, text: str) -> int`: Devuelve el número de tokens en un texto.
- `count_tokens_in_file(self, file_path: Path) -> int`: Devuelve el número de tokens en un archivo.
- `get_token_statistics(self, file_path: Path) -> Dict`: Obtiene un diccionario con estadísticas detalladas del archivo.
- `estimate_cost(...) -> Dict`: Estima el costo de la API para un número de tokens.
- `check_threshold(...) -> Dict`: Verifica si se ha superado un umbral de tokens.

### `count_tokens_in_multiple_files(file_paths: list[Path], model: str = "gpt-4") -> Dict`
- Función standalone para contar tokens en una lista de archivos y devolver estadísticas agregadas.

## 💡 Patrones de Uso
**Contar tokens en un archivo y estimar su costo:**
```python
from pathlib import Path
from autocode.core.ai.token_counter import TokenCounter

file = Path("my_document.txt")
counter = TokenCounter(model="gpt-4")

token_count = counter.count_tokens_in_file(file)
cost_estimate = counter.estimate_cost(token_count)

print(f"El archivo '{file}' tiene {token_count} tokens.")
print(f"Costo de entrada estimado: ${cost_estimate['input_cost_usd']:.4f}")
```

**Verificar si un texto excede el límite de contexto:**
```python
text_prompt = "..."
token_count = counter.count_tokens_in_text(text_prompt)
threshold_check = counter.check_threshold(token_count, threshold=8000)

if threshold_check['exceeds_threshold']:
    print(f"El texto excede el límite por {threshold_check['tokens_over']} tokens.")
```

## ⚠️ Consideraciones
- La precisión del conteo de tokens depende de la biblioteca `tiktoken` y de la correcta especificación del modelo.
- Para modelos no soportados explícitamente por `tiktoken`, el conteo se realiza con una codificación genérica que puede no ser 100% precisa.
- El manejo de errores de lectura de archivos es básico; se asume que los archivos usan codificación UTF-8.

## 🧪 Testing
- Las pruebas deben incluir textos vacíos, textos simples y textos complejos con caracteres especiales.
- Se debe probar con rutas de archivos existentes e inexistentes.
- Verificar que el fallback a `cl100k_base` funciona cuando se proporciona un nombre de modelo desconocido.
- Comprobar que los cálculos de estadísticas y costos son correctos.
