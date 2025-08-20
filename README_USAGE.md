# Guía de Uso - Autocode Framework

## 🚀 Servir la Aplicación

### Comandos de servidor disponibles

#### 1. Servidor Unificado (Recomendado)
```bash
uv run autocode serve
```
Inicia API + MCP en un solo proceso con mounting dinámico.

#### 2. Solo API
```bash
uv run autocode serve-api
```
Inicia únicamente el servidor API.

#### 3. Solo MCP
```bash
uv run autocode serve-mcp
```
Inicia únicamente el servidor MCP (puerto 8001 por defecto).

**Opciones disponibles para todos:**
```bash
uv run autocode serve --host 127.0.0.1 --port 8000 --reload
```

- `--host`: IP donde servir (default: 127.0.0.1)
- `--port`: Puerto a usar (default: 8000 para API/unificado, 8001 para MCP)
- `--reload`: Auto-reload en desarrollo

### Acceso según el comando:
- **serve**: 🌐 Web UI (http://127.0.0.1:8000), 🔌 API (/docs), 🤖 MCP (/sse, /mcp endpoints)
- **serve-api**: 🌐 Web UI (http://127.0.0.1:8000), 🔌 API (/docs)  
- **serve-mcp**: 🤖 MCP Server (http://127.0.0.1:8001)

---

## 💻 CLI (Command Line Interface)

### Comandos disponibles
```bash
# Ver ayuda general
uv run autocode --help

# Ejecutar función hello_world
uv run autocode hello
uv run autocode hello --name "Tu Nombre"
uv run autocode hello -n "Bruno"

# Comandos de servidor
uv run autocode serve           # API + MCP unificado
uv run autocode serve-api       # Solo API
uv run autocode serve-mcp       # Solo MCP
```

### Ejemplos prácticos:
```bash
$ uv run autocode hello
Hello, World!

$ uv run autocode hello --name Bruno
Hello, Bruno!

$ uv run autocode serve --reload
Starting Autocode unified server (API + MCP) on 127.0.0.1:8000
INFO: Uvicorn running on http://127.0.0.1:8000
```

---

## 🔌 API REST (FastAPI)

### Endpoints disponibles

#### 1. Hello World
**GET** `/hello?name=NombreAqui`
```bash
curl "http://127.0.0.1:8000/hello?name=Bruno"
# Response: {"message": "Hello, Bruno!"}
```

**POST** `/hello` (JSON body)
```bash
curl -X POST "http://127.0.0.1:8000/hello" \
  -H "Content-Type: application/json" \
  -d '{"name": "Bruno"}'
# Response: {"message": "Hello, Bruno!"}
```

#### 2. Utilidad
**GET** `/functions` - Lista funciones disponibles
```bash
curl "http://127.0.0.1:8000/functions"
# Response: {"functions": ["hello"]}
```

**GET** `/health` - Health check
```bash
curl "http://127.0.0.1:8000/health"
# Response: {"status": "healthy", "functions": 1}
```

### Documentación interactiva
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

---

## 🤖 MCP (Model Context Protocol)

### ¿Qué es MCP?
El servidor MCP expone las funciones del framework como **herramientas** que pueden ser utilizadas por aplicaciones compatibles con MCP (como Claude Desktop, IDEs, etc.).

### Herramientas disponibles via MCP:
- `hello_get`: Ejecuta hello_world via GET
- `hello_post`: Ejecuta hello_world via POST

### Configuración MCP
El servidor MCP se ejecuta automáticamente cuando usas `serve`:
- **HTTP Transport**: Disponible en rutas `/mcp/*`
- **SSE Transport**: Disponible en `/sse`

### Uso desde aplicaciones MCP:
Las aplicaciones compatibles pueden llamar:
```json
{
  "tool": "hello_get",
  "arguments": {
    "name": "Bruno"
  }
}
```

---

## 🌐 Web UI

### Acceso
Navega a http://127.0.0.1:8000 después de ejecutar `serve`

### Funcionalidades:
1. **Input field**: Ingresa un nombre
2. **Botón "Say Hello!"**: Ejecuta la función
3. **Resultado**: Muestra la respuesta de la API
4. **Arquitectura**: Información del framework

La interfaz utiliza JavaScript para hacer fetch a la API REST y mostrar resultados en tiempo real.

---

## 🧪 Testing

### Ejecutar tests
```bash
# Tests específicos de hello_world
uv run python -m pytest tests/core/test_hello.py -v

# Todos los tests
uv run python -m pytest -v

# Con coverage
uv run python -m pytest --cov=core tests/
```

---

## 🔧 Desarrollo

### Añadir nueva función:

1. **Crear función pura** en `core/nueva_funcion/mi_func.py`:
```python
def mi_func(param: str = "default") -> str:
    return f"Resultado: {param}"
```

2. **Registrar en registry** (`interfaces/registry.py`):
```python
FUNCTION_REGISTRY["mi_func"] = {
    "name": "mi_func",
    "func": mi_func,
    "description": "Mi nueva función",
    "params": [
        {
            "name": "param",
            "type": "str", 
            "description": "Parámetro de entrada",
            "default": "default",
            "required": False
        }
    ]
}
```

3. **Automáticamente disponible** en:
   - CLI: `uv run python -m interfaces.cli mi_func --param valor`
   - API: `GET /mi_func?param=valor`
   - MCP: `mi_func_get` y `mi_func_post` tools
   - Web UI: (necesita actualizar HTML para nuevos forms)

### Estructura del proyecto:
```
autocode/
├── autocode/                    # ✅ Paquete Python principal
│   └── autocode/               # ✅ Módulo interno
│       ├── core/               # ✅ Funciones puras (lógica de negocio)
│       ├── interfaces/         # ✅ Thin layers (CLI, API, MCP)
│       └── web/               # ✅ UI estática incluida en el paquete
├── tests/                      # ✅ Tests unitarios
└── docs/                       # ✅ Documentación
```

---

## 📚 Recursos adicionales

- **Arquitectura**: Ver `docs/project-overview.md`
- **Implementación**: Ver `implementation_plan.md`
- **Tests**: 14 tests unitarios con 100% coverage
- **Dependencias**: Gestionadas con `uv` (ver `.clinerules/dependencies_uv.md`)
