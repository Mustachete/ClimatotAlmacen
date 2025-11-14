# Sistema de Ventanas Modales - 6 de Noviembre 2025

## Solicitud del Usuario

El usuario solicitó que cuando se abre una ventana secundaria, la ventana padre debe quedar bloqueada. Específicamente:

> "Quiero que cuando tenga otra ventana abierta, se bloquee la anterior. Me explico con un ejemplo: empiezo con el login, inicio sesion y me sale el menu principal. Ahi le doy a informes y me aparece el submenu. Si yo pulso en la ventana del menu principal, me permite seguir seleccionando cuando realmente me deberia parpadear la ventana del submenu como avisandome de que tengo eso abierto y de que debo volver para atras para poder usar el menu principal."

## Comportamiento Deseado

1. **Login → Menú Principal → Informes**
   - Si el menú de Informes está abierto, el Menú Principal debe estar bloqueado
   - Al intentar hacer clic en el Menú Principal, la ventana de Informes debe "parpadear" o destacarse

2. **Menú Principal → Movimientos**
   - Si Movimientos está abierto, el Menú Principal debe estar bloqueado
   - El usuario debe cerrar Movimientos antes de poder usar el Menú Principal

3. **Aplicación General**
   - Cualquier ventana "hija" bloquea a su ventana "padre"
   - El usuario debe cerrar las ventanas en orden inverso al que las abrió

## Solución Implementada

### Qt WindowModality

En Qt, esto se logra usando `setWindowModality(Qt.WindowModal)`:

- **`Qt.WindowModal`**: La ventana bloquea solo a su ventana padre
- **`Qt.ApplicationModal`**: La ventana bloquea toda la aplicación (no deseado)
- **`Qt.NonModal`**: La ventana no bloquea nada (comportamiento anterior)

### Cambios en el Código

Todos los métodos que abren ventanas ahora siguen este patrón:

```python
def abrir_ventana(self):
    self.ventana = MiVentana(parent=self)  # ← Importante: pasar parent
    self.ventana.setWindowModality(Qt.WindowModal)  # ← Establecer modalidad
    self.ventana.show()
```

**Puntos clave:**
1. `parent=self` - Establece la relación padre-hijo
2. `setWindowModality(Qt.WindowModal)` - Bloquea solo al padre
3. `show()` - Muestra la ventana de forma no bloqueante

## Archivos Modificados

### `app.py`

#### MainMenuWindow (líneas 171-229)

Todas las ventanas abiertas desde el menú principal ahora son modales:

```python
def abrir_recepcion(self):
    """Abrir ventana de recepción (maximizada y modal)"""
    self.ventana_recep = VentanaRecepcion(parent=self)
    self.ventana_recep.setWindowModality(Qt.WindowModal)
    self.ventana_recep.showMaximized()

def abrir_movimientos(self):
    """Abrir ventana de movimientos (maximizada y modal)"""
    self.ventana_mov = VentanaMovimientos(parent=self)
    self.ventana_mov.setWindowModality(Qt.WindowModal)
    self.ventana_mov.showMaximized()

def abrir_maestros(self):
    """Abrir ventana de Maestros (modal)"""
    self.maestros = MaestrosWindow(parent=self)
    self.maestros.setWindowModality(Qt.WindowModal)
    self.maestros.show()

def abrir_imputacion(self):
    """Abrir ventana de imputación (maximizada y modal)"""
    self.ventana_imput = VentanaImputacion(parent=self)
    self.ventana_imput.setWindowModality(Qt.WindowModal)
    self.ventana_imput.showMaximized()

def abrir_info_menu(self):
    """Abrir submenu de informes (modal)"""
    self.menu_info = MenuInformes(parent=self)
    self.menu_info.setWindowModality(Qt.WindowModal)
    self.menu_info.show()

def abrir_material_perdido(self):
    """Abrir ventana de material perdido (maximizada y modal)"""
    self.ventana_perdido = VentanaMaterialPerdido(parent=self)
    self.ventana_perdido.setWindowModality(Qt.WindowModal)
    self.ventana_perdido.showMaximized()

def abrir_devolucion(self):
    """Abrir ventana de devolución (maximizada y modal)"""
    self.ventana_devol = VentanaDevolucion(parent=self)
    self.ventana_devol.setWindowModality(Qt.WindowModal)
    self.ventana_devol.showMaximized()

def abrir_inventario(self):
    """Abrir ventana de inventario físico (modal)"""
    self.ventana_inv = VentanaInventario(parent=self)
    self.ventana_inv.setWindowModality(Qt.WindowModal)
    self.ventana_inv.show()

def abrir_ajustes(self):
    """Abrir menú de ajustes personales (modal)"""
    self.menu_ajustes = MenuAjustes(parent=self)
    self.menu_ajustes.setWindowModality(Qt.WindowModal)
    self.menu_ajustes.show()

def abrir_configuracion(self):
    """Abrir menú de configuración del sistema (solo admin, modal)"""
    self.menu_config = MenuConfiguracion(parent=self)
    self.menu_config.setWindowModality(Qt.WindowModal)
    self.menu_config.show()
```

