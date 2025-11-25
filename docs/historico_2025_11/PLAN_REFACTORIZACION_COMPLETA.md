# PLAN DE REFACTORIZACIÓN COMPLETA - 155 HORAS

**Fecha inicio:** 2025-11-14
**Duración estimada:** 4 sprints (~40h c/u)
**Objetivo:** Reducir 4,000+ líneas duplicadas y corregir arquitectura

---

## 🎯 OBJETIVOS PRINCIPALES

### Reducción de código:
- **Antes:** 10,458 líneas
- **Después:** ~6,200 líneas (-41%)
- **Eliminación:** 4,000+ líneas duplicadas

### Mejoras de calidad:
- Estilos centralizados: 15% → 95%
- Arquitectura correcta: 35% → 100%
- Mantenibilidad: 3/10 → 8/10
- Test coverage: 0% → 60%+

---

## 📅 SPRINT 1: Fundamentos y Estilos (40 horas)

### Semana 1-2

**Objetivo:** Centralizar estilos y crear infraestructura base

#### Tarea 1.1: Expandir estilos.py (8h)

**Archivo:** `src/ui/estilos.py`

Añadir estilos reutilizables:

```python
# Títulos y descripciones
ESTILO_TITULO_VENTANA = """
    QLabel {
        font-size: 18px;
        font-weight: bold;
        color: #1e3a8a;
        padding: 10px;
    }
"""

ESTILO_DESCRIPCION = """
    QLabel {
        font-size: 13px;
        color: #64748b;
        padding: 5px 10px;
        font-style: italic;
    }
"""

# Tablas de datos
ESTILO_TABLA_DATOS = """
    QTableWidget {
        background-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        gridline-color: #e2e8f0;
    }
    QTableWidget::item {
        padding: 8px;
        border-bottom: 1px solid #f1f5f9;
    }
    QTableWidget::item:selected {
        background-color: #dbeafe;
        color: #1e3a8a;
    }
    QHeaderView::section {
        background-color: #1e3a8a;
        color: white;
        padding: 12px;
        font-weight: bold;
        border: none;
        border-right: 1px solid #1e40af;
    }
"""

# Tabs
ESTILO_TABS = """
    QTabWidget::pane {
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        background-color: white;
        padding: 10px;
    }
    QTabBar::tab {
        background-color: #f1f5f9;
        color: #64748b;
        padding: 10px 20px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }
    QTabBar::tab:selected {
        background-color: #1e3a8a;
        color: white;
    }
"""

# Filtros
ESTILO_PANEL_FILTROS = """
    QGroupBox {
        border: 2px solid #e2e8f0;
        border-radius: 6px;
        margin-top: 10px;
        padding-top: 15px;
        background-color: #f8fafc;
    }
    QGroupBox::title {
        color: #1e3a8a;
        font-weight: bold;
        padding: 5px 10px;
    }
"""

# Alertas
ESTILO_ALERTA_INFO = """
    QLabel {
        background-color: #dbeafe;
        color: #1e40af;
        border-left: 4px solid #3b82f6;
        padding: 10px;
        border-radius: 4px;
    }
"""

ESTILO_ALERTA_WARNING = """
    QLabel {
        background-color: #fef3c7;
        color: #92400e;
        border-left: 4px solid #f59e0b;
        padding: 10px;
        border-radius: 4px;
    }
"""

ESTILO_ALERTA_ERROR = """
    QLabel {
        background-color: #fee2e2;
        color: #991b1b;
        border-left: 4px solid #ef4444;
        padding: 10px;
        border-radius: 4px;
    }
"""
```

**Resultado:** +15 estilos reutilizables

---

#### Tarea 1.2: Refactorizar ventana_consumos.py (5h)

**Antes:** 188 líneas de CSS inline duplicado
**Después:** Usar estilos centralizados

