# Test Plan - Migración de Chat a <auto-chat>

## ✅ Pre-requisitos
- [x] Backup creado en `chat-backup/`
- [x] Nuevo `chat.html` creado (330 líneas)
- [x] `base.html` actualizado con script del generator
- [x] `MIGRATION.md` documentado

## 🧪 Pruebas a Realizar

### 1. Verificar Servidor Arranca
```bash
# Activar entorno
uv run python -m autocode.autocode.interfaces.cli serve --reload

# Verificar endpoints
curl http://localhost:8000/health
curl http://localhost:8000/functions/details
```

**Resultado esperado**: 
- Server arranca sin errores
- `/health` retorna `{"status":"healthy"}`
- `/functions/details` incluye función `chat` con parámetros correctos

### 2. Verificar UI Básica
1. Abrir http://localhost:8000/ en navegador
2. Verificar que aparece el botón flotante (esquina superior izquierda)
3. Click en botón para abrir chat
4. Verificar que la ventana se abre correctamente

**Resultado esperado**:
- ✅ Botón flotante visible
- ✅ Panel de chat se abre/cierra
- ✅ UI se ve correctamente con Tailwind

### 3. Verificar <auto-chat> se Genera
1. Abrir DevTools > Console
2. Buscar log: `✨ Registrado: <auto-chat>`
3. Inspeccionar DOM: Debe existir `<auto-chat id="autoChat">`

**Resultado esperado**:
- ✅ Custom element registrado
- ✅ Elemento presente en DOM
- ✅ No hay errores de JS en console

### 4. Verificar Funcionalidad de Chat
1. Escribir mensaje: "Hola, puedes sumar 5 + 3?"
2. Presionar Enter
3. Esperar respuesta del AI

**Resultado esperado**:
- ✅ Mensaje del usuario aparece en el chat
- ✅ Indicador de "pensando" funciona
- ✅ Respuesta del AI aparece correctamente
- ✅ Context bar se actualiza

### 5. Verificar Drag & Drop
1. Con el chat abierto, arrastrar desde el header
2. Mover a diferentes posiciones
3. Soltar

**Resultado esperado**:
- ✅ Ventana se puede arrastrar
- ✅ Cursor cambia a `grabbing`
- ✅ Ventana no se sale de la pantalla

### 6. Verificar Resize
1. Arrastrar desde el handle inferior derecho
2. Redimensionar más grande y más pequeño
3. Verificar límites mínimos

**Resultado esperado**:
- ✅ Ventana se redimensiona correctamente
- ✅ Respeta límites mínimos (320x400px)
- ✅ Contenido se adapta al nuevo tamaño

### 7. Verificar Context Bar
1. Escribir mensaje largo (sin enviar)
2. Observar context bar actualizándose
3. Enviar mensaje
4. Escribir otro mensaje
5. Observar que el contador aumenta

**Resultado esperado**:
- ✅ Context bar se actualiza con debouncing
- ✅ Colores cambian según porcentaje (verde < 70%, amarillo 70-90%, rojo > 90%)
- ✅ Números se muestran formateados (e.g., "1,234 / 16,000")

### 8. Verificar Nueva Conversación
1. Mantener una conversación de varios mensajes
2. Click en botón "Nueva"
3. Verificar que se limpia todo

**Resultado esperado**:
- ✅ Mensajes se borran
- ✅ Context bar resetea a 0/0
- ✅ Input queda vacío
- ✅ Se puede iniciar nueva conversación

### 9. Verificar Manejo de Errores
1. Detener el servidor
2. Intentar enviar un mensaje
3. Observar mensaje de error

**Resultado esperado**:
- ✅ Mensaje de error aparece en rojo
- ✅ Input se re-habilita
- ✅ No hay crash de la UI

### 10. Verificar Slots Personalizados
1. Inspeccionar DOM con DevTools
2. Verificar que `<auto-chat>` contiene:
   - `<div slot="result-ui" id="messagesContainer">`
   - `<div slot="params-ui">` con input
   - `<button slot="execute-button">` (hidden)

**Resultado esperado**:
- ✅ Slots están correctamente asignados
- ✅ El custom element respeta los slots
- ✅ No hay conflictos de estilos

## 📊 Checklist Final

- [ ] Todas las pruebas pasaron
- [ ] No hay errores en console
- [ ] Performance es aceptable
- [ ] UI/UX es igual o mejor que la original
- [ ] Código es más mantenible (61% menos líneas)

## 🐛 Problemas Encontrados

_(Documentar aquí cualquier problema durante las pruebas)_

---

## 🚀 Si Todo Funciona

1. Eliminar carpeta `chat-backup/` (opcional)
2. Actualizar README.md con info de la migración
3. Commit cambios
4. Celebrar 🎉

## 🔄 Si Hay Problemas

1. Revisar console de DevTools
2. Verificar logs del servidor
3. Si es crítico, hacer rollback:
   ```bash
   rm autocode/autocode/web/components/chat/chat.html
   cp -r autocode/autocode/web/components/chat-backup/* autocode/autocode/web/components/chat/
   ```
4. Reportar issue y analizar

---

**Fecha de creación**: 2025-11-03  
**Última actualización**: 2025-11-03
