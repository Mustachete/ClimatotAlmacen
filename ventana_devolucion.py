# ventana_devolucion.py - Devolución a Proveedor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QComboBox,
    QDateEdit, QGroupBox, QHeaderView, QTextEdit
)
from PySide6.QtCore import Qt, QDate
from pathlib import Path
import sqlite3
import datetime
from estilos import ESTILO_VENTANA
from widgets_personalizados import SpinBoxClimatot

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "db" / "almacen.db"

def get_con():
    """Devuelve conexión a la base de datos"""
    return sqlite3.connect(DB_PATH)

# ========================================
# VENTANA DE DEVOLUCIÓN A PROVEEDOR
# ========================================
class VentanaDevolucion(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("↩️ Devolución a Proveedor")
        self.setFixedSize(1000, 750)
        self.setStyleSheet(ESTILO_VENTANA)
        
        # Lista temporal de artículos a devolver
        self.articulos_temp = []
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # ========== TÍTULO ==========
        titulo = QLabel("↩️ Devolución de Material a Proveedor")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 5px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        desc = QLabel("Registra material que se devuelve al proveedor (defectuoso, equivocado, sobrante...)")
        desc.setStyleSheet("color: #64748b; font-size: 12px; margin-bottom: 10px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # ========== GRUPO: DATOS DE LA DEVOLUCIÓN ==========
        grupo_datos = QGroupBox("📋 Datos de la Devolución")
        datos_layout = QVBoxLayout()
        
        # Fila 1: Fecha y Proveedor
        fila1 = QHBoxLayout()
        
        lbl_fecha = QLabel("📅 Fecha devolución:")
        self.date_fecha = QDateEdit()
        self.date_fecha.setCalendarPopup(True)
        self.date_fecha.setDate(QDate.currentDate())
        self.date_fecha.setDisplayFormat("dd/MM/yyyy")
        self.date_fecha.setMaximumDate(QDate.currentDate())
        
        lbl_proveedor = QLabel("🏭 Proveedor *:")
        self.cmb_proveedor = QComboBox()
        self.cmb_proveedor.setMinimumWidth(250)
        self.cargar_proveedores()
        
        fila1.addWidget(lbl_fecha)
        fila1.addWidget(self.date_fecha)
        fila1.addSpacing(20)
        fila1.addWidget(lbl_proveedor)
        fila1.addWidget(self.cmb_proveedor)
        fila1.addStretch()
        
        # Fila 2: Albarán original (opcional)
        fila2 = QHBoxLayout()
        
        lbl_albaran = QLabel("📄 Nº Albarán original:")
        self.txt_albaran = QLineEdit()
        self.txt_albaran.setPlaceholderText("(Opcional) Si la devolución es de un albarán específico")
        self.txt_albaran.setMinimumWidth(300)
        
        fila2.addWidget(lbl_albaran)
        fila2.addWidget(self.txt_albaran)
        fila2.addStretch()
        
        datos_layout.addLayout(fila1)
        datos_layout.addLayout(fila2)
        
        grupo_datos.setLayout(datos_layout)
        layout.addWidget(grupo_datos)
        
        # ========== GRUPO: MOTIVO ==========
        grupo_motivo = QGroupBox("📝 Motivo de la Devolución")
        motivo_layout = QVBoxLayout()
        
        lbl_motivo = QLabel("Describe el motivo *:")
        self.txt_motivo = QTextEdit()
        self.txt_motivo.setPlaceholderText(
            "Ejemplos:\n"
            "- Material defectuoso\n"
            "- Artículo incorrecto (pedimos X y trajeron Y)\n"
            "- Cantidad incorrecta (pedimos 5 y trajeron 10)\n"
            "- Material sobrante de obra\n"
            "- No cumple especificaciones"
        )
        self.txt_motivo.setMaximumHeight(100)
        
        motivo_layout.addWidget(lbl_motivo)
        motivo_layout.addWidget(self.txt_motivo)
        
        grupo_motivo.setLayout(motivo_layout)
        layout.addWidget(grupo_motivo)
        
        # ========== GRUPO: AÑADIR ARTÍCULOS ==========
        grupo_articulos = QGroupBox("📦 Artículos a Devolver")
        articulos_layout = QVBoxLayout()
        
        # Selector de artículo
        select_layout = QHBoxLayout()
        
        lbl_art = QLabel("Artículo:")
        self.cmb_articulo = QComboBox()
        self.cmb_articulo.setMinimumWidth(350)
        self.cargar_articulos()
        
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
        
        # ========== TABLA DE ARTÍCULOS ==========
        lbl_tabla = QLabel("📋 Artículos a devolver:")
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
        
        # Nota
        nota = QLabel(
            "💡 Los artículos se descontarán del Almacén principal.\n"
            "Asegúrate de que el material esté físicamente en el almacén antes de registrar la devolución."
        )
        nota.setStyleSheet("color: #64748b; font-size: 11px; margin: 5px; padding: 8px; "
                          "background-color: #dbeafe; border-radius: 5px;")
        layout.addWidget(nota)
        
        # ========== BOTONES ==========
        botones_layout = QHBoxLayout()
        
        self.btn_guardar = QPushButton("💾 REGISTRAR DEVOLUCIÓN")
        self.btn_guardar.setMinimumHeight(50)
        self.btn_guardar.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.btn_guardar.clicked.connect(self.guardar_devolucion)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.setMinimumHeight(50)
        self.btn_cancelar.clicked.connect(self.limpiar)
        
        self.btn_volver = QPushButton("⬅️ Volver")
        self.btn_volver.setMinimumHeight(50)
        self.btn_volver.clicked.connect(self.close)
        
        botones_layout.addWidget(self.btn_guardar, 3)
        botones_layout.addWidget(self.btn_cancelar, 1)
        botones_layout.addWidget(self.btn_volver, 1)
        
        layout.addLayout(botones_layout)
    
    def cargar_proveedores(self):
        """Carga los proveedores"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("SELECT id, nombre FROM proveedores ORDER BY nombre")
            rows = cur.fetchall()
            con.close()
            
            self.cmb_proveedor.addItem("(Seleccione proveedor)", None)
            for row in rows:
                self.cmb_proveedor.addItem(row[1], row[0])
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar proveedores:\n{e}")
    
    def cargar_articulos(self):
        """Carga los artículos activos"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("""
                SELECT id, nombre, u_medida
                FROM articulos
                WHERE activo=1
                ORDER BY nombre
            """)
            rows = cur.fetchall()
            con.close()
            
            self.cmb_articulo.addItem("(Seleccione artículo)", None)
            for row in rows:
                texto = f"{row[1]} ({row[2]})"
                self.cmb_articulo.addItem(texto, {
                    'id': row[0],
                    'nombre': row[1],
                    'u_medida': row[2]
                })
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar artículos:\n{e}")
    
    def agregar_articulo(self):
        """Agrega un artículo a la lista temporal"""
        data = self.cmb_articulo.currentData()
        if not data or not isinstance(data, dict):
            QMessageBox.warning(self, "⚠️ Aviso", "Seleccione un artículo.")
            return
        
        cantidad = self.spin_cantidad.value()
        
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
            'cantidad': cantidad
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
    
    def guardar_devolucion(self):
        """Guarda la devolución en la base de datos"""
        # Validaciones
        proveedor_id = self.cmb_proveedor.currentData()
        if not proveedor_id:
            QMessageBox.warning(self, "⚠️ Aviso", "Debe seleccionar un proveedor.")
            return
        
        motivo = self.txt_motivo.toPlainText().strip()
        if not motivo:
            QMessageBox.warning(self, "⚠️ Aviso", "Debe especificar el motivo de la devolución.")
            self.txt_motivo.setFocus()
            return
        
        if not self.articulos_temp:
            QMessageBox.warning(self, "⚠️ Aviso", "Debe agregar al menos un artículo.")
            return
        
        fecha = self.date_fecha.date().toString("yyyy-MM-dd")
        albaran_original = self.txt_albaran.text().strip() or None
        
        # Confirmación
        proveedor_nombre = self.cmb_proveedor.currentText()
        
        respuesta = QMessageBox.question(
            self,
            "↩️ Confirmar devolución",
            f"¿Confirma la devolución de {len(self.articulos_temp)} artículo(s) a:\n\n"
            f"Proveedor: {proveedor_nombre}\n"
            f"Motivo: {motivo[:50]}...\n\n"
            f"Los artículos se descontarán del Almacén.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if respuesta != QMessageBox.Yes:
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            
            # Obtener ID del almacén principal
            cur.execute("SELECT id FROM almacenes WHERE nombre='Almacén' LIMIT 1")
            almacen_id = cur.fetchone()[0]
            
            # Registrar movimientos de devolución
            for art in self.articulos_temp:
                cur.execute("""
                    INSERT INTO movimientos(fecha, tipo, origen_id, destino_id, articulo_id, 
                                           cantidad, motivo, albaran)
                    VALUES(?, 'DEVOLUCION', ?, NULL, ?, ?, ?, ?)
                """, (fecha, almacen_id, art['id'], art['cantidad'], motivo, albaran_original))
            
            con.commit()
            con.close()
            
            QMessageBox.information(
                self,
                "✅ Éxito",
                f"Devolución registrada correctamente.\n\n"
                f"{len(self.articulos_temp)} artículo(s) devueltos a {proveedor_nombre}."
            )
            
            self.limpiar()
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al guardar:\n{e}")
    
    def limpiar(self):
        """Limpia todos los campos"""
        self.articulos_temp = []
        self.actualizar_tabla()
        self.cmb_proveedor.setCurrentIndex(0)
        self.txt_albaran.clear()
        self.txt_motivo.clear()
        self.spin_cantidad.setValue(1)
        self.date_fecha.setDate(QDate.currentDate())