**Cambios:**
1. Importar estilos de estilos.py
2. Reemplazar todos los setStyleSheet inline
3. Verificar que se ve idéntico

**Archivos:**
- `src/ventanas/consultas/ventana_consumos.py`

**Ahorro:** -180 líneas

---

#### Tarea 1.3: Refactorizar ventana_pedido_ideal.py (3h)

**Antes:** 26 líneas inline + tabs personalizados
**Después:** Usar ESTILO_TABS

**Archivos:**
- `src/ventanas/consultas/ventana_pedido_ideal.py`

**Ahorro:** -25 líneas

---

#### Tarea 1.4: Crear widgets_base.py (8h)

**Archivo nuevo:** `src/ui/widgets_base.py`

Widgets reutilizables:

```python
class TituloVentana(QLabel):
    """Título estándar para todas las ventanas"""
    def __init__(self, texto, parent=None):
        super().__init__(texto, parent)
        self.setStyleSheet(ESTILO_TITULO_VENTANA)

class DescripcionVentana(QLabel):
    """Descripción estándar para todas las ventanas"""
    def __init__(self, texto, parent=None):
        super().__init__(texto, parent)
        self.setStyleSheet(ESTILO_DESCRIPCION)

class TablaEstandar(QTableWidget):
    """Tabla con estilos predefinidos"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(ESTILO_TABLA_DATOS)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setAlternatingRowColors(True)

class PanelFiltros(QGroupBox):
    """Panel de filtros estándar"""
    def __init__(self, titulo, parent=None):
        super().__init__(titulo, parent)
        self.setStyleSheet(ESTILO_PANEL_FILTROS)

class Alerta(QLabel):
    """Alertas con iconos y estilos"""
    def __init__(self, texto, tipo='info', parent=None):
        super().__init__(texto, parent)
        if tipo == 'info':
            self.setStyleSheet(ESTILO_ALERTA_INFO)
        elif tipo == 'warning':
            self.setStyleSheet(ESTILO_ALERTA_WARNING)
        elif tipo == 'error':
            self.setStyleSheet(ESTILO_ALERTA_ERROR)
```

**Resultado:** 5 widgets base reutilizables

---

#### Tarea 1.5: Aplicar widgets_base a 3 ventanas (16h)

Refactorizar para usar los widgets base:
- ventana_stock.py
- ventana_historico.py
- ventana_asignaciones.py

**Ahorro:** ~150 líneas

---

**TOTAL SPRINT 1:** 40 horas
**Ahorro líneas:** ~355 líneas
**Entregables:** estilos.py completo, widgets_base.py, 5 ventanas refactorizadas

---

## 📅 SPRINT 2: Clases Base Maestros (40 horas)

### Semana 3-4

**Objetivo:** Eliminar 1,500 líneas duplicadas en maestros

#### Tarea 2.1: Crear VentanaMaestroBase (15h)

**Archivo nuevo:** `src/ui/ventana_maestro_base.py`

Clase base abstracta para todos los maestros:

