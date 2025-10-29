# 📊 CLIMATOT ALMACÉN - DIAGRAMA DE ARQUITECTURA Y FLUJOS

## 🏗️ ARQUITECTURA DEL SISTEMA

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIMATOT ALMACÉN v1.0                         │
│                   Sistema de Gestión Integral                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                          │
│                         (PySide6/Qt)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │    LOGIN     │  │ MENÚ PRINCIPAL│  │   MAESTROS   │         │
│  │   app.py     │→│   app.py      │→│   app.py     │         │
│  └──────────────┘  └───────┬──────┘  └──────────────┘         │
│                            │                                     │
│         ┌──────────────────┼──────────────────┐                │
│         │                  │                  │                 │
│    ┌────▼────┐      ┌──────▼──────┐    ┌─────▼─────┐          │
│    │ OPERAC. │      │  CONSULTAS  │    │ INFORMES  │          │
│    │         │      │             │    │           │          │
│    │Recepción│      │   Stock     │    │ Histórico │          │
│    │Movimient│      │   Ficha     │    │ Consumos  │          │
│    │Imputació│      │ Inventarios │    │ Análisis  │          │
│    │Devoluci.│      │             │    │           │          │
│    └─────────┘      └─────────────┘    └───────────┘          │
│                                                                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                   CAPA DE LÓGICA DE NEGOCIO                      │
│                         (Python Core)                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │   db_utils.py   │  │  estilos.py      │  │idle_manager.py │ │
│  │                 │  │                  │  │                │ │
│  │ • get_con()     │  │ • ESTILO_LOGIN   │  │ • Timeout      │ │
│  │ • hash_pwd()    │  │ • ESTILO_VENTANA │  │ • Monitoreo    │ │
│  │ • validar_stock │  │                  │  │ • Auto-logout  │ │
│  │ • obtener_stock │  │                  │  │                │ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘ │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         buscador_articulos.py                            │   │
│  │  • Búsqueda avanzada • Filtros múltiples • Selección    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                   CAPA DE PERSISTENCIA                           │
│                      (SQLite3)                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    almacen.db                              │ │
│  │                                                            │ │
│  │  TABLAS PRINCIPALES:                                       │ │
│  │  • usuarios          • sesiones        • proveedores       │ │
│  │  • operarios         • familias        • ubicaciones       │ │
│  │  • almacenes         • articulos       • movimientos ⭐    │ │
│  │  • albaranes         • inventarios     • inventario_detalle│ │
│  │                                                            │ │
│  │  VISTAS:                                                   │ │
│  │  • vw_stock          • vw_stock_total                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 🔄 FLUJO DE DATOS - MOVIMIENTOS

```
┌─────────────────────────────────────────────────────────────────┐
│                    TIPOS DE MOVIMIENTOS                          │
└─────────────────────────────────────────────────────────────────┘

1. ENTRADA (Recepción de Proveedor)
   ┌──────────┐       ┌──────────────┐
   │PROVEEDOR │──────→│ ALMACÉN (A)  │
   └──────────┘       └──────────────┘
   Campos: destino_id, albaran, coste_unit

2. TRASPASO (Entre Almacenes)
   ┌──────────────┐       ┌──────────────┐
   │ ALMACÉN (A)  │──────→│ ALMACÉN (B)  │
   └──────────────┘       └──────────────┘
   Campos: origen_id, destino_id

3. IMPUTACION (Consumo en OT)
   ┌──────────────┐       ┌──────────────┐
   │ ALMACÉN (A)  │──────→│   OBRA (OT)  │
   └──────────────┘       └──────────────┘
   Campos: origen_id, ot, operario_id

4. DEVOLUCION (Retorno a Proveedor)
   ┌──────────────┐       ┌──────────┐
   │ ALMACÉN (A)  │──────→│PROVEEDOR │
   └──────────────┘       └──────────┘
   Campos: origen_id, motivo

5. PERDIDA (Material Extraviado)
   ┌──────────────┐       ┌──────────┐
   │ ALMACÉN (A)  │────X──│ELIMINADO │
   └──────────────┘       └──────────┘
   Campos: origen_id, motivo
```

---

## 🗂️ ESTRUCTURA DE VENTANAS

