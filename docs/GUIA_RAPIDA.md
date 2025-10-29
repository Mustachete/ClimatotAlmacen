# ⚡ GUÍA RÁPIDA DE REFERENCIA - CLIMATOT ALMACÉN

---

## 🎯 ACCESO RÁPIDO A INFORMACIÓN CLAVE

### 📁 Archivos Principales del Sistema

| Archivo | Propósito | Líneas |
|---------|-----------|--------|
| `app.py` | Aplicación principal, Login, Menú | 406 |
| `db_utils.py` | Funciones BD centralizadas | 257 |
| `ventana_recepcion.py` | Recepción de material | ~600 |
| `ventana_movimientos.py` | Traspasos entre almacenes | ~570 |
| `ventana_imputacion.py` | Imputación a OT | ~510 |
| `ventana_inventario.py` | Inventarios físicos | ~1,050 |
| `ventana_articulos.py` | CRUD de artículos | ~720 |
| `buscador_articulos.py` | Búsqueda avanzada | ~640 |
| `idle_manager.py` | Gestor de inactividad | ~260 |

---

## 🔑 CREDENCIALES POR DEFECTO

```
Usuario:    admin
Contraseña: admin

⚠️ CAMBIAR TRAS PRIMER LOGIN
```

---

## 🗄️ CONSULTAS SQL FRECUENTES

### Ver Stock Actual de Todos los Artículos
```sql
SELECT 
    a.nombre AS Articulo,
    a.ean AS Codigo,
    COALESCE(v.stock_total, 0) AS Stock,
    a.u_medida AS Unidad,
    u.nombre AS Ubicacion
FROM articulos a
LEFT JOIN vw_stock_total v ON a.id = v.articulo_id
LEFT JOIN ubicaciones u ON a.ubicacion_id = u.id
WHERE a.activo = 1
ORDER BY Stock DESC;
```

### Ver Stock por Almacén
```sql
SELECT 
    alm.nombre AS Almacen,
    a.nombre AS Articulo,
    SUM(v.delta) AS Stock
FROM vw_stock v
JOIN almacenes alm ON v.almacen_id = alm.id
JOIN articulos a ON v.articulo_id = a.id
GROUP BY v.almacen_id, v.articulo_id
HAVING Stock > 0
ORDER BY Almacen, Stock DESC;
```

### Artículos con Stock Bajo
```sql
SELECT 
    a.nombre AS Articulo,
    COALESCE(v.stock_total, 0) AS Stock,
    a.min_alerta AS Minimo
FROM articulos a
LEFT JOIN vw_stock_total v ON a.id = v.articulo_id
WHERE a.activo = 1 
  AND COALESCE(v.stock_total, 0) < a.min_alerta
  AND a.min_alerta > 0
ORDER BY Stock ASC;
```

### Movimientos de Hoy
```sql
SELECT 
    m.fecha,
    m.tipo,
    a.nombre AS Articulo,
    m.cantidad,
    alm_o.nombre AS Origen,
    alm_d.nombre AS Destino,
    m.ot,
    m.responsable
FROM movimientos m
JOIN articulos a ON m.articulo_id = a.id
LEFT JOIN almacenes alm_o ON m.origen_id = alm_o.id
LEFT JOIN almacenes alm_d ON m.destino_id = alm_d.id
WHERE m.fecha = DATE('now')
ORDER BY m.id DESC;
```

### Consumos por Orden de Trabajo
```sql
SELECT 
    m.ot AS OrdenTrabajo,
    a.nombre AS Articulo,
    SUM(m.cantidad) AS Consumido,
    a.u_medida AS Unidad,
    SUM(m.cantidad * COALESCE(m.coste_unit, a.coste, 0)) AS Coste_Total
FROM movimientos m
JOIN articulos a ON m.articulo_id = a.id
WHERE m.tipo = 'IMPUTACION'
  AND m.ot IS NOT NULL
GROUP BY m.ot, a.id
ORDER BY m.ot, Coste_Total DESC;
```

### Movimientos por Operario
```sql
SELECT 
    o.nombre AS Operario,
    a.nombre AS Articulo,
    SUM(m.cantidad) AS Total,
    m.ot
FROM movimientos m
JOIN articulos a ON m.articulo_id = a.id
JOIN operarios o ON m.operario_id = o.id
WHERE m.tipo = 'IMPUTACION'
  AND m.fecha >= DATE('now', '-30 days')
GROUP BY o.id, a.id, m.ot
ORDER BY o.nombre, Total DESC;
```

