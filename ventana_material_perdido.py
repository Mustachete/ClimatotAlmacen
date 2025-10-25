# ventana_material_perdido.py - Registro de Material Perdido
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
# VENTANA DE MATERIAL PERDIDO
# ========================================
class VentanaMaterialPerdido(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚠️ Registro de Material Perdido")
        self.setFixedSize(900, 700)
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # ========== TÍTULO ==========
        titulo = QLabel("⚠️ Registro de Material Perdido")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 5px; color: #dc2626;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        desc = QLabel("⚠️ SOLO ADMINISTRADOR - Registra material perdido, roto o sin justificación")
        desc.setStyleSheet("color: #dc2626; font-size: 13px; margin-bottom: 10px; font-weight: bold;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # ========== GRUPO: DATOS DEL INCIDENTE ==========
        grupo_datos = QGroupBox("📋 Datos del Incidente")
        datos_layout = QVBoxLayout()
        
        # Fila 1: Fecha y Operario
        fila1 = QHBoxLayout()
        
        lbl_fecha = QLabel("📅 Fecha del incidente:")
        self.date_fecha = QDateEdit()
        self.date_fecha.setCalendarPopup(True)
        self.date_fecha.setDate(QDate.currentDate())
        self.date_fecha.setDisplayFormat("dd/MM/yyyy")
        self.date_fecha.setMaximumDate(QDate.currentDate())
        
        lbl_operario = QLabel("👷 Operario responsable *:")
        self.cmb_operario = QComboBox()
        self.cmb_operario.setMinimumWidth(250)
        self.cargar_operarios()
        self.cmb_operario.currentIndexChanged.connect(self.cambio_operario)
        
        fila1.addWidget(lbl_fecha)
        fila1.addWidget(self.date_fecha)
        fila1.addSpacing(20)
        fila1.addWidget(lbl_operario)
        fila1.addWidget(self.cmb_operario)
        fila1.addStretch()
        
        # Fila 2: Furgoneta
        fila2 = QHBoxLayout()
        
        lbl_furgoneta = QLabel("🚚 Furgoneta asignada:")
        self.lbl_furgoneta_asignada = QLabel("(Seleccione operario)")
        self.lbl_furgoneta_asignada.setStyleSheet("color: #64748b; font-style: italic;")
        
        fila2.addWidget(lbl_furgoneta)
        fila2.addWidget(self.lbl_furgoneta_asignada)
        fila2.addStretch()
        
        datos_layout.addLayout(fila1)
        datos_layout.addLayout(fila2)
        
        grupo_datos.setLayout(datos_layout)
        layout.addWidget(grupo_datos)
        
        # ========== GRUPO: ARTÍCULO PERDIDO ==========
        grupo_articulo = QGroupBox("📦 Artículo Perdido")
        articulo_layout = QVBoxLayout()
        
        # Selector de artículo
        select_layout = QHBoxLayout()
        
        lbl_art = QLabel("Artículo *:")
        self.cmb_articulo = QComboBox()
        self.cmb_articulo.setMinimumWidth(350)
        self.cargar_articulos()
        
        lbl_cant = QLabel("Cantidad *:")
        self.spin_cantidad = SpinBoxClimatot()
        self.spin_cantidad.setRange(0.01, 999999)
        self.spin_cantidad.setDecimals(2)
        self.spin_cantidad.setValue(1)
        self.spin_cantidad.setMinimumWidth(120)
        
        select_layout.addWidget(lbl_art)
        select_layout.addWidget(self.cmb_articulo, 2)
        select_layout.addWidget(lbl_cant)
        select_layout.addWidget(self.spin_cantidad)
        select_layout.addStretch()
        
        articulo_layout.addLayout(select_layout)
        
        grupo_articulo.setLayout(articulo_layout)
        layout.addWidget(grupo_articulo)
        
        # ========== GRUPO: MOTIVO ==========
        grupo_motivo = QGroupBox("📝 Motivo / Justificación")
        motivo_layout = QVBoxLayout()
        
        lbl_motivo = QLabel("Describe qué ocurrió *:")
        self.txt_motivo = QTextEdit()
        self.txt_motivo.setPlaceholderText(
            "Ejemplos:\n"
            "- Material roto durante la instalación\n"
            "- Material perdido en el transporte\n"
            "- Error en el conteo\n"
            "- Artículo defectuoso\n"
            "- Sin justificación clara"
        )
        self.txt_motivo.setMaximumHeight(120)
        
        motivo_layout.addWidget(lbl_motivo)
        motivo_layout.addWidget(self.txt_motivo)
        
        grupo_motivo.setLayout(motivo_layout)
        layout.addWidget(grupo_motivo)
        
        # Nota
        nota = QLabel(
            "* Campos obligatorios\n\n"
            "⚠️ Esta acción quedará registrada en el historial del operario.\n"
            "El material se descontará de la furgoneta del operario."
        )
        nota.setStyleSheet("color: #dc2626; font-size: 12px; margin: 10px; padding: 10px; "
                          "background-color: #fee2e2; border-radius: 5px;")
        layout.addWidget(nota)
        
        # ========== BOTONES ==========
        layout.addStretch()
        botones_layout = QHBoxLayout()
        
        self.btn_guardar = QPushButton("⚠️ REGISTRAR PÉRDIDA")
        self.btn_guardar.setMinimumHeight(50)
        self.btn_guardar.setStyleSheet("""
            QPushButton {
                font-size: 15px;
                font-weight: bold;
                background-color: white;
                border: 2px solid #dc2626;
                color: #dc2626;
            }
            QPushButton:hover {
                background-color: #dc2626;
                color: white;
            }
        """)
        self.btn_guardar.clicked.connect(self.guardar_perdida)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.setMinimumHeight(50)
        self.btn_cancelar.clicked.connect(self.limpiar)
        
        self.btn_volver = QPushButton("⬅️ Volver")
        self.btn_volver.setMinimumHeight(50)
        self.btn_volver.clicked.connect(self.close)
        
        botones_layout.addWidget(self.btn_guardar, 2)
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
        """Al cambiar de operario, busca su furgoneta"""
        operario_id = self.cmb_operario.currentData()
        if not operario_id:
            self.lbl_furgoneta_asignada.setText("(Seleccione operario)")
            self.lbl_furgoneta_asignada.setStyleSheet("color: #64748b; font-style: italic;")
            self.furgoneta_id = None
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
            else:
                self.lbl_furgoneta_asignada.setText("⚠️ Sin furgoneta asignada hoy")
                self.lbl_furgoneta_asignada.setStyleSheet("color: #dc2626; font-weight: bold;")
                self.furgoneta_id = None
        except Exception:
            pass
    
    def cargar_articulos(self):
        """Carga todos los artículos activos"""
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
                self.cmb_articulo.addItem(texto, {'id': row[0], 'nombre': row[1], 'u_medida': row[2]})
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar artículos:\n{e}")
    
    def guardar_perdida(self):
        """Guarda el registro de material perdido"""
        # Validaciones
        operario_id = self.cmb_operario.currentData()
        if not operario_id:
            QMessageBox.warning(self, "⚠️ Aviso", "Debe seleccionar un operario responsable.")
            return
        
        if not self.furgoneta_id:
            QMessageBox.warning(self, "⚠️ Aviso", "El operario no tiene furgoneta asignada.")
            return
        
        articulo_data = self.cmb_articulo.currentData()
        if not articulo_data or not isinstance(articulo_data, dict):
            QMessageBox.warning(self, "⚠️ Aviso", "Debe seleccionar un artículo.")
            return
        
        cantidad = self.spin_cantidad.value()
        motivo = self.txt_motivo.toPlainText().strip()
        
        if not motivo:
            QMessageBox.warning(self, "⚠️ Aviso", "Debe especificar el motivo de la pérdida.")
            self.txt_motivo.setFocus()
            return
        
        fecha = self.date_fecha.date().toString("yyyy-MM-dd")
        
        # Confirmación
        operario_nombre = self.cmb_operario.currentText()
        articulo_nombre = articulo_data['nombre']
        
        respuesta = QMessageBox.question(
            self,
            "⚠️ Confirmar registro de pérdida",
            f"¿Confirma el registro de esta pérdida?\n\n"
            f"Operario: {operario_nombre}\n"
            f"Artículo: {articulo_nombre}\n"
            f"Cantidad: {cantidad:.2f} {articulo_data['u_medida']}\n"
            f"Motivo: {motivo[:50]}...\n\n"
            f"Esta acción NO se puede deshacer y quedará en el historial.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if respuesta != QMessageBox.Yes:
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            
            # Obtener nombre del operario
            cur.execute("SELECT nombre FROM operarios WHERE id=?", (operario_id,))
            operario_nombre_bd = cur.fetchone()[0]
            
            # Registrar movimiento de pérdida
            cur.execute("""
                INSERT INTO movimientos(fecha, tipo, origen_id, destino_id, articulo_id, 
                                       cantidad, motivo, responsable)
                VALUES(?, 'PERDIDA', ?, NULL, ?, ?, ?, ?)
            """, (fecha, self.furgoneta_id, articulo_data['id'], cantidad, motivo, operario_nombre_bd))
            
            con.commit()
            con.close()
            
            QMessageBox.information(
                self,
                "✅ Registrado",
                f"Pérdida registrada correctamente.\n\n"
                f"Operario: {operario_nombre_bd}\n"
                f"Artículo: {articulo_nombre}\n"
                f"Cantidad: {cantidad:.2f}"
            )
            
            self.limpiar()
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al guardar:\n{e}")
    
    def limpiar(self):
        """Limpia todos los campos"""
        self.cmb_operario.setCurrentIndex(0)
        self.cmb_articulo.setCurrentIndex(0)
        self.spin_cantidad.setValue(1)
        self.txt_motivo.clear()
        self.date_fecha.setDate(QDate.currentDate())