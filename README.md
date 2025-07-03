# Autocode - Herramientas de Desarrollo Automatizado

Herramientas automatizadas para mejorar los flujos de desarrollo en el proyecto Vidi.

## Funcionalidades

### 1. Verificador de Documentación
Script para verificar si la documentación del proyecto está actualizada comparando fechas de modificación entre archivos de código y documentación.

### 2. Analizador de Cambios Git
Herramienta para analizar cambios git y generar datos estructurados para facilitar la escritura de commits informativos.

## Instalación

El módulo es parte del proyecto Vidi y no requiere instalación separada.

## Uso

### Interfaz de Línea de Comandos

```bash
# Verificar documentación (comportamiento por defecto)
python -m autocode.cli
python -m autocode.cli check-docs

# Analizar cambios git
python -m autocode.cli git-changes

# Analizar cambios con opciones
python -m autocode.cli git-changes --output cambios.json --verbose
```

### API de Python

```python
from autocode import DocChecker, GitAnalyzer
from pathlib import Path

# Verificador de documentación
checker = DocChecker(Path.cwd())
outdated = checker.get_outdated_docs()
output = checker.format_results(outdated)
print(output)

# Analizador de git
analyzer = GitAnalyzer(Path.cwd())
changes = analyzer.analyze_changes()
print(changes)
```

## Verificador de Documentación

### Cómo Funciona

El verificador sigue una estructura de documentación modular:

1. **Documentación del Proyecto**: `docs/_index.md` - Visión general del proyecto
2. **Documentación de Módulos**: `docs/[módulo]/_module.md` - Cada directorio de código tiene documentación modular
3. **Documentación de Archivos**: `docs/[módulo]/[archivo].md` - Documentación individual de archivos

### Salida de Ejemplo

#### Documentación actualizada:
```
✅ Toda la documentación está actualizada
```

#### Documentación desactualizada:
```
❌ Documentación desactualizada encontrada:

Archivos con documentación desactualizada:
- docs/vidi/inference/engine.md (código más reciente)

Archivos sin documentación:
- docs/autocode/_module.md (documentación del módulo)
- autocode/cli.py
- autocode/doc_checker.py
```

## Analizador de Cambios Git

### Cómo Funciona

El analizador de git examina:
- **Cambios staged** (ya añadidos con `git add`)
- **Cambios unstaged** (modificaciones sin añadir)
- **Archivos untracked** (archivos nuevos)
- **Archivos eliminados**
- **Archivos renombrados**

### Salida de Ejemplo

#### Salida en consola:
```
📊 Repository Status:
   Total files changed: 3
   Modified: 1
   Added: 1
   Deleted: 0
   Untracked: 1

📄 Modified Files:
   - autocode/git_analyzer.py
   - autocode/cli.py
   - autocode/README.md

💾 Detailed changes saved to: git_changes.json
```

#### Archivo JSON generado:
```json
{
  "timestamp": "2025-01-07T09:34:00.123456",
  "repository_status": {
    "total_files": 3,
    "modified": 1,
    "added": 1,
    "deleted": 0,
    "untracked": 1,
    "renamed": 0
  },
  "modified_files": [
    "autocode/git_analyzer.py",
    "autocode/cli.py",
    "autocode/README.md"
  ],
  "changes": [
    {
      "file": "autocode/git_analyzer.py",
      "status": "untracked",
      "staged": false,
      "additions": 245,
      "deletions": 0,
      "diff": "+++ New file content:\n..."
    },
    {
      "file": "autocode/cli.py",
      "status": "modified",
      "staged": false,
      "additions": 85,
      "deletions": 12,
      "diff": "@@ -1,12 +1,85 @@\n..."
    }
  ]
}
```

### Opciones de Comando

- `--output, -o`: Especifica el archivo de salida JSON (por defecto: `git_changes.json`)
- `--verbose, -v`: Muestra información detallada de los diffs en la consola

### Estados de Archivos

- **modified**: Archivo modificado
- **added**: Archivo añadido al índice
- **deleted**: Archivo eliminado
- **untracked**: Archivo nuevo sin seguimiento
- **renamed**: Archivo renombrado
- **copied**: Archivo copiado

## Códigos de Salida

### check-docs
- `0`: Toda la documentación está actualizada
- `1`: Hay documentación desactualizada o faltante

### git-changes
- `0`: Análisis completado exitosamente
- `1`: Error durante el análisis

## Integración con Workflows

### Automatización de Commits
```bash
# Generar análisis de cambios
python -m autocode.cli git-changes

# Usar el JSON generado para escribir commits informativos
# (el archivo git_changes.json contiene toda la información necesaria)
```

### Verificación de Documentación en CI/CD
```bash
# Verificar documentación antes de commit
python -m autocode.cli check-docs
if [ $? -eq 0 ]; then
    echo "✅ Documentación actualizada"
else
    echo "❌ Actualizar documentación"
    exit 1
fi
