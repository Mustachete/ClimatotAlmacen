# ventana_articulos.py - Gestión de Artículos
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QHeaderView, QComboBox, QCheckBox, QTextEdit,
    QDoubleSpinBox, QScrollArea, QGroupBox
)
from PySide6.QtCore import Qt
from pathlib import Path
import sqlite3
from estilos import ESTILO_DIALOGO, ESTILO_VENTANA
from db_utils import get_con

# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR ARTÍCULO
# ========================================
class DialogoArticulo(QDialog):
    def __init__(self, parent=None, articulo_id=None):
        super().__init__(parent)
        self.articulo_id = articulo_id
        self.setWindowTitle("✏️ Editar Artículo" if articulo_id else "➕ Nuevo Artículo")
        self.setFixedSize(700, 700)
        self.setStyleSheet(ESTILO_DIALOGO)
        
        # Scroll area para todo el contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # ========== GRUPO 1: IDENTIFICACIÓN ==========
        grupo_id = QGroupBox("📋 Identificación del Artículo")
        form_id = QFormLayout()
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre descriptivo del artículo")
        
        self.txt_ean = QLineEdit()
        self.txt_ean.setPlaceholderText("Código de barras EAN (opcional)")
        
        self.txt_ref = QLineEdit()
        self.txt_ref.setPlaceholderText("Referencia del fabricante/proveedor")
        
        self.txt_palabras = QTextEdit()
        self.txt_palabras.setPlaceholderText("Palabras clave para búsquedas (ej: montante, barra omega, pladur)")
        self.txt_palabras.setMaximumHeight(60)
        
        form_id.addRow("📦 Nombre *:", self.txt_nombre)
        form_id.addRow("🔢 EAN:", self.txt_ean)
        form_id.addRow("🏷️ Referencia:", self.txt_ref)
        form_id.addRow("🔍 Palabras clave:", self.txt_palabras)
        
        grupo_id.setLayout(form_id)
        layout.addWidget(grupo_id)
        
        # ========== GRUPO 2: CLASIFICACIÓN ==========
        grupo_clasif = QGroupBox("📂 Clasificación y Ubicación")
        form_clasif = QFormLayout()
        
        self.cmb_familia = QComboBox()
        self.cargar_familias()
        
        self.cmb_ubicacion = QComboBox()
        self.cargar_ubicaciones()
        
        self.cmb_proveedor = QComboBox()
        self.cargar_proveedores()
        
        self.txt_marca = QLineEdit()
        self.txt_marca.setPlaceholderText("Marca del producto")
        
        form_clasif.addRow("📂 Familia:", self.cmb_familia)
        form_clasif.addRow("📍 Ubicación:", self.cmb_ubicacion)
        form_clasif.addRow("🏭 Proveedor principal:", self.cmb_proveedor)
        form_clasif.addRow("🏢 Marca:", self.txt_marca)
        
        grupo_clasif.setLayout(form_clasif)
        layout.addWidget(grupo_clasif)
        
        # ========== GRUPO 3: UNIDADES Y STOCK ==========
        grupo_stock = QGroupBox("📊 Unidades y Stock")
        form_stock = QFormLayout()
        
        self.cmb_unidad = QComboBox()
        self.cmb_unidad.addItems(["unidad", "metro", "kilogramo", "litro", "metro cuadrado", "caja", "pack"])
        self.cmb_unidad.setEditable(True)
        
        self.spin_min = QDoubleSpinBox()
        self.spin_min.setRange(0, 999999)
        self.spin_min.setDecimals(2)
        self.spin_min.setSuffix(" unidades")
        
        form_stock.addRow("📏 Unidad de medida:", self.cmb_unidad)
        form_stock.addRow("⚠️ Stock mínimo (alerta):", self.spin_min)
        
        grupo_stock.setLayout(form_stock)
        layout.addWidget(grupo_stock)
        
        # ========== GRUPO 4: PRECIOS ==========
        grupo_precios = QGroupBox("💰 Precios")
        form_precios = QFormLayout()
        
        self.spin_coste = QDoubleSpinBox()
        self.spin_coste.setRange(0, 999999)
        self.spin_coste.setDecimals(2)
        self.spin_coste.setPrefix("€ ")
        
        self.spin_pvp = QDoubleSpinBox()
        self.spin_pvp.setRange(0, 999999)
        self.spin_pvp.setDecimals(2)
        self.spin_pvp.setPrefix("€ ")
        
        self.spin_iva = QDoubleSpinBox()
        self.spin_iva.setRange(0, 100)
        self.spin_iva.setDecimals(0)
        self.spin_iva.setValue(21)
        self.spin_iva.setSuffix(" %")
        
        form_precios.addRow("💵 Coste (compra):", self.spin_coste)
        form_precios.addRow("💶 PVP sin IVA:", self.spin_pvp)
        form_precios.addRow("📈 IVA:", self.spin_iva)
        
        grupo_precios.setLayout(form_precios)
        layout.addWidget(grupo_precios)
        
        # ========== ESTADO ==========
        self.chk_activo = QCheckBox("✅ Artículo activo (visible en el sistema)")
        self.chk_activo.setChecked(True)
        self.chk_activo.setStyleSheet("font-weight: bold; margin: 10px;")
        layout.addWidget(self.chk_activo)
        
        # Nota
        nota = QLabel("* El nombre es obligatorio. Los demás campos son opcionales.")
        nota.setStyleSheet("color: gray; font-size: 11px; margin: 5px;")
        layout.addWidget(nota)
        
        scroll.setWidget(content_widget)
        
        # Layout principal del diálogo
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        
        # Botones
        btn_layout = QHBoxLayout()
        
        self.btn_guardar = QPushButton("💾 Guardar Artículo")
        self.btn_guardar.clicked.connect(self.guardar)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(self.btn_cancelar)
        main_layout.addLayout(btn_layout)
        
        # Si estamos editando, cargar datos
        if self.articulo_id:
            self.cargar_datos()
        
        # Focus en el campo de nombre
        self.txt_nombre.setFocus()
    
    def cargar_familias(self):
        """Carga las familias en el combo"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("SELECT id, nombre FROM familias ORDER BY nombre")
            rows = cur.fetchall()
            con.close()
            
            self.cmb_familia.addItem("(Sin familia)", None)
            for row in rows:
                self.cmb_familia.addItem(row[1], row[0])
        except Exception:
            pass
    
    def cargar_ubicaciones(self):
        """Carga las ubicaciones en el combo"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("SELECT id, nombre FROM ubicaciones ORDER BY nombre")
            rows = cur.fetchall()
            con.close()
            
            self.cmb_ubicacion.addItem("(Sin ubicación)", None)
            for row in rows:
                self.cmb_ubicacion.addItem(row[1], row[0])
        except Exception:
            pass
    
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
    
    def cargar_datos(self):
        """Carga los datos del artículo a editar"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("""
                SELECT ean, ref_proveedor, nombre, palabras_clave, u_medida, min_alerta,
                       ubicacion_id, proveedor_id, familia_id, marca, coste, pvp_sin, iva, activo
                FROM articulos WHERE id=?
            """, (self.articulo_id,))
            row = cur.fetchone()
            con.close()
            
            if row:
                self.txt_ean.setText(row[0] or "")
                self.txt_ref.setText(row[1] or "")
                self.txt_nombre.setText(row[2] or "")
                self.txt_palabras.setPlainText(row[3] or "")
                
                # Unidad de medida
                idx = self.cmb_unidad.findText(row[4] or "unidad")
                if idx >= 0:
                    self.cmb_unidad.setCurrentIndex(idx)
                
                self.spin_min.setValue(row[5] or 0)
                
                # Ubicación
                if row[6]:
                    idx = self.cmb_ubicacion.findData(row[6])
                    if idx >= 0:
                        self.cmb_ubicacion.setCurrentIndex(idx)
                
                # Proveedor
                if row[7]:
                    idx = self.cmb_proveedor.findData(row[7])
                    if idx >= 0:
                        self.cmb_proveedor.setCurrentIndex(idx)
                
                # Familia
                if row[8]:
                    idx = self.cmb_familia.findData(row[8])
                    if idx >= 0:
                        self.cmb_familia.setCurrentIndex(idx)
                
                self.txt_marca.setText(row[9] or "")
                self.spin_coste.setValue(row[10] or 0)
                self.spin_pvp.setValue(row[11] or 0)
                self.spin_iva.setValue(row[12] or 21)
                self.chk_activo.setChecked(row[13] == 1)
                
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar datos:\n{e}")
    
    def guardar(self):
        """Guarda el artículo (nuevo o editado)"""
        nombre = self.txt_nombre.text().strip()
        
        if not nombre:
            QMessageBox.warning(self, "⚠️ Aviso", "El nombre del artículo es obligatorio.")
            self.txt_nombre.setFocus()
            return
        
        # Recoger todos los datos
        ean = self.txt_ean.text().strip() or None
        ref = self.txt_ref.text().strip() or None
        palabras = self.txt_palabras.toPlainText().strip() or None
        u_medida = self.cmb_unidad.currentText()
        min_alerta = self.spin_min.value()
        ubicacion_id = self.cmb_ubicacion.currentData()
        proveedor_id = self.cmb_proveedor.currentData()
        familia_id = self.cmb_familia.currentData()
        marca = self.txt_marca.text().strip() or None
        coste = self.spin_coste.value()
        pvp = self.spin_pvp.value()
        iva = self.spin_iva.value()
        activo = 1 if self.chk_activo.isChecked() else 0
        
        try:
            con = get_con()
            cur = con.cursor()
            
            if self.articulo_id:
                # Editar existente
                cur.execute("""
                    UPDATE articulos 
                    SET ean=?, ref_proveedor=?, nombre=?, palabras_clave=?, u_medida=?,
                        min_alerta=?, ubicacion_id=?, proveedor_id=?, familia_id=?,
                        marca=?, coste=?, pvp_sin=?, iva=?, activo=?
                    WHERE id=?
                """, (ean, ref, nombre, palabras, u_medida, min_alerta, ubicacion_id,
                      proveedor_id, familia_id, marca, coste, pvp, iva, activo, self.articulo_id))
                mensaje = f"✅ Artículo '{nombre}' actualizado correctamente."
            else:
                # Crear nuevo
                cur.execute("""
                    INSERT INTO articulos(ean, ref_proveedor, nombre, palabras_clave, u_medida,
                                         min_alerta, ubicacion_id, proveedor_id, familia_id,
                                         marca, coste, pvp_sin, iva, activo)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (ean, ref, nombre, palabras, u_medida, min_alerta, ubicacion_id,
                      proveedor_id, familia_id, marca, coste, pvp, iva, activo))
                mensaje = f"✅ Artículo '{nombre}' creado correctamente."
            
            con.commit()
            con.close()
            
            QMessageBox.information(self, "✅ Éxito", mensaje)
            self.accept()
            
        except sqlite3.IntegrityError as e:
            if "ean" in str(e).lower():
                QMessageBox.warning(self, "⚠️ Aviso", f"Ya existe un artículo con el EAN '{ean}'.")
            elif "ref_proveedor" in str(e).lower():
                QMessageBox.warning(self, "⚠️ Aviso", f"Ya existe un artículo con la referencia '{ref}'.")
            else:
                QMessageBox.warning(self, "⚠️ Aviso", "Ya existe un artículo con esos datos únicos.")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al guardar:\n{e}")

