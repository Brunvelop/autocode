# Task Template: Guía para Crear Tasks Independientes y Completas

## Estructura del Template

```markdown
# Task XXX: [Título Descriptivo de la Tarea]

## Contexto del Proyecto
[Proporciona una visión general breve pero completa del proyecto entero, su propósito, componentes clave y tecnologías utilizadas. Explica cómo esta task encaja en el panorama general SIN referenciar otras tasks. Incluye convenciones relevantes del proyecto como gestión de dependencias (ej. usar uv), estructura de directorios, o estándares de código.]

## Estado Actual [del Componente o Área Afectada]
[Describe la implementación actual en detalle. Incluye:
- Rutas de archivos relevantes (ej. autocode/cli.py)
- Fragmentos completos de código de la estructura, funciones o clases existentes
- Cualquier comportamiento, output o limitación actual
Usa bloques de código para mostrar el código actual exacto, haciéndolo listo para copiar-pegar como referencia.]

### Estructura Completa Actual
```python
# Código completo actual con contexto
# Incluir imports, estructura de clases/funciones, etc.
```

### Ejemplos de [Handlers/Funciones/Componentes] Actuales
```python
# Ejemplos específicos del código existente
# Mostrar el funcionamiento actual
```

### [Configuración/Dependencias/Otros] Relevantes
```python
# Cualquier configuración, dependencias o código relacionado
# que sea necesario para entender el contexto
```

## Objetivo de la [Refactorización/Implementación/Mejora]
[Establece claramente qué logra esta task. Explica los beneficios (ej. mejor mantenibilidad, consistencia). Especifica requerimientos no funcionales como preservar comportamiento existente o lograr cierta cobertura.]

## Instrucciones Paso a Paso

### 1. [Primer Paso - ej. Instalar Dependencias]
```bash
# Comandos exactos a ejecutar
uv add [paquete]
```

### 2. [Segundo Paso - ej. Refactorizar Estructura Principal]
[Descripción del cambio]

```python
# Código nuevo completo
# Incluir toda la estructura necesaria
```

### 3. [Tercer Paso - ej. Convertir Componentes Específicos]
[Instrucciones detalladas]

```python
# Ejemplos específicos de los cambios
# Mostrar antes y después si es relevante
```

### 4. [Manejar Casos Complejos]
[Para casos especiales o complejos:]

```python
# Código para manejar casos edge
# Explicar el razonamiento
```

### 5. [Actualizar Configuración/Imports]
```python
# Cambios necesarios en imports, configuración, etc.
```

## Criterios de Verificación

### Comandos a Probar
1. **[Caso 1]**: `comando` debe mostrar [resultado esperado]
2. **[Caso 2]**: `comando` debe funcionar con [parámetros]
3. **[Caso 3]**: `comando` debe manejar [caso edge]

### Verificaciones Específicas
- [Criterio 1]: [Descripción específica y cómo verificarlo]
- [Criterio 2]: [Métrica o comportamiento esperado]
- [Criterio 3]: [Pruebas de no-regresión]

### Comparación Antes/Después
[Si es refactorización:]
Para al menos X comandos/funciones:
1. Ejecutar implementación anterior y guardar output
2. Ejecutar nueva implementación y comparar output
3. Verificar que sean idénticos

### [Verificaciones Adicionales]
[Tests específicos, métricas de cobertura, etc.]

## Template de Commit Message
```
[type]([scope]): [descripción corta en inglés]

- [Bullet point de cambio específico 1]
- [Bullet point de cambio específico 2]
- [Bullet point de cambio específico 3]
- [Cualquier impacto o nota adicional]
```
```

## Principios Clave para Escribir Tasks

### 1. **Independencia Total**
- Cada task debe ser implementable sin leer otras tasks
- Incluir todo el contexto necesario dentro de la task
- No asumir conocimiento previo del codebase
- Una task = un commit atómico

### 2. **Contexto Suficiente**
- **Contexto del Proyecto**: Visión general del proyecto completo
- **Estado Actual**: Código existente con ejemplos completos  
- **Objetivo**: Qué se logra y por qué es valioso
- **Instrucciones**: Pasos detallados y ejecutables
- **Verificación**: Cómo confirmar que funciona correctamente

### 3. **Código Completo y Ejecutable**
- Incluir fragmentos completos de código, no parciales
- Mostrar estructura completa de archivos cuando sea relevante
- Proporcionar comandos exactos (con flags y parámetros)
- Incluir ejemplos de input/output esperados