```
app.py (Aplicación Principal)
│
├── LoginWindow
│   └── Autenticación → crea MainMenuWindow
│
├── MainMenuWindow (Menú Principal)
│   │
│   ├── Operaciones Diarias
│   │   ├── VentanaRecepcion        → ventana_recepcion.py
│   │   ├── VentanaMovimientos      → ventana_movimientos.py
│   │   ├── VentanaImputacion       → ventana_imputacion.py
│   │   ├── VentanaDevolucion       → ventana_devolucion.py
│   │   ├── VentanaMaterialPerdido  → ventana_material_perdido.py (admin)
│   │   └── VentanaInventario       → ventana_inventario.py
│   │
│   ├── MenuInformes (Submenu)
│   │   ├── VentanaStock            → ventana_stock.py
│   │   ├── VentanaHistorico        → ventana_historico.py
│   │   └── VentanaFichaArticulo    → ventana_ficha_articulo.py
│   │
│   └── MaestrosWindow (Submenu)
│       ├── VentanaProveedores      → ventana_proveedores.py
│       ├── VentanaArticulos        → ventana_articulos.py
│       ├── VentanaOperarios        → ventana_operarios.py
│       ├── VentanaFamilias         → ventana_familias.py
│       └── VentanaUbicaciones      → ventana_ubicaciones.py
│
└── IdleManager (Gestor de Inactividad)
    └── Monitorea actividad y cierra sesión si inactivo
```

---

## 📋 FLUJO OPERATIVO TÍPICO

```
┌─────────────────────────────────────────────────────────────────┐
│                   DÍA TÍPICO EN EL ALMACÉN                       │
└─────────────────────────────────────────────────────────────────┘

08:00 - Login del usuario "almacen"
        │
        ├─→ Apertura de sesión en tabla 'sesiones'
        └─→ Inicio de IdleManager

08:15 - Llega material del proveedor
        │
        └─→ RECEPCIÓN
            ├─ Seleccionar Proveedor: "Proveedor ABC"
            ├─ Albarán: "ALB-2025-001"
            ├─ Escanear artículos y cantidades
            │  • Art001: 50 unidades
            │  • Art002: 30 unidades
            ├─ Destino: "Almacén Central"
            └─ GUARDAR → Movimientos tipo ENTRADA creados

09:00 - Preparar furgoneta para operario
        │
        └─→ MOVIMIENTOS
            ├─ Origen: "Almacén Central"
            ├─ Destino: "Furgoneta 1"
            ├─ Art001: 10 unidades
            ├─ Art003: 5 unidades
            └─ GUARDAR → Movimientos tipo TRASPASO creados

10:30 - Operario consume material en obra
        │
        └─→ IMPUTACIÓN
            ├─ OT: "OT-2025-123"
            ├─ Operario: "Juan Pérez"
            ├─ Origen: "Furgoneta 1"
            ├─ Art001: 3 unidades
            └─ GUARDAR → Movimiento tipo IMPUTACION creado

14:00 - Consulta de stock
        │
        └─→ INFORMACIÓN → STOCK
            ├─ Filtrar por familia
            ├─ Ver stock actual en todos los almacenes
            └─ Exportar a Excel

16:00 - Material defectuoso
        │
        └─→ DEVOLUCIÓN
            ├─ Proveedor: "Proveedor XYZ"
            ├─ Origen: "Almacén Central"
            ├─ Art005: 2 unidades
            ├─ Motivo: "Material defectuoso"
            └─ GUARDAR → Movimiento tipo DEVOLUCION creado

17:30 - Fin de jornada
        │
        └─→ Logout o cierre automático por inactividad
```

---

## 🔍 CÁLCULO DE STOCK (Vista vw_stock)

