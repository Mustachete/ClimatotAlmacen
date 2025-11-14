# Sistema de Autenticación y Gestión de Sesiones

## Resumen

Se ha implementado un sistema completo de autenticación y gestión de sesiones de usuario en ClimatotAlmacen. Este sistema reemplaza los valores hardcodeados de `usuario="admin"` con un sistema de sesiones que rastrea qué usuario está realizando cada operación.

## Fecha de Implementación

31 de Octubre de 2025

## Componentes Implementados

### 1. Base de Datos

La tabla `usuarios` ya existía en el esquema (`db/schema.sql`):

```sql
CREATE TABLE IF NOT EXISTS usuarios(
  usuario     TEXT PRIMARY KEY,
  pass_hash   TEXT NOT NULL,
  rol         TEXT NOT NULL DEFAULT 'almacen',
  activo      INTEGER NOT NULL DEFAULT 1
);
```

**Roles disponibles:**
- `admin`: Administrador con acceso completo
- `almacen`: Personal de almacén con acceso a operaciones estándar
- `operario`: Operarios de campo con acceso limitado

### 2. Repositorio: `src/repos/usuarios_repo.py`

Repositorio de acceso a datos de usuarios.

**Funciones principales:**
- `get_by_usuario(usuario: str)` - Obtiene un usuario por nombre
- `get_todos(filtro_texto, solo_activos, limit)` - Lista usuarios con filtros
- `crear_usuario(usuario, pass_hash, rol, activo)` - Crea nuevo usuario
- `actualizar_usuario(usuario, pass_hash, rol, activo)` - Actualiza usuario
- `eliminar_usuario(usuario)` - Elimina usuario
- `verificar_es_unico_usuario()` - Verifica si es el único usuario en el sistema

### 3. Servicio: `src/services/usuarios_service.py`

Lógica de negocio y validaciones para usuarios.

**Validaciones implementadas:**
- Usuario: mínimo 3 caracteres, solo alfanuméricos, guiones y guiones bajos
- Contraseña: mínimo 4 caracteres, máximo 100
- Rol: debe ser 'admin', 'almacen' u 'operario'
- Unicidad: no permite usuarios duplicados
- Protección: no permite eliminar el único usuario del sistema

**Funciones principales:**
- `autenticar_usuario(usuario, password)` - Autentica y devuelve datos del usuario
- `crear_usuario(usuario, password, rol, activo, usuario_creador)` - Crea usuario con validaciones
- `actualizar_usuario(usuario, password, rol, activo, usuario_modificador)` - Actualiza usuario
- `eliminar_usuario(usuario, usuario_eliminador)` - Elimina usuario con protecciones
- `obtener_usuarios(filtro_texto, solo_activos, limit)` - Lista usuarios
- `obtener_usuario(usuario)` - Obtiene datos de un usuario específico

### 4. Gestor de Sesiones: `src/core/session_manager.py`

Singleton que mantiene el estado de la sesión del usuario actual.

**Clase `SessionManager`:**

**Métodos:**
- `login(usuario, rol)` - Inicia sesión
- `logout()` - Cierra sesión
- `get_usuario_actual()` - Obtiene el usuario actual
- `get_rol_actual()` - Obtiene el rol actual
- `is_authenticated()` - Verifica si hay sesión activa
- `is_admin()` - Verifica si el usuario es admin
- `is_almacen()` - Verifica si el usuario tiene rol de almacén
- `is_operario()` - Verifica si el usuario es operario
- `get_session_info()` - Obtiene información completa de la sesión

**Uso:**
```python
from src.core.session_manager import session_manager

# Durante el login
session_manager.login(usuario="juan", rol="admin")

# En cualquier parte de la aplicación
usuario_actual = session_manager.get_usuario_actual()
es_admin = session_manager.is_admin()

# Durante el logout
session_manager.logout()
```

### 5. Ventana de Login: `src/ventanas/ventana_login.py`

Ventana de autenticación con diseño corporativo Climatot.

**Características:**
- Diseño limpio y profesional usando `ESTILO_LOGIN`
- Validación de campos requeridos
- Integración con `usuarios_service` para autenticación
- Automáticamente registra la sesión en `session_manager`
- Soporte para Enter/Return en los campos
- Mensajes claros de error