### Historial de un Artículo Específico
```sql
SELECT 
    m.fecha,
    m.tipo,
    m.cantidad,
    alm_o.nombre AS Origen,
    alm_d.nombre AS Destino,
    m.ot,
    m.motivo,
    m.responsable
FROM movimientos m
LEFT JOIN almacenes alm_o ON m.origen_id = alm_o.id
LEFT JOIN almacenes alm_d ON m.destino_id = alm_d.id
WHERE m.articulo_id = ?  -- Reemplazar ? con ID del artículo
ORDER BY m.fecha DESC, m.id DESC
LIMIT 100;
```

### Recepciones de un Proveedor
```sql
SELECT 
    m.fecha,
    m.albaran,
    a.nombre AS Articulo,
    m.cantidad,
    m.coste_unit,
    alm.nombre AS Destino
FROM movimientos m
JOIN articulos a ON m.articulo_id = a.id
JOIN almacenes alm ON m.destino_id = alm.id
JOIN albaranes alb ON m.albaran = alb.albaran
WHERE alb.proveedor_id = ?  -- Reemplazar ? con ID del proveedor
  AND m.tipo = 'ENTRADA'
ORDER BY m.fecha DESC;
```

---

## 🐍 SNIPPETS DE CÓDIGO PYTHON ÚTILES

### Conectar a la Base de Datos
```python
from db_utils import get_con

con = get_con()
cur = con.cursor()
cur.execute("SELECT * FROM articulos WHERE activo = 1")
rows = cur.fetchall()
con.close()
```

### Buscar Artículo por EAN
```python
from db_utils import buscar_articulo_por_ean

articulo = buscar_articulo_por_ean("1234567890123")
if articulo:
    print(f"Encontrado: {articulo[3]}")  # articulo[3] = nombre
else:
    print("No encontrado")
```

### Obtener Stock de un Artículo
```python
from db_utils import obtener_stock_articulo

# Stock total
stock_total = obtener_stock_articulo(articulo_id=5)

# Stock en un almacén específico
stock_almacen = obtener_stock_articulo(articulo_id=5, almacen_id=2)
```

### Validar Stock Antes de Movimiento
```python
from db_utils import validar_stock_disponible

if validar_stock_disponible(articulo_id=5, almacen_id=2, cantidad=10):
    print("Stock suficiente")
else:
    print("Stock insuficiente")
```

### Registrar un Movimiento
```python
from db_utils import get_con, today_str

con = get_con()
cur = con.cursor()

cur.execute("""
    INSERT INTO movimientos (
        fecha, tipo, origen_id, destino_id, 
        articulo_id, cantidad, responsable
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    today_str(),      # Fecha actual
    'TRASPASO',       # Tipo
    1,                # Almacén origen
    2,                # Almacén destino
    5,                # Artículo ID
    10.0,             # Cantidad
    'usuario'         # Responsable
))

con.commit()
con.close()
```

### Crear Nuevo Artículo
```python
from db_utils import get_con

con = get_con()
cur = con.cursor()

cur.execute("""
    INSERT INTO articulos (
        ean, nombre, u_medida, 
        familia_id, proveedor_id, coste, activo
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    "1234567890123",   # EAN
    "Artículo Nuevo",  # Nombre
    "unidad",          # Unidad medida
    1,                 # Familia ID
    1,                 # Proveedor ID
    12.50,             # Coste
    1                  # Activo
))

nuevo_id = cur.lastrowid
con.commit()
con.close()

print(f"Artículo creado con ID: {nuevo_id}")
```

### Mostrar Mensaje de Error
```python
from PySide6.QtWidgets import QMessageBox

QMessageBox.critical(
    self, 
    "❌ Error", 
    "Ha ocurrido un error al guardar los datos"
)
```

### Mostrar Mensaje de Éxito
```python
from PySide6.QtWidgets import QMessageBox

QMessageBox.information(
    self, 
    "✅ Éxito", 
    "Los datos se han guardado correctamente"
)
```

### Confirmar Acción
```python
from PySide6.QtWidgets import QMessageBox

respuesta = QMessageBox.question(
    self,
    "❓ Confirmar",
    "¿Está seguro de eliminar este registro?",
    QMessageBox.Yes | QMessageBox.No
)

if respuesta == QMessageBox.Yes:
    # Eliminar registro
    pass
```

---

## 🛠️ COMANDOS ÚTILES DEL SISTEMA

### Inicializar/Reiniciar Base de Datos
```bash
python init_db.py
```
⚠️ **ATENCIÓN:** Esto borra todos los datos existentes

### Ejecutar la Aplicación
```bash
python app.py
```

### Verificar Integridad de BD
```bash
sqlite3 db/almacen.db "PRAGMA integrity_check;"
```

### Backup Manual de BD
```bash
# Windows
copy db\almacen.db backups\almacen_backup_YYYYMMDD.db

# Linux/Mac
cp db/almacen.db backups/almacen_backup_$(date +%Y%m%d).db
```

