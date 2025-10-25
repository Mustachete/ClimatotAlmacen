# ventana_recepcion.py - Recepción de Albaranes
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QHeaderView, QComboBox, QDateEdit, QSpinBox,
    QDoubleSpinBox, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt, QDate
from pathlib import Path
import sqlite3
import datetime
from estilos import ESTILO_DIALOGO, ESTILO_VENTANA
from widgets_personalizados import SpinBoxClimatot
from db_utils import get_con

def today_str():
    """Devuelve fecha actual en formato YYYY-MM-DD"""
    return datetime.date.today().strftime("%Y-%m-%d")

# ========================================
# DIÁLOGO PARA REGISTRAR ALBARÁN
# ========================================
class DialogoRecepcion(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 Recepción de Albarán")
        self.setFixedSize(900, 700)
        self.setStyleSheet(ESTILO_DIALOGO)
        
        # Lista temporal de artículos a recibir
        self.articulos_temp = []
        
        layout = QVBoxLayout(self)
        
        # ========== GRUPO 1: DATOS DEL ALBARÁN ==========
        grupo_albaran = QGroupBox("📄 Datos del Albarán")
        form_albaran = QFormLayout()
        
        self.txt_num_albaran = QLineEdit()
        self.txt_num_albaran.setPlaceholderText("Número de albarán del proveedor")
        
        self.date_fecha = QDateEdit()
        self.date_fecha.setCalendarPopup(True)
        self.date_fecha.setDate(QDate.currentDate())
        self.date_fecha.setDisplayFormat("dd/MM/yyyy")
        self.date_fecha.setMaximumDate(QDate.currentDate())  # No permitir fechas futuras
        
        self.cmb_proveedor = QComboBox()
        self.cargar_proveedores()
        
        form_albaran.addRow("📋 Nº Albarán *:", self.txt_num_albaran)
        form_albaran.addRow("📅 Fecha:", self.date_fecha)
        form_albaran.addRow("🏭 Proveedor:", self.cmb_proveedor)
        
        grupo_albaran.setLayout(form_albaran)
        layout.addWidget(grupo_albaran)
        
        # ========== GRUPO 2: AÑADIR ARTÍCULOS ==========
        grupo_articulos = QGroupBox("📦 Añadir Artículos al Albarán")
        layout_articulos = QVBoxLayout()
        
        # Selector de artículo
        h1 = QHBoxLayout()
        lbl_art = QLabel("Artículo:")
        self.cmb_articulo = QComboBox()
        self.cmb_articulo.setMinimumWidth(300)
        self.cargar_articulos()
        
        lbl_cant = QLabel("Cantidad:")
        self.spin_cantidad = SpinBoxClimatot()
        self.spin_cantidad.setRange(0.01, 999999)
        self.spin_cantidad.setDecimals(2)
        self.spin_cantidad.setValue(1)
        
        lbl_coste = QLabel("Coste unit.:")
        self.spin_coste = SpinBoxClimatot()
        self.spin_coste.setRange(0, 999999)
        self.spin_coste.setDecimals(2)
        self.spin_coste.setPrefix("€ ")
        
        self.btn_agregar = QPushButton("➕ Agregar")
        self.btn_agregar.clicked.connect(self.agregar_articulo)
        
        h1.addWidget(lbl_art)
        h1.addWidget(self.cmb_articulo, 2)
        h1.addWidget(lbl_cant)
        h1.addWidget(self.spin_cantidad)
        h1.addWidget(lbl_coste)
        h1.addWidget(self.spin_coste)
        h1.addWidget(self.btn_agregar)
        
        layout_articulos.addLayout(h1)
        
        # Tabla de artículos agregados
        self.tabla_articulos = QTableWidget()
        self.tabla_articulos.setColumnCount(5)
        self.tabla_articulos.setHorizontalHeaderLabels(["ID", "Artículo", "Cantidad", "Coste Unit.", "Acciones"])
        self.tabla_articulos.setColumnHidden(0, True)
        self.tabla_articulos.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_articulos.setMaximumHeight(250)
        
        layout_articulos.addWidget(self.tabla_articulos)
        
        grupo_articulos.setLayout(layout_articulos)
        layout.addWidget(grupo_articulos)
        
        # Nota
        nota = QLabel("* El número de albarán es obligatorio. Si ya existe, se preguntará si desea continuar.")
        nota.setStyleSheet("color: gray; font-size: 11px; margin: 5px;")
        layout.addWidget(nota)
        
        # Botones finales
        layout.addStretch()
        btn_layout = QHBoxLayout()
        
        self.btn_guardar = QPushButton("💾 Guardar Recepción")
        self.btn_guardar.clicked.connect(self.guardar)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)
        
        # Focus inicial
        self.txt_num_albaran.setFocus()
    
    def cargar_proveedores(self):
        """Carga los proveedores en el combo"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("SELECT id, nombre FROM proveedores ORDER BY nombre")
            rows = cur.fetchall()
            con.close()
            
            self.cmb_proveedor.addItem("(Sin proveedor)", None)
            for row in rows:
                self.cmb_proveedor.addItem(row[1], row[0])
        except Exception:
            pass
    
    def cargar_articulos(self):
        """Carga los artículos activos en el combo"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("""
                SELECT id, nombre, u_medida, coste 
                FROM articulos 
                WHERE activo=1 
                ORDER BY nombre
            """)
            rows = cur.fetchall()
            con.close()
            
            for row in rows:
                texto = f"{row[1]} ({row[2]})"
                self.cmb_articulo.addItem(texto, row[0])
                # Pre-cargar el coste si existe
                if row[3]:
                    self.cmb_articulo.setItemData(self.cmb_articulo.count() - 1, row[3], Qt.UserRole + 1)
        except Exception:
            pass
    
    def agregar_articulo(self):
        """Agrega un artículo a la lista temporal"""
        if self.cmb_articulo.currentIndex() < 0:
            QMessageBox.warning(self, "⚠️ Aviso", "Seleccione un artículo.")
            return
        
        articulo_id = self.cmb_articulo.currentData()
        articulo_nombre = self.cmb_articulo.currentText()
        cantidad = self.spin_cantidad.value()
        coste = self.spin_coste.value()
        
        # Verificar si ya está agregado
        for art in self.articulos_temp:
            if art['id'] == articulo_id:
                QMessageBox.warning(self, "⚠️ Aviso", "Este artículo ya está en la lista.\nEdite la cantidad si es necesario.")
                return
        
        # Agregar a lista temporal
        self.articulos_temp.append({
            'id': articulo_id,
            'nombre': articulo_nombre,
            'cantidad': cantidad,
            'coste': coste
        })
        
        self.actualizar_tabla_articulos()
        
        # Resetear campos
        self.spin_cantidad.setValue(1)
        self.spin_coste.setValue(0)
    
    def actualizar_tabla_articulos(self):
        """Actualiza la tabla con los artículos temporales"""
        self.tabla_articulos.setRowCount(len(self.articulos_temp))
        
        for i, art in enumerate(self.articulos_temp):
            # ID
            self.tabla_articulos.setItem(i, 0, QTableWidgetItem(str(art['id'])))
            # Artículo
            self.tabla_articulos.setItem(i, 1, QTableWidgetItem(art['nombre']))
            # Cantidad
            self.tabla_articulos.setItem(i, 2, QTableWidgetItem(f"{art['cantidad']:.2f}"))
            # Coste
            self.tabla_articulos.setItem(i, 3, QTableWidgetItem(f"€ {art['coste']:.2f}"))
            
            # Botón quitar
            btn_quitar = QPushButton("🗑️ Quitar")
            btn_quitar.clicked.connect(lambda checked, idx=i: self.quitar_articulo(idx))
            self.tabla_articulos.setCellWidget(i, 4, btn_quitar)
    
    def quitar_articulo(self, index):
        """Quita un artículo de la lista temporal"""
        if 0 <= index < len(self.articulos_temp):
            del self.articulos_temp[index]
            self.actualizar_tabla_articulos()
    
    def guardar(self):
        """Guarda la recepción del albarán"""
        num_albaran = self.txt_num_albaran.text().strip()
        
        if not num_albaran:
            QMessageBox.warning(self, "⚠️ Aviso", "El número de albarán es obligatorio.")
            self.txt_num_albaran.setFocus()
            return
        
        if not self.articulos_temp:
            QMessageBox.warning(self, "⚠️ Aviso", "Debe agregar al menos un artículo al albarán.")
            return
        
        fecha = self.date_fecha.date().toString("yyyy-MM-dd")
        proveedor_id = self.cmb_proveedor.currentData()
        
        try:
            con = get_con()
            cur = con.cursor()
            
            # Verificar si el albarán ya existe
            cur.execute("SELECT albaran FROM albaranes WHERE albaran=?", (num_albaran,))
            if cur.fetchone():
                respuesta = QMessageBox.question(
                    self,
                    "⚠️ Albarán duplicado",
                    f"El albarán '{num_albaran}' ya está registrado.\n\n"
                    "¿Desea continuar de todos modos?\n",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if respuesta != QMessageBox.Yes:
                    con.close()
                    return
            else:
                # Registrar el albarán
                cur.execute(
                    "INSERT INTO albaranes(albaran, proveedor_id, fecha) VALUES(?,?,?)",
                    (num_albaran, proveedor_id, fecha)
                )
            
            # Obtener ID del almacén principal
            cur.execute("SELECT id FROM almacenes WHERE nombre='Almacén' LIMIT 1")
            almacen_id = cur.fetchone()[0]
            
            # Registrar movimientos de entrada para cada artículo
            for art in self.articulos_temp:
                cur.execute("""
                    INSERT INTO movimientos(fecha, tipo, origen_id, destino_id, articulo_id, 
                                           cantidad, coste_unit, albaran)
                    VALUES(?, 'ENTRADA', NULL, ?, ?, ?, ?, ?)
                """, (fecha, almacen_id, art['id'], art['cantidad'], art['coste'], num_albaran))
            
            con.commit()
            con.close()
            
            QMessageBox.information(
                self, 
                "✅ Éxito", 
                f"Albarán '{num_albaran}' registrado correctamente.\n\n"
                f"Se han añadido {len(self.articulos_temp)} artículo(s) al almacén."
            )
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al guardar:\n{e}")

# ========================================
# VENTANA PRINCIPAL DE RECEPCIÓN
# ========================================
class VentanaRecepcion(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 Recepción de Albaranes")
        self.resize(950, 600)
        self.setMinimumSize(800, 500)
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("📦 Recepción de Albaranes de Proveedores")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        desc = QLabel("Registra la entrada de material al almacén desde proveedores")
        desc.setStyleSheet("color: gray; font-size: 12px; margin-bottom: 10px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # Botón para nueva recepción
        btn_layout = QHBoxLayout()
        
        self.btn_nueva = QPushButton("➕ Nueva Recepción")
        self.btn_nueva.setMinimumHeight(45)
        self.btn_nueva.clicked.connect(self.nueva_recepcion)
        
        btn_layout.addWidget(self.btn_nueva)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Filtros
        filtro_layout = QHBoxLayout()
        
        lbl_buscar = QLabel("🔍 Buscar:")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por número de albarán o proveedor...")
        self.txt_buscar.textChanged.connect(self.buscar)
        
        filtro_layout.addWidget(lbl_buscar)
        filtro_layout.addWidget(self.txt_buscar)
        
        layout.addLayout(filtro_layout)
        
        # Tabla de albaranes
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Nº Albarán", "Proveedor", "Fecha", "Artículos"])
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.tabla)
        
        # Botón volver
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)
        
        # Cargar datos iniciales
        self.cargar_albaranes()
    
    def cargar_albaranes(self, filtro=""):
        """Carga los albaranes registrados"""
        try:
            con = get_con()
            cur = con.cursor()
            
            if filtro:
                cur.execute("""
                    SELECT a.albaran, p.nombre, a.fecha,
                           (SELECT COUNT(DISTINCT articulo_id) FROM movimientos WHERE albaran=a.albaran) as num_arts
                    FROM albaranes a
                    LEFT JOIN proveedores p ON a.proveedor_id = p.id
                    WHERE a.albaran LIKE ? OR p.nombre LIKE ?
                    ORDER BY a.fecha DESC, a.albaran
                """, (f"%{filtro}%", f"%{filtro}%"))
            else:
                cur.execute("""
                    SELECT a.albaran, p.nombre, a.fecha,
                           (SELECT COUNT(DISTINCT articulo_id) FROM movimientos WHERE albaran=a.albaran) as num_arts
                    FROM albaranes a
                    LEFT JOIN proveedores p ON a.proveedor_id = p.id
                    ORDER BY a.fecha DESC, a.albaran
                """)
            
            rows = cur.fetchall()
            con.close()
            
            self.tabla.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                self.tabla.setItem(i, 0, QTableWidgetItem(row[0]))
                self.tabla.setItem(i, 1, QTableWidgetItem(row[1] or "(Sin proveedor)"))
                # Convertir fecha a formato dd/MM/yyyy
                try:
                    fecha_obj = datetime.datetime.strptime(row[2], "%Y-%m-%d")
                    fecha_mostrar = fecha_obj.strftime("%d/%m/%Y")
                except:
                    fecha_mostrar = row[2]
                self.tabla.setItem(i, 2, QTableWidgetItem(fecha_mostrar))
                self.tabla.setItem(i, 3, QTableWidgetItem(f"{row[3]} artículo(s)"))
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar albaranes:\n{e}")
    
    def buscar(self):
        """Filtra la tabla"""
        filtro = self.txt_buscar.text().strip()
        self.cargar_albaranes(filtro)
    
    def nueva_recepcion(self):
        """Abre el diálogo para nueva recepción"""
        dialogo = DialogoRecepcion(self)
        if dialogo.exec():
            self.cargar_albaranes()