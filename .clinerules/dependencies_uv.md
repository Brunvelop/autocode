# Clinerule: Gestión de Dependencias con uv

## Regla Principal
SIEMPRE usar uv para gestión de dependencias en proyectos Python que tengan `pyproject.toml`.

## Comandos Obligatorios

### Añadir Dependencias
- **Dependencia de producción**: `uv add [paquete]`
- **Dependencia de desarrollo**: `uv add --dev [paquete]`
- **Dependencia específica**: `uv add [paquete]==1.2.3`
- **Dependencia con extras**: `uv add [paquete][extra]`

### Sincronización
- **Después de añadir dependencias**: `uv sync`
- **Actualizar lock file**: `uv lock --upgrade`

## Verificaciones Automáticas

### Antes de Escribir Código
1. **Verificar imports**: Antes de usar `import requests`, `from flask import`, etc.
2. **Comprobar pyproject.toml**: Verificar si la dependencia ya está listada
3. **Añadir si falta**: Usar `uv add [paquete]` si no está presente
4. **Sincronizar**: Ejecutar `uv sync` para actualizar el entorno

### Flujo de Trabajo
```bash
# 1. Detectar nueva dependencia necesaria
# 2. Añadir con uv
uv add requests

# 3. Sincronizar entorno
uv sync

# 4. Continuar con el desarrollo
```

## Comandos PROHIBIDOS
- ❌ `pip install [paquete]`
- ❌ `conda install [paquete]`
- ❌ `poetry add [paquete]`
- ❌ Modificar manualmente `pyproject.toml` para dependencias

## Comandos PERMITIDOS
- ✅ `uv add [paquete]`
- ✅ `uv add --dev [paquete]`
- ✅ `uv sync`
- ✅ `uv run [comando]`
- ✅ `uv lock --upgrade`

## Recordatorios Importantes

### Para Cline
- **NUNCA** usar pip, conda, o poetry en proyectos con `pyproject.toml`
- **SIEMPRE** verificar dependencias antes de escribir código que las requiera
- **SIEMPRE** usar `uv add` para nuevas dependencias
- **SIEMPRE** ejecutar `uv sync` después de añadir dependencias
- **VERIFICAR** que el archivo `uv.lock` se actualice correctamente

### Detección de Dependencias Faltantes
Cuando encuentres imports como:
- `import requests` → `uv add requests`
- `from flask import Flask` → `uv add flask`
- `import pytest` → `uv add --dev pytest`
- `from fastapi import FastAPI` → `uv add fastapi`

### Estructura de Archivos a Mantener
```
proyecto/
├── pyproject.toml    # Configuración y dependencias
├── uv.lock          # Lock file (mantener actualizado)
└── .venv/           # Entorno virtual
```

## Comandos de Verificación

### Verificar Estado del Proyecto
```bash
# Ver dependencias instaladas
uv pip list

# Verificar sincronización
uv sync --dry-run

# Comprobar actualizaciones disponibles
uv lock --upgrade --dry-run
```

### En Caso de Problemas
```bash
# Regenerar entorno virtual
uv sync --reinstall

# Limpiar cache
uv cache clean

# Verificar configuración
uv python list
```

## Notas Importantes
- Mantener siempre `uv.lock` en el control de versiones
- El entorno virtual `.venv/` NO debe estar en git
- Usar `uv run` para ejecutar comandos en el entorno virtual
