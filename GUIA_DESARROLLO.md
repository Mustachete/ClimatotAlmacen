# 🛠️ Guía de Desarrollo - Sistema Climatot Almacén

Esta guía establece las **convenciones, patrones y mejores prácticas** para desarrollar y mantener el sistema.

---

## 📐 Arquitectura del Sistema

### Patrón de 3 Capas

El sistema sigue estrictamente una arquitectura en 3 capas:

```
┌─────────────────────────────────────┐
│   CAPA DE PRESENTACIÓN (UI)         │  ← src/ventanas/, src/ui/
│   - Ventanas y diálogos             │
│   - Widgets personalizados          │
│   - NO contiene lógica de negocio   │
└──────────────┬──────────────────────┘
               │ Llama a ↓
┌──────────────▼──────────────────────┐
│   CAPA DE LÓGICA DE NEGOCIO         │  ← src/services/
│   - Validaciones complejas          │
│   - Reglas de negocio               │
│   - Orquestación de operaciones     │
│   - NO contiene SQL directo         │
└──────────────┬──────────────────────┘
               │ Llama a ↓
┌──────────────▼──────────────────────┐
│   CAPA DE ACCESO A DATOS            │  ← src/repos/
│   - Consultas SQL                   │
│   - Operaciones CRUD                │
│   - NO contiene lógica de negocio   │
└─────────────────────────────────────┘
```

### Reglas Fundamentales

1. **Las ventanas NUNCA escriben SQL directamente**
   - ❌ Incorrecto: `cur.execute("SELECT * FROM articulos")`
   - ✅ Correcto: `articulos_service.obtener_todos()`

2. **Los services NUNCA contienen SQL**
   - ❌ Incorrecto: Service con `cur.execute()`
   - ✅ Correcto: Service llama a `articulos_repo.obtener_todos()`

3. **Los repos SOLO hacen SQL, sin validaciones**
   - ❌ Incorrecto: Repo validando precio > 0
   - ✅ Correcto: Repo ejecuta INSERT/UPDATE, service valida

---

## 🏗️ Cómo Crear Nuevas Funcionalidades

### 1️⃣ Crear una Ventana Maestro (ABM)

Las ventanas maestro heredan de `VentanaMaestroBase` para máxima reutilización.

**Estructura de archivos necesarios:**
```
src/repos/mi_entidad_repo.py          # Capa de datos
src/services/mi_entidad_service.py    # Lógica de negocio
src/ventanas/maestros/ventana_mi_entidad.py   # Ventana principal
src/ventanas/maestros/dialogo_mi_entidad.py   # Diálogo de edición
```

**Ejemplo completo:**

**1. Crear el Repository (`src/repos/mi_entidad_repo.py`):**

```python
# mi_entidad_repo.py
from src.core.db_utils import get_con

def obtener_todos():
    """Obtiene todas las entidades activas"""
    con = get_con()
    cur = con.cursor()
    cur.execute("SELECT id, nombre, descripcion FROM mi_tabla WHERE activo = 1")
    rows = cur.fetchall()
    con.close()
    return rows

def obtener_por_id(id):
    """Obtiene una entidad por ID"""
    con = get_con()
    cur = con.cursor()
    cur.execute("SELECT id, nombre, descripcion FROM mi_tabla WHERE id = ?", (id,))
    row = cur.fetchone()
    con.close()
    return row

def crear(nombre, descripcion):
    """Crea una nueva entidad"""
    con = get_con()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO mi_tabla (nombre, descripcion, activo) VALUES (?, ?, 1)",
        (nombre, descripcion)
    )
    con.commit()
    nuevo_id = cur.lastrowid
    con.close()
    return nuevo_id

def actualizar(id, nombre, descripcion):
    """Actualiza una entidad existente"""
    con = get_con()
    cur = con.cursor()
    cur.execute(
        "UPDATE mi_tabla SET nombre = ?, descripcion = ? WHERE id = ?",
        (nombre, descripcion, id)
    )
    con.commit()
    con.close()

def eliminar(id):
    """Desactiva lógicamente una entidad"""
    con = get_con()
    cur = con.cursor()
    cur.execute("UPDATE mi_tabla SET activo = 0 WHERE id = ?", (id,))
    con.commit()
    con.close()
```

