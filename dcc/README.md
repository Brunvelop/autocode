# DCC - Document-Code Compression

> "El código es la implementación, el DCC es la esencia"

## ¿Qué es un DCC?

Un **DCC** (Document-Code Compression) es un documento ultra-denso que captura la arquitectura y patrones de un sistema de forma **bidireccional**:

- **Código → DCC**: Dado el código, puedes extraer su DCC analizando axiomas, contratos e invariantes
- **DCC → Código**: Dado el DCC, diferentes programadores pueden generar código **isomórfico** (misma estructura, diferente implementación)

## Filosofía

### 1. Compresión, no Documentación

Un DCC NO es documentación tradicional. Es una **semilla generativa** que contiene las restricciones mínimas necesarias para reproducir un sistema.

```
Código fuente     →  10,000+ líneas
DCC               →  ~200 líneas
Ratio compresión  →  50:1
```

### 2. Bidireccionalidad

```
┌─────────┐         ┌─────────┐
│  CÓDIGO │ ←─────→ │   DCC   │
└─────────┘         └─────────┘
     ↑                   ↑
     │   Isomorfismo     │
     │   estructural     │
     └───────────────────┘
```

El DCC y el código son **representaciones equivalentes** del mismo sistema en diferentes niveles de abstracción.

### 3. Convergencia

Dado un DCC, diferentes programadores producirán implementaciones **distintas pero equivalentes**:

- Mismos axiomas respetados
- Mismos contratos implementados
- Mismos patrones aplicados
- Diferente estilo, nombres, organización interna

### 4. Verificabilidad

Los invariantes de un DCC son **testeables**. Si el código viola un axioma, hay un bug o el DCC está desactualizado.

---

## Estructura de un DCC

Todo DCC debe contener estas secciones (en orden):

### AXIOMAS
Verdades fundamentales no negociables. Si se violan, el sistema deja de funcionar.
```
A1. Nombre del axioma
    → Explicación concisa
```

### CONTRATOS
Interfaces, tipos y estructuras que definen los límites del sistema.
```python
NombreContrato:
    campo: Tipo  # Descripción
```

### TOPOLOGÍA
Diagrama ASCII del grafo de dependencias. Qué conoce a qué.
```
Módulo A ← Módulo B ← Módulo C
(Las flechas apuntan hacia lo que se conoce)
```

### PATRONES
Patrones de diseño recurrentes con su entrada, proceso, salida e invariantes.
```
Patrón: Nombre
Entrada:    ...
Proceso:    ...
Salida:     ...
Invariante: ...
```

### INVARIANTES
Propiedades que siempre son verdaderas, expresadas en notación semi-formal.
```
∀ x ∈ Conjunto:
    propiedad(x) = true
```

### TRANSFORMACIONES
Mapeos explícitos entre representaciones (tipos, formatos, capas).
```
Entrada  ──────────►  Salida
  A                     A'
  B                     B'
```

### FLUJO DE VIDA
El ciclo completo de un elemento desde su creación hasta su consumo.

### ANTI-PATRONES
Lo que NO hacer, con la solución correcta.
```
✗ Acción incorrecta
  → Solución correcta
```

### EXTENSIÓN
Recetas de pasos mínimos para casos comunes de extensión.

### VERIFICACIÓN
Comandos o scripts para validar que el código respeta el DCC.

---

## Cómo Crear un DCC

### Paso 1: Identificar Axiomas
Pregúntate: "¿Qué reglas, si se rompen, destruyen el sistema?"

### Paso 2: Extraer Contratos
Busca las interfaces/tipos que son el "pegamento" entre módulos.

### Paso 3: Dibujar Topología
Mapea las dependencias. ¿Quién importa a quién?

### Paso 4: Reconocer Patrones
Identifica estructuras repetidas en el código.

### Paso 5: Formalizar Invariantes
Convierte las "reglas implícitas" en propiedades explícitas.

### Paso 6: Documentar Transformaciones
¿Cómo fluyen los datos entre capas?

### Paso 7: Definir Anti-patrones
¿Qué errores son comunes y cómo evitarlos?

---

## Cómo Leer un DCC (para regenerar código)

1. **Lee los AXIOMAS** - Son las restricciones fundamentales
2. **Implementa los CONTRATOS** - Son tu API interna
3. **Respeta la TOPOLOGÍA** - Define la arquitectura de imports
4. **Aplica los PATRONES** - Son las recetas de implementación
5. **Verifica los INVARIANTES** - Son tus tests de arquitectura
6. **Evita los ANTI-PATRONES** - Son trampas conocidas

---

## Estructura de Carpeta

Esta carpeta espeja la estructura del código:

```
dcc/
├── README.md        # Este archivo
├── autocode.md      # DCC raíz del proyecto
├── core/            # DCCs de autocode/core/
├── interfaces/      # DCCs de autocode/interfaces/
└── web/             # DCCs de autocode/web/
```

---

## Convenciones

- **Nombre de archivo**: Mismo que el módulo/paquete que describe
- **Formato**: Markdown con bloques de código
- **Diagramas**: ASCII art (para ser diff-friendly en git)
- **Longitud**: Máximo ~300 líneas por DCC
- **Lenguaje**: Español (igual que el equipo)

### Granularidad

Un módulo merece un **DCC único** cuando:
- Los axiomas aplican a todos sus archivos
- Hay un patrón arquitectónico unificador
- Los archivos comparten el mismo dominio semántico

Si los submódulos tienen axiomas independientes → **un DCC por submódulo**.

---

## Relación con ARCHITECTURE.md

| ARCHITECTURE.md | DCC |
|-----------------|-----|
| Narrativo | Estructurado |
| Explica "por qué" | Define "qué restricciones" |
| Para humanos nuevos | Para regenerar código |
| Puede ser largo | Máximo comprimido |
| Un solo archivo | Uno por módulo |

**Pueden coexistir**: ARCHITECTURE.md para onboarding, DCC para la "semilla" del código.

---

> **Meta-nota**: Este README es, en cierto sentido, el "DCC del formato DCC" 🌀
