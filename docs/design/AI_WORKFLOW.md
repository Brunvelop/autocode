# AI-Assisted Development Workflow

Este documento define la arquitectura y metodología de trabajo para el desarrollo de software asistido por IA en Autocode. El objetivo es establecer un flujo robusto donde el **Diseño** sea la fuente de la verdad y el **Código** sea una implementación derivada.

## 1. Filosofía: Model-Driven Development (MDD)

En este flujo, **no se escribe código directamente en la rama principal**.
*   El **Humano** y la **IA** colaboran en el plano del **Diseño (Lógica)**.
*   La **IA** actúa como un "compilador inteligente" que traduce ese diseño a **Código Ejecutable**.
*   El **Código** es efímero y derivado; el **Diseño** es persistente y fundamental.

---

## 2. Estrategia de Ramas

El repositorio se organiza en tres niveles de abstracción:

### `main` (Producción / Código)
*   **Contenido:** Código fuente ejecutable (Python, JS), testados y listos para producción.
*   **Regla de Oro:** **Inmutable por humanos**. Solo recibe merges automáticos que han sido **validados por tests y aprobados explícitamente por un humano**.
*   **Fuente de Verdad:** Ejecución.

### `design` (Arquitectura / Blueprints)
*   **Contenido:** Archivos de especificación (`.yaml`) y planes de ejecución (`.plan.yaml`).
*   **Estructura:** Espejo 1:1 de la estructura de carpetas de `main`.
    *   `src/app.py` -> `blueprints/src/app.yaml`
    *   `tests/test_app.py` -> `blueprints_tests/src/test_app.yaml`
*   **Regla de Oro:** Aquí es donde ocurre la creatividad. Se definen firmas, lógica y tests en pseudocódigo estructurado.
*   **Fuente de Verdad:** Intención y Lógica.

### `dev/feature-name` (Implementación)
*   **Contenido:** Código en desarrollo.
*   **Ciclo de Vida:** Efímero.
    *   **Nace de:** `main` (necesita el código base actual para funcionar).
    *   **Se guía por:** `design` (implementa lo que dice la especificación).
    *   **Muere:** Al mergearse en `main`.

---

## 3. El Blueprint (Especificación)

Cada archivo de código tiene su contraparte en YAML (`.pseudo.yaml` o `.yaml`). Este formato combina estructura estricta (para automatización) con lógica expresiva (para humanos/LLMs).

### Schema del Blueprint

```yaml
meta:
  file_path: "autocode/core/processor.py"
  language: "python"
  description: "Procesa datos de entrada y normaliza salidas."

dependencies: [logging, typing, pandas]

# Definición de Clases o Funciones Globales
functions:
  process_data:
    # --- AUTOMATIZABLE (AST) ---
    signature:
      args: 
        - data: Dict[str, Any]
        - strict: bool = False
      returns: DataFrame
    
    metrics:
      loc: 45
      complexity: 5 # Ciclomática
    
    # --- DISEÑO (Humano + IA) ---
    description: "Toma un diccionario crudo y lo convierte en DataFrame normalizado."
    
    logic: |
      1. Validar que 'data' no esté vacío.
      2. Si strict=True, verificar schema con Pydantic.
      3. Normalizar columnas usando 'standard_mapping'.
      4. Retornar DataFrame de Pandas.
      
    tests:
      - name: "Empty Data"
        input: {}
        expect: ValueError
      - name: "Valid Data"
        input: {id: 1, val: "A"}
        expect: DataFrame(rows=1)
```

---

## 4. Flujo de Trabajo (Ciclo de Vida)

### FASE 0: Sync Up (Automatizado)
Antes de empezar cualquier diseño, el estado actual del código en `main` debe reflejarse en `design` para tener la foto real.
1.  **Script de Sincronización:** Lee el código de `main`.
2.  **Acción:**
    *   Actualiza `signature`, `metrics` y `dependencies`.
    *   Detecta y extrae **nuevos tests** que hayan aparecido en el código.
3.  **Nota Importante:** **Jamás modifica el campo `logic`**. La lógica es territorio humano/diseño.

### FASE 1: Diseño & Propuesta
*Contexto: Rama `design`*
1.  **Humano:** "Quiero añadir validación de email a `process_data`."
2.  **IA:** Modifica `blueprints/autocode/core/processor.yaml`.
    *   Actualiza `logic` añadiendo el paso de validación.
    *   Añade un caso en `tests` ("Email Inválido -> Error").
3.  **Revisión:** El humano lee el YAML (fácil de entender) y aprueba.
4.  **Commit:** Se guarda el nuevo diseño en la rama `design`.

### FASE 2: Implementación (IA)
*Contexto: Rama `dev/feature-email-val`*
1.  **Branch:** Se crea una rama temporal desde `main`.
2.  **Lectura:** La IA lee el YAML aprobado de `design`.
3.  **Codificación:**
    *   La IA escribe el código Python/JS necesario para cumplir la `logic`.
    *   La IA escribe los tests unitarios (`pytest`) necesarios para cumplir los `tests` del YAML.
4.  **Ejecución:** Se corren los tests. Si fallan, la IA corrige el código (NO el diseño).

### FASE 3: Verificación & Merge
1.  **Pull Request:** La IA abre un PR hacia `main`.
2.  **Check Automático:**
    *   ¿El código cumple las firmas del diseño?
    *   ¿Los tests pasan?
    *   ¿La complejidad ciclomática está dentro de límites?
3.  **Aprobación Humana:** El humano revisa y aprueba el PR. **Paso obligatorio**.
4.  **Merge:** Se fusiona a `main`.

---

## 5. El "Loop de Realidad" (Manejo de Excepciones)

¿Qué pasa si durante la **Fase 2 (Implementación)** la IA descubre que el diseño es imposible o ineficiente?

1.  **Detener:** La IA pausa la codificación.
2.  **Design Change Request (DCR):** La IA propone un cambio al archivo YAML en la rama `design`.
3.  **Aprobación:** El humano aprueba el cambio de diseño.
4.  **Rebase:** La rama de desarrollo actualiza su referencia de diseño y continúa.

**Regla:** Nunca se cambia la lógica en el código sin antes cambiarla en el diseño.

---

## 6. UX: Design Studio

Para facilitar este flujo, se desarrollará una interfaz web (`autocode/web/`) que permita:
1.  **Explorar Blueprints:** Visualizar el árbol de archivos de diseño (.yaml).
2.  **Diff Visual:** Ver cambios propuestos en la lógica (YAML diff).
3.  **Commit Planner:** Ver la lista de pasos que la IA ejecutará (en formato .yaml).