**2. Crear el Service (`src/services/mi_entidad_service.py`):**

```python
# mi_entidad_service.py
from src.repos import mi_entidad_repo
from src.utils.validaciones import validar_campo_obligatorio

def obtener_todos():
    """Obtiene todas las entidades"""
    return mi_entidad_repo.obtener_todos()

def obtener_por_id(id):
    """Obtiene una entidad por ID"""
    return mi_entidad_repo.obtener_por_id(id)

def crear(nombre, descripcion):
    """
    Crea una nueva entidad con validaciones

    Raises:
        ValueError: Si las validaciones fallan
    """
    # VALIDACIONES DE NEGOCIO AQUÍ
    validar_campo_obligatorio(nombre, "Nombre")

    if len(nombre) < 3:
        raise ValueError("El nombre debe tener al menos 3 caracteres")

    if nombre.strip() != nombre:
        raise ValueError("El nombre no puede tener espacios al inicio o final")

    # Si todo OK, delegar al repo
    return mi_entidad_repo.crear(nombre.strip(), descripcion.strip())

def actualizar(id, nombre, descripcion):
    """
    Actualiza una entidad con validaciones

    Raises:
        ValueError: Si las validaciones fallan
    """
    validar_campo_obligatorio(nombre, "Nombre")

    if len(nombre) < 3:
        raise ValueError("El nombre debe tener al menos 3 caracteres")

    mi_entidad_repo.actualizar(id, nombre.strip(), descripcion.strip())

def eliminar(id):
    """Elimina (desactiva) una entidad"""
    mi_entidad_repo.eliminar(id)
```

**3. Crear el Diálogo (`src/ventanas/maestros/dialogo_mi_entidad.py`):**

```python
# dialogo_mi_entidad.py
from PySide6.QtWidgets import QLineEdit, QTextEdit
from src.ui.dialogo_maestro_base import DialogoMaestroBase
from src.services import mi_entidad_service

class DialogoMiEntidad(DialogoMaestroBase):
    def __init__(self, parent=None, datos=None):
        super().__init__(
            parent=parent,
            titulo="Mi Entidad",
            datos=datos,
            service=mi_entidad_service
        )

    def _crear_campos(self):
        """Define los campos del formulario"""
        # Campo nombre
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ingrese el nombre...")
        self.agregar_campo("Nombre *", self.txt_nombre)

        # Campo descripción
        self.txt_descripcion = QTextEdit()
        self.txt_descripcion.setPlaceholderText("Descripción opcional...")
        self.txt_descripcion.setMaximumHeight(100)
        self.agregar_campo("Descripción", self.txt_descripcion)

    def _cargar_datos_formulario(self, datos):
        """Carga los datos en el formulario (para edición)"""
        self.txt_nombre.setText(datos[1])  # Nombre
        self.txt_descripcion.setPlainText(datos[2] or "")  # Descripción

    def _obtener_datos_formulario(self):
        """Obtiene los datos del formulario para guardar"""
        return {
            'nombre': self.txt_nombre.text().strip(),
            'descripcion': self.txt_descripcion.toPlainText().strip()
        }
```

**4. Crear la Ventana Principal (`src/ventanas/maestros/ventana_mi_entidad.py`):**

```python
# ventana_mi_entidad.py
from src.ui.ventana_maestro_base import VentanaMaestroBase
from src.services import mi_entidad_service
from src.ventanas.maestros.dialogo_mi_entidad import DialogoMiEntidad

class VentanaMiEntidad(VentanaMaestroBase):
    def __init__(self, parent=None):
        super().__init__(
            parent=parent,
            titulo="Gestión de Mi Entidad",
            descripcion="Administra el catálogo de mi entidad",
            servicio=mi_entidad_service,
            dialogo_clase=DialogoMiEntidad,
            columnas=["ID", "Nombre", "Descripción"],
            columnas_visibles=[False, True, True]  # ID oculto
        )
```

**¡Listo! Con solo ~70 líneas tienes un ABM completo.**

---