### 4. **Estructura Clara**
- Usar títulos descriptivos (## y ###)
- Agrupar código relacionado en bloques
- Separar claramente instrucciones de verificación
- Mantener orden lógico: contexto → estado → objetivo → implementación → verificación

### 5. **Verificación Robusta**
- Incluir múltiples formas de verificar (manual y automática)
- Especificar outputs esperados exactos
- Incluir casos edge y manejo de errores
- Proporcionar métricas objetivas (cobertura, performance, etc.)

## Ejemplos de Buenos Contextos de Proyecto

### Para Proyectos Python con CLI
```markdown
## Contexto del Proyecto
Este proyecto, [nombre], es una herramienta para [propósito]. Su responsabilidad principal es [función principal], incluyendo [funcionalidades específicas]. El proyecto utiliza:

- **Python** con gestión de dependencias via `uv`
- **[Framework/Librería]** para [propósito específico]  
- **Estructura modular** en `[directorio]/` como paquete principal
- **CLI** implementado con [argparse/Typer/etc.]
- **Tests** organizados en directorio `tests/`

### Módulos Core del Proyecto
```python
# Imports principales que usa el sistema
from .core.[módulo] import [Clases]
from .api.models import [Modelos]
```
```

### Para Proyectos Web/API
```markdown
## Contexto del Proyecto  
Este proyecto autocode tiene una API [FastAPI/Flask/etc.] que [propósito de la API]. El objetivo es [objetivo específico]. El proyecto usa:

- **[Framework]** para la API REST
- **Estructura modular** con separación entre lógica y presentación
- **[Base de datos/Storage]** para persistencia
- **[Autenticación/Autorización]** si aplica
```

## Antipatrones a Evitar

### ❌ Referencias a Otras Tasks
```markdown
# MAL
## Contexto
Después de completar la task anterior de refactorización CLI...

# BIEN  
## Contexto del Proyecto
Este proyecto autocode utiliza un CLI basado en [tecnología] para manejar comandos como [ejemplos]...
```

### ❌ Código Incompleto
```markdown
# MAL
```python
def function():
    # ... resto del código
```

# BIEN
```python
def function(param1: str, param2: Optional[int] = None) -> int:
    """Complete function with full implementation."""
    project_root = Path.cwd()
    config = load_config()
    # ... código completo
    return result
```
```

### ❌ Instrucciones Vagas
```markdown
# MAL
3. Actualizar el CLI para usar Typer

# BIEN
3. Refactorizar la Estructura Principal
Reemplazar el argparse con Typer app:

```python
import typer
from typing import Optional, List

app = typer.Typer(help="Automated code quality and development tools")

@app.command("check-docs")
def check_docs(
    doc_index_output: Optional[str] = typer.Option(None, "--doc-index-output", help="Override output path")
) -> int:
    """Check if documentation is up to date"""
    # Mantener la lógica actual exactamente igual
    project_root = Path.cwd()
    # ... resto de implementación
```
```

### ❌ Verificación Insuficiente
```markdown
# MAL
## Verificación
- Ejecutar tests
- Verificar que funciona

# BIEN
## Criterios de Verificación

### Comandos a Probar
1. **Help general**: `uv run autocode --help` debe mostrar todos los comandos
2. **Help específico**: `uv run autocode check-docs --help` debe mostrar opciones del comando
3. **Funcionamiento**: `uv run autocode check-docs` debe ejecutar igual que antes

### Verificaciones Específicas
- El output de cada comando debe ser **idéntico** al anterior
- Los códigos de retorno (0 para éxito, 1 para error) deben mantenerse
- Ejecutar `pytest` si hay tests existentes - todos deben pasar
```

## Checklist para Revisar Tasks

### ✅ Antes de Escribir
- [ ] ¿La task es implementable por alguien que nunca vio este código?
- [ ] ¿Incluye todo el contexto necesario del proyecto?
- [ ] ¿Es una unidad de trabajo atómica (un commit)?

### ✅ Durante la Escritura
- [ ] ¿El contexto explica el proyecto completo brevemente?
- [ ] ¿El estado actual incluye código completo y funcional?
- [ ] ¿Las instrucciones son paso-a-paso y ejecutables?
- [ ] ¿Cada comando/código es copy-paste ready?

### ✅ Después de Escribir
- [ ] ¿Un programador nuevo podría implementar esto sin ayuda?
- [ ] ¿Los criterios de verificación son objetivos y completos?
- [ ] ¿El commit message refleja exactamente lo que se implementa?
- [ ] ¿No hay referencias a otras tasks o conocimiento externo?

## Uso de Este Template

1. **Copia** la estructura del template
2. **Reemplaza** cada sección con contenido específico de tu task
3. **Incluye** código completo y comandos exactos
4. **Verifica** que sea independiente y completa
5. **Prueba** mentalmente: ¿podría un nuevo programador implementar esto?

Una good task es aquella que permite a cualquier programador, sin conocimiento previo del proyecto, implementar la solución completa en un solo commit siguiendo las instrucciones exactas proporcionadas.