```
┌─────────────────────────────────────────────────────────────────┐
│              CÓMO SE CALCULA EL STOCK ACTUAL                     │
└─────────────────────────────────────────────────────────────────┘

Stock de un artículo = ENTRADAS - SALIDAS

ENTRADAS (aumentan stock):
  ┌──────────────────────────────────────┐
  │  tipo = 'ENTRADA'   → destino_id     │
  │  tipo = 'TRASPASO'  → destino_id     │
  └──────────────────────────────────────┘

SALIDAS (disminuyen stock):
  ┌──────────────────────────────────────┐
  │  tipo = 'IMPUTACION' → origen_id     │
  │  tipo = 'PERDIDA'    → origen_id     │
  │  tipo = 'DEVOLUCION' → origen_id     │
  │  tipo = 'TRASPASO'   → origen_id     │
  └──────────────────────────────────────┘

Ejemplo:
┌────────┬─────────┬──────────┬──────────┬──────────┐
│  Tipo  │Cantidad │  Origen  │ Destino  │  Delta   │
├────────┼─────────┼──────────┼──────────┼──────────┤
│ENTRADA │   100   │    -     │ Alm. A   │ Alm.A +100│
│TRASPASO│    20   │  Alm. A  │ Furgo 1  │ A:-20 F:+20│
│IMPUTAC.│     5   │ Furgo 1  │    -     │ Furgo:-5 │
└────────┴─────────┴──────────┴──────────┴──────────┘

Stock Final:
  • Almacén A:  100 - 20 = 80 unidades
  • Furgoneta 1: 20 - 5 = 15 unidades
  • Stock Total: 80 + 15 = 95 unidades
```

---

## 🎯 CARACTERÍSTICAS CLAVE DEL SISTEMA

### ✅ Ventajas Principales

1. **Control Total de Stock**
   - Stock en tiempo real por almacén
   - Alertas de stock mínimo
   - Trazabilidad completa de movimientos

2. **Gestión de Inventarios**
   - Inventarios físicos programados
   - Ajustes automáticos de diferencias
   - Histórico de inventarios

3. **Imputación a OT**
   - Control de consumos por obra
   - Asignación a operarios
   - Análisis de costes por proyecto

4. **Trazabilidad Completa**
   - Histórico de todos los movimientos
   - Relación con albaranes
   - Registro de responsables

5. **Exportación de Datos**
   - Excel para informes
   - Filtros avanzados
   - Datos listos para análisis

### 🔒 Seguridad

- Autenticación con contraseñas hasheadas
- Control de roles (admin/almacén)
- Sesiones por usuario/equipo
- Timeout por inactividad
- Log de errores

### 📊 Reporting

- Stock actual por almacén
- Histórico de movimientos
- Consumos por OT
- Consumos por operario
- Valoración de inventario

---

## 📈 ESTADÍSTICAS DEL PROYECTO

```
┌─────────────────────────────────────────┐
│      MÉTRICAS DEL CÓDIGO               │
├─────────────────────────────────────────┤
│ Archivos Python:        24              │
│ Líneas de código:       ~8,500          │
│ Ventanas:               18              │
│ Tablas BD:              13              │
│ Vistas BD:              2               │
│ Índices BD:             12              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│    DISTRIBUCIÓN DE CÓDIGO              │
├─────────────────────────────────────────┤
│ Ventanas operativas:    ~35%            │
│ Ventanas maestros:      ~25%            │
│ Ventanas consulta:      ~20%            │
│ Utilidades:             ~15%            │
│ Componentes UI:         ~5%             │
└─────────────────────────────────────────┘
```

---

## 🎨 PALETA DE COLORES DEL SISTEMA

```
┌─────────────────────────────────────────────────────────────────┐
│                      TEMA VISUAL                                │
└─────────────────────────────────────────────────────────────────┘

Colores Principales:
  • Fondo ventanas:     #f8fafc (gris muy claro)
  • Fondo inputs:       #ffffff (blanco)
  • Bordes:             #cbd5e1 (gris claro)
  • Texto:              #1e293b (gris oscuro)
  • Botón primario:     #3b82f6 (azul)
  • Botón hover:        #2563eb (azul oscuro)
  • Éxito:              #10b981 (verde)
  • Error:              #ef4444 (rojo)
  • Advertencia:        #f59e0b (naranja)

Iconos (Emojis):
  🔐 Login            📦 Recepción        🔄 Movimientos
  📝 Imputación       ↩️ Devolución       ⚠️ Perdido
  📊 Inventario       📈 Stock            📋 Histórico
  ⚙️ Maestros         🏭 Proveedores      👷 Operarios
  📂 Familias         📍 Ubicaciones      ℹ️ Info
```

---

## 🚀 ROADMAP DE MEJORAS