```python
from abc import ABC, abstractmethod

class VentanaMaestroBase(QWidget, ABC):
    """
    Clase base para todas las ventanas de maestros.
    Implementa la estructura común: tabla + formulario + botones.
    """

    def __init__(self, titulo, descripcion, parent=None):
        super().__init__(parent)
        self.setStyleSheet(ESTILO_VENTANA)

        layout = QVBoxLayout(self)

        # Header estándar
        layout.addWidget(TituloVentana(titulo))
        layout.addWidget(DescripcionVentana(descripcion))

        # Buscador estándar
        self.crear_buscador(layout)

        # Tabla estándar
        self.tabla = TablaEstandar()
        self.configurar_columnas_tabla()
        self.tabla.itemSelectionChanged.connect(self.on_seleccion_cambio)
        layout.addWidget(self.tabla)

        # Formulario
        self.crear_formulario(layout)

        # Botones estándar
        self.crear_botones(layout)

        # Cargar datos inicial
        self.cargar_datos()

    @abstractmethod
    def configurar_columnas_tabla(self):
        """Debe definir las columnas de la tabla"""
        pass

    @abstractmethod
    def crear_formulario(self, layout):
        """Debe crear el formulario de edición"""
        pass

    @abstractmethod
    def get_service(self):
        """Debe retornar el service a usar"""
        pass

    def cargar_datos(self, filtro=""):
        """Carga datos usando el service"""
        service = self.get_service()
        datos = service.listar_todos(filtro)
        self.mostrar_en_tabla(datos)

    def guardar(self):
        """Guarda usando el service"""
        datos = self.obtener_datos_formulario()
        service = self.get_service()

        if self.id_actual:
            exito, msg = service.actualizar(self.id_actual, datos)
        else:
            exito, msg = service.crear(datos)

        if exito:
            QMessageBox.information(self, "✅ Éxito", msg)
            self.cargar_datos()
            self.limpiar_formulario()
        else:
            QMessageBox.warning(self, "⚠️ Error", msg)

    # ... más métodos comunes ...
```

**Resultado:** 1 clase base con toda la lógica común

---

#### Tarea 2.2: Migrar ventana_familias.py (3h)

**Antes:** 220 líneas
**Después:** ~80 líneas

```python
from src.ui.ventana_maestro_base import VentanaMaestroBase
from src.services import familias_service

class VentanaFamilias(VentanaMaestroBase):
    def __init__(self, parent=None):
        super().__init__(
            titulo="Gestión de Familias",
            descripcion="Administra las familias de artículos",
            parent=parent
        )

    def configurar_columnas_tabla(self):
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Descripción"])
        self.tabla.setColumnHidden(0, True)

    def crear_formulario(self, layout):
        form = QFormLayout()
        self.txt_nombre = QLineEdit()
        self.txt_descripcion = QTextEdit()
        form.addRow("Nombre:", self.txt_nombre)
        form.addRow("Descripción:", self.txt_descripcion)
        layout.addLayout(form)

    def get_service(self):
        return familias_service

    def obtener_datos_formulario(self):
        return {
            'nombre': self.txt_nombre.text(),
            'descripcion': self.txt_descripcion.toPlainText()
        }
```

**Ahorro:** -140 líneas

---

#### Tarea 2.3: Migrar ventanas maestros restantes (22h)

Migrar uno por uno:
1. ventana_proveedores.py (3h) - -150 líneas
2. ventana_operarios.py (3h) - -130 líneas
3. ventana_ubicaciones.py (3h) - -120 líneas
4. ventana_furgonetas.py (4h) - -180 líneas
5. ventana_usuarios.py (4h) - -150 líneas
6. ventana_articulos.py (5h) - -200 líneas (más complejo)

**Ahorro total:** ~1,070 líneas

---

**TOTAL SPRINT 2:** 40 horas
**Ahorro líneas:** ~1,210 líneas
**Entregables:** VentanaMaestroBase + 7 maestros refactorizados

---

## 📅 SPRINT 3: Clases Base Operativas (40 horas)

### Semana 5-6

**Objetivo:** Eliminar 2,500 líneas duplicadas en operativas

#### Tarea 3.1: Crear VentanaOperativaBase (20h)

**Archivo nuevo:** `src/ui/ventana_operativa_base.py`

Clase base para operaciones con artículos:

```python
class VentanaOperativaBase(QWidget, ABC):
    """
    Clase base para ventanas operativas (recepción, traspaso, etc.)
    Incluye: formulario principal + tabla de artículos + totales
    """

    def __init__(self, titulo, descripcion, parent=None):
        super().__init__(parent)
        # Estructura común:
        # - Formulario de cabecera (fecha, referencia, etc.)
        # - Buscador de artículos
        # - Tabla temporal de artículos
        # - Botones Guardar/Cancelar
        pass

    @abstractmethod
    def crear_formulario_cabecera(self, layout):
        """Formulario específico de cada operación"""
        pass

    @abstractmethod
    def validar_guardar(self):
        """Validaciones específicas antes de guardar"""
        pass

    @abstractmethod
    def ejecutar_guardado(self):
        """Lógica de guardado específica"""
        pass

    def agregar_articulo_temp(self, articulo, cantidad):
        """Lógica común para agregar artículos"""
        self.articulos_temp.append({'articulo': articulo, 'cantidad': cantidad})
        self.actualizar_tabla_temp()

    # ... más métodos comunes ...
```

**Resultado:** Clase base con estructura común

---

#### Tarea 3.2: Migrar ventanas operativas (20h)

1. ventana_recepcion.py (5h) - -200 líneas
2. ventana_devolucion.py (4h) - -180 líneas
3. ventana_imputacion.py (4h) - -170 líneas
4. ventana_movimientos.py (4h) - -150 líneas
5. ventana_material_perdido.py (3h) - -140 líneas

**Ahorro:** ~840 líneas

---

**TOTAL SPRINT 3:** 40 horas
**Ahorro líneas:** ~840 líneas
**Entregables:** VentanaOperativaBase + 5 operativas refactorizadas

---

## 📅 SPRINT 4: Services y Arquitectura (35 horas)

### Semana 7-8

**Objetivo:** Completar la arquitectura 3 capas correcta

#### Tarea 4.1: Crear services faltantes (15h)

1. **almacenes_service.py** (4h)
   - listar_almacenes()
   - get_almacen_by_nombre()
   - crear_almacen()
   - etc.

2. **completar operarios_service.py** (3h)
   - Métodos de consulta que faltan

3. **completar proveedores_service.py** (3h)
   - Métodos de consulta que faltan

4. **completar ubicaciones_service.py** (3h)
   - Métodos de consulta que faltan

5. **consultas_service.py** (2h)
   - Para ventanas de consultas (stock, historico, etc.)

---

#### Tarea 4.2: Eliminar acceso directo a BD (20h)

Actualizar las 11 ventanas que acceden a BD:

1. ventana_stock.py (2h)
2. ventana_historico.py (2h)
3. ventana_asignaciones.py (2h)
4. ventana_inventario.py (2h)
5. ventana_recepcion.py (2h)
6. ventana_devolucion.py (2h)
7. ventana_imputacion.py (2h)
8. ventana_movimientos.py (2h)
9. ventana_material_perdido.py (2h)
10. dialogs_configuracion.py (1h)
11. ventana_ficha_articulo.py (1h)

**Resultado:** 0 ventanas con acceso directo a BD

---

**TOTAL SPRINT 4:** 35 horas
**Entregables:** Arquitectura 100% correcta, 5 services completos

---

## 📊 RESUMEN TOTAL

| Sprint | Horas | Líneas Eliminadas | Entregables |
|--------|-------|-------------------|-------------|
| 1 | 40h | -355 | Estilos + Widgets base |
| 2 | 40h | -1,210 | Maestros refactorizados |
| 3 | 40h | -840 | Operativas refactorizadas |
| 4 | 35h | N/A | Arquitectura correcta |
| **TOTAL** | **155h** | **-2,405+** | Sistema refactorizado |

---

## ✅ CRITERIOS DE ÉXITO

1. ✅ Reducción >= 40% en líneas de código
2. ✅ 0 estilos inline (excepto casos especiales)
3. ✅ 0 accesos directos a BD desde ventanas
4. ✅ Todas las ventanas maestros usan VentanaMaestroBase
5. ✅ Todas las operativas usan VentanaOperativaBase
6. ✅ Tests unitarios para services principales
7. ✅ Documentación actualizada

---

## 🚀 ¿EMPEZAMOS?

**Próximo paso:** Sprint 1, Tarea 1.1 - Expandir estilos.py

¿Confirmamos?
