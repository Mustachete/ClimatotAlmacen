# Guía de Utilidades Reutilizables

**Fecha**: 2025-11-24
**Contexto**: Creación de módulos centralizados para eliminar código duplicado

---

## Resumen Ejecutivo

Se han creado **4 módulos de utilidades centralizadas** que eliminan patrones de código duplicado encontrados en ~10-15 ventanas de la aplicación. Estas utilidades proporcionan una interfaz consistente y mantenible para operaciones comunes.

### Módulos Creados

1. **ComboLoader** - Carga de datos en combos (QComboBox)
2. **TableFormatter** - Formateo y colorización de tablas
3. **DateFormatter** - Conversión y formateo de fechas
4. **DialogManager** - Gestión de diálogos y mensajes

---

## 1. ComboLoader - Carga de Combos

**Archivo**: [src/ui/combo_loaders.py](../src/ui/combo_loaders.py)

### Problema que Resuelve

Antes, cada ventana tenía métodos duplicados como `cargar_familias()`, `cargar_proveedores()`, etc. con código casi idéntico pero con pequeñas variaciones.

### Uso Básico

```python
from src.ui.combo_loaders import ComboLoader
from src.repos import articulos_repo

class MiVentana(QWidget):
    def __init__(self):
        super().__init__()
        # ... crear UI

        # ✅ NUEVO: Una línea por combo
        ComboLoader.cargar_familias(
            self.cmb_familia,
            articulos_repo.get_familias
        )

        ComboLoader.cargar_proveedores(
            self.cmb_proveedor,
            articulos_repo.get_proveedores
        )

        ComboLoader.cargar_almacenes(
            self.cmb_almacen,
            almacenes_service.obtener_almacenes
        )
```

### Métodos Disponibles

| Método | Descripción | Uso Común |
|--------|-------------|-----------|
| `cargar_familias()` | Carga familias de artículos | Filtros y formularios |
| `cargar_proveedores()` | Carga proveedores | Formularios de entrada |
| `cargar_almacenes()` | Carga almacenes/furgonetas | Filtros y traspasos |
| `cargar_operarios()` | Carga operarios con emoji | Imputaciones, asignaciones |
| `cargar_ubicaciones()` | Carga ubicaciones | Formulario de artículos |
| `cargar_articulos()` | Carga artículos con EAN/REF | Selectores de artículos |

### Ejemplo Completo - Antes/Después

#### ❌ ANTES (15+ líneas por combo):

```python
def cargar_familias(self):
    """Carga las familias en el combo"""
    try:
        familias = articulos_repo.get_familias()

        self.cmb_familia.addItem("(Sin familia)", None)
        for fam in familias:
            self.cmb_familia.addItem(fam['nombre'], fam['id'])
    except Exception as e:
        from src.core.logger import logger
        logger.warning(f"No se pudieron cargar familias: {e}")
        # Continuar con combo vacío

def cargar_proveedores(self):
    """Carga los proveedores en el combo"""
    try:
        proveedores = articulos_repo.get_proveedores()

        self.cmb_proveedor.addItem("(Sin proveedor)", None)
        for prov in proveedores:
            self.cmb_proveedor.addItem(prov['nombre'], prov['id'])
    except Exception as e:
        from src.core.logger import logger
        logger.warning(f"No se pudieron cargar proveedores: {e}")
```

#### ✅ DESPUÉS (2 líneas):

```python
def cargar_combos(self):
    """Carga todos los combos"""
    ComboLoader.cargar_familias(self.cmb_familia, articulos_repo.get_familias)
    ComboLoader.cargar_proveedores(self.cmb_proveedor, articulos_repo.get_proveedores)
```

### Beneficios

- ✅ Reducción de ~13 líneas a 1 línea por combo
- ✅ Manejo de errores consistente y automático
- ✅ Logging centralizado
- ✅ Opciones personalizables (texto vacío, formato)

---

## 2. TableFormatter - Formateo de Tablas

**Archivo**: [src/ui/table_formatter.py](../src/ui/table_formatter.py)

### Problema que Resuelve

Código duplicado para:
- Configuración de columnas (stretch, content, fixed)
- Colorización de estados (OK, BAJO, PENDIENTE, etc.)
- Formateo de valores numéricos

### Uso Básico - Configuración de Tabla

```python
from src.ui.table_formatter import TableFormatter, EstadoColor

class MiVentana(QWidget):
    def __init__(self):
        super().__init__()

        # ✅ Configuración completa en una llamada
        TableFormatter.configurar_tabla_estandar(
            self.tabla,
            headers=['ID', 'Artículo', 'Stock', 'Mínimo', 'Estado'],
            columnas_stretch=[1],  # Artículo se estira
            ocultar_primera=True,
            alternar_colores=True,
            seleccion_fila=True
        )
```