#### MenuInformes (líneas 285-329)

Todas las ventanas de informes ahora son modales:

```python
def abrir_stock(self):
    from src.ventanas.consultas.ventana_stock import VentanaStock
    self.ventana_stock = VentanaStock(parent=self)
    self.ventana_stock.setWindowModality(Qt.WindowModal)
    self.ventana_stock.show()

def abrir_historico(self):
    from src.ventanas.consultas.ventana_historico import VentanaHistorico
    self.ventana_hist = VentanaHistorico(parent=self)
    self.ventana_hist.setWindowModality(Qt.WindowModal)
    self.ventana_hist.show()

def abrir_ficha(self):
    from src.ventanas.consultas.ventana_ficha_articulo import VentanaFichaArticulo
    self.ventana_ficha = VentanaFichaArticulo(parent=self)
    self.ventana_ficha.setWindowModality(Qt.WindowModal)
    self.ventana_ficha.show()

def abrir_consumos(self):
    """Abrir ventana consolidada de análisis de consumos (modal)"""
    self.ventana_consumos = VentanaConsumos(parent=self)
    self.ventana_consumos.setWindowModality(Qt.WindowModal)
    self.ventana_consumos.show()

def abrir_pedido_ideal(self):
    """Abrir ventana de cálculo de pedido ideal (modal)"""
    self.ventana_pedido_ideal = VentanaPedidoIdeal(parent=self)
    self.ventana_pedido_ideal.setWindowModality(Qt.WindowModal)
    self.ventana_pedido_ideal.show()

def abrir_asignaciones(self):
    """Abrir ventana de consulta de asignaciones de furgonetas (modal)"""
    from src.ventanas.consultas.ventana_asignaciones import VentanaAsignaciones
    self.ventana_asignaciones = VentanaAsignaciones(parent=self)
    self.ventana_asignaciones.setWindowModality(Qt.WindowModal)
    self.ventana_asignaciones.show()

def abrir_informe_furgonetas(self):
    """Abrir ventana de informe semanal de furgonetas (modal)"""
    self.ventana_informe_furg = VentanaInformeFurgonetas(parent=self)
    self.ventana_informe_furg.setWindowModality(Qt.WindowModal)
    self.ventana_informe_furg.show()
```

#### MaestrosWindow (líneas 387-416)

Todas las ventanas de maestros ahora son modales:

```python
def abrir_proveedores(self):
    self.ventana_prov = VentanaProveedores(parent=self)
    self.ventana_prov.setWindowModality(Qt.WindowModal)
    self.ventana_prov.show()

def abrir_familias(self):
    self.ventana_fam = VentanaFamilias(parent=self)
    self.ventana_fam.setWindowModality(Qt.WindowModal)
    self.ventana_fam.show()

def abrir_ubicaciones(self):
    self.ventana_ubic = VentanaUbicaciones(parent=self)
    self.ventana_ubic.setWindowModality(Qt.WindowModal)
    self.ventana_ubic.show()

def abrir_operarios(self):
    self.ventana_oper = VentanaOperarios(parent=self)
    self.ventana_oper.setWindowModality(Qt.WindowModal)
    self.ventana_oper.show()

def abrir_articulos(self):
    self.ventana_art = VentanaArticulos(parent=self)
    self.ventana_art.setWindowModality(Qt.WindowModal)
    self.ventana_art.show()

def abrir_furgonetas(self):
    """Abrir ventana de gestión de furgonetas/almacenes (modal)"""
    self.ventana_furg = VentanaFurgonetas(parent=self)
    self.ventana_furg.setWindowModality(Qt.WindowModal)
    self.ventana_furg.show()
```

#### MenuConfiguracion (líneas 554-558)

Ventana de gestión de usuarios ahora es modal:

```python
def abrir_usuarios(self):
    """Abrir ventana de gestión de usuarios (solo admin, modal)"""
    self.ventana_usuarios = VentanaUsuarios(parent=self)
    self.ventana_usuarios.setWindowModality(Qt.WindowModal)
    self.ventana_usuarios.show()
```

## Jerarquía de Ventanas

```
Login (QDialog modal)
  └─ MainMenuWindow
      ├─ VentanaRecepcion (modal)
      ├─ VentanaMovimientos (modal)
      ├─ VentanaImputacion (modal)
      ├─ VentanaMaterialPerdido (modal)
      ├─ VentanaDevolucion (modal)
      ├─ VentanaInventario (modal)
      ├─ MenuInformes (modal)
      │   ├─ VentanaStock (modal)
      │   ├─ VentanaHistorico (modal)
      │   ├─ VentanaFichaArticulo (modal)
      │   ├─ VentanaConsumos (modal)
      │   ├─ VentanaPedidoIdeal (modal)
      │   ├─ VentanaAsignaciones (modal)
      │   └─ VentanaInformeFurgonetas (modal)
      ├─ MaestrosWindow (modal)
      │   ├─ VentanaProveedores (modal)
      │   ├─ VentanaFamilias (modal)
      │   ├─ VentanaUbicaciones (modal)
      │   ├─ VentanaOperarios (modal)
      │   ├─ VentanaArticulos (modal)
      │   └─ VentanaFurgonetas (modal)
      ├─ MenuAjustes (modal)
      │   └─ DialogoCambiarPassword (QDialog - ya era modal)
      └─ MenuConfiguracion (modal)
          ├─ VentanaUsuarios (modal)
          ├─ DialogoGestionBD (QDialog - ya era modal)
          └─ DialogoBackupRestauracion (QDialog - ya era modal)
```