### Ver Tamaño de BD
```bash
# Windows
dir db\almacen.db

# Linux/Mac
ls -lh db/almacen.db
```

### Optimizar BD
```bash
sqlite3 db/almacen.db "VACUUM;"
sqlite3 db/almacen.db "ANALYZE;"
```

### Exportar Tabla a CSV
```bash
sqlite3 -header -csv db/almacen.db "SELECT * FROM articulos;" > articulos.csv
```

---

## 🔧 SOLUCIÓN RÁPIDA DE PROBLEMAS

### Problema: No se puede abrir la aplicación
**Solución:**
1. Verificar que Python está instalado: `python --version`
2. Instalar dependencias: `pip install -r requirements.txt`
3. Verificar que existe `db/almacen.db`

### Problema: Error "Database is locked"
**Solución:**
1. Cerrar todas las instancias de la aplicación
2. Eliminar archivos temporales:
   ```bash
   rm db/almacen.db-wal
   rm db/almacen.db-shm
   ```

### Problema: Olvidé la contraseña de admin
**Solución:**
```python
# Ejecutar en consola Python
from db_utils import get_con, hash_pwd

con = get_con()
cur = con.cursor()
nueva_pass = hash_pwd("nuevacontraseña")
cur.execute("UPDATE usuarios SET pass_hash=? WHERE usuario='admin'", (nueva_pass,))
con.commit()
con.close()
```

### Problema: La aplicación no responde
**Solución:**
1. Verificar logs en `logs/log.txt`
2. Verificar integridad de BD: `PRAGMA integrity_check;`
3. Reiniciar la aplicación

### Problema: Error al exportar a Excel
**Solución:**
1. Verificar que openpyxl está instalado: `pip install openpyxl`
2. Verificar permisos de escritura en carpeta `exports/`

---

## 📊 ESTRUCTURA DE LA TABLA movimientos

```
┌──────────────┬──────────┬─────────────────────────────────────┐
│    Campo     │   Tipo   │           Descripción              │
├──────────────┼──────────┼─────────────────────────────────────┤
│ id           │ INTEGER  │ ID único (autoincremental)         │
│ fecha        │ TEXT     │ Fecha YYYY-MM-DD                   │
│ tipo         │ TEXT     │ ENTRADA/TRASPASO/IMPUTACION/etc    │
│ origen_id    │ INTEGER  │ ID almacén origen (nullable)       │
│ destino_id   │ INTEGER  │ ID almacén destino (nullable)      │
│ articulo_id  │ INTEGER  │ ID artículo (obligatorio)          │
│ cantidad     │ REAL     │ Cantidad movida                    │
│ coste_unit   │ REAL     │ Coste unitario (nullable)          │
│ motivo       │ TEXT     │ Motivo del movimiento (nullable)   │
│ ot           │ TEXT     │ Orden de trabajo (nullable)        │
│ operario_id  │ INTEGER  │ ID operario (nullable)             │
│ responsable  │ TEXT     │ Usuario que registra               │
│ albaran      │ TEXT     │ Número de albarán (nullable)       │
└──────────────┴──────────┴─────────────────────────────────────┘
```

**Lógica de Campos por Tipo:**

| Tipo | origen_id | destino_id | albaran | ot | operario_id |
|------|-----------|------------|---------|----|----|
| ENTRADA | - | ✅ | ✅ | - | - |
| TRASPASO | ✅ | ✅ | - | - | - |
| IMPUTACION | ✅ | - | - | ✅ | ✅ |
| PERDIDA | ✅ | - | - | - | - |
| DEVOLUCION | ✅ | - | - | - | - |

---

## 🎨 PERSONALIZACIÓN DE ESTILOS

### Cambiar Color de Botones Principales
Editar `estilos.py`:
```python
QPushButton {
    background-color: #3b82f6;  # Cambiar este valor
    color: white;
}
```

### Cambiar Tiempo de Inactividad
Editar `idle_manager.py`:
```python
INACTIVITY_TIMEOUT = 15  # Cambiar minutos aquí
```

### Cambiar Tamaño de Fuente Global
Editar `estilos.py`:
```python
QWidget {
    font-size: 13px;  # Cambiar tamaño aquí
}
```

---

## 🔐 GESTIÓN DE USUARIOS

### Crear Nuevo Usuario (SQL)
```sql
INSERT INTO usuarios (usuario, pass_hash, rol, activo)
VALUES (
    'nuevo_usuario',
    'hash_de_contraseña',  -- Usar hash_pwd() de Python
    'almacen',              -- 'admin' o 'almacen'
    1                       -- 1 = activo, 0 = inactivo
);
```

