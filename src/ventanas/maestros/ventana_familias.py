# ventana_familias.py - Gestión de Familias de Artículos
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
# DIÁLOGO PARA AÑADIR/EDITAR FAMILIA
# ========================================
class DialogoFamilia(QDialog):
    def __init__(self, parent=None, familia_id=None):
        super().__init__(parent)
        self.familia_id = familia_id
        self.setWindowTitle("✏️ Editar Familia" if familia_id else "➕ Nueva Familia")
        self.setFixedSize(450, 200)
        self.setStyleSheet(ESTILO_DIALOGO)
        
        layout = QVBoxLayout(self)
        
        # Formulario
        form = QFormLayout()
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Calefacción, Climatización...")
        form.addRow("📂 Nombre de la Familia *:", self.txt_nombre)
        
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
        if self.familia_id:
            self.cargar_datos()
        
        # Focus en el campo de texto
        self.txt_nombre.setFocus()
    
    def cargar_datos(self):
        """Carga los datos de la familia a editar"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("SELECT nombre FROM familias WHERE id=?", (self.familia_id,))
            row = cur.fetchone()
            con.close()
            
            if row:
                self.txt_nombre.setText(row[0] or "")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar datos:\n{e}")
    
    def guardar(self):
        """Guarda la familia (nueva o editada)"""
        nombre = self.txt_nombre.text().strip()
        
        if not nombre:
            QMessageBox.warning(self, "⚠️ Aviso", "El nombre de la familia es obligatorio.")
            self.txt_nombre.setFocus()
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            
            if self.familia_id:
                # Editar existente
                cur.execute("UPDATE familias SET nombre=? WHERE id=?", (nombre, self.familia_id))
                mensaje = f"✅ Familia '{nombre}' actualizada correctamente."
            else:
                # Crear nueva
                cur.execute("INSERT INTO familias(nombre) VALUES(?)", (nombre,))
                mensaje = f"✅ Familia '{nombre}' creada correctamente."
            
            con.commit()
            con.close()
            
            QMessageBox.information(self, "✅ Éxito", mensaje)
            self.accept()
            
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "⚠️ Aviso", f"Ya existe una familia con el nombre '{nombre}'.")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al guardar:\n{e}")

# ========================================
# VENTANA PRINCIPAL DE FAMILIAS
# ========================================
class VentanaFamilias(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📂 Gestión de Familias de Artículos")
        self.resize(700, 500)
        self.setMinimumSize(600, 400)
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("📂 Gestión de Familias de Artículos")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        # Descripción
        desc = QLabel("Las familias sirven para categorizar y organizar los artículos del almacén")
        desc.setStyleSheet("color: gray; font-size: 12px; margin-bottom: 10px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # Barra de búsqueda y botones superiores
        top_layout = QHBoxLayout()
        
        lbl_buscar = QLabel("🔍 Buscar:")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Escriba para buscar...")
        self.txt_buscar.textChanged.connect(self.buscar)
        
        self.btn_nuevo = QPushButton("➕ Nueva Familia")
        self.btn_nuevo.clicked.connect(self.nueva_familia)
        
        self.btn_editar = QPushButton("✏️ Editar")
        self.btn_editar.clicked.connect(self.editar_familia)
        self.btn_editar.setEnabled(False)
        
        self.btn_eliminar = QPushButton("🗑️ Eliminar")
        self.btn_eliminar.clicked.connect(self.eliminar_familia)
        self.btn_eliminar.setEnabled(False)
        
        top_layout.addWidget(lbl_buscar)
        top_layout.addWidget(self.txt_buscar)
        top_layout.addWidget(self.btn_nuevo)
        top_layout.addWidget(self.btn_editar)
        top_layout.addWidget(self.btn_eliminar)
        
        layout.addLayout(top_layout)
        
        # Tabla de familias
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(2)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre de la Familia"])
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self.seleccion_cambiada)
        self.tabla.doubleClicked.connect(self.editar_familia)
        
        # Ocultar columna ID
        self.tabla.setColumnHidden(0, True)
        
        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Nombre ocupa todo
        
        layout.addWidget(self.tabla)
        
        # Botón volver
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)
        
        # Cargar datos iniciales
        self.cargar_familias()
    
    def cargar_familias(self, filtro=""):
        """Carga las familias en la tabla"""
        try:
            con = get_con()
            cur = con.cursor()
            
            if filtro:
                cur.execute("""
                    SELECT id, nombre 
                    FROM familias 
                    WHERE nombre LIKE ?
                    ORDER BY nombre
                """, (f"%{filtro}%",))
            else:
                cur.execute("SELECT id, nombre FROM familias ORDER BY nombre")
            
            rows = cur.fetchall()
            con.close()
            
            self.tabla.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                for j, valor in enumerate(row):
                    item = QTableWidgetItem(str(valor) if valor else "")
                    self.tabla.setItem(i, j, item)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar familias:\n{e}")
    
    def buscar(self):
        """Filtra la tabla según el texto de búsqueda"""
        filtro = self.txt_buscar.text().strip()
        self.cargar_familias(filtro)
    
    def seleccion_cambiada(self):
        """Se activan/desactivan botones según la selección"""
        hay_seleccion = len(self.tabla.selectedItems()) > 0
        self.btn_editar.setEnabled(hay_seleccion)
        self.btn_eliminar.setEnabled(hay_seleccion)
    
    def nueva_familia(self):
        """Abre el diálogo para crear una nueva familia"""
        dialogo = DialogoFamilia(self)
        if dialogo.exec():
            self.cargar_familias()
    
    def editar_familia(self):
        """Abre el diálogo para editar la familia seleccionada"""
        seleccion = self.tabla.currentRow()
        if seleccion < 0:
            return
        
        familia_id = int(self.tabla.item(seleccion, 0).text())
        dialogo = DialogoFamilia(self, familia_id)
        if dialogo.exec():
            self.cargar_familias()
    
    def eliminar_familia(self):
        """Elimina la familia seleccionada"""
        seleccion = self.tabla.currentRow()
        if seleccion < 0:
            return
        
        familia_id = int(self.tabla.item(seleccion, 0).text())
        nombre = self.tabla.item(seleccion, 1).text()
        
        # Confirmar eliminación
        respuesta = QMessageBox.question(
            self,
            "⚠️ Confirmar eliminación",
            f"¿Está seguro de eliminar la familia '{nombre}'?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if respuesta != QMessageBox.Yes:
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("DELETE FROM familias WHERE id=?", (familia_id,))
            con.commit()
            con.close()
            
            QMessageBox.information(self, "✅ Éxito", f"Familia '{nombre}' eliminada correctamente.")
            self.cargar_familias()
            
        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self, 
                "⚠️ No se puede eliminar",
                f"La familia '{nombre}' tiene artículos asociados.\n\n"
                "No se puede eliminar una familia que está siendo usada."
            )
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al eliminar:\n{e}")