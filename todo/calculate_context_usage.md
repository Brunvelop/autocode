# feat(ai): añadir soporte de path a calculate_context_usage

## Descripción

`calculate_context_usage()` actualmente solo acepta una lista de mensajes (`messages`).
Se quiere añadir un parámetro opcional `path` que permita calcular cuántos tokens
ocupa el contenido de un directorio completo, leyendo sus archivos recursivamente.

## Comportamiento esperado

```python
# Uso actual (backward compatible, sin cambios)
calculate_context_usage(model="gpt-4o", messages=[...])

# Nuevo: pasar una carpeta
calculate_context_usage(model="gpt-4o", path="autocode/core/ai")

# Nuevo: combinar ambos
calculate_context_usage(model="gpt-4o", messages=[...], path="autocode/core/ai")
```

## Especificación

- `path: Optional[str] = None` — ruta a un directorio (o archivo)
- Si se pasa `path`: leer recursivamente todos los archivos de texto del directorio,
  concatenar su contenido y contabilizarlo como un mensaje `user`
- Si se pasan `messages` y `path`: sumar ambos conteos
- Si no se puede leer un archivo (binario, permisos), ignorarlo silenciosamente
- El resultado devuelve los mismos campos que ahora (`total_tokens`, `max_tokens`, `percentage`, etc.)

## Archivos a modificar

- `autocode/core/ai/pipelines.py` — añadir el parámetro y la lógica de lectura
- `tests/unit/core/ai/test_pipelines.py` — tests con mock filesystem + mock litellm

## Notas

- Ver plan detallado en Commit 9 del plan de refactor del módulo AI
- Útil para estimar si un proyecto cabe en el contexto antes de enviarlo al LLM