**Uso:**
```python
login_window = VentanaLogin()
resultado = login_window.exec()

if resultado == QDialog.Accepted:
    user_data = login_window.get_usuario_autenticado()
    # user_data contiene: {'usuario': '...', 'rol': '...'}
```

### 6. Actualización de `app.py`

El archivo principal de la aplicación fue actualizado para:

1. Usar `VentanaLogin` en lugar de la clase `LoginWindow` anterior
2. Obtener datos de sesión de `session_manager` en `MainMenuWindow`
3. Registrar inicio/fin de sesión correctamente
4. Cerrar sesión en `session_manager` al hacer logout

**Cambios clave:**
```python
# Antes
class MainMenuWindow(QWidget):
    def __init__(self, usuario, rol, login_window):
        self.usuario = usuario
        self.rol = rol

# Ahora
class MainMenuWindow(QWidget):
    def __init__(self, login_window):
        self.usuario = session_manager.get_usuario_actual()
        self.rol = session_manager.get_rol_actual()
```

### 7. Actualización de todas las Ventanas

**Archivos actualizados (10 ventanas):**
- `src/ventanas/maestros/ventana_ubicaciones.py`
- `src/ventanas/maestros/ventana_familias.py`
- `src/ventanas/maestros/ventana_operarios.py`
- `src/ventanas/maestros/ventana_proveedores.py`
- `src/ventanas/maestros/ventana_articulos.py`
- `src/ventanas/operativas/ventana_inventario.py`
- `src/ventanas/operativas/ventana_imputacion.py`
- `src/ventanas/operativas/ventana_recepcion.py`
- `src/ventanas/operativas/ventana_devolucion.py`
- `src/ventanas/operativas/ventana_material_perdido.py`

**Cambio realizado:**

Todas las llamadas a servicios ahora usan el usuario de la sesión activa:

```python
# Antes
exito, mensaje = ubicaciones_service.crear_ubicacion(
    nombre=nombre,
    usuario="admin"  # ❌ Hardcodeado
)

# Ahora
exito, mensaje = ubicaciones_service.crear_ubicacion(
    nombre=nombre,
    usuario=session_manager.get_usuario_actual() or "admin"  # ✅ Usuario real
)
```

**Nota:** Se usa `or "admin"` como fallback para casos excepcionales donde no haya sesión activa (no debería ocurrir en uso normal).

## Scripts de Utilidad

### `scripts/init_admin.py`

Script para crear el primer usuario administrador del sistema.

**Uso:**
```bash
python scripts/init_admin.py
```

**Características:**
- Verifica que exista la base de datos
- Detecta si ya hay usuarios en el sistema
- Solicita datos de forma interactiva
- Valida longitud de usuario y contraseña
- Confirma la contraseña
- Crea el usuario con rol 'admin'

**Ejemplo de ejecución:**
```
============================================================
CREAR USUARIO ADMINISTRADOR INICIAL
============================================================

Ingrese los datos del nuevo administrador:

Usuario (min 3 caracteres): admin
Contraseña (min 4 caracteres): ****
Confirmar contraseña: ****

Creando usuario administrador...
[OK] Usuario 'admin' creado correctamente

============================================================
Usuario administrador creado correctamente
============================================================

Ahora puede ejecutar la aplicación con: python app.py
```

### `scripts/update_session_manager.py`

Script que automatizó la actualización de todas las ventanas para usar `session_manager`.

**Funcionalidad:**
- Agrega import de `session_manager` a cada ventana
- Reemplaza todas las ocurrencias de `usuario="admin"` con `usuario=session_manager.get_usuario_actual() or "admin"`
- Procesa 10 archivos de ventanas automáticamente
- Reporta el progreso de cada archivo

## Flujo de Autenticación

### 1. Inicio de la Aplicación

```
Usuario ejecuta: python app.py
    ↓
Se muestra VentanaLogin
    ↓
Usuario ingresa credenciales
    ↓
usuarios_service.autenticar_usuario()
    ├─ Valida usuario existe
    ├─ Verifica que esté activo
    └─ Compara hash de contraseña
    ↓
session_manager.login(usuario, rol)
    ↓
Se registra sesión en tabla 'sesiones'
    ↓
Se abre MainMenuWindow
    ↓
Se inicia idle_manager
```