### 2️⃣ Crear una Ventana Operativa

Las ventanas operativas **NO tienen clase base** (aún), pero siguen patrones comunes.

**Estructura recomendada:**

```python
# ventana_mi_operacion.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from src.ui.widgets_base import TituloVentana, BotonPrimario
from src.ui.estilos import ESTILO_VENTANA
from src.services import mi_operacion_service

class VentanaMiOperacion(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mi Operación")
        self.setStyleSheet(ESTILO_VENTANA)

        layout = QVBoxLayout(self)

        # Título
        titulo = TituloVentana("Mi Operación")
        layout.addWidget(titulo)

        # ... resto de la UI ...

        # Botón acción
        btn_guardar = BotonPrimario("💾 Guardar")
        btn_guardar.clicked.connect(self.guardar)
        layout.addWidget(btn_guardar)

    def guardar(self):
        """Ejecuta la operación usando el service"""
        try:
            # Obtener datos del formulario
            datos = self._obtener_datos()

            # Llamar al service (que valida y ejecuta)
            mi_operacion_service.ejecutar_operacion(datos)

            QMessageBox.information(self, "✅ Éxito", "Operación completada")
            self.close()

        except ValueError as e:
            # Errores de validación
            QMessageBox.warning(self, "⚠️ Validación", str(e))
        except Exception as e:
            # Errores inesperados
            QMessageBox.critical(self, "❌ Error", f"Error: {e}")
```

---

## 🎨 Convenciones de UI

### Uso de Widgets Base

**SIEMPRE usar los widgets de `src/ui/widgets_base.py`:**

```python
from src.ui.widgets_base import (
    TituloVentana,           # Títulos principales
    DescripcionVentana,      # Descripciones/subtítulos
    TablaEstandar,           # Tablas con estilo uniforme
    BotonPrimario,           # Botones de acción principal (verde)
    BotonSecundario,         # Botones secundarios (gris)
    BotonPeligro,            # Botones de eliminación (rojo)
    Alerta                   # Mensajes de alerta/info/error
)
```

### Uso de Estilos

**SIEMPRE usar constantes de `src/ui/estilos.py`:**

```python
from src.ui.estilos import (
    ESTILO_VENTANA,          # Estilo base de ventanas
    ESTILO_ALERTA_ERROR,     # Alerta roja
    ESTILO_ALERTA_INFO,      # Alerta azul
    ESTILO_ALERTA_EXITO,     # Alerta verde
    ESTILO_ALERTA_WARNING,   # Alerta amarilla
    COLOR_PRIMARIO,          # Color principal del tema
    COLOR_SECUNDARIO,        # Color secundario
    # ... etc
)
```

**❌ NUNCA hacer esto:**

```python
self.setStyleSheet("background-color: #f0f0f0; padding: 10px;")  # NO!
```

**✅ SIEMPRE hacer esto:**

```python
self.setStyleSheet(ESTILO_VENTANA)  # SÍ!
```

### Iconos y Emojis

Usar emojis para mejorar la UX:

```python
TituloVentana("📦 Recepción de Material")
BotonPrimario("💾 Guardar")
BotonSecundario("🔄 Actualizar")
BotonPeligro("🗑️ Eliminar")
QMessageBox.information(self, "✅ Éxito", "...")
QMessageBox.warning(self, "⚠️ Advertencia", "...")
QMessageBox.critical(self, "❌ Error", "...")
```

---

## 📝 Convenciones de Código

### Nombrado

```python
# Archivos
mi_modulo.py                    # snake_case

# Clases
class MiClase:                  # PascalCase

# Funciones y variables
def mi_funcion():               # snake_case
mi_variable = 10                # snake_case

# Constantes
MI_CONSTANTE = 100              # UPPER_SNAKE_CASE

# Widgets Qt (por convención)
self.txt_nombre = QLineEdit()   # txt_ para QLineEdit
self.cmb_familia = QComboBox()  # cmb_ para QComboBox
self.chk_activo = QCheckBox()   # chk_ para QCheckBox
self.btn_guardar = QPushButton() # btn_ para QPushButton
self.tabla = QTableWidget()     # sin prefijo
self.lbl_titulo = QLabel()      # lbl_ para QLabel
```