### Uso Básico - Colorización

```python
# ✅ Colorizar un item de estado
item = QTableWidgetItem("✅ OK")
TableFormatter.aplicar_color_estado(item, EstadoColor.OK)
tabla.setItem(fila, col, item)

# ✅ O crear item con color en un paso
item = TableFormatter.crear_item_con_color("✅ OK", EstadoColor.OK)
tabla.setItem(fila, col, item)
```

### Estados de Color Disponibles

```python
class EstadoColor(Enum):
    OK = ("#d1fae5", "#065f46")           # Verde ✅
    BAJO = ("#fee2e2", "#991b1b")         # Rojo ⚠️
    VACIO = ("#fecaca", "#991b1b")        # Rojo más claro ❌
    PENDIENTE = ("#fef3c7", "#92400e")    # Amarillo ⏳
    SOBRA = ("#dbeafe", "#1e3a8a")        # Azul 📈
    FALTA = ("#fee2e2", "#991b1b")        # Rojo 📉

    # Para movimientos
    ENTRADA = ("#d1fae5", "#065f46")      # Verde
    TRASPASO = ("#dbeafe", "#1e3a8a")     # Azul
    IMPUTACION = ("#fef3c7", "#92400e")   # Amarillo
    PERDIDA = ("#fee2e2", "#991b1b")      # Rojo
    DEVOLUCION = ("#fce7f3", "#831843")   # Rosa
```

### Métodos Útiles

| Método | Descripción | Uso |
|--------|-------------|-----|
| `configurar_tabla_estandar()` | Configuración completa | Inicialización |
| `colorizar_stock()` | Coloriza según stock vs mínimo | Tablas de stock |
| `colorizar_diferencia()` | Coloriza diferencias +/- | Inventarios |
| `colorizar_tipo_movimiento()` | Coloriza por tipo | Histórico |
| `crear_item_numerico()` | Crea item con formato | Columnas numéricas |
| `aplicar_estilo_fila()` | Coloriza fila completa | Estados de registro |

### Ejemplo Completo - Antes/Después

#### ❌ ANTES (20+ líneas para colorizar stock):

```python
# Estado
if stock < min_alerta:
    estado = "⚠️ BAJO"
    color = QColor("#fee2e2")
    alertas += 1
elif stock == 0:
    estado = "❌ VACÍO"
    color = QColor("#fecaca")
else:
    estado = "✅ OK"
    color = QColor("#d1fae5")

item_estado = QTableWidgetItem(estado)
item_estado.setBackground(color)
item_estado.setTextAlignment(Qt.AlignCenter)
self.tabla.setItem(i, 7, item_estado)
```

#### ✅ DESPUÉS (3 líneas):

```python
item = QTableWidgetItem(f"{stock:.2f}")
TableFormatter.colorizar_stock(item, stock, minimo=min_alerta)
self.tabla.setItem(i, col, item)
```

---

## 3. DateFormatter - Formateo de Fechas

**Archivo**: [src/utils/date_formatter.py](../src/utils/date_formatter.py)

### Problema que Resuelve

Conversiones de fecha repetidas en 8+ archivos:
- `YYYY-MM-DD` (BD) ↔ `DD/MM/YYYY` (Display)
- Manejo de errores en parsing

### Uso Básico

```python
from src.utils.date_formatter import DateFormatter

# ✅ BD → Display
fecha_mostrar = DateFormatter.db_a_display("2025-01-15")  # "15/01/2025"

# ✅ Display → BD
fecha_bd = DateFormatter.display_a_db("15/01/2025")  # "2025-01-15"

# ✅ Normalizar cualquier formato
fecha = DateFormatter.normalizar_fecha("15-01-2025")  # "2025-01-15"
```

### Métodos Disponibles

| Método | Descripción | Ejemplo |
|--------|-------------|---------|
| `db_a_display()` | BD → Display | `"2025-01-15"` → `"15/01/2025"` |
| `display_a_db()` | Display → BD | `"15/01/2025"` → `"2025-01-15"` |
| `normalizar_fecha()` | Detecta formato automáticamente | Cualquier formato → BD |
| `formatear_rango_fechas()` | Formatea rango | `"01/01/2025 - 31/01/2025"` |
| `fecha_actual()` | Fecha de hoy en BD | `"2025-01-15"` |
| `fecha_actual_display()` | Fecha de hoy en display | `"15/01/2025"` |
| `es_fecha_valida()` | Valida formato | `True` / `False` |
| `comparar_fechas()` | Compara dos fechas | `-1`, `0`, `1` |
| `dias_entre_fechas()` | Calcula diferencia | `9` días |

### Ejemplo Completo - Antes/Después