### 2. Durante el Uso de la Aplicación

```
Usuario realiza operación (ej: crear artículo)
    ↓
ventana_articulos.py llama a articulos_service.crear_articulo()
    ↓
Pasa como parámetro: usuario=session_manager.get_usuario_actual()
    ↓
El servicio registra la operación con el usuario real
    ↓
log_operacion("articulos", "crear", usuario_real, detalles)
```

### 3. Cierre de Sesión

```
Usuario hace clic en "Cambiar Usuario"
    ↓
MainMenuWindow.logout()
    ├─ idle_manager.stop()
    ├─ log_fin_sesion(usuario, hostname)
    ├─ session_manager.logout()
    └─ Muestra VentanaLogin de nuevo
```

## Auditoría y Logs

Todas las operaciones de usuarios quedan registradas en los logs:

**Logs de autenticación:**
```
2025-10-31 10:15:23 | SESION | Usuario: juan | Login desde: DESKTOP-ABC123
2025-10-31 10:15:45 | OPERACION | usuarios | crear | Usuario: juan | Detalles: Usuario: pedro, Rol: almacen
2025-10-31 12:30:15 | SESION | Usuario: juan | Logout desde: DESKTOP-ABC123
```

**Logs de operaciones:**
```
2025-10-31 10:20:30 | OPERACION | articulos | crear | Usuario: juan | Detalles: Artículo ID: 145, Nombre: Válvula 3/4"
2025-10-31 10:25:12 | OPERACION | movimientos | crear | Usuario: pedro | Detalles: Tipo: ENTRADA, Artículo ID: 145
```

**Logs de validación:**
```
2025-10-31 10:18:45 | VALIDACION | usuarios | password | Contraseña muy corta
2025-10-31 10:19:03 | VALIDACION | usuarios | autenticar | Contraseña incorrecta: juan
```

## Migración y Retrocompatibilidad

### Datos Existentes

Todos los movimientos, artículos y demás registros creados ANTES de implementar este sistema tienen `responsable` con el valor anterior. Esto es aceptable y no requiere migración.

### Nuevos Registros

Todos los registros creados DESPUÉS de la implementación incluirán el usuario real que realizó la operación, obtenido de `session_manager`.

### Fallback

En el caso excepcional de que `session_manager.get_usuario_actual()` devuelva `None`, se usa `"admin"` como fallback mediante:

```python
usuario=session_manager.get_usuario_actual() or "admin"
```

Esto no debería ocurrir en uso normal, ya que todas las ventanas operativas requieren login previo.

## Seguridad

### Hash de Contraseñas

Las contraseñas se almacenan usando SHA256:

```python
from src.core.db_utils import hash_pwd

password_hash = hash_pwd("mi_contraseña")
# Resultado: "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62fb1b8a015c01c0"
```

### Validaciones

- **Longitud mínima de usuario:** 3 caracteres
- **Longitud mínima de contraseña:** 4 caracteres
- **Caracteres permitidos en usuario:** a-z, A-Z, 0-9, -, _
- **Unicidad:** No se permiten usuarios duplicados
- **Estado:** Usuarios inactivos no pueden iniciar sesión
- **Protección:** No se puede eliminar el último usuario del sistema
- **Autoprotección:** No se puede eliminar el propio usuario

## Roles y Permisos

### Admin
- Acceso completo a todas las funcionalidades
- Puede ver "Material Perdido"
- Puede ver "Configuración"
- Puede crear, editar y eliminar usuarios

### Almacen
- Acceso a todas las operaciones estándar
- Recepciones, movimientos, imputaciones, devoluciones
- Acceso a todos los maestros
- Acceso a consultas e informes

### Operario
- Acceso limitado (definir según necesidades)
- Actualmente tiene los mismos permisos que 'almacen' excepto funciones admin

**Nota:** Los permisos específicos por rol pueden refinarse más adelante agregando validaciones en cada ventana usando `session_manager.is_admin()`, `session_manager.is_almacen()`, etc.

## Archivos Creados

