# 🏢 Sistema Climatot Almacén

Sistema integral de gestión de almacén para empresas de climatización, desarrollado en Python con PySide6 (Qt).

## 📋 Descripción

Sistema completo de gestión de inventario que incluye:
- Gestión de artículos, proveedores, operarios y furgonetas
- Control de stock en múltiples almacenes y furgonetas
- Movimientos de material (recepciones, traspasos, imputaciones, devoluciones)
- Inventarios físicos con ajustes
- Análisis de consumos y pedidos ideales sugeridos
- Sistema de autenticación con roles y permisos
- Informes y consultas avanzadas

## 🚀 Inicio Rápido

### Instalación

1. **Clonar el repositorio:**
```bash
git clone https://github.com/tu-usuario/ClimatotAlmacen.git
cd ClimatotAlmacen
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Crear usuario administrador:**
```bash
python scripts/init_admin.py
```

4. **Ejecutar aplicación:**
```bash
python app.py
```

### Primer Acceso

El script `init_admin.py` te guiará para crear el primer usuario administrador.

**Usuarios de prueba (si usas la BD de ejemplo):**
- Admin: `admin` / `admin123`
- Almacén: `almacen` / `almacen123`
- Operario: `operario1` / `operario123`

## 🏗️ Arquitectura

### Estructura del Proyecto

```
ClimatotAlmacen/
├── app.py                      # Punto de entrada principal
├── src/
│   ├── core/                   # Módulos centrales
│   │   ├── db_utils.py         # Utilidades de base de datos
│   │   ├── logger.py           # Sistema de logging
│   │   ├── session_manager.py  # Gestión de sesiones
│   │   └── idle_manager.py     # Gestión de inactividad
│   ├── repos/                  # Capa de acceso a datos (SQL)
│   │   ├── articulos_repo.py
│   │   ├── movimientos_repo.py
│   │   ├── furgonetas_repo.py
│   │   └── ...
│   ├── services/               # Capa de lógica de negocio
│   │   ├── articulos_service.py
│   │   ├── movimientos_service.py
│   │   ├── pedido_ideal_service.py
│   │   └── ...
│   ├── ui/                     # Componentes base de UI
│   │   ├── estilos.py          # Estilos centralizados
│   │   ├── widgets_base.py     # Widgets reutilizables
│   │   ├── ventana_maestro_base.py    # Clase base para ventanas maestro
│   │   └── dialogo_maestro_base.py    # Clase base para diálogos
│   ├── ventanas/               # Ventanas de la aplicación
│   │   ├── maestros/           # Ventanas de gestión de maestros
│   │   ├── operativas/         # Ventanas de operaciones diarias
│   │   └── consultas/          # Ventanas de informes y consultas
│   └── utils/                  # Utilidades varias
│       └── validaciones.py     # Validaciones centralizadas
├── db/                         # Base de datos SQLite
│   └── almacen.db
├── scripts/                    # Scripts de utilidad
│   ├── init_admin.py           # Crear usuario admin
│   ├── init_db.py              # Inicializar BD
│   └── backup_db.py            # Backup manual
├── logs/                       # Archivos de log (rotativos)
├── docs/                       # Documentación
└── requirements.txt            # Dependencias Python
```

### Arquitectura de 3 Capas

El sistema sigue el patrón de arquitectura en capas:

1. **Capa de Presentación (UI)** - `src/ventanas/`, `src/ui/`
   - Ventanas y diálogos de la interfaz gráfica
   - Clases base reutilizables para ventanas maestro
   - Widgets personalizados

2. **Capa de Lógica de Negocio (Services)** - `src/services/`
   - Reglas de negocio
   - Validaciones complejas
   - Orquestación de operaciones

3. **Capa de Acceso a Datos (Repositories)** - `src/repos/`
   - Consultas SQL
   - Operaciones CRUD
   - Sin lógica de negocio

### Base de Datos

**Motor:** SQLite3

**Tablas principales:**
- `usuarios` - Gestión de usuarios y autenticación
- `articulos` - Catálogo de artículos
- `proveedores` - Proveedores de material
- `familias` - Categorías de artículos
- `almacenes` - Almacenes y furgonetas (tipo)
- `ubicaciones` - Ubicaciones dentro de almacenes
- `operarios` - Personal de la empresa
- `furgonetas` - Vehículos de la flota
- `movimientos` - Todos los movimientos de stock
- `inventarios` - Inventarios físicos realizados
- `albaranes` - Albaranes de recepción

**Vistas:**
- `vw_stock` - Stock actual agregado por artículo/almacén
- `vw_furgonetas_estado_actual` - Estado actual de furgonetas y asignaciones

## 🔐 Sistema de Autenticación

### Roles y Permisos

- **admin**: Acceso total al sistema
- **almacen**: Gestión de stock, recepciones, movimientos
- **operario**: Consultas limitadas, imputaciones básicas

### Características de Seguridad

- Contraseñas hasheadas con SHA256
- Gestión de sesiones con timeout por inactividad
- Auditoría completa de operaciones por usuario
- Sistema de permisos basado en roles

## 📊 Funcionalidades Principales

### Maestros (CRUD Completo)
- ✅ Familias de Artículos
- ✅ Proveedores
- ✅ Artículos (con stock mínimo, precio, proveedor)
- ✅ Ubicaciones
- ✅ Operarios
- ✅ Furgonetas
- ✅ Usuarios

### Operaciones Diarias
- ✅ Recepción de Material (albaranes)
- ✅ Hacer Movimientos (traspasos entre almacenes/furgonetas)
- ✅ Imputar Material a OT
- ✅ Devolución a Proveedor
- ✅ Material Perdido
- ✅ Inventario Físico

### Consultas e Informes
- ✅ Consulta de Stock (con alertas de mínimo)
- ✅ Histórico de Movimientos
- ✅ Ficha de Artículo (detalle completo)
- ✅ Análisis de Consumos (por período, familia, artículo)
- ✅ Pedido Ideal Sugerido (basado en consumo histórico)
- ✅ Asignaciones de Furgonetas
- ✅ Informe Semanal de Furgonetas

## 🛠️ Tecnologías

- **Python 3.12+** - Lenguaje principal
- **PySide6 (Qt 6)** - Framework de interfaz gráfica
- **SQLite3** - Base de datos embebida
- **pandas** - Procesamiento de datos y exportación
- **openpyxl** - Exportación a Excel

## 📖 Documentación Adicional

- [GUIA_DESARROLLO.md](GUIA_DESARROLLO.md) - **Guía completa para desarrolladores** (convenciones, patrones, ejemplos)
- [ESTADO_PROYECTO.md](ESTADO_PROYECTO.md) - Estado actual del proyecto, qué falta, próximos pasos
- [docs/SISTEMA_AUTENTICACION.md](docs/SISTEMA_AUTENTICACION.md) - Detalles del sistema de autenticación
- [docs/PLAN_REFACTORIZACION_COMPLETA.md](docs/PLAN_REFACTORIZACION_COMPLETA.md) - Plan de refactorización en curso

## 🤝 Contribuir

Este es un proyecto privado para uso interno. Para consultas o sugerencias, contacta al equipo de desarrollo.

## 📝 Licencia

Propiedad de Climatot. Todos los derechos reservados.

## 📧 Contacto

Para soporte técnico o consultas, contacta al administrador del sistema.

---

**Última actualización:** Noviembre 2024
**Versión:** 1.0.0 (En desarrollo activo)