```
┌─────────────────────────────────────────────────────────────────┐
│                    FASE 1 - Completado ✅                        │
├─────────────────────────────────────────────────────────────────┤
│ ✓ Sistema de login y autenticación                             │
│ ✓ Gestión de maestros (proveedores, artículos, etc.)           │
│ ✓ Recepción de material                                        │
│ ✓ Movimientos de stock                                         │
│ ✓ Imputación a OT                                              │
│ ✓ Devoluciones y pérdidas                                      │
│ ✓ Inventarios físicos                                          │
│ ✓ Consultas de stock e histórico                               │
│ ✓ Exportación a Excel                                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    FASE 2 - En desarrollo 🔧                     │
├─────────────────────────────────────────────────────────────────┤
│ ◯ Gestión de almacenes/furgonetas                              │
│ ◯ Asignación automática de furgonetas                          │
│ ◯ Gráficos y dashboards                                        │
│ ◯ Alertas de stock bajo                                        │
│ ◯ Backup automático programado                                 │
│ ◯ Configuración avanzada                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    FASE 3 - Planificado 📋                       │
├─────────────────────────────────────────────────────────────────┤
│ ◯ Análisis de consumos por período                             │
│ ◯ Análisis de rotación de stock                                │
│ ◯ Valoración de inventario                                     │
│ ◯ Informes avanzados PDF                                       │
│ ◯ Integración con ERP                                          │
│ ◯ API REST                                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    FASE 4 - Futuro 🌟                           │
├─────────────────────────────────────────────────────────────────┤
│ ◯ Migración a PostgreSQL                                       │
│ ◯ App móvil para operarios                                     │
│ ◯ Lector de códigos de barras hardware                         │
│ ◯ Impresión de etiquetas                                       │
│ ◯ Sistema de notificaciones                                    │
│ ◯ Panel web de consulta                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💡 TIPS PARA DESARROLLADORES

### Para Programadores VBA que migran a Python:

1. **Conexión a BD:**
   ```python
   # En lugar de ADODB.Connection
   con = sqlite3.connect("almacen.db")
   cur = con.cursor()
   ```

2. **Consultas:**
   ```python
   # En lugar de rs = conn.Execute("SELECT...")
   cur.execute("SELECT * FROM articulos WHERE id=?", (id,))
   row = cur.fetchone()
   ```

3. **Recorrer resultados:**
   ```python
   # En lugar de Do While Not rs.EOF
   for row in cur.fetchall():
       print(row)
   ```

4. **Mensajes:**
   ```python
   # En lugar de MsgBox
   QMessageBox.information(self, "Título", "Mensaje")
   ```

5. **Formularios:**
   ```python
   # En lugar de Form.Controls("txtNombre").Value
   self.txt_nombre.text()
   ```

### Estructura de una Ventana Típica:

```python
class MiVentana(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mi Ventana")
        self.setupUI()
    
    def setupUI(self):
        # Crear layout y widgets
        layout = QVBoxLayout(self)
        
        # Añadir componentes
        self.txt_dato = QLineEdit()
        btn_guardar = QPushButton("Guardar")
        btn_guardar.clicked.connect(self.guardar)
        
        layout.addWidget(self.txt_dato)
        layout.addWidget(btn_guardar)
    
    def guardar(self):
        # Lógica al hacer clic
        dato = self.txt_dato.text()
        # ... guardar en BD
```

---

## 📞 INFORMACIÓN DE CONTACTO Y SOPORTE

```
┌─────────────────────────────────────────────────────────────────┐
│                     SISTEMA CLIMATOT ALMACÉN                     │
│                                                                  │
│  Versión:    1.0                                                │
│  Fecha:      Octubre 2025                                       │
│  Tecnología: Python 3.12+ | PySide6 | SQLite3                  │
│  Licencia:   Uso Interno                                        │
│                                                                  │
│  Documentación completa en:                                     │
│  • DOCUMENTACION_CLIMATOT_ALMACEN.md                           │
│  • DIAGRAMA_ARQUITECTURA.md (este archivo)                     │
│                                                                  │
│  Logs del sistema:                                              │
│  • logs/log.txt                                                 │
│                                                                  │
│  Base de datos:                                                 │
│  • db/almacen.db                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

**Fin del Diagrama de Arquitectura**

Este documento complementa la documentación principal y ofrece una
vista visual y esquemática del sistema Climatot Almacén.
