# Guía Completa de OpenCode: Modo Headless y Automatización

## Índice
1. [Introducción y Modo Headless](#introducción-y-modo-headless)
2. [Instalación Rápida](#instalación-rápida)
3. [Configuración para Modo Headless](#configuración-para-modo-headless)
4. [Modo No Interactivo (Headless) - Guía Completa](#modo-no-interactivo-headless---guía-completa)
5. [Ejemplos Reales Probados en Modo Headless](#ejemplos-reales-probados-en-modo-headless)
6. [Herramientas Automáticas del Asistente IA](#herramientas-automáticas-del-asistente-ia)
7. [Scripts de Automatización](#scripts-de-automatización)
8. [Integración en Pipelines CI/CD](#integración-en-pipelines-cicd)
9. [Casos de Uso Avanzados](#casos-de-uso-avanzados)
10. [Mejores Prácticas para Automatización](#mejores-prácticas-para-automatización)

---

## Introducción y Modo Headless

OpenCode es un asistente de IA terminal construido en Go que ofrece dos modos de operación. El **modo headless (no interactivo)** es su funcionalidad más poderosa para automatización, scripting e integración en pipelines de desarrollo.

### ¿Qué es el Modo Headless?

El modo headless permite ejecutar OpenCode sin interfaz gráfica, ideal para:
- **Automatización de tareas** de desarrollo
- **Integración en scripts** bash/PowerShell
- **Pipelines CI/CD** automatizados
- **Análisis programático** de código
- **Generación automática** de documentación
- **Monitoreo continuo** de calidad de código

### Características Clave del Modo Headless

- ✅ **Auto-aprobación de permisos** - Sin intervención manual
- ✅ **Salida directa a stdout** - Fácil integración con scripts
- ✅ **Formato JSON estructurado** - Para procesamiento automático
- ✅ **Modo silencioso** - Sin spinners para scripts
- ✅ **Herramientas automáticas** - La IA usa herramientas sin preguntar
- ✅ **Cambio de directorio** - Análisis de proyectos específicos

---

## Instalación Rápida

### Windows (Recomendado - Go Install)
```bash
go install github.com/opencode-ai/opencode@latest
```

### Linux/macOS (Script de Instalación)
```bash
curl -fsSL https://raw.githubusercontent.com/opencode-ai/opencode/refs/heads/main/install | bash
```

### Verificación de Instalación
```bash
opencode --help
```

---

## Configuración para Modo Headless

### Archivo de Configuración Básico

Crear `.opencode.json` en el directorio del proyecto:

```json
{
  "providers": {
    "anthropic": {
      "apiKey": "sk-ant-...",
      "disabled": false
    }
  },
  "agents": {
    "coder": {
      "model": "claude-4-sonnet",
      "maxTokens": 8192
    },
    "task": {
      "model": "claude-4-sonnet",
      "maxTokens": 4000
    },
    "quick": {
      "model": "claude-4-sonnet",
      "maxTokens": 1500
    }
  },
  "debug": false,
  "autoCompact": true
}
```

### Configuración Optimizada para Automatización

```json
{
  "providers": {
    "anthropic": {
      "apiKey": "sk-ant-...",
      "disabled": false
    }
  },
  "agents": {
    "automation": {
      "model": "claude-4-sonnet",
      "maxTokens": 8192,
      "reasoningEffort": "high"
    },
    "analysis": {
      "model": "claude-4-sonnet",
      "maxTokens": 6000
    },
    "quick": {
      "model": "claude-4-sonnet",
      "maxTokens": 2000
    }
  },
  "shell": {
    "path": "/bin/bash",
    "args": ["-l"]
  },
  "debug": false,
  "autoCompact": true
}
```

### ⚠️ Protección de Seguridad (CRÍTICO)

**SIEMPRE** añadir a `.gitignore`:
```gitignore
# OpenCode configuration (contains API keys)
.opencode.json
.opencode/
```

**SIEMPRE** añadir a `.clineignore`:
```
# OpenCode configuration (contains API keys)
.opencode.json
.opencode/
```

---

## Modo No Interactivo (Headless) - Guía Completa

### Sintaxis Básica

```bash
opencode -p "tu prompt aquí" [opciones]
```

### Flags Esenciales para Modo Headless

| Flag | Corto | Descripción | Uso en Automatización |
|------|-------|-------------|----------------------|
| `--prompt` | `-p` | Prompt único en modo no interactivo | **OBLIGATORIO** |
| `--quiet` | `-q` | Ocultar spinner | **RECOMENDADO** para scripts |
| `--output-format` | `-f` | Formato de salida (text, json) | **JSON** para procesamiento |
| `--cwd` | `-c` | Directorio de trabajo | Para análisis de proyectos |
| `--debug` | `-d` | Modo debug | Solo para troubleshooting |

### Ejemplos de Sintaxis

```bash
# Básico
opencode -p "Analiza este código" -q

# Con formato JSON
opencode -p "Genera reporte" -f json -q

# Cambiar directorio
opencode -c /path/to/project -p "Analiza estructura" -q

# Completo para automatización
opencode -c /path/to/project -p "Análisis completo" -f json -q > report.json
```

---

## Ejemplos Reales Probados en Modo Headless

### Configuración Probada Exitosamente

```json
{
  "providers": {
    "anthropic": {
      "apiKey": "sk-ant-...",
      "disabled": false
    }
  },
  "agents": {
    "coder": {
      "model": "claude-4-sonnet",
      "maxTokens": 64000
    }
  },
  "debug": false,
  "autoCompact": true
}
```

### 1. Prueba de Conectividad ✅

```bash
opencode -p "Hola, ¿puedes confirmar que estás funcionando correctamente?" -q
```

**Resultado:**
```
Sí, estoy funcionando correctamente. Puedo ver tu directorio con el archivo test_example.py.
```

### 2. Análisis con Formato JSON ✅

```bash
opencode -p "Analiza brevemente el archivo test_example.py" -f json -q
```

**Resultado:**
```json
{
  "response": "El archivo contiene una implementación recursiva básica de Fibonacci con un TODO para optimización. Calcula el 10º número de la secuencia e imprime el resultado."
}
```

### 3. Uso Automático de Herramientas ✅

```bash
opencode -p "Usa la herramienta view para leer el archivo test_example.py y luego propón una optimización para la función de Fibonacci" -q
```

**Resultado:**
```
Optimización aplicada: cambié la recursión simple por memoización, reduciendo la complejidad de O(2^n) a O(n). Ahora almacena resultados calculados para evitar recálculos.
```

### 4. Generación Automática de Código ✅

```bash
opencode -p "Lee el archivo test_example.py, optimízalo usando memoización, y crea un nuevo archivo llamado fibonacci_optimized.py con la versión mejorada" -q
```

**Resultado:** Generó archivo completo (1022 bytes) con:
- Memoización usando `@lru_cache(maxsize=None)`
- Implementación iterativa alternativa
- Múltiples casos de prueba [10, 20, 30, 50]
- Documentación profesional con docstrings

### 5. Análisis Completo de Proyecto ✅

```bash
opencode -p "Lista todos los archivos en el directorio actual y analiza la estructura del proyecto" -q
```

**Resultado:**
```
El proyecto contiene 2 archivos Python:
- fibonacci_optimized.py - implementación optimizada de Fibonacci
- test_example.py - archivo de pruebas

Es un proyecto simple de Python enfocado en algoritmos de Fibonacci con sus respectivas pruebas.
```

### 6. Reporte Detallado en JSON ✅

```bash
opencode -p "Genera un reporte completo del proyecto incluyendo: 1) Lista de archivos, 2) Análisis de cada archivo Python, 3) Recomendaciones de mejora, 4) Estructura sugerida" -f json -q
```

**Resultado:** Reporte profesional de 2KB+ que identificó:
- **Bug crítico**: Diccionario mutable como parámetro por defecto (`memo={}`)
- **Análisis detallado** de cada archivo
- **Recomendaciones específicas**: Type hints, tests unitarios, manejo de errores
- **Estructura de proyecto** siguiendo estándares de la industria

---

## Herramientas Automáticas del Asistente IA

En modo headless, OpenCode usa automáticamente estas herramientas sin preguntar:

### Herramientas de Archivos (Probadas ✅)

#### `view` - Leer archivos ✅
```bash
opencode -p "Revisa el contenido del archivo main.py y explica qué hace"
```

#### `write` - Crear archivos ✅
```bash
opencode -p "Crea un archivo utils.py con funciones de utilidad para el proyecto"
```

#### `ls` - Listar directorios ✅
```bash
opencode -p "Lista todos los archivos del proyecto y categorízalos por tipo"
```

#### `grep` - Buscar en archivos
```bash
opencode -p "Busca todas las funciones que contengan 'error' o 'exception' en el código"
```

#### `edit` - Modificar archivos
```bash
opencode -p "Optimiza la función calculate_fibonacci en el archivo main.py"
```

#### `patch` - Aplicar cambios específicos
```bash
opencode -p "Aplica el patrón singleton a la clase DatabaseManager"
```

### Herramientas del Sistema

#### `bash` - Ejecutar comandos
```bash
opencode -p "Ejecuta 'git status' y analiza el estado del repositorio"
```

#### `fetch` - Obtener datos de URLs
```bash
opencode -p "Obtén la documentación de la API desde https://api.example.com/docs"
```

#### `sourcegraph` - Buscar código público
```bash
opencode -p "Busca ejemplos de implementación de JWT en repositorios públicos"
```

#### `agent` - Sub-tareas complejas
```bash
opencode -p "Analiza el rendimiento del código y propón optimizaciones específicas"
```

---

## Scripts de Automatización

### 1. Análisis Diario de Código

```bash
#!/bin/bash
# daily_code_analysis.sh

PROJECT_PATH="$1"
REPORT_DIR="reports/$(date +%Y-%m-%d)"
mkdir -p "$REPORT_DIR"

echo "🔍 Iniciando análisis diario de código..."

# Análisis de calidad
opencode -c "$PROJECT_PATH" -p "
Genera un análisis diario de calidad de código:
1. Nuevos TODOs y FIXMEs añadidos
2. Funciones con alta complejidad ciclomática
3. Archivos que necesitan refactoring
4. Patrones de código problemáticos
5. Recomendaciones prioritarias para hoy
" -f json -q > "$REPORT_DIR/quality_analysis.json"

# Análisis de seguridad
opencode -c "$PROJECT_PATH" -p "
Realiza un análisis de seguridad enfocado en:
1. Vulnerabilidades de inyección SQL
2. Validación de entrada insuficiente
3. Manejo inseguro de credenciales
4. Exposición de datos sensibles
5. Configuraciones de seguridad débiles
" -f json -q > "$REPORT_DIR/security_analysis.json"

# Análisis de rendimiento
opencode -c "$PROJECT_PATH" -p "
Analiza el rendimiento del código:
1. Consultas de base de datos ineficientes
2. Algoritmos con complejidad alta
3. Uso excesivo de memoria
4. Cuellos de botella en loops
5. Oportunidades de optimización
" -f json -q > "$REPORT_DIR/performance_analysis.json"

echo "✅ Análisis completado. Reportes en $REPORT_DIR/"
```

### 2. Generación Automática de Documentación

```bash
#!/bin/bash
# auto_documentation.sh

PROJECT_PATH="$1"
DOCS_DIR="docs/auto-generated"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$DOCS_DIR"

echo "📚 Generando documentación automática..."

# README principal
opencode -c "$PROJECT_PATH" -p "
Genera un README.md completo y profesional:
1. Descripción clara del proyecto y su propósito
2. Instrucciones detalladas de instalación
3. Ejemplos de uso con código
4. Guía de configuración
5. Información de contribución y licencia
6. Badges de estado del proyecto
" -q > "README.md"

# Documentación de API
opencode -c "$PROJECT_PATH" -p "
Crea documentación completa de API:
1. Endpoints disponibles con métodos HTTP
2. Parámetros de entrada y validaciones
3. Ejemplos de requests y responses
4. Códigos de error y su significado
5. Autenticación y autorización
6. Rate limiting y mejores prácticas
" -q > "$DOCS_DIR/api_documentation.md"

# Guía de arquitectura
opencode -c "$PROJECT_PATH" -p "
Documenta la arquitectura del sistema:
1. Diagrama de componentes principales
2. Flujo de datos entre módulos
3. Patrones de diseño utilizados
4. Decisiones arquitectónicas importantes
5. Dependencias externas
6. Guía para nuevos desarrolladores
" -q > "$DOCS_DIR/architecture_guide.md"

# Changelog automático
opencode -c "$PROJECT_PATH" -p "
Genera un CHANGELOG.md basado en commits recientes:
1. Nuevas funcionalidades añadidas
2. Bugs corregidos
3. Mejoras de rendimiento
4. Cambios breaking
5. Deprecaciones
" -q > "CHANGELOG.md"

echo "✅ Documentación generada en $DOCS_DIR/"
```

### 3. Pre-commit Hook Inteligente

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "🤖 Ejecutando análisis pre-commit con OpenCode..."

# Análisis de archivos modificados
MODIFIED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|js|ts|go|java)$')

if [ -z "$MODIFIED_FILES" ]; then
    echo "✅ No hay archivos de código modificados"
    exit 0
fi

# Crear reporte temporal
TEMP_REPORT="/tmp/opencode_precommit_$(date +%s).json"

# Análisis de calidad de archivos modificados
opencode -p "
Analiza los siguientes archivos modificados para commit:
$(echo "$MODIFIED_FILES" | tr '\n' ' ')

Verifica:
1. Calidad del código y mejores prácticas
2. Posibles bugs o errores lógicos
3. Cumplimiento de estándares de codificación
4. Seguridad y vulnerabilidades
5. Rendimiento y optimizaciones

Responde con 'APPROVED' si todo está bien, o 'REJECTED' con razones específicas.
" -f json -q > "$TEMP_REPORT"

# Verificar resultado
RESULT=$(cat "$TEMP_REPORT" | jq -r '.response' | head -1)

if [[ "$RESULT" == *"REJECTED"* ]]; then
    echo "❌ Commit rechazado por OpenCode:"
    cat "$TEMP_REPORT" | jq -r '.response'
    rm "$TEMP_REPORT"
    exit 1
else
    echo "✅ Commit aprobado por OpenCode"
    rm "$TEMP_REPORT"
    exit 0
fi
```

---

## Integración en Pipelines CI/CD

### GitHub Actions con OpenCode

```yaml
# .github/workflows/opencode_analysis.yml
name: OpenCode AI Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  ai-code-review:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      with:
        fetch-depth: 0
    
    - name: Install OpenCode
      run: |
        curl -fsSL https://raw.githubusercontent.com/opencode-ai/opencode/refs/heads/main/install | bash
        echo "$HOME/.local/bin" >> $GITHUB_PATH
    
    - name: AI Code Analysis
      env:
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      run: |
        mkdir -p reports
        
        # Análisis completo
        opencode -p "
        Realiza un análisis completo del código:
        1. Calidad general y mejores prácticas
        2. Posibles bugs y vulnerabilidades
        3. Oportunidades de optimización
        4. Cumplimiento de estándares
        5. Recomendaciones específicas
        
        Genera un reporte detallado en formato JSON.
        " -f json -q > reports/analysis.json
    
    - name: Generate Summary
      run: |
        # Extraer resumen para comentario
        jq -r '.response' reports/analysis.json > reports/summary.txt
    
    - name: Comment PR
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const summary = fs.readFileSync('reports/summary.txt', 'utf8');
          
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: `## 🤖 OpenCode AI Analysis\n\n${summary}`
          });
    
    - name: Upload Reports
      uses: actions/upload-artifact@v3
      with:
        name: opencode-reports
        path: reports/
```

### GitLab CI con OpenCode

```yaml
# .gitlab-ci.yml
stages:
  - analysis

opencode_analysis:
  stage: analysis
  image: golang:1.21
  
  before_script:
    - go install github.com/opencode-ai/opencode@latest
  
  script:
    - mkdir -p reports
    
    # Análisis de calidad
    - |
      opencode -p "
      Analiza la calidad del código en este proyecto:
      1. Estructura y organización
      2. Patrones de diseño
      3. Deuda técnica
      4. Métricas de complejidad
      5. Recomendaciones de mejora
      " -f json -q > reports/quality.json
    
    # Análisis de seguridad
    - |
      opencode -p "
      Realiza un análisis de seguridad:
      1. Vulnerabilidades conocidas
      2. Configuraciones inseguras
      3. Manejo de datos sensibles
      4. Validación de entrada
      5. Medidas de mitigación
      " -f json -q > reports/security.json
  
  artifacts:
    reports:
      junit: reports/*.json
    paths:
      - reports/
    expire_in: 1 week
  
  only:
    - merge_requests
    - main
```

---

## Casos de Uso Avanzados

### 1. Monitoreo Continuo de Calidad

```bash
#!/bin/bash
# continuous_quality_monitor.sh

PROJECT_PATH="$1"
WEBHOOK_URL="$2"  # Slack/Teams webhook
THRESHOLD_SCORE=7  # Puntuación mínima de calidad

while true; do
    echo "🔍 Ejecutando monitoreo de calidad..."
    
    # Análisis de calidad
    QUALITY_REPORT=$(opencode -c "$PROJECT_PATH" -p "
    Evalúa la calidad del código en una escala de 1-10:
    1. Legibilidad y mantenibilidad
    2. Cumplimiento de estándares
    3. Cobertura de tests
    4. Documentación
    5. Deuda técnica
    
    Responde solo con el número de puntuación seguido de un resumen breve.
    " -q)
    
    # Extraer puntuación
    SCORE=$(echo "$QUALITY_REPORT" | grep -o '^[0-9]' | head -1)
    
    if [ "$SCORE" -lt "$THRESHOLD_SCORE" ]; then
        # Enviar alerta
        curl -X POST "$WEBHOOK_URL" \
             -H 'Content-Type: application/json' \
             -d "{
                 \"text\": \"⚠️ Alerta de Calidad de Código\",
                 \"attachments\": [{
                     \"color\": \"danger\",
                     \"fields\": [{
                         \"title\": \"Puntuación\",
                         \"value\": \"$SCORE/10\",
                         \"short\": true
                     }, {
                         \"title\": \"Proyecto\",
                         \"value\": \"$PROJECT_PATH\",
                         \"short\": true
                     }, {
                         \"title\": \"Detalles\",
                         \"value\": \"$QUALITY_REPORT\"
                     }]
                 }]
             }"
    fi
    
    # Esperar 1 hora antes del próximo check
    sleep 3600
done
```

### 2. Generador de Tests Automático

```bash
#!/bin/bash
# auto_test_generator.sh

PROJECT_PATH="$1"
TEST_DIR="tests/auto-generated"

mkdir -p "$TEST_DIR"

echo "🧪 Generando tests automáticos..."

# Encontrar archivos sin tests
FILES_WITHOUT_TESTS=$(opencode -c "$PROJECT_PATH" -p "
Lista todos los archivos de código que NO tienen tests correspondientes.
Responde solo con los nombres de archivo, uno por línea.
" -q)

# Generar tests para cada archivo
while IFS= read -r file; do
    if [ -n "$file" ]; then
        echo "Generando tests para $file..."
        
        TEST_FILE="$TEST_DIR/test_$(basename "$file" .py).py"
        
        opencode -c "$PROJECT_PATH" -p "
        Genera tests unitarios completos para el archivo $file:
        1. Tests para todas las funciones públicas
        2. Tests de casos edge
        3. Tests de manejo de errores
        4. Mocks para dependencias externas
        5. Fixtures para datos de prueba
        
        Usa pytest como framework y sigue mejores prácticas.
        " -q > "$TEST_FILE"
        
        echo "✅ Tests generados: $TEST_FILE"
    fi
done <<< "$FILES_WITHOUT_TESTS"

echo "🎉 Generación de tests completada"
```

### 3. Refactoring Automático

```bash
#!/bin/bash
# auto_refactor.sh

PROJECT_PATH="$1"
BACKUP_DIR="backup/$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"

echo "🔧 Iniciando refactoring automático..."

# Crear backup
cp -r "$PROJECT_PATH"/* "$BACKUP_DIR/"

# Identificar código que necesita refactoring
REFACTOR_CANDIDATES=$(opencode -c "$PROJECT_PATH" -p "
Identifica archivos que necesitan refactoring urgente:
1. Funciones muy largas (>50 líneas)
2. Clases con demasiadas responsabilidades
3. Código duplicado
4. Complejidad ciclomática alta
5. Violaciones de principios SOLID

Responde con nombres de archivo y razón específica.
" -f json -q)

echo "$REFACTOR_CANDIDATES" | jq -r '.response' > "$BACKUP_DIR/refactor_plan.txt"

# Aplicar refactoring automático
opencode -c "$PROJECT_PATH" -p "
Aplica refactoring automático siguiendo estos principios:
1. Extraer funciones pequeñas y específicas
2. Eliminar código duplicado
3. Aplicar principio de responsabilidad única
4. Mejorar nombres de variables y funciones
5. Añadir documentación donde falte

Modifica los archivos directamente manteniendo la funcionalidad.
" -q

echo "✅ Refactoring completado. Backup en: $BACKUP_DIR"
echo "📋 Plan de refactoring guardado en: $BACKUP_DIR/refactor_plan.txt"
```

---

## Mejores Prácticas para Automatización

### 1. Configuración de Tokens Optimizada

```json
{
  "agents": {
    "automation": {
      "model": "claude-4-sonnet",
      "maxTokens": 8192,
      "reasoningEffort": "high"
    },
    "quick_analysis": {
      "model": "claude-4-sonnet",
      "maxTokens": 2000
    },
    "detailed_report": {
      "model": "claude-4-sonnet",
      "maxTokens": 6000
    },
    "code_generation": {
      "model": "claude-4-sonnet",
      "maxTokens": 4000
    }
  }
}
```

### 2. Manejo de Errores en Scripts

```bash
#!/bin/bash
# robust_opencode_script.sh

set -euo pipefail  # Salir en cualquier error

PROJECT_PATH="$1"
MAX_RETRIES=3
RETRY_DELAY=5

run_opencode_with_retry() {
    local prompt="$1"
    local output_file="$2"
    local retry_count=0
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        if opencode -c "$PROJECT_PATH" -p "$prompt" -f json -q > "$output_file" 2>/dev/null; then
            echo "✅ Análisis exitoso: $output_file"
            return 0
        else
            retry_count=$((retry_count + 1))
            echo "⚠️ Intento $retry_count falló, reintentando en ${RETRY_DELAY}s..."
            sleep $RETRY_DELAY
        fi
    done
    
    echo "❌ Error: Falló después de $MAX_RETRIES intentos"
    return 1
}

# Uso
run_opencode_with_retry "Analiza la calidad del código" "quality_report.json"
```

### 3. Validación de Salida JSON

```bash
#!/bin/bash
# validate_opencode_output.sh

validate_json_output() {
    local file="$1"
    
    if [ ! -f "$file" ]; then
        echo "❌ Archivo no encontrado: $file"
        return 1
    fi
    
    if ! jq empty "$file" 2>/dev/null; then
        echo "❌ JSON inválido en: $file"
        return 1
    fi
    
    if [ "$(jq -r '.response // empty' "$file")" = "" ]; then
        echo "❌ Respuesta vacía en: $file"
        return 1
    fi
    
    echo "✅ JSON válido: $file"
    return 0
}

# Ejemplo de uso
opencode -p "Analiza el código" -f json -q > output.json
validate_json_output "output.json"
```

### 4. Logging y Monitoreo

```bash
#!/bin/bash
# opencode_with_logging.sh

LOG_DIR="logs/opencode"
LOG_FILE="$LOG_DIR/$(date +%Y%m%d).log"

mkdir -p "$LOG_DIR"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

run_analysis() {
    local prompt="$1"
    local output_file="$2"
    
    log_message "🚀 Iniciando análisis: $prompt"
    
    local start_time=$(date +%s)
    
    if opencode -p "$prompt" -f json -q > "$output_file"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_message "✅ Análisis completado en ${duration}s: $output_file"
        return 0
    else
        log_message "❌ Error en análisis: $prompt"
        return 1
    fi
}

# Uso
run_analysis "Analiza la calidad del código" "quality.json"
```

### 5. Configuración de Variables de Entorno

```bash
# .env para OpenCode
export OPENCODE_CONFIG_PATH="/path/to/.opencode.json"
export OPENCODE_LOG_LEVEL="INFO"
export OPENCODE_TIMEOUT="300"
export ANTHROPIC_API_KEY="sk-ant-..."

# Script de configuración
setup_opencode_env() {
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "❌ Error: ANTHROPIC_API_KEY no configurada"
        exit 1
    fi
    
    if [ ! -f "$OPENCODE_CONFIG_PATH" ]; then
        echo "❌ Error: Archivo de configuración no encontrado"
        exit 1
    fi
    
    echo "✅ Entorno OpenCode configurado correctamente"
}
```

---

## Conclusión

El modo headless de OpenCode es una herramienta extremadamente poderosa para automatización de desarrollo. Las capacidades confirmadas incluyen:

### ✅ Funcionalidades Validadas
- **Análisis automático de código