### Imports

**Orden de imports:**

```python
# 1. Biblioteca estándar
import sqlite3
from pathlib import Path
from datetime import datetime

# 2. Bibliotecas de terceros
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt

# 3. Módulos locales
from src.core.db_utils import get_con
from src.ui.estilos import ESTILO_VENTANA
from src.services import articulos_service
```

### Docstrings

**Usar estilo Google:**

```python
def mi_funcion(parametro1, parametro2):
    """
    Breve descripción de la función.

    Args:
        parametro1 (str): Descripción del parámetro 1
        parametro2 (int): Descripción del parámetro 2

    Returns:
        dict: Diccionario con los resultados

    Raises:
        ValueError: Si parametro1 está vacío
        Exception: Si ocurre un error inesperado
    """
    pass
```

---

## 🔍 Validaciones

### Validaciones en Services

**TODAS las validaciones van en la capa de servicios:**

```python
# mi_service.py
from src.utils.validaciones import (
    validar_campo_obligatorio,
    validar_email,
    validar_telefono,
    validar_numero_positivo
)

def crear_proveedor(nombre, email, telefono, precio):
    """Crea un proveedor con todas las validaciones"""

    # Validaciones básicas
    validar_campo_obligatorio(nombre, "Nombre")
    validar_email(email)
    validar_telefono(telefono)
    validar_numero_positivo(precio, "Precio")

    # Validaciones personalizadas
    if len(nombre) < 3:
        raise ValueError("El nombre debe tener al menos 3 caracteres")

    if precio > 999999:
        raise ValueError("El precio no puede superar 999,999")

    # Si todo OK, llamar al repo
    return proveedor_repo.crear(nombre, email, telefono, precio)
```

### Manejo de Errores en UI

**Patrón estándar:**

```python
def guardar(self):
    """Guarda los datos con manejo de errores"""
    try:
        datos = self._obtener_datos()
        mi_service.crear(datos)

        QMessageBox.information(self, "✅ Éxito", "Guardado correctamente")
        self.accept()  # Cerrar diálogo

    except ValueError as e:
        # Errores de validación (esperados)
        QMessageBox.warning(self, "⚠️ Validación", str(e))

    except Exception as e:
        # Errores inesperados
        QMessageBox.critical(self, "❌ Error", f"Error inesperado:\n{e}")
```

---

## 🗄️ Base de Datos

### Conexiones

**SIEMPRE usar `get_con()` de `src.core.db_utils`:**

```python
from src.core.db_utils import get_con

def mi_consulta():
    con = get_con()
    cur = con.cursor()

    cur.execute("SELECT * FROM tabla")
    rows = cur.fetchall()

    con.close()  # IMPORTANTE: Siempre cerrar
    return rows
```

### Transacciones

**Para operaciones múltiples:**

```python
def operacion_compleja():
    con = get_con()
    cur = con.cursor()

    try:
        # Operación 1
        cur.execute("INSERT INTO tabla1 ...")

        # Operación 2
        cur.execute("UPDATE tabla2 ...")

        # Si todo OK, commit
        con.commit()

    except Exception as e:
        # Si algo falla, rollback
        con.rollback()
        raise e

    finally:
        con.close()
```

### SQL Seguro

**SIEMPRE usar parámetros (evita SQL injection):**

```python
# ❌ NUNCA hacer esto:
cur.execute(f"SELECT * FROM users WHERE nombre = '{nombre}'")

# ✅ SIEMPRE hacer esto:
cur.execute("SELECT * FROM users WHERE nombre = ?", (nombre,))
```

---

## 📦 Commits y Git

### Conventional Commits

**Formato:** `tipo(scope): descripción`

**Tipos:**
- `feat` - Nueva funcionalidad
- `fix` - Corrección de bug
- `refactor` - Refactorización sin cambios de funcionalidad
- `docs` - Cambios en documentación
- `style` - Formateo, estilos (no CSS, sino código)
- `test` - Añadir o corregir tests
- `chore` - Tareas de mantenimiento

**Ejemplos:**