```
src/repos/usuarios_repo.py                    - 85 líneas
src/services/usuarios_service.py              - 273 líneas
src/core/session_manager.py                   - 69 líneas
src/ventanas/ventana_login.py                 - 147 líneas
scripts/init_admin.py                         - 89 líneas
scripts/update_session_manager.py             - 90 líneas
docs/SISTEMA_AUTENTICACION.md                 - Este archivo
```

## Archivos Modificados

```
app.py                                        - Login flow completamente refactorizado
src/ventanas/maestros/ventana_ubicaciones.py  - Usa session_manager
src/ventanas/maestros/ventana_familias.py     - Usa session_manager
src/ventanas/maestros/ventana_operarios.py    - Usa session_manager
src/ventanas/maestros/ventana_proveedores.py  - Usa session_manager
src/ventanas/maestros/ventana_articulos.py    - Usa session_manager
src/ventanas/operativas/ventana_inventario.py - Usa session_manager
src/ventanas/operativas/ventana_imputacion.py - Usa session_manager
src/ventanas/operativas/ventana_recepcion.py  - Usa session_manager
src/ventanas/operativas/ventana_devolucion.py - Usa session_manager
src/ventanas/operativas/ventana_material_perdido.py - Usa session_manager
```

## Testing Manual

Para probar el sistema completo:

### 1. Inicializar Base de Datos (si es primera vez)
```bash
python init_db.py
```

### 2. Crear Usuario Administrador
```bash
python scripts/init_admin.py
```
- Ingresar usuario: `admin`
- Ingresar contraseña: `admin` (o la que prefieras)

### 3. Ejecutar Aplicación
```bash
python app.py
```

### 4. Probar Login
- Login con credenciales correctas → Debe abrir menú principal
- Login con credenciales incorrectas → Debe mostrar error
- Login con usuario inactivo → Debe mostrar "Usuario desactivado"

### 5. Probar Operaciones
- Crear un artículo nuevo
- Verificar en logs que aparece el usuario correcto
- Crear una recepción
- Verificar en logs que aparece el usuario correcto

### 6. Probar Logout
- Click en "Cambiar Usuario"
- Debe volver a la pantalla de login
- Verificar en logs el registro de logout

### 7. Probar Gestión de Usuarios (si es admin)
- Crear ventana_usuarios.py para gestionar usuarios desde la UI
- O usar directamente SQL: `SELECT * FROM usuarios;`

## Próximos Pasos Sugeridos

### 1. Ventana de Gestión de Usuarios (Alta Prioridad)
Crear `src/ventanas/maestros/ventana_usuarios.py` para:
- Listar usuarios existentes
- Crear nuevos usuarios
- Editar usuarios (cambiar contraseña, rol, estado)
- Eliminar usuarios (con protecciones)
- Filtrar por rol, estado activo/inactivo

### 2. Validación de Permisos por Ventana (Media Prioridad)
Refinar permisos según rol en cada ventana:
```python
class VentanaMaterialPerdido(QWidget):
    def __init__(self):
        if not session_manager.is_admin():
            QMessageBox.warning(
                None,
                "Acceso Denegado",
                "Solo administradores pueden acceder a esta función"
            )
            return
        super().__init__()
        # ...
```

### 3. Cambio de Contraseña (Media Prioridad)
Agregar funcionalidad para que usuarios cambien su propia contraseña:
- Ventana de cambio de contraseña
- Validar contraseña anterior
- Solicitar nueva contraseña (2 veces)
- Actualizar hash en BD

### 4. Historial de Sesiones (Baja Prioridad)
Crear ventana para ver:
- Historial de inicios/cierres de sesión
- Sesiones activas actualmente
- Estadísticas de uso por usuario

### 5. Políticas de Contraseñas Más Fuertes (Baja Prioridad)
- Aumentar longitud mínima a 8 caracteres
- Requerir mayúsculas, minúsculas, números
- Implementar expiración de contraseñas
- Historial de contraseñas (no repetir las últimas 5)

## Conclusión

El sistema de autenticación y gestión de sesiones está completamente implementado y funcional. Todas las operaciones ahora rastrean el usuario real que las realizó, proporcionando una auditoría completa y trazabilidad de todas las acciones en el sistema.

**Estado:** ✅ Completado y Funcional
**Fecha:** 31 de Octubre de 2025
**Archivos nuevos:** 7
**Archivos modificados:** 11
**Total de líneas agregadas:** ~750 líneas
