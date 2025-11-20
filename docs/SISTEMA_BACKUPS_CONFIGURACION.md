# Sistema de Configuración de Backups

**Fecha de implementación:** 18 de noviembre de 2025

## Resumen

Se ha implementado un sistema completo de configuración de backups que permite personalizar el comportamiento de las copias de seguridad del sistema.

## Características Implementadas

### 1. **Configuración Persistente en Base de Datos**

Se creó la tabla `config_backups` con los siguientes campos:

- `max_backups`: Número máximo de backups a mantener (por defecto: 20)
- `permitir_multiples_diarios`: Permite crear múltiples backups por día (por defecto: Sí)
- `backup_auto_inicio`: Crea backup automático al iniciar sesión (por defecto: No)
- `backup_auto_cierre`: Crea backup automático al cerrar (por defecto: No)
- `retencion_dias`: Días de retención (NULL = sin límite)
- `ruta_backups`: Ubicación personalizada (NULL = usar por defecto)
- `ultima_actualizacion`: Timestamp de última modificación

### 2. **Servicio de Configuración**

**Archivo:** `src/services/backup_config_service.py`

Funciones principales:
- `obtener_configuracion()`: Obtiene la configuración actual
- `guardar_configuracion(config)`: Guarda cambios en la BD
- `actualizar_campo(campo, valor)`: Actualiza un campo específico
- `obtener_ruta_backups()`: Retorna la ruta configurada o la por defecto

### 3. **Sistema de Backups Actualizado**

**Archivo:** `scripts/backup_db.py`

Mejoras implementadas:
- Lee configuración desde la BD en lugar de constantes hardcodeadas
- Respeta la opción de múltiples backups diarios
- Soporta rutas personalizadas de backups
- Limpieza automática según dos criterios:
  - Número máximo de backups
  - Retención por días (opcional)
- Nuevo parámetro `forzar` para ignorar restricciones

### 4. **Diálogo de Configuración**

**Archivo:** `src/ventanas/dialogo_config_backups.py`

Permite configurar:
- Número máximo de backups (1-100)
- Retención por días (0 = sin límite)
- Checkbox: Permitir múltiples backups diarios
- Checkbox: Backup automático al iniciar sesión
- Checkbox: Backup automático al cerrar aplicación
- Ubicación personalizada de backups

**Acceso:**
Configuración → Backup y Restauración → ⚙️ Configurar Backups...

### 5. **Backups Automáticos**

#### Backup al Iniciar Sesión
**Ubicación:** `src/ventanas/ventana_login.py:158-175`

Después de un login exitoso, si está habilitado en configuración, se crea un backup automáticamente.

#### Backup al Cerrar
**Ubicación:** `app.py:174-197`

Antes de cerrar la aplicación, si está habilitado en configuración, se crea un backup automáticamente.

## Scripts de Migración

### Aplicar la Configuración

Para aplicar la tabla de configuración en una BD existente:

```bash
python scripts/aplicar_config_backups.py
```

Esto creará la tabla `config_backups` y aplicará valores por defecto.

## Uso

### Desde el Código

```python
from src.services.backup_config_service import obtener_configuracion, guardar_configuracion, BackupConfig

# Obtener configuración actual
config = obtener_configuracion()
print(f"Max backups: {config.max_backups}")

# Guardar nueva configuración
nueva_config = BackupConfig(
    max_backups=30,
    permitir_multiples_diarios=True,
    backup_auto_inicio=True,
    backup_auto_cierre=False,
    retencion_dias=60
)
guardar_configuracion(nueva_config)
```

### Crear Backup Manual

```python
from scripts.backup_db import crear_backup

# Crear backup respetando configuración
crear_backup(mostrar_log=True, forzar=False)

# Forzar backup incluso si ya existe uno hoy
crear_backup(mostrar_log=True, forzar=True)
```

## Cambios en el Comportamiento

### Antes
- Límite hardcodeado de 20 backups
- Solo 1 backup por día (restricción fija)
- No había backups automáticos
- Ruta fija: `db/backups`

### Ahora
- Número de backups configurable (1-100)
- Múltiples backups por día (configurable)
- Backups automáticos al inicio/cierre (opcional)
- Retención por días (opcional, complementa al límite numérico)
- Ruta personalizable
- Configuración persistente en BD

## Compatibilidad

- ✅ Totalmente compatible con backups existentes
- ✅ Si no existe configuración, usa valores por defecto
- ✅ No requiere cambios en código existente
- ✅ Funciona sin cambios en instalaciones antiguas

## Archivos Modificados

1. `scripts/backup_db.py` - Sistema de backups actualizado
2. `src/services/backup_config_service.py` - Nuevo servicio
3. `src/ventanas/dialogo_config_backups.py` - Nuevo diálogo
4. `src/ventanas/dialogs_configuracion.py` - Botón de configuración agregado
5. `src/ventanas/ventana_login.py` - Backup automático al inicio
6. `app.py` - Backup automático al cerrar

## Archivos Nuevos

1. `scripts/crear_config_backups.sql` - Script SQL para crear tabla
2. `scripts/aplicar_config_backups.py` - Aplicar configuración a BD
3. `src/services/backup_config_service.py` - Servicio de configuración
4. `src/ventanas/dialogo_config_backups.py` - Interfaz de configuración

## Notas Técnicas

- La tabla usa un `CHECK(id = 1)` para garantizar solo una fila de configuración
- El sistema es tolerante a fallos: si la configuración no se puede leer, usa valores por defecto
- Los backups automáticos no bloquean la aplicación si fallan
- La limpieza aplica dos criterios: número máximo Y retención por días (si está configurado)

## Pruebas Realizadas

✅ Creación de tabla de configuración
✅ Guardado y recuperación de configuración
✅ Creación de backups con nueva configuración
✅ Limpieza automática respetando límites
✅ Backup automático al inicio (código implementado)
✅ Backup automático al cierre (código implementado)
✅ Compatibilidad con código existente