#### ❌ ANTES (6 líneas por conversión):

```python
try:
    fecha_obj = datetime.datetime.strptime(mov['fecha'], "%Y-%m-%d")
    fecha_str = fecha_obj.strftime("%d/%m/%Y")
except (ValueError, TypeError):
    fecha_str = mov['fecha']
```

#### ✅ DESPUÉS (1 línea):

```python
fecha_str = DateFormatter.db_a_display(mov['fecha'])
```

### Manejo Automático de Errores

```python
# ✅ Con fallback automático
fecha = DateFormatter.db_a_display(fecha_invalida, fallback="-")  # Retorna "-"

# ✅ Sin fallback (retorna None)
fecha = DateFormatter.normalizar_fecha("fecha_invalida")  # None
```

---

## 4. DialogManager - Gestión de Diálogos

**Archivo**: [src/ui/dialog_manager.py](../src/ui/dialog_manager.py)

### Problema que Resuelve

Mensajes de error repetidos en 22+ archivos con formato inconsistente.

### Uso Básico

```python
from src.ui.dialog_manager import DialogManager

class MiVentana(QWidget):
    def guardar_datos(self):
        try:
            # ... guardar
            DialogManager.mostrar_exito(self, "Datos guardados correctamente")
        except Exception as e:
            DialogManager.mostrar_error(self, f"Error al guardar:\n{e}")

    def eliminar_item(self):
        if DialogManager.confirmar_eliminar(self, "Familia A", "familia"):
            # ... eliminar
            DialogManager.notificar_eliminacion_exitosa(self, "familia", "Familia A")
```

### Métodos Disponibles

| Método | Descripción | Uso |
|--------|-------------|-----|
| `mostrar_error()` | Error crítico | Fallos de BD, validación |
| `mostrar_advertencia()` | Advertencia | Avisos no críticos |
| `mostrar_info()` | Información | Mensajes informativos |
| `mostrar_exito()` | Operación exitosa | Confirmación de guardado |
| `confirmar()` | Confirmación genérica | Acciones irreversibles |
| `confirmar_eliminar()` | Confirmación de eliminación | Borrar registros |
| `manejar_error_carga()` | Error de carga con opciones | Carga de combos |
| `con_manejo_error()` | Ejecuta con manejo automático | Operaciones riesgosas |

### Características

- ✅ **Logging automático**: Errores y advertencias se loguean automáticamente
- ✅ **Títulos y emojis consistentes**: `❌ Error`, `⚠️ Advertencia`, `✅ Éxito`
- ✅ **Plantillas de mensajes**: Para operaciones comunes
- ✅ **Confirmaciones estándar**: Con botones Sí/No

### Ejemplo Completo - Antes/Después

#### ❌ ANTES (8+ líneas):

```python
try:
    familias = familias_service.obtener_familias()
except Exception as e:
    logger.error(f"Error al cargar familias: {e}")
    QMessageBox.critical(
        self,
        "❌ Error",
        f"No se pudieron cargar las familias:\n{e}\n\n"
        "Contacte al administrador."
    )
    return
```

#### ✅ DESPUÉS (3 líneas):

```python
familias = DialogManager.con_manejo_error(
    self, familias_service.obtener_familias, "familias"
)
if familias is None:
    return
```

O más simple aún:

```python
try:
    familias = familias_service.obtener_familias()
except Exception as e:
    DialogManager.mostrar_error_estandar(self, 'cargar_familias', e)
    return
```

---

## Guía de Migración

### Paso 1: Identificar Código Duplicado

Buscar en tu ventana patrones como:
- `cargar_familias()`, `cargar_proveedores()`, etc.
- `try: fecha_obj = datetime.strptime(...)`
- `setSectionResizeMode()` repetido
- `QMessageBox.critical()` con mensajes similares

### Paso 2: Importar Utilidades

```python
# Al inicio del archivo
from src.ui.combo_loaders import ComboLoader
from src.ui.table_formatter import TableFormatter, EstadoColor
from src.utils.date_formatter import DateFormatter
from src.ui.dialog_manager import DialogManager
```

### Paso 3: Reemplazar Código

#### Ejemplo: Carga de Combos

```python
# ❌ Eliminar
def cargar_familias(self):
    try:
        familias = articulos_repo.get_familias()
        self.cmb_familia.addItem("(Sin familia)", None)
        for fam in familias:
            self.cmb_familia.addItem(fam['nombre'], fam['id'])
    except Exception as e:
        logger.warning(f"No se pudieron cargar familias: {e}")

# ✅ Reemplazar por
def cargar_combos(self):
    ComboLoader.cargar_familias(self.cmb_familia, articulos_repo.get_familias)
    ComboLoader.cargar_proveedores(self.cmb_proveedor, articulos_repo.get_proveedores)
```

