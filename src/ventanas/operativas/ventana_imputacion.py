# ventana_imputacion.py - Imputar Material a OT
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QComboBox,
    QDateEdit, QGroupBox, QHeaderView
)
from PySide6.QtCore import Qt, QDate
from pathlib import Path
import sqlite3
import datetime
from src.ui.estilos import ESTILO_VENTANA
from src.ui.widgets_personalizados import SpinBoxClimatot
from src.core.db_utils import get_con

# ========================================
# VENTANA DE IMPUTACIÓN
# ========================================
class VentanaImputacion(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝 Imputar Material a Orden de Trabajo")
        self.setFixedSize(1100, 750)
        self.setStyleSheet(ESTILO_VENTANA)
        
        # Lista temporal de artículos
        self.articulos_temp = []
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # ========== TÍTULO ==========
        titulo = QLabel("📝 Imputar Material a Orden de Trabajo")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 5px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        desc = QLabel("Registra el material usado por los operarios en trabajos de instalación")
        desc.setStyleSheet("color: #64748b; font-size: 12px; margin-bottom: 10px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # ========== GRUPO: DATOS DE LA IMPUTACIÓN ==========
        grupo_datos = QGroupBox("📋 Datos de la Imputación")
        datos_layout = QHBoxLayout()
        
        # Fecha
        lbl_fecha = QLabel("📅 Fecha consumo:")
        self.date_fecha = QDateEdit()
        self.date_fecha.setCalendarPopup(True)
        self.date_fecha.setDate(QDate.currentDate())
        self.date_fecha.setDisplayFormat("dd/MM/yyyy")
        self.date_fecha.setMaximumDate(QDate.currentDate())
        
        # Operario
        lbl_operario = QLabel("👷 Operario:")
        self.cmb_operario = QComboBox()
        self.cmb_operario.setMinimumWidth(200)
        self.cargar_operarios()
        self.cmb_operario.currentIndexChanged.connect(self.cambio_operario)
        
        # Furgoneta
        lbl_furgoneta = QLabel("🚚 Furgoneta:")
        self.lbl_furgoneta_asignada = QLabel("(Seleccione operario)")
        self.lbl_furgoneta_asignada.setStyleSheet("color: #64748b; font-style: italic;")
        
        datos_layout.addWidget(lbl_fecha)
        datos_layout.addWidget(self.date_fecha)
        datos_layout.addSpacing(20)
        datos_layout.addWidget(lbl_operario)
        datos_layout.addWidget(self.cmb_operario)
        datos_layout.addSpacing(20)
        datos_layout.addWidget(lbl_furgoneta)
        datos_layout.addWidget(self.lbl_furgoneta_asignada)
        datos_layout.addStretch()
        
        grupo_datos.setLayout(datos_layout)
        layout.addWidget(grupo_datos)
        
        # ========== GRUPO: ORDEN DE TRABAJO ==========
        grupo_ot = QGroupBox("🔧 Orden de Trabajo")
        ot_layout = QHBoxLayout()
        
        lbl_ot = QLabel("📄 Nº OT:")
        self.txt_ot = QLineEdit()
        self.txt_ot.setPlaceholderText("Número de Orden de Trabajo (ej: OT-2025-001)")
        self.txt_ot.setMinimumWidth(300)
        
        ot_layout.addWidget(lbl_ot)
        ot_layout.addWidget(self.txt_ot)
        ot_layout.addStretch()
        
        nota_ot = QLabel("💡 Si no hay OT específica, puedes dejarla en blanco")
        nota_ot.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
        
        ot_vlayout = QVBoxLayout()
        ot_vlayout.addLayout(ot_layout)
        ot_vlayout.addWidget(nota_ot)
        
        grupo_ot.setLayout(ot_vlayout)
        layout.addWidget(grupo_ot)
        
        # ========== GRUPO: SELECCIONAR ARTÍCULOS ==========
        grupo_articulos = QGroupBox("📦 Seleccionar Artículos Consumidos")
        articulos_layout = QVBoxLayout()
        
        # Selector de artículo
        select_layout = QHBoxLayout()
        
        lbl_art = QLabel("Artículo:")
        self.cmb_articulo = QComboBox()
        self.cmb_articulo.setMinimumWidth(400)
        self.cmb_articulo.currentIndexChanged.connect(self.articulo_seleccionado)
        
        lbl_cant = QLabel("Cantidad:")
        self.spin_cantidad = SpinBoxClimatot()
        self.spin_cantidad.setRange(0.01, 999999)
        self.spin_cantidad.setDecimals(2)
        self.spin_cantidad.setValue(1)
        self.spin_cantidad.setMinimumWidth(120)
        
        self.btn_agregar = QPushButton("➕ Agregar")
        self.btn_agregar.setMinimumHeight(40)
        self.btn_agregar.clicked.connect(self.agregar_articulo)
        
        select_layout.addWidget(lbl_art)
        select_layout.addWidget(self.cmb_articulo, 2)
        select_layout.addWidget(lbl_cant)
        select_layout.addWidget(self.spin_cantidad)
        select_layout.addWidget(self.btn_agregar)
        
        articulos_layout.addLayout(select_layout)
        
        grupo_articulos.setLayout(articulos_layout)
        layout.addWidget(grupo_articulos)
        
        # ========== TABLA DE ARTÍCULOS SELECCIONADOS ==========
        lbl_tabla = QLabel("📋 Artículos a imputar:")
        lbl_tabla.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_tabla)
        
        self.tabla_articulos = QTableWidget()
        self.tabla_articulos.setColumnCount(5)
        self.tabla_articulos.setHorizontalHeaderLabels(["ID", "Artículo", "U.Medida", "Cantidad", "Acciones"])
        self.tabla_articulos.setColumnHidden(0, True)
        
        header = self.tabla_articulos.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.tabla_articulos.setMinimumHeight(200)
        layout.addWidget(self.tabla_articulos)
        
        # ========== BOTONES FINALES ==========
        botones_layout = QHBoxLayout()
        
        self.btn_guardar = QPushButton("💾 GUARDAR IMPUTACIÓN")
        self.btn_guardar.setMinimumHeight(50)
        self.btn_guardar.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.btn_guardar.clicked.connect(self.guardar_imputacion)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.setMinimumHeight(50)
        self.btn_cancelar.clicked.connect(self.limpiar_todo)
        
        self.btn_volver = QPushButton("⬅️ Volver")
        self.btn_volver.setMinimumHeight(50)
        self.btn_volver.clicked.connect(self.close)
        
        botones_layout.addWidget(self.btn_guardar, 3)
        botones_layout.addWidget(self.btn_cancelar, 1)
        botones_layout.addWidget(self.btn_volver, 1)
        
        layout.addLayout(botones_layout)
    
    def cargar_operarios(self):
        """Carga los operarios activos"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("""
                SELECT id, nombre, rol_operario 
                FROM operarios 
                WHERE activo=1 
                ORDER BY rol_operario DESC, nombre
            """)
            rows = cur.fetchall()
            con.close()
            
            self.cmb_operario.addItem("(Seleccione operario)", None)
            for row in rows:
                emoji = "👷" if row[2] == "oficial" else "🔨"
                texto = f"{emoji} {row[1]} ({row[2]})"
                self.cmb_operario.addItem(texto, row[0])
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar operarios:\n{e}")
    
    def cambio_operario(self):
        """Al cambiar de operario, busca su furgoneta y carga artículos"""
        operario_id = self.cmb_operario.currentData()
        if not operario_id:
            self.lbl_furgoneta_asignada.setText("(Seleccione operario)")
            self.lbl_furgoneta_asignada.setStyleSheet("color: #64748b; font-style: italic;")
            self.cmb_articulo.clear()
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
            cur.execute("""
                SELECT a.nombre, af.furgoneta_id
                FROM asignaciones_furgoneta af
                JOIN almacenes a ON af.furgoneta_id = a.id
                WHERE af.operario_id=? AND af.fecha=?
            """, (operario_id, fecha_hoy))
            row = cur.fetchone()
            con.close()
            
            if row:
                self.lbl_furgoneta_asignada.setText(f"🚚 Furgoneta {row[0]}")
                self.lbl_furgoneta_asignada.setStyleSheet("color: #1e3a8a; font-weight: bold;")
                self.furgoneta_id = row[1]
                self.cargar_articulos_furgoneta()
            else:
                self.lbl_furgoneta_asignada.setText("⚠️ Sin furgoneta asignada hoy")
                self.lbl_furgoneta_asignada.setStyleSheet("color: #dc2626; font-weight: bold;")
                self.furgoneta_id = None
                self.cmb_articulo.clear()
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error:\n{e}")
    
    def cargar_articulos_furgoneta(self):
        """Carga los artículos disponibles en la furgoneta del operario"""
        if not self.furgoneta_id:
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            # Obtener stock actual en la furgoneta
            cur.execute("""
                SELECT a.id, a.nombre, a.u_medida, COALESCE(SUM(v.delta), 0) as stock
                FROM articulos a
                LEFT JOIN vw_stock v ON a.id = v.articulo_id AND v.almacen_id = ?
                WHERE a.activo = 1
                GROUP BY a.id, a.nombre, a.u_medida
                HAVING stock > 0
                ORDER BY a.nombre
            """, (self.furgoneta_id,))
            rows = cur.fetchall()
            con.close()
            
            self.cmb_articulo.clear()
            self.cmb_articulo.addItem("(Seleccione artículo)", None)
            
            for row in rows:
                texto = f"{row[1]} ({row[2]}) - Stock: {row[3]:.2f}"
                self.cmb_articulo.addItem(texto, {
                    'id': row[0],
                    'nombre': row[1],
                    'u_medida': row[2],
                    'stock': row[3]
                })
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar artículos:\n{e}")
    
    def articulo_seleccionado(self):
        """Cuando se selecciona un artículo, ajustar cantidad máxima"""
        data = self.cmb_articulo.currentData()
        if data and isinstance(data, dict):
            # Ajustar rango según stock disponible
            self.spin_cantidad.setRange(0.01, data['stock'])
            self.spin_cantidad.setValue(min(1.0, data['stock']))
    
    def agregar_articulo(self):
        """Agrega un artículo a la lista"""
        data = self.cmb_articulo.currentData()
        if not data or not isinstance(data, dict):
            QMessageBox.warning(self, "⚠️ Aviso", "Seleccione un artículo.")
            return
        
        cantidad = self.spin_cantidad.value()
        
        # Verificar que no exceda el stock
        if cantidad > data['stock']:
            QMessageBox.warning(self, "⚠️ Aviso", f"No hay suficiente stock.\nDisponible: {data['stock']:.2f}")
            return
        
        # Verificar si ya está agregado
        for art in self.articulos_temp:
            if art['id'] == data['id']:
                QMessageBox.warning(self, "⚠️ Aviso", "Este artículo ya está en la lista.")
                return
        
        # Agregar
        self.articulos_temp.append({
            'id': data['id'],
            'nombre': data['nombre'],
            'u_medida': data['u_medida'],
            'cantidad': cantidad,
            'stock': data['stock']
        })
        
        self.actualizar_tabla()
        self.spin_cantidad.setValue(1)
    
    def actualizar_tabla(self):
        """Actualiza la tabla con los artículos temporales"""
        self.tabla_articulos.setRowCount(len(self.articulos_temp))
        
        for i, art in enumerate(self.articulos_temp):
            self.tabla_articulos.setItem(i, 0, QTableWidgetItem(str(art['id'])))
            self.tabla_articulos.setItem(i, 1, QTableWidgetItem(art['nombre']))
            self.tabla_articulos.setItem(i, 2, QTableWidgetItem(art['u_medida']))
            self.tabla_articulos.setItem(i, 3, QTableWidgetItem(f"{art['cantidad']:.2f}"))
            
            btn_quitar = QPushButton("🗑️ Quitar")
            btn_quitar.clicked.connect(lambda checked, idx=i: self.quitar_articulo(idx))
            self.tabla_articulos.setCellWidget(i, 4, btn_quitar)
    
    def quitar_articulo(self, index):
        """Quita un artículo de la lista"""
        if 0 <= index < len(self.articulos_temp):
            del self.articulos_temp[index]
            self.actualizar_tabla()
    
    def guardar_imputacion(self):
        """Guarda la imputación en la base de datos"""
        # Validaciones
        operario_id = self.cmb_operario.currentData()
        if not operario_id:
            QMessageBox.warning(self, "⚠️ Aviso", "Debe seleccionar un operario.")
            return
        
        if not self.furgoneta_id:
            QMessageBox.warning(self, "⚠️ Aviso", "El operario no tiene furgoneta asignada.")
            return
        
        if not self.articulos_temp:
            QMessageBox.warning(self, "⚠️ Aviso", "Debe agregar al menos un artículo.")
            return
        
        fecha = self.date_fecha.date().toString("yyyy-MM-dd")
        ot = self.txt_ot.text().strip() or None
        
        try:
            con = get_con()
            cur = con.cursor()
            
            # Obtener nombre del operario
            cur.execute("SELECT nombre FROM operarios WHERE id=?", (operario_id,))
            operario_nombre = cur.fetchone()[0]
            
            # Registrar movimientos de imputación
            for art in self.articulos_temp:
                cur.execute("""
                    INSERT INTO movimientos(fecha, tipo, origen_id, destino_id, articulo_id, cantidad, ot, responsable)
                    VALUES(?, 'IMPUTACION', ?, NULL, ?, ?, ?, ?)
                """, (fecha, self.furgoneta_id, art['id'], art['cantidad'], ot, operario_nombre))
            
            con.commit()
            con.close()
            
            ot_texto = f" en OT: {ot}" if ot else ""
            QMessageBox.information(
                self,
                "✅ Éxito",
                f"Imputación registrada correctamente.\n\n"
                f"{len(self.articulos_temp)} artículo(s) consumidos por {operario_nombre}{ot_texto}."
            )
            
            self.limpiar_todo()
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al guardar:\n{e}")
    
    def limpiar_todo(self):
        """Limpia todos los campos"""
        self.articulos_temp = []
        self.actualizar_tabla()
        self.txt_ot.clear()
        self.spin_cantidad.setValue(1)
        self.cmb_operario.setCurrentIndex(0)