# Guía de Inicio Rápido - ClimatotAlmacen

## Primera Instalación (5 minutos)

### 1. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 2. Inicializar Base de Datos
```bash
python init_db.py
```
✅ Esto crea `db/almacen.db` con todas las tablas y vistas necesarias

### 3. Crear Usuario Administrador
```bash
python scripts/init_admin.py
```

Ejemplo:
```
Usuario (min 3 caracteres): admin
Contraseña (min 4 caracteres): admin123
Confirmar contraseña: admin123
[OK] Usuario 'admin' creado correctamente
```

### 4. Iniciar Aplicación
```bash
python app.py
```

### 5. Iniciar Sesión
- Ingresar usuario: `admin`
- Ingresar contraseña: `admin123`
- Click "Iniciar Sesión"

¡Listo! Ya puedes usar el sistema.

---

## Uso Diario

### Iniciar la Aplicación
```bash
python app.py
```

### Operaciones Comunes

#### Recibir Material
1. Click en "Recepción"
2. Seleccionar proveedor
3. Ingresar número de albarán
4. Agregar artículos y cantidades
5. Guardar

#### Hacer un Traspaso
1. Click en "Hacer Movimientos"
2. Seleccionar "TRASPASO"
3. Seleccionar almacén origen y destino
4. Seleccionar artículo y cantidad
5. Guardar

#### Imputar Material a Obra
1. Click en "Imputar Material"
2. Ingresar número de OT
3. Seleccionar operario
4. Seleccionar almacén/furgoneta de origen
5. Agregar artículos y cantidades
6. Guardar

#### Consultar Stock
1. Click en "Info e Informes"
2. Click en "Consulta de Stock"
3. Seleccionar almacén (o "Todos")
4. Opcionalmente filtrar por texto
5. Ver stock disponible

---

## Gestión de Usuarios (Solo Admin)

### Crear Nuevo Usuario

**Método 1: Script (Recomendado)**
```bash
python scripts/init_admin.py
```

**Método 2: Código Python**
```python
from src.services import usuarios_service

exito, mensaje = usuarios_service.crear_usuario(
    usuario="juan",
    password="pass1234",
    rol="almacen",  # opciones: admin, almacen, operario
    activo=True,
    usuario_creador="admin"
)
print(mensaje)
```

### Roles Disponibles

- **admin**: Acceso completo + gestión de usuarios
- **almacen**: Operaciones estándar de almacén
- **operario**: Acceso limitado (configurable)

---

## Solución Rápida de Problemas

### "No se encuentra la base de datos"
```bash
python init_db.py
```

### "Usuario o contraseña incorrectos"
- Verificar credenciales
- Crear nuevo admin si olvidaste la contraseña:
  ```bash
  python scripts/init_admin.py
  ```

### Ver errores recientes
```bash
# Windows
type logs\app.log | findstr /C:"ERROR"

# Linux/Mac
tail -100 logs/app.log | grep ERROR
```

### Hacer backup manual
```bash
python scripts/backup_db.py
```

---

## Documentación Completa

- **Sistema de Autenticación**: `docs/SISTEMA_AUTENTICACION.md`
- **Resumen Técnico Completo**: `docs/RESUMEN_IMPLEMENTACION_COMPLETA.md`
- **Arquitectura de 3 Capas**: `docs/REFACTORIZACION_FINAL_COMPLETA.md`

---

## Características Principales

✅ **Autenticación Completa**
- Login/logout seguro
- Contraseñas hasheadas (SHA256)
- Gestión de roles y permisos
- Auditoría de todas las operaciones

✅ **Gestión de Inventario**
- Artículos con familias y ubicaciones
- Control de stock en tiempo real
- Alertas de stock mínimo

✅ **Movimientos de Material**
- Recepciones de proveedores
- Traspasos entre almacenes
- Imputaciones a obras (OT)
- Devoluciones a proveedores
- Material perdido

✅ **Inventario Físico**
- Conteos con detección de diferencias
- Ajustes automáticos de stock
- Trazabilidad completa

✅ **Consultas e Informes**
- Stock por almacén
- Histórico de movimientos
- Análisis de consumos
- Pedido ideal sugerido

✅ **Auditoría**
- Logs de todas las operaciones
- Trazabilidad por usuario
- Registro de sesiones

---

## Arquitectura del Sistema

```
┌──────────────────────────────────┐
│   UI (PySide6)                   │ ← Ventanas
│   - ventana_login.py             │
│   - ventanas/maestros/*.py       │
│   - ventanas/operativas/*.py     │
└────────────┬─────────────────────┘
             │ Llama a servicios
┌────────────▼─────────────────────┐
│   SERVICES (Lógica de Negocio)   │ ← Validaciones + Logging
│   - usuarios_service.py          │
│   - articulos_service.py         │
│   - movimientos_service.py       │
└────────────┬─────────────────────┘
             │ Usa repositorios
┌────────────▼─────────────────────┐
│   REPOS (Acceso a Datos)         │ ← Solo SQL
│   - usuarios_repo.py             │
│   - articulos_repo.py            │
│   - movimientos_repo.py          │
└────────────┬─────────────────────┘
             │ Ejecuta queries
┌────────────▼─────────────────────┐
│   SQLite Database                │
│   db/almacen.db                  │
└──────────────────────────────────┘

     ┌─────────────────────┐
     │ SessionManager      │ ← Usuario actual
     │ (Singleton)         │
     └─────────────────────┘
```

---

## Próximos Pasos Sugeridos

1. **Familiarizarse con el sistema**: Probar todas las operaciones
2. **Crear usuarios adicionales**: Uno por cada persona que usará el sistema
3. **Cargar datos maestros**: Proveedores, artículos, familias, ubicaciones
4. **Configurar almacenes**: Crear almacenes y furgonetas
5. **Empezar a operar**: Registrar recepciones y movimientos

---

## Soporte

- **Documentación**: Carpeta `docs/`
- **Logs**: Carpeta `logs/app.log`
- **Backups**: Carpeta `backups/` (automáticos diarios)

---

**Versión**: 2.0
**Fecha**: 31 de Octubre de 2025