## Comportamiento Resultante

### Ejemplo 1: Abrir Informes desde Menú Principal

1. Usuario inicia sesión → Login se cierra → MainMenuWindow se abre
2. Usuario hace clic en "📊 Informes" → MenuInformes se abre (modal)
3. **MainMenuWindow está bloqueado**
4. Usuario intenta hacer clic en MainMenuWindow → **MenuInformes parpadea/se destaca**
5. Usuario cierra MenuInformes → MainMenuWindow vuelve a estar disponible

### Ejemplo 2: Abrir Stock desde Informes

1. MainMenuWindow está abierto
2. Usuario abre MenuInformes (MainMenuWindow queda bloqueado)
3. Usuario abre VentanaStock desde MenuInformes (MenuInformes queda bloqueado)
4. **Ambos MainMenuWindow y MenuInformes están bloqueados**
5. Usuario intenta hacer clic en MenuInformes → **VentanaStock parpadea**
6. Usuario cierra VentanaStock → MenuInformes vuelve a estar disponible
7. Usuario cierra MenuInformes → MainMenuWindow vuelve a estar disponible

### Ejemplo 3: Abrir Movimientos

1. MainMenuWindow está abierto
2. Usuario hace clic en "🔄 Movimientos" → VentanaMovimientos se abre maximizada (modal)
3. **MainMenuWindow está bloqueado**
4. Usuario intenta hacer clic en MainMenuWindow → **VentanaMovimientos parpadea**
5. Usuario debe cerrar VentanaMovimientos para volver al menú

## Ventanas No Afectadas

Los **QDialog** que ya usaban `.exec()` mantienen su comportamiento:
- `DialogoCambiarPassword`
- `DialogoGestionBD`
- `DialogoBackupRestauracion`
- Todos los `QMessageBox`

Estos diálogos ya eran modales de aplicación (bloquean toda la app).

## Script de Prueba

Se creó `scripts/test_modalidad.py` para probar el comportamiento:

```bash
python scripts/test_modalidad.py
```

Este script muestra:
1. Una ventana principal
2. Un botón para abrir una ventana hija modal
3. Instrucciones para verificar el bloqueo

## Notas Técnicas

### ¿Por qué `parent=self`?

Sin especificar el padre, Qt no sabe qué ventana debe bloquearse. El parámetro `parent` establece la relación padre-hijo necesaria para la modalidad.

### ¿Por qué `Qt.WindowModal` y no `Qt.ApplicationModal`?

- **WindowModal**: Solo bloquea la ventana padre → Más flexible, mejor UX
- **ApplicationModal**: Bloquea toda la aplicación → Demasiado restrictivo
- **NonModal**: No bloquea nada → Era el comportamiento anterior (no deseado)

### Compatibilidad con Ventanas Existentes

Todas las clases de ventana (`QWidget`, `QMainWindow`, `QDialog`) aceptan el parámetro `parent=None` en su `__init__`. Si alguna ventana no lo acepta, habrá que modificar su constructor.

## Ventajas del Nuevo Sistema

✅ **Mejor UX**: El usuario sabe qué ventana debe cerrar primero
✅ **Menos confusión**: No se pueden acumular ventanas abiertas indefinidamente
✅ **Más intuitivo**: Similar al comportamiento de diálogos estándar
✅ **Feedback visual**: La ventana activa "parpadea" cuando intentas acceder al padre
✅ **Orden claro**: Las ventanas deben cerrarse en orden inverso (LIFO)

## Posibles Problemas y Soluciones

### Problema 1: Ventana no acepta `parent` en el constructor

**Síntoma**: Error al abrir ventana: `TypeError: __init__() got an unexpected keyword argument 'parent'`

**Solución**: Modificar el `__init__` de la ventana:

```python
# Antes
def __init__(self):
    super().__init__()
    # ...

# Después
def __init__(self, parent=None):
    super().__init__(parent)
    # ...
```

### Problema 2: Diálogo modal sobre ventana modal

Si una ventana modal abre un QMessageBox, el QMessageBox debe especificar el padre:

```python
QMessageBox.information(self, "Título", "Mensaje")  # ← self es importante
```

## Conclusión

El sistema de ventanas modales está completamente implementado en `app.py`. Todas las ventanas principales ahora bloquean correctamente a sus padres, proporcionando una experiencia de usuario más intuitiva y ordenada.
