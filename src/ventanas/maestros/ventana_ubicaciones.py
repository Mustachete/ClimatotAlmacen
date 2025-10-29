# ventana_ubicaciones.py - Gestión de Ubicaciones del Almacén
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QHeaderView
)
from PySide6.QtCore import Qt
from pathlib import Path
import sqlite3
from src.ui.estilos import ESTILO_DIALOGO, ESTILO_VENTANA
from src.core.db_utils import get_con

# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR UBICACIÓN
# ========================================
class DialogoUbicacion(QDialog):
    def __init__(self, parent=None, ubicacion_id=None):
        super().__init__(parent)
        self.ubicacion_id = ubicacion_id
        self.setWindowTitle("✏️ Editar Ubicación" if ubicacion_id else "➕ Nueva Ubicación")
        self.setFixedSize(450, 200)
        self.setStyleSheet(ESTILO_DIALOGO)
        
        layout = QVBoxLayout(self)
        
        # Formulario
        form = QFormLayout()
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: A1, B2, Estantería 5...")
        form.addRow("📍 Código/Nombre de Ubicación *:", self.txt_nombre)
        
        layout.addLayout(form)
        
        # Nota obligatorio
        nota = QLabel("* Campo obligatorio")
        nota.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(nota)
        
        # Botones
        layout.addStretch()
        btn_layout = QHBoxLayout()
        
        self.btn_guardar = QPushButton("💾 Guardar")
        self.btn_guardar.clicked.connect(self.guardar)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)
        
        # Si estamos editando, cargar datos
        if self.ubicacion_id:
            self.cargar_datos()
        
        # Focus en el campo de texto
        self.txt_nombre.setFocus()
    
    def cargar_datos(self):
        """Carga los datos de la ubicación a editar"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("SELECT nombre FROM ubicaciones WHERE id=?", (self.ubicacion_id,))
            row = cur.fetchone()
            con.close()
            
            if row:
                self.txt_nombre.setText(row[0] or "")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar datos:\n{e}")
    
    def guardar(self):
        """Guarda la ubicación (nueva o editada)"""
        nombre = self.txt_nombre.text().strip()
        
        if not nombre:
            QMessageBox.warning(self, "⚠️ Aviso", "El nombre de la ubicación es obligatorio.")
            self.txt_nombre.setFocus()
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            
            if self.ubicacion_id:
                # Editar existente
                cur.execute("UPDATE ubicaciones SET nombre=? WHERE id=?", (nombre, self.ubicacion_id))
                mensaje = f"✅ Ubicación '{nombre}' actualizada correctamente."
            else:
                # Crear nueva
                cur.execute("INSERT INTO ubicaciones(nombre) VALUES(?)", (nombre,))
                mensaje = f"✅ Ubicación '{nombre}' creada correctamente."
            
            con.commit()
            con.close()
            
            QMessageBox.information(self, "✅ Éxito", mensaje)
            self.accept()
            
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "⚠️ Aviso", f"Ya existe una ubicación con el nombre '{nombre}'.")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al guardar:\n{e}")

# ========================================
# VENTANA PRINCIPAL DE UBICACIONES
# ========================================
class VentanaUbicaciones(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📍 Gestión de Ubicaciones del Almacén")
        self.resize(700, 500)
        self.setMinimumSize(600, 400)
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("📍 Gestión de Ubicaciones del Almacén")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        # Descripción
        desc = QLabel("Las ubicaciones sirven para identificar dónde está físicamente cada artículo en el almacén")
        desc.setStyleSheet("color: gray; font-size: 12px; margin-bottom: 10px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # Barra de búsqueda y botones superiores
        top_layout = QHBoxLayout()
        
        lbl_buscar = QLabel("🔍 Buscar:")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Escriba para buscar...")
        self.txt_buscar.textChanged.connect(self.buscar)
        
        self.btn_nuevo = QPushButton("➕ Nueva Ubicación")
        self.btn_nuevo.clicked.connect(self.nueva_ubicacion)
        
        self.btn_editar = QPushButton("✏️ Editar")
        self.btn_editar.clicked.connect(self.editar_ubicacion)
        self.btn_editar.setEnabled(False)
        
        self.btn_eliminar = QPushButton("🗑️ Eliminar")
        self.btn_eliminar.clicked.connect(self.eliminar_ubicacion)
        self.btn_eliminar.setEnabled(False)
        
        top_layout.addWidget(lbl_buscar)
        top_layout.addWidget(self.txt_buscar)
        top_layout.addWidget(self.btn_nuevo)
        top_layout.addWidget(self.btn_editar)
        top_layout.addWidget(self.btn_eliminar)
        
        layout.addLayout(top_layout)
        
        # Tabla de ubicaciones
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(2)
        self.tabla.setHorizontalHeaderLabels(["ID", "Ubicación"])
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self.seleccion_cambiada)
        self.tabla.doubleClicked.connect(self.editar_ubicacion)
        
        # Ocultar columna ID
        self.tabla.setColumnHidden(0, True)
        
        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Ubicación ocupa todo
        
        layout.addWidget(self.tabla)
        
        # Botón volver
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)
        
        # Cargar datos iniciales
        self.cargar_ubicaciones()
    
    def cargar_ubicaciones(self, filtro=""):
        """Carga las ubicaciones en la tabla"""
        try:
            con = get_con()
            cur = con.cursor()
            
            if filtro:
                cur.execute("""
                    SELECT id, nombre 
                    FROM ubicaciones 
                    WHERE nombre LIKE ?
                    ORDER BY nombre
                """, (f"%{filtro}%",))
            else:
                cur.execute("SELECT id, nombre FROM ubicaciones ORDER BY nombre")
            
            rows = cur.fetchall()
            con.close()
            
            self.tabla.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                for j, valor in enumerate(row):
                    item = QTableWidgetItem(str(valor) if valor else "")
                    self.tabla.setItem(i, j, item)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar ubicaciones:\n{e}")
    
    def buscar(self):
        """Filtra la tabla según el texto de búsqueda"""
        filtro = self.txt_buscar.text().strip()
        self.cargar_ubicaciones(filtro)
    
    def seleccion_cambiada(self):
        """Se activan/desactivan botones según la selección"""
        hay_seleccion = len(self.tabla.selectedItems()) > 0
        self.btn_editar.setEnabled(hay_seleccion)
        self.btn_eliminar.setEnabled(hay_seleccion)
    
    def nueva_ubicacion(self):
        """Abre el diálogo para crear una nueva ubicación"""
        dialogo = DialogoUbicacion(self)
        if dialogo.exec():
            self.cargar_ubicaciones()
    
    def editar_ubicacion(self):
        """Abre el diálogo para editar la ubicación seleccionada"""
        seleccion = self.tabla.currentRow()
        if seleccion < 0:
            return
        
        ubicacion_id = int(self.tabla.item(seleccion, 0).text())
        dialogo = DialogoUbicacion(self, ubicacion_id)
        if dialogo.exec():
            self.cargar_ubicaciones()
    
    def eliminar_ubicacion(self):
        """Elimina la ubicación seleccionada"""
        seleccion = self.tabla.currentRow()
        if seleccion < 0:
            return
        
        ubicacion_id = int(self.tabla.item(seleccion, 0).text())
        nombre = self.tabla.item(seleccion, 1).text()
        
        # Confirmar eliminación
        respuesta = QMessageBox.question(
            self,
            "⚠️ Confirmar eliminación",
            f"¿Está seguro de eliminar la ubicación '{nombre}'?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if respuesta != QMessageBox.Yes:
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("DELETE FROM ubicaciones WHERE id=?", (ubicacion_id,))
            con.commit()
            con.close()
            
            QMessageBox.information(self, "✅ Éxito", f"Ubicación '{nombre}' eliminada correctamente.")
            self.cargar_ubicaciones()
            
        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self, 
                "⚠️ No se puede eliminar",
                f"La ubicación '{nombre}' tiene artículos asociados.\n\n"
                "No se puede eliminar una ubicación que está siendo usada."
            )
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al eliminar:\n{e}")