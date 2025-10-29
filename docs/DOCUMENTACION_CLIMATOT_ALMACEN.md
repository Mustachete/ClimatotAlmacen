# 📦 SISTEMA CLIMATOT ALMACÉN - DOCUMENTACIÓN COMPLETA

**Versión:** 1.0  
**Fecha:** 27 de Octubre de 2025  
**Tecnología:** Python + PySide6 + SQLite  

---

## 📑 ÍNDICE

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Estructura de Archivos](#estructura-de-archivos)
4. [Base de Datos](#base-de-datos)
5. [Módulos del Sistema](#módulos-del-sistema)
6. [Funcionalidades Principales](#funcionalidades-principales)
7. [Flujo de Trabajo](#flujo-de-trabajo)
8. [Instalación y Configuración](#instalación-y-configuración)
9. [Guía de Mantenimiento](#guía-de-mantenimiento)

---

## 1. RESUMEN EJECUTIVO

### 🎯 Propósito del Sistema
Sistema de gestión integral de almacén para empresa de climatización, que controla:
- Recepción de material
- Movimientos de stock entre almacenes/furgonetas
- Imputación de material a órdenes de trabajo
- Control de stock en tiempo real
- Inventarios físicos
- Gestión de devoluciones y material perdido

### 💡 Tecnologías Utilizadas
- **Lenguaje:** Python 3.12/3.13
- **Framework UI:** PySide6 (Qt para Python)
- **Base de Datos:** SQLite3
- **Librerías adicionales:** pandas, openpyxl, QtAwesome

### 👥 Usuarios del Sistema
- **Administrador:** Acceso completo a todas las funciones
- **Usuario Almacén:** Acceso a operaciones diarias (recepción, movimientos, imputación)

---

## 2. ARQUITECTURA DEL SISTEMA

### 🏗️ Patrón de Diseño
El sistema sigue una arquitectura modular con:
- **Separación de responsabilidades:** Cada ventana/módulo tiene su propio archivo
- **Centralización de utilidades:** Funciones comunes en `db_utils.py`
- **Gestión centralizada de estilos:** `estilos.py`
- **Gestión de inactividad:** `idle_manager.py` (singleton)

### 📊 Diagrama de Flujo Principal
```
┌─────────────┐
│   LOGIN     │ (app.py)
└──────┬──────┘
       │
       v
┌─────────────────┐
│  MENÚ PRINCIPAL │
└────────┬────────┘
         │
    ┌────┴────┬─────────┬──────────┬────────────┐
    v         v         v          v            v
 Recepción  Movim.  Imputación  Maestros   Informes
```

### 🔐 Sistema de Seguridad
- **Autenticación:** Login con usuario y contraseña hasheada (SHA256)
- **Control de sesiones:** Registro de sesiones activas por usuario/equipo
- **Timeout automático:** Cierre de sesión por inactividad (configurable)
- **Roles de usuario:** Limitación de funciones según rol

---

## 3. ESTRUCTURA DE ARCHIVOS

### 📂 Estructura de Directorios
```
ClimatotAlmacen/
│
├── 📄 app.py                          # Aplicación principal + Login + Menú
├── 📄 init_db.py                      # Inicialización de base de datos
├── 📄 db_utils.py                     # Utilidades de BD (conexión, consultas)
├── 📄 estilos.py                      # Estilos visuales Qt (CSS-like)
├── 📄 idle_manager.py                 # Gestor de inactividad (singleton)
├── 📄 ui_common.py                    # Componentes UI comunes
├── 📄 widgets_personalizados.py       # Widgets Qt personalizados
├── 📄 config_utils.py                 # Utilidades de configuración
├── 📄 buscador_articulos.py           # Diálogo de búsqueda de artículos
├── 📄 actualizar_bd_inventario.py     # Script auxiliar BD inventarios
│
├── 🪟 VENTANAS DEL SISTEMA:
│   ├── ventana_recepcion.py          # Recepción de material
│   ├── ventana_movimientos.py        # Movimientos entre almacenes
│   ├── ventana_imputacion.py         # Imputación a OT
│   ├── ventana_devolucion.py         # Devolución a proveedor
│   ├── ventana_material_perdido.py   # Registro de pérdidas
│   ├── ventana_inventario.py         # Inventarios físicos
│   ├── ventana_stock.py              # Consulta de stock
│   ├── ventana_historico.py          # Histórico de movimientos
│   ├── ventana_ficha_articulo.py     # Ficha completa de artículo
│   │
│   └── MAESTROS:
│       ├── ventana_articulos.py      # Gestión de artículos
│       ├── ventana_proveedores.py    # Gestión de proveedores
│       ├── ventana_operarios.py      # Gestión de operarios
│       ├── ventana_familias.py       # Gestión de familias
│       └── ventana_ubicaciones.py    # Gestión de ubicaciones
│
├── 📁 db/
│   ├── almacen.db                    # Base de datos SQLite
│   └── schema.sql                    # Esquema de la BD
│
├── 📁 config/
│   └── app.ini                       # Configuración de la app
│
├── 📁 backups/                       # Backups automáticos de BD
├── 📁 exports/                       # Exportaciones Excel
├── 📁 logs/                          # Logs de errores
│
└── 📄 requirements.txt                # Dependencias Python
```

### 📋 Archivos Clave

#### **app.py** (Archivo principal - 406 líneas)
- Clase `LoginWindow`: Ventana de inicio de sesión
- Clase `MainMenuWindow`: Menú principal con botones de navegación
- Clase `MenuInformes`: Submenú de informes y consultas
- Clase `MaestrosWindow`: Submenú de gestión de maestros
- Función `main()`: Punto de entrada de la aplicación

#### **db_utils.py** (Utilidades centralizadas - 257 líneas)
Funciones principales:
- `get_con()`: Obtiene conexión SQLite con configuraciones óptimas
- `hash_pwd()`: Hasheo de contraseñas con SHA256
- `today_str()`: Fecha actual en formato YYYY-MM-DD
- `validar_stock_disponible()`: Verifica stock antes de movimientos
- `obtener_stock_articulo()`: Calcula stock actual
- `buscar_articulo_por_ean()`: Búsqueda por código de barras
- `log_err()`: Registro de errores en archivo de log

#### **estilos.py** (9,439 bytes)
Define constantes con estilos Qt (similar a CSS):
- `ESTILO_LOGIN`: Estilos para ventana de login
- `ESTILO_VENTANA`: Estilos globales de las ventanas

#### **idle_manager.py** (8,187 bytes)
Gestor de inactividad (patrón Singleton):
- Monitorea actividad del usuario con un QTimer
- Cierra sesión automáticamente tras X minutos de inactividad
- Se reinicia con cualquier interacción del usuario

---

## 4. BASE DE DATOS

### 🗄️ Motor: SQLite3
**Ubicación:** `db/almacen.db`

### 📐 Esquema de Tablas

#### **Tabla: usuarios**
Gestión de usuarios del sistema.
```sql
CREATE TABLE usuarios (
  usuario     TEXT PRIMARY KEY,
  pass_hash   TEXT NOT NULL,           -- Contraseña hasheada (SHA256)
  rol         TEXT NOT NULL DEFAULT 'almacen',  -- 'admin' o 'almacen'
  activo      INTEGER NOT NULL DEFAULT 1
);
```

#### **Tabla: sesiones**
Control de sesiones activas.
```sql
CREATE TABLE sesiones (
  usuario         TEXT NOT NULL,
  inicio_utc      INTEGER NOT NULL,    -- Timestamp de inicio
  ultimo_ping_utc INTEGER NOT NULL,    -- Último ping de actividad
  hostname        TEXT NOT NULL,       -- Equipo desde donde se conecta
  PRIMARY KEY(usuario, hostname)
);
```

#### **Tabla: proveedores**
Maestro de proveedores.
```sql
CREATE TABLE proveedores (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre   TEXT UNIQUE NOT NULL,
  telefono TEXT,
  contacto TEXT,
  email    TEXT,
  notas    TEXT
);
```

#### **Tabla: operarios**
Maestro de operarios/técnicos.
```sql
CREATE TABLE operarios (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre       TEXT UNIQUE NOT NULL,
  rol_operario TEXT NOT NULL DEFAULT 'ayudante',  -- 'oficial', 'ayudante'
  activo       INTEGER NOT NULL DEFAULT 1
);
```

#### **Tabla: familias**
Categorías de artículos.
```sql
CREATE TABLE familias (
  id     INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT UNIQUE NOT NULL
);
```

#### **Tabla: ubicaciones**
Ubicaciones físicas en el almacén.
```sql
CREATE TABLE ubicaciones (
  id     INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT UNIQUE NOT NULL
);
```

#### **Tabla: almacenes**
Almacenes y furgonetas.
```sql
CREATE TABLE almacenes (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre  TEXT UNIQUE NOT NULL,
  tipo    TEXT DEFAULT 'almacen'  -- 'almacen' o 'furgoneta'
);
```

#### **Tabla: articulos** ⭐ (Tabla central)
Maestro de artículos/productos.
```sql
CREATE TABLE articulos (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  ean                 TEXT UNIQUE,              -- Código de barras
  ref_proveedor       TEXT,                     -- Referencia del proveedor
  nombre              TEXT NOT NULL,
  palabras_clave      TEXT,                     -- Para búsquedas
  u_medida            TEXT DEFAULT 'unidad',   -- Unidad de medida
  min_alerta          REAL DEFAULT 0,           -- Stock mínimo para alerta
  ubicacion_id        INTEGER,
  proveedor_id        INTEGER,
  familia_id          INTEGER,
  marca               TEXT,
  coste               REAL DEFAULT 0,           -- Coste unitario
  pvp_sin             REAL DEFAULT 0,           -- Precio venta sin IVA
  iva                 REAL DEFAULT 21,          -- % IVA
  activo              INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY(ubicacion_id)  REFERENCES ubicaciones(id),
  FOREIGN KEY(proveedor_id)  REFERENCES proveedores(id),
  FOREIGN KEY(familia_id)    REFERENCES familias(id)
);
```

#### **Tabla: movimientos** ⭐ (Tabla de transacciones)
Todos los movimientos de stock.
```sql
CREATE TABLE movimientos (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  fecha       TEXT NOT NULL,                    -- YYYY-MM-DD
  tipo        TEXT NOT NULL,                    -- Ver tipos abajo
  origen_id   INTEGER,                          -- Almacén origen (si aplica)
  destino_id  INTEGER,                          -- Almacén destino (si aplica)
  articulo_id INTEGER NOT NULL,
  cantidad    REAL NOT NULL,
  coste_unit  REAL,
  motivo      TEXT,
  ot          TEXT,                             -- Orden de trabajo
  operario_id INTEGER,
  responsable TEXT,                             -- Usuario que hace el movimiento
  albaran     TEXT,                             -- Número de albarán
  FOREIGN KEY(origen_id)   REFERENCES almacenes(id),
  FOREIGN KEY(destino_id)  REFERENCES almacenes(id),
  FOREIGN KEY(articulo_id) REFERENCES articulos(id),
  FOREIGN KEY(operario_id) REFERENCES operarios(id),
  CHECK(tipo IN ('ENTRADA','TRASPASO','IMPUTACION','PERDIDA','DEVOLUCION'))
);
```

**Tipos de Movimiento:**
- `ENTRADA`: Recepción de material (destino_id obligatorio)
- `TRASPASO`: Movimiento entre almacenes (origen_id y destino_id obligatorios)
- `IMPUTACION`: Consumo en OT (origen_id obligatorio)
- `PERDIDA`: Material perdido/dañado (origen_id obligatorio)
- `DEVOLUCION`: Devolución a proveedor (origen_id obligatorio)

#### **Tabla: albaranes**
Registro de albaranes de proveedores.
```sql
CREATE TABLE albaranes (
  albaran      TEXT PRIMARY KEY,
  proveedor_id INTEGER,
  fecha        TEXT NOT NULL,
  FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
);
```

#### **Tabla: asignaciones_furgoneta**
Asignación de furgonetas a operarios.
```sql
CREATE TABLE asignaciones_furgoneta (
  operario_id   INTEGER NOT NULL,
  fecha         TEXT NOT NULL,
  furgoneta_id  INTEGER NOT NULL,
  PRIMARY KEY (operario_id, fecha),
  FOREIGN KEY(operario_id)   REFERENCES operarios(id),
  FOREIGN KEY(furgoneta_id)  REFERENCES almacenes(id)
);
```

#### **Tabla: inventarios**
Cabecera de inventarios físicos.
```sql
CREATE TABLE inventarios (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  fecha        TEXT NOT NULL,
  responsable  TEXT NOT NULL,
  almacen_id   INTEGER,
  observaciones TEXT,
  estado       TEXT NOT NULL DEFAULT 'EN_PROCESO',  -- 'EN_PROCESO', 'FINALIZADO'
  fecha_cierre TEXT,
  FOREIGN KEY(almacen_id) REFERENCES almacenes(id)
);
```

#### **Tabla: inventario_detalle**
Detalle de inventarios físicos.
```sql
CREATE TABLE inventario_detalle (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  inventario_id   INTEGER NOT NULL,
  articulo_id     INTEGER NOT NULL,
  stock_teorico   REAL NOT NULL DEFAULT 0,   -- Stock según sistema
  stock_contado   REAL NOT NULL DEFAULT 0,   -- Stock contado físicamente
  diferencia      REAL NOT NULL DEFAULT 0,   -- stock_contado - stock_teorico
  FOREIGN KEY(inventario_id) REFERENCES inventarios(id) ON DELETE CASCADE,
  FOREIGN KEY(articulo_id) REFERENCES articulos(id)
);
```

### 📊 Vistas (Views)

#### **Vista: vw_stock**
Calcula el stock por almacén y artículo sumando entradas y restando salidas.
```sql
CREATE VIEW vw_stock AS
  -- ENTRADAS Y TRASPASOS (aumentan stock del destino)
  SELECT destino_id AS almacen_id, articulo_id, SUM(cantidad) AS delta
  FROM movimientos
  WHERE tipo IN ('ENTRADA','TRASPASO')
  GROUP BY destino_id, articulo_id
  
  UNION ALL
  
  -- SALIDAS (disminuyen stock del origen)
  SELECT origen_id AS almacen_id, articulo_id, SUM(-cantidad) AS delta
  FROM movimientos
  WHERE tipo IN ('IMPUTACION','PERDIDA','DEVOLUCION','TRASPASO')
    AND origen_id IS NOT NULL
  GROUP BY origen_id, articulo_id;
```

#### **Vista: vw_stock_total**
Stock total de cada artículo (sumando todos los almacenes).
```sql
CREATE VIEW vw_stock_total AS
  SELECT articulo_id, SUM(delta) AS stock_total
  FROM vw_stock
  GROUP BY articulo_id;
```

### 🔍 Índices para Optimización
```sql
CREATE INDEX idx_movimientos_articulo ON movimientos(articulo_id);
CREATE INDEX idx_movimientos_fecha ON movimientos(fecha);
CREATE INDEX idx_movimientos_tipo ON movimientos(tipo);
CREATE INDEX idx_movimientos_ot ON movimientos(ot);
CREATE INDEX idx_movimientos_operario ON movimientos(operario_id);
CREATE INDEX idx_articulos_nombre ON articulos(nombre);
CREATE INDEX idx_articulos_ean ON articulos(ean);
CREATE INDEX idx_articulos_ref ON articulos(ref_proveedor);
CREATE INDEX idx_articulos_palabras ON articulos(palabras_clave);
CREATE INDEX idx_inventarios_fecha ON inventarios(fecha);
CREATE INDEX idx_inventarios_almacen ON inventarios(almacen_id);
CREATE INDEX idx_inventario_detalle_inv ON inventario_detalle(inventario_id);
CREATE INDEX idx_inventario_detalle_art ON inventario_detalle(articulo_id);
```

---

## 5. MÓDULOS DEL SISTEMA

### 🪟 VENTANAS OPERATIVAS

#### **ventana_recepcion.py** (18,665 bytes)
**Funcionalidad:** Recepción de material de proveedores.

**Flujo:**
1. Seleccionar proveedor
2. Introducir número de albarán
3. Escanear/buscar artículos
4. Introducir cantidades
5. Seleccionar almacén destino
6. Registrar recepción

**Características:**
- Búsqueda de artículos por EAN (código de barras)
- Búsqueda avanzada de artículos
- Validación de datos antes de guardar
- Registro de albarán en tabla `albaranes`
- Inserción masiva en tabla `movimientos`

---

#### **ventana_movimientos.py** (18,027 bytes)
**Funcionalidad:** Movimientos de stock entre almacenes/furgonetas.

**Flujo:**
1. Seleccionar almacén origen
2. Seleccionar almacén destino
3. Buscar artículo
4. Introducir cantidad
5. Verificar stock disponible
6. Registrar traspaso

**Validaciones:**
- Stock suficiente en origen
- Almacén origen ≠ almacén destino
- Cantidad > 0

**Tipo de movimiento:** `TRASPASO`

---

#### **ventana_imputacion.py** (16,092 bytes)
**Funcionalidad:** Imputar material a órdenes de trabajo.

**Flujo:**
1. Introducir número de OT
2. Seleccionar operario (opcional)
3. Seleccionar almacén origen
4. Buscar artículo
5. Introducir cantidad
6. Validar stock
7. Registrar imputación

**Validaciones:**
- OT no vacía
- Stock suficiente en origen
- Cantidad > 0

**Tipo de movimiento:** `IMPUTACION`

---

#### **ventana_devolucion.py** (14,317 bytes)
**Funcionalidad:** Devolución de material a proveedor.

**Flujo:**
1. Seleccionar proveedor
2. Seleccionar almacén origen
3. Buscar artículo
4. Introducir cantidad
5. Motivo de devolución
6. Registrar devolución

**Validaciones:**
- Stock suficiente en origen
- Cantidad > 0

**Tipo de movimiento:** `DEVOLUCION`

---

#### **ventana_material_perdido.py** (13,520 bytes)
**Funcionalidad:** Registrar material perdido o dañado.

**Restricción:** Solo visible para rol 'admin'

**Flujo:**
1. Seleccionar almacén origen
2. Buscar artículo
3. Introducir cantidad perdida
4. Motivo de la pérdida
5. Registrar

**Validaciones:**
- Stock suficiente en origen
- Cantidad > 0

**Tipo de movimiento:** `PERDIDA`

---

#### **ventana_inventario.py** (33,696 bytes)
**Funcionalidad:** Gestión de inventarios físicos.

**Características:**
- Crear nuevo inventario
- Cargar artículos del almacén seleccionado
- Introducir cantidades contadas
- Calcular diferencias (contado - teórico)
- Finalizar inventario
- Generar ajustes automáticos

**Flujo:**
1. Crear inventario (fecha, responsable, almacén)
2. Sistema carga stock teórico de todos los artículos
3. Usuario introduce stock contado
4. Sistema calcula diferencias
5. Al finalizar: genera movimientos de ajuste

**Tablas utilizadas:**
- `inventarios` (cabecera)
- `inventario_detalle` (líneas)

---

### 📊 VENTANAS DE CONSULTA

#### **ventana_stock.py** (13,182 bytes)
**Funcionalidad:** Consulta de stock actual.

**Características:**
- Filtros: Familia, artículo, almacén
- Búsqueda por palabras clave
- Visualización en tabla con columnas:
  - Artículo
  - EAN
  - Stock total
  - Stock por almacén
  - Ubicación
  - Unidad de medida
- Exportación a Excel
- Alerta de stock bajo (< mínimo)

---

#### **ventana_historico.py** (15,318 bytes)
**Funcionalidad:** Histórico de todos los movimientos.

**Filtros disponibles:**
- Rango de fechas
- Tipo de movimiento
- Artículo
- Almacén (origen/destino)
- Orden de trabajo
- Operario

**Columnas visualizadas:**
- Fecha
- Tipo
- Artículo
- Cantidad
- Origen → Destino
- OT
- Operario
- Albarán
- Responsable

**Acciones:**
- Exportación a Excel
- Visualización de detalles

---

#### **ventana_ficha_articulo.py** (25,219 bytes)
**Funcionalidad:** Ficha completa de un artículo.

**Información mostrada:**
1. **Datos generales:**
   - Nombre, EAN, referencia
   - Familia, proveedor, marca
   - Ubicación, unidad de medida
   - Costes y precios

2. **Stock actual:**
   - Stock total
   - Stock por almacén

3. **Histórico de movimientos:**
   - Tabla con todos los movimientos del artículo
   - Filtros por fecha y tipo

4. **Estadísticas:**
   - Consumo mensual
   - Gráficos (pendiente)

---

### ⚙️ VENTANAS DE MAESTROS

#### **ventana_articulos.py** (23,121 bytes)
**Funcionalidad:** Alta, baja y modificación de artículos.

**Campos del formulario:**
- EAN (código de barras)
- Referencia proveedor
- Nombre *
- Palabras clave
- Familia
- Proveedor
- Marca
- Ubicación
- Unidad de medida
- Stock mínimo
- Coste
- PVP sin IVA
- IVA %
- Activo (checkbox)

**Acciones:**
- Nuevo artículo
- Modificar artículo
- Eliminar artículo (marca como inactivo)
- Búsqueda y filtros

---

#### **ventana_proveedores.py** (12,274 bytes)
**Funcionalidad:** Gestión de proveedores.

**Campos:**
- Nombre *
- Teléfono
- Contacto
- Email
- Notas

**Acciones:**
- Alta, baja, modificación
- Búsqueda

---

#### **ventana_operarios.py** (13,537 bytes)
**Funcionalidad:** Gestión de operarios/técnicos.

**Campos:**
- Nombre *
- Rol (Oficial / Ayudante)
- Activo

**Acciones:**
- Alta, baja, modificación
- Búsqueda
- Filtrar por activos

---

#### **ventana_familias.py** (10,718 bytes)
**Funcionalidad:** Gestión de familias de artículos.

**Campos:**
- Nombre *

**Acciones:**
- Alta, baja, modificación
- Búsqueda

---

#### **ventana_ubicaciones.py** (10,887 bytes)
**Funcionalidad:** Gestión de ubicaciones físicas en almacén.

**Campos:**
- Nombre *

**Acciones:**
- Alta, baja, modificación
- Búsqueda

---

### 🔧 MÓDULOS AUXILIARES

#### **buscador_articulos.py** (20,554 bytes)
**Funcionalidad:** Diálogo emergente de búsqueda avanzada de artículos.

**Características:**
- Búsqueda por:
  - Nombre (contiene texto)
  - EAN
  - Referencia proveedor
  - Palabras clave
  - Familia
  - Proveedor
- Tabla de resultados con doble clic para seleccionar
- Búsqueda en tiempo real (mientras escribe)

**Uso:** Se invoca desde otras ventanas cuando se necesita seleccionar un artículo.

---

#### **widgets_personalizados.py** (9,358 bytes)
**Funcionalidad:** Widgets Qt personalizados reutilizables.

**Componentes:**
- `LineEditNumerico`: Campo de texto que solo acepta números
- `LineEditEAN`: Campo para códigos de barras con validación
- `ComboBoxBuscador`: ComboBox con búsqueda integrada
- Otros componentes personalizados

---

#### **idle_manager.py** (8,187 bytes)
**Funcionalidad:** Gestor de inactividad (Singleton).

**Características:**
- Monitorea actividad del usuario con QTimer
- Configurable: tiempo de inactividad (minutos)
- Al detectar inactividad:
  1. Muestra advertencia
  2. Cierra sesión automáticamente
  3. Vuelve a la ventana de login
- Se reinicia con cualquier evento del usuario

**Implementación:**
```python
# Inicio del gestor (en app.py tras login exitoso)
idle_manager = get_idle_manager()
idle_manager.start(login_window=self, main_window=self.main)

# Detener el gestor (al cerrar sesión o app)
idle_manager.stop()
```

---

## 6. FUNCIONALIDADES PRINCIPALES

### 🎯 Flujos de Trabajo Clave

#### **1. RECEPCIÓN DE MATERIAL**
```
Usuario → Recepción → Selecciona Proveedor → Introduce Albarán
       ↓
    Escanea/Busca Artículos → Introduce Cantidades
       ↓
    Selecciona Almacén Destino → GUARDA
       ↓
    Sistema registra:
      • Albarán en tabla `albaranes`
      • Movimientos tipo ENTRADA en tabla `movimientos`
```

#### **2. MOVIMIENTO DE STOCK**
```
Usuario → Movimientos → Selecciona Origen y Destino
       ↓
    Busca Artículo → Introduce Cantidad
       ↓
    Sistema valida stock disponible en origen
       ↓
    GUARDA → Registra movimiento tipo TRASPASO
       ↓
    Stock actualizado automáticamente (vistas SQL)
```

#### **3. IMPUTACIÓN A OT**
```
Usuario → Imputación → Introduce OT → Selecciona Operario
       ↓
    Selecciona Almacén Origen → Busca Artículo
       ↓
    Introduce Cantidad → Sistema valida stock
       ↓
    GUARDA → Registra movimiento tipo IMPUTACION
```

#### **4. INVENTARIO FÍSICO**
```
Admin → Inventario → Nuevo Inventario
       ↓
    Introduce Fecha, Responsable, Almacén
       ↓
    Sistema carga stock teórico de todos los artículos
       ↓
    Usuario cuenta físicamente y registra cantidades
       ↓
    Sistema calcula diferencias
       ↓
    Finalizar → Genera movimientos de ajuste automático
```

---

### 🔐 Control de Acceso

#### **Funciones Públicas (ambos roles):**
- Recepción
- Movimientos
- Imputación
- Devoluciones
- Inventarios
- Consultas (Stock, Histórico, Fichas)
- Gestión de Maestros

#### **Funciones Restringidas (solo admin):**
- Material Perdido
- Configuración (en desarrollo)
- Eliminar registros críticos

---

### 🎨 Características de la Interfaz

#### **Diseño:**
- Interfaz Qt moderna con estilos personalizados
- Iconos con emojis para mejor UX
- Validaciones en tiempo real
- Mensajes de error/éxito descriptivos
- Búsqueda en tiempo real en combos

#### **Usabilidad:**
- Atajos de teclado (Enter para confirmar, Esc para cancelar)
- Doble clic para seleccionar en tablas
- Búsqueda con filtros múltiples
- Exportación a Excel en consultas

---

## 7. FLUJO DE TRABAJO

### 📋 Ciclo de Vida del Material

```
┌─────────────────┐
│   PROVEEDOR     │
└────────┬────────┘
         │ Albarán
         v
┌─────────────────┐
│   RECEPCIÓN     │ ← tipo: ENTRADA
│   (Almacén A)   │
└────────┬────────┘
         │
    ┌────┴─────┐
    v          v
┌────────┐  ┌────────────┐
│Almacén │  │ Furgoneta  │ ← tipo: TRASPASO
│Central │  │  Operario  │
└───┬────┘  └─────┬──────┘
    │             │
    v             v
┌──────────────────────┐
│  IMPUTACIÓN A OT     │ ← tipo: IMPUTACION
│  (Consumo en obra)   │
└──────────────────────┘

    Flujos alternativos:
    
┌──────────────┐         ┌────────────────┐
│ DEVOLUCIÓN   │         │ MATERIAL       │
│ A PROVEEDOR  │         │ PERDIDO        │
└──────────────┘         └────────────────┘
```

---

## 8. INSTALACIÓN Y CONFIGURACIÓN

### 📥 Requisitos Previos
- Python 3.12 o 3.13
- pip (gestor de paquetes Python)
- Sistema operativo: Windows, Linux o macOS

### 🔧 Instalación

#### **Paso 1: Descargar el Proyecto**
```bash
# Clonar o descargar el ZIP y extraer
cd ClimatotAlmacen
```

#### **Paso 2: Instalar Dependencias**
```bash
pip install -r requirements.txt
```

**Librerías que se instalarán:**
- PySide6 (Framework Qt)
- pandas (Análisis de datos)
- openpyxl (Exportación Excel)
- QtAwesome (Iconos)
- Y dependencias adicionales

#### **Paso 3: Inicializar Base de Datos**
```bash
python init_db.py
```

Este script crea:
- Directorio `db/` con `almacen.db`
- Todas las tablas según `schema.sql`
- Usuario admin por defecto:
  - Usuario: `admin`
  - Contraseña: `admin` (cambiar tras primer login)

#### **Paso 4: Ejecutar la Aplicación**
```bash
python app.py
```

### ⚙️ Configuración Adicional

#### **Archivo config/app.ini**
```ini
[app]
timeout_minutos = 15
backup_automatico = true
ruta_backups = ./backups
```

#### **Cambiar Tiempo de Inactividad**
Editar en `idle_manager.py`:
```python
INACTIVITY_TIMEOUT = 15  # minutos
```

---

## 9. GUÍA DE MANTENIMIENTO

### 🔄 Backups de Base de Datos

#### **Backup Manual:**
```bash
# Copiar el archivo almacen.db
cp db/almacen.db backups/almacen_backup_$(date +%Y%m%d).db
```

#### **Backup Automático:**
El sistema puede configurarse para hacer backups automáticos (función en desarrollo).

### 🛠️ Mantenimiento de BD

#### **Optimizar Base de Datos:**
```sql
-- Ejecutar periódicamente
VACUUM;
ANALYZE;
```

#### **Verificar Integridad:**
```sql
PRAGMA integrity_check;
```

#### **Ver Tamaño de BD:**
```bash
ls -lh db/almacen.db
```

### 📊 Consultas SQL Útiles

#### **Ver usuarios activos:**
```sql
SELECT * FROM usuarios WHERE activo = 1;
```

#### **Ver sesiones actuales:**
```sql
SELECT * FROM sesiones;
```

#### **Stock total por artículo:**
```sql
SELECT 
    a.nombre, 
    COALESCE(v.stock_total, 0) as stock
FROM articulos a
LEFT JOIN vw_stock_total v ON a.id = v.articulo_id
WHERE a.activo = 1
ORDER BY stock DESC;
```

#### **Artículos con stock bajo:**
```sql
SELECT 
    a.nombre, 
    a.min_alerta,
    COALESCE(v.stock_total, 0) as stock
FROM articulos a
LEFT JOIN vw_stock_total v ON a.id = v.articulo_id
WHERE a.activo = 1 
  AND COALESCE(v.stock_total, 0) < a.min_alerta
ORDER BY stock ASC;
```

#### **Movimientos de hoy:**
```sql
SELECT 
    m.fecha,
    m.tipo,
    a.nombre as articulo,
    m.cantidad,
    m.ot,
    m.responsable
FROM movimientos m
JOIN articulos a ON m.articulo_id = a.id
WHERE m.fecha = DATE('now')
ORDER BY m.id DESC;
```

#### **Consumos por OT:**
```sql
SELECT 
    m.ot,
    a.nombre as articulo,
    SUM(m.cantidad) as total,
    m.fecha
FROM movimientos m
JOIN articulos a ON m.articulo_id = a.id
WHERE m.tipo = 'IMPUTACION'
  AND m.ot IS NOT NULL
GROUP BY m.ot, a.id
ORDER BY m.ot, total DESC;
```

### 🐛 Solución de Problemas

#### **Error: Base de datos bloqueada**
```bash
# Verificar que no haya otras instancias abiertas
# Eliminar archivo de bloqueo si existe
rm db/almacen.db-wal
rm db/almacen.db-shm
```

#### **Error: Tabla no existe**
```bash
# Reinicializar base de datos
python init_db.py
# PRECAUCIÓN: Esto borra todos los datos
```

#### **Pérdida de contraseña admin**
```python
# Ejecutar en consola Python:
from db_utils import get_con, hash_pwd

con = get_con()
cur = con.cursor()
nueva_pass = hash_pwd("nueva_contraseña")
cur.execute("UPDATE usuarios SET pass_hash=? WHERE usuario='admin'", (nueva_pass,))
con.commit()
con.close()
```

### 📈 Mejoras Futuras Planificadas

1. **Funcionalidades:**
   - Gestión de almacenes/furgonetas
   - Análisis de consumos por período
   - Gráficos y estadísticas
   - Alertas de stock bajo automáticas
   - Sistema de permisos más granular

2. **Técnicas:**
   - Migración a PostgreSQL para entorno multiusuario
   - API REST para integración con otros sistemas
   - App móvil para operarios
   - Impresión de etiquetas de artículos
   - Lector de código de barras hardware

3. **Reportes:**
   - Informe de consumos por operario
   - Informe de consumos por familia
   - Análisis de rotación de stock
   - Valoración de inventario

---

## 📝 NOTAS FINALES

### 💡 Buenas Prácticas

1. **Hacer backup regular** de la base de datos
2. **No eliminar registros**, marcar como inactivos
3. **Validar datos** antes de insertar en BD
4. **Usar transacciones** para operaciones múltiples
5. **Cerrar conexiones** después de cada operación
6. **Loguear errores** en archivo de log

### 🔒 Seguridad

- Las contraseñas se almacenan hasheadas (SHA256)
- Control de sesiones por usuario y equipo
- Timeout automático por inactividad
- Validación de datos de entrada
- Permisos por rol de usuario

### 📞 Soporte

Para dudas o problemas:
1. Revisar logs en `logs/log.txt`
2. Verificar integridad de BD
3. Consultar esta documentación
4. Contactar al administrador del sistema

---

**Fin de la Documentación**

---

## APÉNDICE A: Equivalencias VBA ↔ Python

Para programadores VBA que migran a Python:

| Concepto VBA | Equivalente Python |
|--------------|-------------------|
| `ADODB.Connection` | `sqlite3.connect()` |
| `Recordset` | `cursor.fetchall()` / DataFrame |
| `rs.MoveNext` | bucle `for` en cursor |
| `rs.EOF` | `if not row:` |
| `DLookup()` | función personalizada con SELECT |
| `DoCmd.RunSQL` | `cursor.execute()` + `commit()` |
| `MsgBox` | `QMessageBox` |
| `InputBox` | `QInputDialog` |
| `Form_Load` | `__init__()` |
| `Private Sub btn_Click()` | `def on_button_clicked():` |
| `Format(Date, "yyyy-mm-dd")` | `datetime.strftime("%Y-%m-%d")` |
| `IsNumeric()` | `try: float(x)` |
| `Dim x As Integer` | `x: int = 0` (type hint) |

---

**Versión del Documento:** 1.0  
**Última Actualización:** 27 de Octubre de 2025  
**Autor:** Sistema Climatot Almacén  
