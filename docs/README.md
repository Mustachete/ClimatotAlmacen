# Documentación - Sistema ClimatotAlmacen

Documentación oficial del sistema de gestión de almacén ClimatotAlmacen.

---

## 📚 Guías Principales

### 🚀 Inicio Rápido
- [GUIA_RAPIDA.md](GUIA_RAPIDA.md) - Guía de inicio rápido para nuevos desarrolladores
- [DOCUMENTACION_CLIMATOT_ALMACEN.md](DOCUMENTACION_CLIMATOT_ALMACEN.md) - Documentación completa del sistema

### 🏗️ Arquitectura
- [DIAGRAMA_ARQUITECTURA.md](DIAGRAMA_ARQUITECTURA.md) - Arquitectura del sistema (3 capas: UI → Services → Repos)

### 🔐 Sistemas Core
- [SISTEMA_AUTENTICACION.md](SISTEMA_AUTENTICACION.md) - Sistema de autenticación y roles
- [SISTEMA_BACKUPS_CONFIGURACION.md](SISTEMA_BACKUPS_CONFIGURACION.md) - Sistema de backups automáticos

### 🛠️ Utilidades y Componentes
- [GUIA_UTILIDADES_REUTILIZABLES.md](GUIA_UTILIDADES_REUTILIZABLES.md) - Guía completa de utilidades reutilizables:
  - ComboLoader - Carga estandarizada de combos
  - TableFormatter - Formateo de tablas
  - DateFormatter - Conversión de fechas
  - DialogManager - Gestión de diálogos

---

## 🗂️ Estructura del Proyecto

```
ClimatotAlmacen/
├── src/
│   ├── core/           # Núcleo: BD, logging, sesiones, excepciones
│   ├── repos/          # Capa de datos (acceso a PostgreSQL)
│   ├── services/       # Capa de negocio (lógica de validación)
│   ├── ui/             # Componentes UI base (VentanaMaestroBase, widgets)
│   ├── utils/          # Utilidades (date_formatter)
│   ├── validators/     # Validadores centralizados (uso futuro)
│   ├── ventanas/       # Ventanas de la aplicación
│   │   ├── maestros/   # Ventanas CRUD (artículos, proveedores, etc.)
│   │   ├── operativas/ # Ventanas operativas (recepción, movimientos, etc.)
│   │   └── consultas/  # Ventanas de consulta (stock, histórico, etc.)
│   └── dialogs/        # Diálogos auxiliares
├── scripts/            # Scripts de mantenimiento y migración
├── db/                 # Base de datos PostgreSQL
├── docs/               # Documentación
└── assets/             # Recursos (iconos, imágenes)
```

---

## 📖 Componentes Principales

### Ventanas Maestros (CRUD)
Todas heredan de `VentanaMaestroBase`:
- Familias
- Proveedores
- Artículos
- Ubicaciones
- Operarios
- Furgonetas
- Usuarios

### Ventanas Operativas
- Recepción (entradas de proveedor)
- Movimientos (traspasos entre almacenes)
- Imputación (consumo a obra/OT)
- Devolución
- Material Perdido
- Inventario Físico

### Ventanas de Consulta
- Stock (consulta con filtros múltiples)
- Histórico (movimientos con filtros)
- Ficha de Artículo (vista completa)
- Consumos (análisis por período)
- Pedido Ideal (basado en histórico)
- Asignaciones de Furgonetas
- Informe de Furgonetas

---

## 🔧 Utilidades Reutilizables

### ComboLoader
Carga estandarizada de QComboBox:
```python
from src.ui.combo_loaders import ComboLoader

ComboLoader.cargar_familias(self.cmb_familia, articulos_repo.get_familias)
ComboLoader.cargar_proveedores(self.cmb_proveedor, articulos_repo.get_proveedores)
```

### TableFormatter
Formateo consistente de tablas con colores:
```python
from src.ui.table_formatter import TableFormatter

TableFormatter.colorear_fila_stock_bajo(tabla, fila, stock_actual, stock_minimo)
TableFormatter.formatear_numero(tabla, fila, columna, cantidad, decimales=2)
```

### DateFormatter
Conversión de fechas entre formatos:
```python
from src.utils.date_formatter import DateFormatter

fecha_visual = DateFormatter.db_to_visual("2025-11-25")  # "25/11/2025"
fecha_db = DateFormatter.visual_to_db("25/11/2025")      # "2025-11-25"
```

---

## 🔐 Seguridad

### Autenticación
- Sistema de usuarios con roles (admin, almacen, operario)
- Contraseñas hasheadas con **bcrypt** (migrado desde SHA256)
- Sistema híbrido: soporta contraseñas legacy + bcrypt
- Migración automática al hacer login

### Sesiones
- Gestión de sesiones con timeout configurable
- Cierre automático por inactividad
- Auditoría de sesiones en BD

---

## 📦 Base de Datos

**Motor:** PostgreSQL (migrado desde SQLite)
**Tablas principales:**
- `usuarios`, `sesiones`
- `proveedores`, `operarios`, `familias`, `ubicaciones`, `almacenes`
- `articulos` (tabla central)
- `movimientos` (tabla central de operaciones)
- `inventarios`, `inventario_detalle`
- `asignaciones_furgoneta`

**Vistas:**
- `vw_stock` - Stock por almacén y artículo
- `vw_stock_total` - Stock total por artículo

---

## 🔗 Enlaces Útiles

### Documentación Histórica
- [historico_2025_11/](historico_2025_11/) - Documentación de refactorización noviembre 2025
- [historico/](historico/) - Documentación de sesiones anteriores

### Estado del Proyecto
- [../ESTADO_PROYECTO.md](../ESTADO_PROYECTO.md) - Estado actual del proyecto
- [../GUIA_DESARROLLO.md](../GUIA_DESARROLLO.md) - Guía para nuevos desarrolladores
- [../README.md](../README.md) - README principal

---

## 💡 Convenciones de Código

### Nomenclatura
- **snake_case**: funciones, variables, archivos
- **PascalCase**: clases
- **UPPER_CASE**: constantes

### Imports
Orden estándar:
1. Librería estándar de Python
2. Librerías de terceros
3. Imports locales del proyecto

### Docstrings
Estilo Google:
```python
def funcion(param1: str, param2: int) -> bool:
    """
    Descripción breve de la función.

    Args:
        param1: Descripción del parámetro 1
        param2: Descripción del parámetro 2

    Returns:
        bool: Descripción del retorno

    Raises:
        ValueError: Cuando ocurre X
    """
```

---

## 🚀 Próximos Pasos

Ver [ESTADO_PROYECTO.md](../ESTADO_PROYECTO.md) para:
- Tareas pendientes
- Estado de Sprints
- Roadmap del proyecto

---

**Última actualización:** 25 de Noviembre de 2025