# ========================================
# VENTANA PRINCIPAL DE ARTÍCULOS
# ========================================
class VentanaArticulos(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 Gestión de Artículos")
        self.resize(1100, 650)
        self.setMinimumSize(900, 500)
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("📦 Gestión de Artículos del Almacén")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        # Barra de búsqueda y filtros
        top_layout = QHBoxLayout()
        
        lbl_buscar = QLabel("🔍 Buscar:")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre, EAN, referencia o palabras clave...")
        self.txt_buscar.textChanged.connect(self.buscar)
        
        lbl_familia = QLabel("Familia:")
        self.cmb_familia_filtro = QComboBox()
        self.cmb_familia_filtro.addItem("Todas", None)
        self.cargar_familias_filtro()
        self.cmb_familia_filtro.currentTextChanged.connect(self.buscar)
        
        lbl_estado = QLabel("Estado:")
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(["Todos", "Solo Activos", "Solo Inactivos"])
        self.cmb_estado.currentTextChanged.connect(self.buscar)
        
        top_layout.addWidget(lbl_buscar)
        top_layout.addWidget(self.txt_buscar, 3)
        top_layout.addWidget(lbl_familia)
        top_layout.addWidget(self.cmb_familia_filtro, 1)
        top_layout.addWidget(lbl_estado)
        top_layout.addWidget(self.cmb_estado, 1)
        
        layout.addLayout(top_layout)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        
        self.btn_nuevo = QPushButton("➕ Nuevo Artículo")
        self.btn_nuevo.clicked.connect(self.nuevo_articulo)
        
        self.btn_editar = QPushButton("✏️ Editar")
        self.btn_editar.clicked.connect(self.editar_articulo)
        self.btn_editar.setEnabled(False)
        
        self.btn_eliminar = QPushButton("🗑️ Eliminar")
        self.btn_eliminar.clicked.connect(self.eliminar_articulo)
        self.btn_eliminar.setEnabled(False)
        
        btn_layout.addWidget(self.btn_nuevo)
        btn_layout.addWidget(self.btn_editar)
        btn_layout.addWidget(self.btn_eliminar)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Tabla de artículos
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "EAN", "Ref", "Nombre", "Familia", "U.Medida", "Stock Mín", "Coste", "Estado"
        ])
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self.seleccion_cambiada)
        self.tabla.doubleClicked.connect(self.editar_articulo)
        
        # Ocultar columna ID
        self.tabla.setColumnHidden(0, True)
        
        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Nombre
        
        layout.addWidget(self.tabla)
        
        # Botón volver
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)
        
        # Cargar datos iniciales
        self.cargar_articulos()
    
    def cargar_familias_filtro(self):
        """Carga las familias en el combo de filtro"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("SELECT id, nombre FROM familias ORDER BY nombre")
            rows = cur.fetchall()
            con.close()
            
            for row in rows:
                self.cmb_familia_filtro.addItem(row[1], row[0])
        except Exception:
            pass
    
    def cargar_articulos(self):
        """Carga los artículos en la tabla"""
        filtro_texto = self.txt_buscar.text().strip()
        familia_id = self.cmb_familia_filtro.currentData()
        estado = self.cmb_estado.currentText()
        
        try:
            con = get_con()
            cur = con.cursor()
            
            query = """
                SELECT a.id, a.ean, a.ref_proveedor, a.nombre, f.nombre, 
                       a.u_medida, a.min_alerta, a.coste, a.activo
                FROM articulos a
                LEFT JOIN familias f ON a.familia_id = f.id
                WHERE 1=1
            """
            params = []
            
            if filtro_texto:
                query += """ AND (a.nombre LIKE ? OR a.ean LIKE ? OR 
                                 a.ref_proveedor LIKE ? OR a.palabras_clave LIKE ?)"""
                params.extend([f"%{filtro_texto}%"] * 4)
            
            if familia_id:
                query += " AND a.familia_id = ?"
                params.append(familia_id)
            
            if estado == "Solo Activos":
                query += " AND a.activo = 1"
            elif estado == "Solo Inactivos":
                query += " AND a.activo = 0"
            
            query += " ORDER BY a.nombre"
            
            cur.execute(query, params)
            rows = cur.fetchall()
            con.close()
            
            self.tabla.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                # ID
                self.tabla.setItem(i, 0, QTableWidgetItem(str(row[0])))
                # EAN
                self.tabla.setItem(i, 1, QTableWidgetItem(row[1] or ""))
                # Ref
                self.tabla.setItem(i, 2, QTableWidgetItem(row[2] or ""))
                # Nombre
                self.tabla.setItem(i, 3, QTableWidgetItem(row[3]))
                # Familia
                self.tabla.setItem(i, 4, QTableWidgetItem(row[4] or "-"))
                # U.Medida
                self.tabla.setItem(i, 5, QTableWidgetItem(row[5] or "unidad"))
                # Stock Mín
                self.tabla.setItem(i, 6, QTableWidgetItem(str(row[6] or 0)))
                # Coste
                self.tabla.setItem(i, 7, QTableWidgetItem(f"€ {row[7]:.2f}" if row[7] else "€ 0.00"))
                # Estado
                estado_txt = "✅ Activo" if row[8] == 1 else "❌ Inactivo"
                item_estado = QTableWidgetItem(estado_txt)
                if row[8] == 0:
                    item_estado.setForeground(Qt.gray)
                self.tabla.setItem(i, 8, item_estado)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar artículos:\n{e}")
    
    def buscar(self):
        """Filtra la tabla"""
        self.cargar_articulos()
    
    def seleccion_cambiada(self):
        """Se activan/desactivan botones según la selección"""
        hay_seleccion = len(self.tabla.selectedItems()) > 0
        self.btn_editar.setEnabled(hay_seleccion)
        self.btn_eliminar.setEnabled(hay_seleccion)
    
    def nuevo_articulo(self):
        """Abre el diálogo para crear un nuevo artículo"""
        dialogo = DialogoArticulo(self)
        if dialogo.exec():
            self.cargar_articulos()
    
    def editar_articulo(self):
        """Abre el diálogo para editar el artículo seleccionado"""
        seleccion = self.tabla.currentRow()
        if seleccion < 0:
            return
        
        articulo_id = int(self.tabla.item(seleccion, 0).text())
        dialogo = DialogoArticulo(self, articulo_id)
        if dialogo.exec():
            self.cargar_articulos()
    
    def eliminar_articulo(self):
        """Elimina el artículo seleccionado"""
        seleccion = self.tabla.currentRow()
        if seleccion < 0:
            return
        
        articulo_id = int(self.tabla.item(seleccion, 0).text())
        nombre = self.tabla.item(seleccion, 3).text()
        
        respuesta = QMessageBox.question(
            self,
            "⚠️ Confirmar eliminación",
            f"¿Está seguro de eliminar el artículo '{nombre}'?\n\n"
            "Esta acción no se puede deshacer.\n"
            "Si el artículo tiene movimientos, no podrá eliminarse.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if respuesta != QMessageBox.Yes:
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("DELETE FROM articulos WHERE id=?", (articulo_id,))
            con.commit()
            con.close()
            
            QMessageBox.information(self, "✅ Éxito", f"Artículo '{nombre}' eliminado correctamente.")
            self.cargar_articulos()
            
        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self, 
                "⚠️ No se puede eliminar",
                f"El artículo '{nombre}' tiene movimientos asociados.\n\n"
                "En lugar de eliminarlo, puede marcarlo como 'Inactivo' editándolo."
            )
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al eliminar:\n{e}")