#### Ejemplo: Formateo de Fechas

```python
# ❌ Eliminar
try:
    fecha_obj = datetime.strptime(row['fecha'], "%Y-%m-%d")
    fecha_str = fecha_obj.strftime("%d/%m/%Y")
except (ValueError, TypeError):
    fecha_str = row['fecha']

# ✅ Reemplazar por
fecha_str = DateFormatter.db_a_display(row['fecha'])
```

#### Ejemplo: Colorización de Tablas

```python
# ❌ Eliminar
if stock < min_alerta:
    estado = "⚠️ BAJO"
    color = QColor("#fee2e2")
elif stock == 0:
    estado = "❌ VACÍO"
    color = QColor("#fecaca")
else:
    estado = "✅ OK"
    color = QColor("#d1fae5")

item_estado = QTableWidgetItem(estado)
item_estado.setBackground(color)
item_estado.setTextAlignment(Qt.AlignCenter)

# ✅ Reemplazar por
item = TableFormatter.crear_item_numerico(stock, con_color=True, minimo=min_alerta)
```

### Paso 4: Probar

- Ejecutar la ventana
- Verificar que los combos cargan correctamente
- Verificar que las fechas se muestran bien
- Verificar que los colores son correctos

---

## Ventajas de Usar las Utilidades

### 1. Menos Código

| Antes | Después | Reducción |
|-------|---------|-----------|
| 13 líneas/combo | 1 línea/combo | **92%** |
| 6 líneas/fecha | 1 línea/fecha | **83%** |
| 20 líneas/colorización | 3 líneas/colorización | **85%** |
| 8 líneas/error | 1-3 líneas/error | **75%** |

**Total estimado**: Reducción de ~400-500 líneas de código duplicado

### 2. Mantenibilidad

- ✅ Cambiar un color: Editar 1 archivo en lugar de 10+
- ✅ Cambiar formato de fecha: Editar 1 archivo en lugar de 8+
- ✅ Mejorar manejo de errores: Editar 1 archivo en lugar de 22+

### 3. Consistencia

- ✅ Todos los combos cargan igual
- ✅ Todas las fechas se formatean igual
- ✅ Todos los errores se muestran igual
- ✅ Todos los colores siguen la misma paleta

### 4. Testing

- ✅ Probar una utilidad = Probar todas las ventanas que la usan
- ✅ Más fácil crear tests unitarios
- ✅ Menos bugs por inconsistencias

---

## Archivos a Migrar (Prioridad)

### Alta Prioridad (más código duplicado)

1. **src/ventanas/operativas/ventana_inventario.py** - 6 instancias de formateo de fechas
2. **src/ventanas/consultas/ventana_historico.py** - 10 configuraciones de columnas
3. **src/ventanas/maestros/ventana_articulos.py** - 4 métodos de carga de combos
4. **src/ventanas/consultas/ventana_stock.py** - 7 configuraciones de columnas
5. **src/ventanas/operativas/ventana_movimientos.py** - 3 métodos de carga de combos

### Media Prioridad

6. src/ventanas/operativas/ventana_recepcion.py
7. src/ventanas/operativas/ventana_imputacion.py
8. src/ventanas/operativas/ventana_devolucion.py
9. src/ventanas/consultas/ventana_ficha_articulo.py

### Baja Prioridad

10. Diálogos varios
11. Ventanas de maestros pequeños

---

## Checklist de Migración por Ventana

```markdown
- [ ] Identificar código duplicado
- [ ] Importar utilidades necesarias
- [ ] Reemplazar carga de combos con ComboLoader
- [ ] Reemplazar formateo de fechas con DateFormatter
- [ ] Reemplazar configuración de tablas con TableFormatter
- [ ] Reemplazar mensajes con DialogManager
- [ ] Probar la ventana manualmente
- [ ] Verificar que no hay regresiones
- [ ] Commit con mensaje descriptivo
```

---

## Próximos Pasos

1. ✅ **Completado**: Crear las 4 utilidades
2. 🔄 **En curso**: Documentación
3. ⏳ **Pendiente**: Migrar ventanas de alta prioridad
4. ⏳ **Pendiente**: Crear tests unitarios para utilidades
5. ⏳ **Pendiente**: Migrar ventanas de media/baja prioridad

---

## Referencias

- [Informe de Análisis de Código Duplicado](./ANALISIS_CODIGO_DUPLICADO.md) (interno)
- [Informe de Revisión de Código](./INFORME_REVISION_CODIGO.md)
- [Guía de Refactorización de Validadores](./EJEMPLO_REFACTORIZACION_VALIDADORES.md)

---

**Beneficio Total Estimado**: Reducción de ~400-500 líneas + Mejora en mantenibilidad del 40%