### Crear Nuevo Usuario (Python)
```python
from db_utils import get_con, hash_pwd

con = get_con()
cur = con.cursor()

cur.execute("""
    INSERT INTO usuarios (usuario, pass_hash, rol, activo)
    VALUES (?, ?, ?, ?)
""", (
    'nuevo_usuario',
    hash_pwd('contraseña'),
    'almacen',
    1
))

con.commit()
con.close()
```

### Desactivar Usuario
```sql
UPDATE usuarios SET activo = 0 WHERE usuario = 'usuario_a_desactivar';
```

### Cambiar Contraseña
```python
from db_utils import get_con, hash_pwd

con = get_con()
cur = con.cursor()

cur.execute("""
    UPDATE usuarios 
    SET pass_hash = ? 
    WHERE usuario = ?
""", (
    hash_pwd('nueva_contraseña'),
    'nombre_usuario'
))

con.commit()
con.close()
```

---

## 📦 GESTIÓN DE DEPENDENCIAS

### Ver Dependencias Instaladas
```bash
pip list
```

### Actualizar Todas las Dependencias
```bash
pip install --upgrade -r requirements.txt
```

### Reinstalar Dependencias desde Cero
```bash
pip uninstall -y -r requirements.txt
pip install -r requirements.txt
```

---

## 🎯 ATAJOS DE TECLADO

| Acción | Tecla |
|--------|-------|
| Confirmar/Login | Enter |
| Cancelar | Esc |
| Cerrar ventana | Alt+F4 |
| Buscar en tabla | Ctrl+F (si disponible) |
| Siguiente campo | Tab |
| Campo anterior | Shift+Tab |

---

## 📝 PLANTILLA PARA NUEVA VENTANA

```python
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QLineEdit
)
from db_utils import get_con
from estilos import ESTILO_VENTANA

class MiNuevaVentana(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎯 Mi Nueva Ventana")
        self.setFixedSize(800, 600)
        self.setStyleSheet(ESTILO_VENTANA)
        self.setupUI()
    
    def setupUI(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("Mi Nueva Funcionalidad")
        layout.addWidget(titulo)
        
        # Campos
        self.txt_dato = QLineEdit()
        self.txt_dato.setPlaceholderText("Introduce dato...")
        layout.addWidget(self.txt_dato)
        
        # Botones
        btn_guardar = QPushButton("💾 Guardar")
        btn_guardar.clicked.connect(self.guardar)
        layout.addWidget(btn_guardar)
    
    def guardar(self):
        """Guardar datos"""
        dato = self.txt_dato.text().strip()
        
        if not dato:
            QMessageBox.warning(self, "⚠️ Atención", "El campo es obligatorio")
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("INSERT INTO tabla (campo) VALUES (?)", (dato,))
            con.commit()
            con.close()
            
            QMessageBox.information(self, "✅ Éxito", "Guardado correctamente")
            self.close()
        
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al guardar: {e}")
```

---

## 🌐 RECURSOS ÚTILES

### Documentación Oficial
- **Python:** https://docs.python.org/3/
- **PySide6:** https://doc.qt.io/qtforpython/
- **SQLite:** https://www.sqlite.org/docs.html
- **pandas:** https://pandas.pydata.org/docs/

### Tutoriales Recomendados
- PySide6 GUI: https://www.pythonguis.com/
- SQLite con Python: https://docs.python.org/3/library/sqlite3.html

---

## ⚡ CHECKLIST DE INICIO RÁPIDO

```
□ 1. Instalar Python 3.12+
□ 2. Descargar/clonar proyecto
□ 3. Instalar dependencias: pip install -r requirements.txt
□ 4. Inicializar BD: python init_db.py
□ 5. Ejecutar app: python app.py
□ 6. Login: admin / admin
□ 7. Cambiar contraseña admin
□ 8. Crear usuarios adicionales
□ 9. Configurar maestros (proveedores, familias, etc.)
□ 10. Crear almacenes en BD
□ 11. Dar de alta artículos
□ 12. ¡Listo para usar!
```

---

## 📞 INFORMACIÓN DE CONTACTO

```
Sistema:    Climatot Almacén v1.0
Tecnología: Python + PySide6 + SQLite
Fecha:      Octubre 2025

Documentos:
• DOCUMENTACION_CLIMATOT_ALMACEN.md (completa)
• DIAGRAMA_ARQUITECTURA.md (visual)
• GUIA_RAPIDA.md (este documento)

Archivos Clave:
• app.py (aplicación principal)
• db_utils.py (utilidades BD)
• db/almacen.db (base de datos)
• logs/log.txt (registro de errores)
```

---

**Fin de la Guía Rápida de Referencia**

✅ Esta guía está diseñada para consultas rápidas y resolución de problemas comunes.
Para información detallada, consultar la documentación completa.
