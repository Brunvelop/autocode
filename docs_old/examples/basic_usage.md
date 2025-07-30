# Ejemplo de Uso Básico

## 🎯 Propósito
Este script de ejemplo demuestra cómo utilizar las funcionalidades principales de `autocode` de forma **programática**, es decir, importando y utilizando sus clases directamente desde otro script de Python, en lugar de a través de la línea de comandos.

## 🏗️ Arquitectura
El script es lineal y simple:
1.  **Importa las clases necesarias**: Importa `DocChecker` y `GitAnalyzer` desde el `core` de `autocode`.
2.  **Define una función `main`**: Encapsula la lógica de la demostración.
3.  **Instancia los Componentes**: Crea instancias de `DocChecker` y `GitAnalyzer`, pasándoles el directorio raíz del proyecto.
4.  **Ejecuta las Verificaciones**: Llama a los métodos de las instancias para realizar las verificaciones de documentación y de Git.
5.  **Imprime los Resultados**: Muestra un resumen de los resultados en la consola.

## 📋 Responsabilidades
- **Demostrar el Uso de `DocChecker`**: Muestra cómo obtener una lista de la documentación desactualizada.
- **Demostrar el Uso de `GitAnalyzer`**: Muestra cómo obtener un resumen del estado del repositorio y una lista de los archivos modificados.
- **Servir como Punto de Partida**: Actúa como un ejemplo simple para los desarrolladores que quieran integrar `autocode` en sus propios flujos de trabajo automatizados.

## 🔗 Dependencias
### Internas
- `autocode.core.docs.DocChecker`
- `autocode.core.git.GitAnalyzer`

### Externas
- `pathlib`: Para la manipulación de rutas.

## 💡 Patrones de Uso
Para ejecutar este ejemplo, un usuario simplemente correría el script desde la raíz del proyecto:
```bash
python examples/basic_usage.py
```
El script analizará el estado actual del proyecto y mostrará los resultados directamente en la terminal.

## ⚠️ Consideraciones
- El script asume que se ejecuta desde el directorio raíz del proyecto `autocode`.
- La salida es una versión simplificada de lo que las herramientas pueden hacer; el verdadero poder reside en los datos estructurados que devuelven los métodos.