```bash
git commit -m "feat(articulos): añadir filtro por familia en listado"
git commit -m "fix(recepcion): corregir validación de EAN duplicado"
git commit -m "refactor(maestros): migrar ventana_proveedores a clase base"
git commit -m "docs: actualizar README con nuevas funcionalidades"
```

### Workflow de Branches

```bash
main                    # Producción estable
├── develop            # Desarrollo activo
├── feature/mi-feature # Nueva funcionalidad
├── fix/bug-123        # Corrección de bug
└── refactor/nombre    # Refactorización
```

---

## ✅ Checklist para Nuevas Funcionalidades

Antes de dar por terminada una nueva funcionalidad, verifica:

### Código
- [ ] Sigue arquitectura de 3 capas (UI → Service → Repo)
- [ ] Usa clases base cuando corresponde
- [ ] Usa widgets y estilos centralizados
- [ ] Tiene validaciones en el service
- [ ] Maneja errores correctamente
- [ ] Tiene docstrings en funciones públicas
- [ ] Nombres descriptivos y consistentes

### Funcionalidad
- [ ] Funciona correctamente (probado manualmente)
- [ ] Muestra mensajes claros al usuario
- [ ] Valida todos los campos obligatorios
- [ ] No permite datos inválidos
- [ ] Cierra conexiones de BD correctamente

### UI/UX
- [ ] Interfaz intuitiva y clara
- [ ] Usa iconos/emojis apropiados
- [ ] Botones con etiquetas descriptivas
- [ ] Campos con placeholders útiles
- [ ] Mensajes de éxito/error claros

### Git
- [ ] Commit con mensaje descriptivo
- [ ] Código formateado consistentemente
- [ ] Sin archivos de debug/temporales
- [ ] Sin contraseñas o datos sensibles

---

## 🚨 Errores Comunes a Evitar

### ❌ NO hacer SQL en ventanas

```python
# ❌ MAL
class VentanaArticulos(QWidget):
    def cargar_datos(self):
        con = get_con()
        cur.execute("SELECT * FROM articulos")  # NO!
```

### ❌ NO duplicar estilos inline

```python
# ❌ MAL
self.setStyleSheet("background: white; padding: 10px;")
btn.setStyleSheet("background: green; color: white;")

# ✅ BIEN
self.setStyleSheet(ESTILO_VENTANA)
btn = BotonPrimario("Guardar")
```

### ❌ NO validar en repos

```python
# ❌ MAL
def crear_articulo(nombre, precio):
    if not nombre:  # NO validar aquí!
        raise ValueError("Nombre obligatorio")

# ✅ BIEN - Validar en service
def crear_articulo(nombre, precio):
    validar_campo_obligatorio(nombre, "Nombre")  # Service
    return articulo_repo.crear(nombre, precio)   # Repo solo SQL
```

### ❌ NO cerrar conexiones

```python
# ❌ MAL
def obtener_datos():
    con = get_con()
    cur = con.cursor()
    cur.execute("SELECT ...")
    return cur.fetchall()  # Conexión queda abierta!

# ✅ BIEN
def obtener_datos():
    con = get_con()
    cur = con.cursor()
    cur.execute("SELECT ...")
    rows = cur.fetchall()
    con.close()  # Siempre cerrar
    return rows
```

---

## 📚 Recursos Adicionales

- [README.md](README.md) - Guía general del proyecto
- [ESTADO_PROYECTO.md](ESTADO_PROYECTO.md) - Estado actual y pendientes
- [docs/SISTEMA_AUTENTICACION.md](docs/SISTEMA_AUTENTICACION.md) - Sistema de login y permisos
- [docs/PLAN_REFACTORIZACION_COMPLETA.md](docs/PLAN_REFACTORIZACION_COMPLETA.md) - Plan de refactorización

---

## 🤝 ¿Dudas?

Si tienes dudas sobre cómo implementar algo:

1. **Busca ejemplos** en el código existente (ventanas maestro son buena referencia)
2. **Revisa esta guía** para patrones y convenciones
3. **Consulta con el equipo** antes de implementar de forma diferente

---

**Última actualización:** 16 de Noviembre de 2024
**Versión:** 1.0.0
