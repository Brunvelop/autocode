# Interfaz de Línea de Comandos (CLI)

## 🎯 Propósito
Este módulo proporciona una interfaz de línea de comandos (CLI) unificada para acceder a todas las funcionalidades del sistema `autocode`. Actúa como el punto de entrada principal para que los usuarios y los sistemas de automatización (como CI/CD) interactúen con las herramientas de análisis y generación.

## 🏗️ Arquitectura
La CLI se construye utilizando el módulo `argparse` de Python, que es el estándar para crear interfaces de línea de comandos.

1.  **`create_parser()`**: Esta función define toda la estructura de la CLI, incluyendo el comando principal (`autocode`) y todos los subcomandos disponibles (`check-docs`, `git-changes`, `daemon`, etc.). Para cada subcomando, define los argumentos, flags y opciones que acepta.
2.  **`main()`**: Es el punto de entrada que se ejecuta cuando se llama al script. Parsea los argumentos de la línea de comandos proporcionados por el usuario.
3.  **Enrutamiento de Comandos**: Basándose en el subcomando proporcionado por el usuario, `main()` llama a la función manejadora correspondiente (ej. `check_docs_command`, `git_changes_command`).
4.  **Funciones Manejadoras**: Cada subcomando tiene su propia función manejadora (ej. `check_docs_command`). Esta función:
    -   Carga la configuración del proyecto (`autocode_config.yml`).
    -   Instancia la clase del `core` necesaria (ej. `DocChecker`).
    -   Ejecuta la lógica de negocio.
    -   Formatea y muestra los resultados en la consola.
    -   Devuelve un código de salida (`0` para éxito, `1` para error) para la integración con scripts y sistemas de CI.

## 📋 Responsabilidades
- **Definir la Interfaz de Usuario**: Establece los comandos, subcomandos y argumentos que los usuarios pueden utilizar.
- **Parsear Argumentos**: Interpreta los argumentos proporcionados por el usuario en la línea de comandos.
- **Cargar Configuración**: Encuentra y carga el archivo `autocode_config.yml` para configurar las herramientas.
- **Invocar la Lógica del `core`**: Actúa como una capa delgada que conecta la entrada del usuario con la lógica de negocio implementada en los módulos del `core`.
- **Presentar Resultados**: Formatea la salida de las herramientas de una manera clara y legible para la consola.
- **Gestionar Códigos de Salida**: Devuelve códigos de salida estándar para indicar el éxito o fracaso de una operación.

## 🔗 Dependencias
### Internas
- Todos los módulos del `core` (`DocChecker`, `GitAnalyzer`, `TestChecker`, `OpenCodeExecutor`, `CodeToDesign`, `TokenCounter`).
- El módulo `api` para el subcomando `daemon`.

### Externas
- `argparse`: Para construir la CLI.
- `PyYAML`: Para cargar el archivo de configuración.
- `uvicorn` y `fastapi`: Dependencias opcionales para el subcomando `daemon`.

## 📊 Interfaces Públicas (Subcomandos)
-   **`check-docs`**: Verifica el estado de la documentación.
-   **`check-tests`**: Verifica el estado de los tests.
-   **`git-changes`**: Analiza los cambios en el repositorio de Git.
-   **`daemon`**: Inicia un servidor web para el monitoreo en tiempo real.
-   **`opencode`**: Ejecuta análisis de IA con OpenCode.
-   **`code-to-design`**: Genera documentación de diseño a partir del código.
-   **`count-tokens`**: Cuenta tokens en archivos para análisis de LLM.

## 💡 Patrones de Uso
**Verificar la documentación desde la terminal:**
```bash
autocode check-docs
```

**Analizar los cambios de Git y guardarlos en un archivo:**
```bash
autocode git-changes --output mis_cambios.json --verbose
```

**Generar el diseño para el código en el directorio `src`:**
```bash
autocode code-to-design --directories src --languages python javascript --diagrams classes components
```

## ⚠️ Consideraciones
- La CLI está diseñada para ser el principal punto de interacción para los usuarios.
- La lógica de negocio compleja no reside aquí, sino en los módulos del `core`, manteniendo la CLI como una capa de entrada delgada.
