## Objetivo
Generar un mensaje de commit detallado, pensado para ser usado como contexto por una LLM, a partir de los cambios que están en staging.

El resultado debe ser **un único mensaje de commit** con una primera línea tipo Conventional Commits y un cuerpo estructurado en secciones.

---

## 1. Inspecciona los cambios

1. Ejecuta internamente:
   - `git --no-pager diff --cached` para ver el diff actual.
   - (Opcional) `git status --short` para entender qué archivos se han añadido, modificado o eliminado.

2. Lee el diff con calma y detecta:
   - Archivos y módulos afectados.
   - Tipo de cambio: nueva funcionalidad, corrección de bug, refactor, docs, tests, chore, etc.
   - Si hay cambios de contrato (API, modelos, formatos de fichero, etc.).

---

## 2. Analiza, clasifica y valora el cambio

A partir del diff:

1. **Clasificación**
   - Determina el **tipo de cambio principal** usando una de estas etiquetas:
     - `feat`, `fix`, `refactor`, `chore`, `docs`, `test`.
   - Identifica las **áreas afectadas** (por ejemplo: `api`, `inference_matrix`, `web`, `tests`, `infra`, etc.).
   - Estima el **nivel de riesgo**: `bajo`, `medio` o `alto`.
   - Decide si hay **breaking changes** (sí/no) y por qué.

2. **Valoración**
   - Explica si el diseño te parece bueno o si ves problemas.
   - Menciona trade‑offs relevantes (acoplamiento, complejidad, deuda técnica, etc.).
   - Señala posibles mejoras futuras o dudas abiertas.

---

## 3. Formato del mensaje de commit

Redacta el mensaje de commit siguiendo **exactamente** este formato:

```text
<tipo>(área opcional): resumen breve y descriptivo del cambio principal

## 1. Visión general
__Tema principal del cambio__

- Explica en 2–4 bullets qué problema resuelves o qué objetivo persigues.

## 2. Clasificación
- Tipo de cambio: feat | fix | refactor | chore | docs | test
- Áreas afectadas: lista de áreas lógicas del código (api, inference_matrix, web, tests, infra, ...).
- Nivel de riesgo: bajo | medio | alto
- Breaking change: sí/no (si es sí, explica brevemente por qué y qué rompe).

## 3. Qué cambia
- Resumen por archivo o módulo de los cambios importantes.
- No enumeres cada línea, céntrate en el comportamiento y en las decisiones de diseño.

## 4. Valoración
- Explica por qué consideras que el cambio es bueno (o qué problemas tiene).
- Menciona trade‑offs, posibles puntos débiles y mejoras futuras.

## 5. Tests
- Indica qué tipos de tests existen y cuáles se han ejecutado (unit, integration, e2e, manual).
- Si no hay tests que cubran este cambio, dilo explícitamente y explica el riesgo.
```

Notas importantes sobre el formato:
- La **primera línea** debe usar un `tipo` como `feat`, `fix`, `refactor`, `chore`, `docs` o `test`.
- El `área opcional` puede ser un módulo o dominio (`inference_matrix`, `api`, `web`, `video_editor`, etc.).
- El resumen de la primera línea debe ser conciso (≈72 caracteres) y escrito en español, pero puede incluir nombres de clases/métodos en inglés.

---

## 4. Reglas de estilo

- Escribe todo el cuerpo del mensaje en **español**, dejando en inglés solo nombres propios de código (clases, funciones, rutas, tipos).
- No inventes cambios ni tests: describe únicamente lo que realmente está en el diff y/o en los tests del proyecto.
- Si falta algo importante (por ejemplo, tests para un cambio arriesgado), menciónalo en las secciones de **Valoración** y **Tests**.
- Evita repetir literalmente el diff; aporta contexto y sentido: qué problema se resuelve, cómo y con qué impacto.

---

## 5. Salida esperada

Cuando uses este workflow para generar un mensaje de commit:

- Responde **únicamente** con el mensaje de commit final en el formato especificado arriba.
- No añadas explicaciones adicionales fuera del mensaje.
- Puedes envolver el mensaje completo en un bloque de código `text` para que sea fácil de copiar y pegar.
