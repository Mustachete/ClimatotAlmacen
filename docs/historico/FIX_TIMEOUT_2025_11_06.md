# Fix del Sistema de Timeout - 6 de Noviembre 2025

## Problema Reportado

El usuario reportó que cuando la sesión llevaba 20 minutos de inactividad:
- ✅ Sí aparecía el aviso a los 15 minutos (5 minutos antes del cierre)
- ❌ El diálogo de advertencia NO se cerraba automáticamente
- ❌ No se cerraba la sesión automáticamente al llegar a los 20 minutos

**Mensaje del usuario:**
> "Si que me sale el aviso de los 5 minutos, pero no se cierra."

## Causa del Problema

El diálogo de advertencia se mostraba con `msg.exec()`, que es **bloqueante**. Esto significa que:
1. El timer de verificación se pausaba mientras el diálogo estaba abierto
2. El código no podía continuar ejecutándose hasta que el usuario hiciera clic en OK
3. No había forma de cerrar automáticamente el diálogo desde `_force_logout()`

## Solución Implementada

### 1. Cambio de Diálogo Bloqueante a NO Bloqueante

**Antes (bloqueante):**
```python
msg = QMessageBox()
# ... configuración ...
msg.exec()  # ← BLOQUEA la ejecución
```

**Después (no bloqueante):**
```python
self.warning_dialog = QMessageBox()
# ... configuración ...
self.warning_dialog.show()  # ← NO bloquea la ejecución
self.warning_dialog.finished.connect(self._on_warning_closed)
```

### 2. Nuevo Método para Manejar el Cierre del Diálogo

```python
def _on_warning_closed(self, result):
    """
    Maneja el cierre del diálogo de advertencia.
    Si el usuario hizo clic en OK, resetea la actividad.
    """
    if result == QMessageBox.Ok:
        # Usuario confirmó que está trabajando - resetear actividad
        self.last_activity = time.time()
        self.warning_shown = False

    # Limpiar la referencia
    self.warning_dialog = None
```

### 3. Cierre Forzado del Diálogo en `_force_logout()`

```python
def _force_logout(self):
    # ... código existente ...

    # ✅ NUEVO: Cerrar el diálogo de advertencia si está abierto
    if self.warning_dialog and self.warning_dialog.isVisible():
        try:
            self.warning_dialog.close()
            self.warning_dialog = None
        except Exception as e:
            logger.warning(f"Error al cerrar diálogo de advertencia: {e}")

    # ... resto del código de cierre ...
```

### 4. Mantener el Timer Activo Durante la Advertencia

**Antes:**
```python
def _show_warning(self):
    self.timer.stop()  # ← Pausaba el timer
    msg.exec()
    self.timer.start()  # ← Lo reiniciaba después
```

**Después:**
```python
def _show_warning(self):
    # ✅ NO pausar el timer - debe seguir ejecutándose para forzar cierre
    self.warning_dialog.show()  # ← Diálogo no bloqueante
```

## Cambios en Archivos

### `src/core/idle_manager.py`

#### Línea 47 - Nueva Referencia
```python
self.warning_dialog = None  # ← Referencia al diálogo de advertencia
```

#### Líneas 138-161 - Método `_show_warning()` Modificado
- Cambiado de `exec()` (bloqueante) a `show()` (no bloqueante)
- Almacena referencia en `self.warning_dialog`
- Conecta señal `finished` al nuevo método `_on_warning_closed`
- Ya NO pausa el timer

#### Líneas 163-174 - Nuevo Método `_on_warning_closed()`
- Maneja el evento cuando el usuario cierra el diálogo
- Si hace clic en OK, resetea la actividad
- Limpia la referencia `self.warning_dialog`

#### Líneas 193-200 - Modificación en `_force_logout()`
- Verifica si `self.warning_dialog` existe y está visible
- Lo cierra forzosamente con `.close()`
- Limpia la referencia
- Ocurre ANTES de cerrar las demás ventanas

## Comportamiento Esperado

### Caso 1: Usuario Hace Clic en OK
1. ⏱️ 15 minutos: Aparece advertencia "quedan 5 minutos"
2. 👆 Usuario hace clic en OK
3. ✅ Se resetea el contador de actividad
4. ✅ El diálogo se cierra
5. ✅ El sistema continúa monitoreando

### Caso 2: Usuario NO Hace Clic (Inactivo)
1. ⏱️ 15 minutos: Aparece advertencia "quedan 5 minutos"
2. 👤 Usuario no hace nada
3. ⏱️ 20 minutos: Timer detecta timeout
4. ❌ `_force_logout()` cierra el diálogo de advertencia automáticamente
5. ❌ Cierra todas las ventanas de la aplicación
6. ℹ️ Muestra mensaje "Sesión Cerrada por inactividad"
7. 🔐 Vuelve a la pantalla de login

## Script de Prueba

Se creó `scripts/test_timeout.py` para probar el comportamiento con tiempos reducidos:
- Advertencia a los 10 segundos
- Timeout a los 20 segundos

Para probar:
```bash
python scripts/test_timeout.py
```

## Verificación

✅ El timer sigue ejecutándose mientras el diálogo está visible
✅ El diálogo se cierra automáticamente al timeout
✅ Todas las ventanas se cierran correctamente
✅ Vuelve a la pantalla de login
✅ No hay bucles infinitos ni bloqueos

## Notas Técnicas

### PySide6 QMessageBox Modes

- **`exec()`**: Bloqueante, espera interacción del usuario
- **`show()`**: No bloqueante, permite que el código continúe
- **`open()`**: Similar a show(), pero más apropiado para diálogos modales

### Timer Behavior

El `QTimer` continúa ejecutando `_check_idle()` cada segundo incluso mientras el diálogo está visible, lo que permite detectar el timeout y cerrar todo forzosamente.

### Signal/Slot Connection

```python
self.warning_dialog.finished.connect(self._on_warning_closed)
```

Este patrón permite reaccionar al cierre del diálogo (ya sea por OK o por cierre forzado) de manera asíncrona.

## Conclusión

El sistema de timeout ahora funciona correctamente:
- El diálogo de advertencia aparece pero no bloquea el sistema
- El timeout se detecta incluso con el diálogo abierto
- El diálogo se cierra automáticamente al alcanzar el timeout
- La sesión se cierra limpiamente y vuelve al login
