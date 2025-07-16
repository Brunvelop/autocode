# OpenCodeExecutor

## 🎯 Propósito
Proporciona una interfaz para ejecutar análisis de `OpenCode` de forma programática y en modo "headless" (sin interfaz gráfica), gestionando la configuración, la ejecución de comandos y el formato de los resultados para su uso en flujos de trabajo automatizados.

## 🏗️ Arquitectura
El módulo se centra en la clase `OpenCodeExecutor`, que encapsula la lógica para interactuar con la herramienta de línea de comandos `opencode`. Carga una configuración desde un archivo `autocode_config.yml`, pero permite la sobreescritura de parámetros clave en tiempo de ejecución. Utiliza el módulo `subprocess` de Python para ejecutar `opencode` en un proceso separado, capturando su salida y errores.

## 📋 Responsabilidades
- **Cargar Configuración**: Lee la configuración específica para `opencode` desde `autocode_config.yml` o utiliza valores por defecto si no existe.
- **Verificar Disponibilidad**: Comprueba si el comando `opencode` está instalado y es accesible en el `PATH` del sistema.
- **Construir y Ejecutar Comandos**: Ensambla dinámicamente los comandos de `opencode` basados en la configuración y los parámetros proporcionados.
- **Manejar Prompts**: Carga prompts desde archivos `.md` y los inyecta en la ejecución de `opencode`.
- **Formatear Salida**: Procesa la salida (stdout/stderr) de `opencode` y la formatea en texto legible por humanos o en formato JSON estructurado.
- **Validar Entorno**: Ofrece una función de utilidad (`validate_opencode_setup`) para verificar que la configuración de `opencode` es correcta.

## 🔗 Dependencias
### Internas
- `autocode.prompts`: Para cargar, listar y obtener información sobre los prompts disponibles.

### Externas
- `PyYAML`: Para parsear el archivo de configuración `autocode_config.yml`.
- `subprocess`: Para ejecutar el proceso de `opencode`.
- `json`: Para formatear la salida en JSON.
- `pathlib`: Para la gestión de rutas de archivos.

## 📊 Interfaces Públicas
### `class OpenCodeExecutor`
- `__init__(self, project_root: Path, config_file: Optional[Path] = None)`: Constructor de la clase.
- `is_opencode_available(self) -> bool`: Verifica si `opencode` está disponible.
- `list_prompts(self) -> List[str]`: Lista los nombres de los prompts disponibles.
- `get_prompts_info(self) -> Dict[str, str]`: Obtiene metadatos de los prompts.
- `execute_opencode(...) -> Tuple[int, str, str]`: Ejecuta un comando `opencode` con un prompt de texto.
- `execute_with_prompt_file(...) -> Tuple[int, str, str]`: Ejecuta `opencode` usando un prompt desde un archivo.
- `format_output(...) -> str`: Formatea la salida de la ejecución.

### `validate_opencode_setup(project_root: Path) -> Tuple[bool, str]`
- Función standalone para validar la configuración de `opencode` en el proyecto.

## 💡 Patrones de Uso
**Ejecutar un análisis simple con un prompt de un archivo:**
```python
from pathlib import Path
from autocode.core.ai.opencode_executor import OpenCodeExecutor

project_path = Path('.')
executor = OpenCodeExecutor(project_path)

if executor.is_opencode_available():
    exit_code, stdout, stderr = executor.execute_with_prompt_file('hola-mundo')
    
    formatted_output = executor.format_output(exit_code, stdout, stderr)
    print(formatted_output)
```

**Obtener salida en formato JSON:**
```python
exit_code, stdout, stderr = executor.execute_with_prompt_file(
    'hola-mundo', 
    json_output=True
)
formatted_json = executor.format_output(
    exit_code, 
    stdout, 
    stderr, 
    json_output=True
)
print(formatted_json)
```

## ⚠️ Consideraciones
- El módulo depende de que la herramienta `opencode` esté instalada y accesible en el `PATH` del sistema.
- La ejecución de `opencode` puede ser un proceso largo. El `timeout` por defecto es de 300 segundos, pero puede ser configurado.
- La gestión de errores se basa en el código de salida y la captura de `stderr`.

## 🧪 Testing
- Para probar este componente, es necesario tener una instalación funcional de `opencode`.
- Las pruebas deben cubrir casos de éxito, fallo (prompt no encontrado, error de `opencode`), y timeouts.
- Se debe verificar que los argumentos de la línea de comandos se construyen correctamente según la configuración.
