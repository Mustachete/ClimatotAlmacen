# ventana_proveedores.py - Gestión de Proveedores
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QTextEdit, QHeaderView
)
from PySide6.QtCore import Qt
from pathlib import Path
import sqlite3
from estilos import ESTILO_DIALOGO, ESTILO_VENTANA

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "db" / "almacen.db"

def get_con():
    """Devuelve conexión a la base de datos"""
    return sqlite3.connect(DB_PATH)

# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR PROVEEDOR
# ========================================
class DialogoProveedor(QDialog):
    def __init__(self, parent=None, proveedor_id=None):
        super().__init__(parent)
        self.proveedor_id = proveedor_id
        self.setWindowTitle("✏️ Editar Proveedor" if proveedor_id else "➕ Nuevo Proveedor")
        self.setFixedSize(500, 400)
        self.setStyleSheet(ESTILO_DIALOGO)
        
        layout = QVBoxLayout(self)
        
        # Formulario
        form = QFormLayout()
        
        self.txt_nombre = QLineEdit()
        self.txt_telefono = QLineEdit()
        self.txt_contacto = QLineEdit()
        self.txt_email = QLineEdit()
        self.txt_notas = QTextEdit()
        self.txt_notas.setMaximumHeight(100)
        
        form.addRow("📛 Nombre *:", self.txt_nombre)
        form.addRow("📞 Teléfono:", self.txt_telefono)
        form.addRow("👤 Contacto:", self.txt_contacto)
        form.addRow("📧 Email:", self.txt_email)
        form.addRow("📝 Notas:", self.txt_notas)
        
        layout.addLayout(form)
        
        # Nota obligatorio
        nota = QLabel("* Campos obligatorios")
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
        if self.proveedor_id:
            self.cargar_datos()
    
    def cargar_datos(self):
        """Carga los datos del proveedor a editar"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute(
                "SELECT nombre, telefono, contacto, email, notas FROM proveedores WHERE id=?",
                (self.proveedor_id,)
            )
            row = cur.fetchone()
            con.close()
            
            if row:
                self.txt_nombre.setText(row[0] or "")
                self.txt_telefono.setText(row[1] or "")
                self.txt_contacto.setText(row[2] or "")
                self.txt_email.setText(row[3] or "")
                self.txt_notas.setPlainText(row[4] or "")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar datos:\n{e}")
    
    def guardar(self):
        """Guarda el proveedor (nuevo o editado)"""
        nombre = self.txt_nombre.text().strip()
        
        if not nombre:
            QMessageBox.warning(self, "⚠️ Aviso", "El nombre del proveedor es obligatorio.")
            self.txt_nombre.setFocus()
            return
        
        telefono = self.txt_telefono.text().strip()
        contacto = self.txt_contacto.text().strip()
        email = self.txt_email.text().strip()
        notas = self.txt_notas.toPlainText().strip()
        
        try:
            con = get_con()
            cur = con.cursor()
            
            if self.proveedor_id:
                # Editar existente
                cur.execute("""
                    UPDATE proveedores 
                    SET nombre=?, telefono=?, contacto=?, email=?, notas=?
                    WHERE id=?
                """, (nombre, telefono, contacto, email, notas, self.proveedor_id))
                mensaje = f"✅ Proveedor '{nombre}' actualizado correctamente."
            else:
                # Crear nuevo
                cur.execute("""
                    INSERT INTO proveedores(nombre, telefono, contacto, email, notas)
                    VALUES(?,?,?,?,?)
                """, (nombre, telefono, contacto, email, notas))
                mensaje = f"✅ Proveedor '{nombre}' creado correctamente."
            
            con.commit()
            con.close()
            
            QMessageBox.information(self, "✅ Éxito", mensaje)
            self.accept()
            
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "⚠️ Aviso", f"Ya existe un proveedor con el nombre '{nombre}'.")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al guardar:\n{e}")

# ========================================
# VENTANA PRINCIPAL DE PROVEEDORES
# ========================================
class VentanaProveedores(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🏭 Gestión de Proveedores")
        self.setFixedSize(950, 650)
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("🏭 Gestión de Proveedores")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        # Barra de búsqueda y botones superiores
        top_layout = QHBoxLayout()
        
        lbl_buscar = QLabel("🔍 Buscar:")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre, teléfono, contacto o email...")
        self.txt_buscar.textChanged.connect(self.buscar)
        
        self.btn_nuevo = QPushButton("➕ Nuevo Proveedor")
        self.btn_nuevo.clicked.connect(self.nuevo_proveedor)
        
        self.btn_editar = QPushButton("✏️ Editar")
        self.btn_editar.clicked.connect(self.editar_proveedor)
        self.btn_editar.setEnabled(False)
        
        self.btn_eliminar = QPushButton("🗑️ Eliminar")
        self.btn_eliminar.clicked.connect(self.eliminar_proveedor)
        self.btn_eliminar.setEnabled(False)
        
        top_layout.addWidget(lbl_buscar)
        top_layout.addWidget(self.txt_buscar)
        top_layout.addWidget(self.btn_nuevo)
        top_layout.addWidget(self.btn_editar)
        top_layout.addWidget(self.btn_eliminar)
        
        layout.addLayout(top_layout)
        
        # Tabla de proveedores
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Teléfono", "Contacto", "Email", "Notas"])
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self.seleccion_cambiada)
        self.tabla.doubleClicked.connect(self.editar_proveedor)
        
        # Ocultar columna ID
        self.tabla.setColumnHidden(0, True)
        
        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Nombre
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Teléfono
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Contacto
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Email
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Notas
        
        layout.addWidget(self.tabla)
        
        # Botón volver
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)
        
        # Cargar datos iniciales
        self.cargar_proveedores()
    
    def cargar_proveedores(self, filtro=""):
        """Carga los proveedores en la tabla"""
        try:
            con = get_con()
            cur = con.cursor()
            
            if filtro:
                cur.execute("""
                    SELECT id, nombre, telefono, contacto, email, notas 
                    FROM proveedores 
                    WHERE nombre LIKE ? 
                       OR telefono LIKE ?
                       OR contacto LIKE ?
                       OR email LIKE ?
                    ORDER BY nombre
                """, (f"%{filtro}%", f"%{filtro}%", f"%{filtro}%", f"%{filtro}%"))
            else:
                cur.execute("""
                    SELECT id, nombre, telefono, contacto, email, notas 
                    FROM proveedores 
                    ORDER BY nombre
                """)
            
            rows = cur.fetchall()
            con.close()
            
            self.tabla.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                for j, valor in enumerate(row):
                    item = QTableWidgetItem(str(valor) if valor else "")
                    self.tabla.setItem(i, j, item)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar proveedores:\n{e}")
            
    def buscar(self):
        """Filtra la tabla según el texto de búsqueda"""
        filtro = self.txt_buscar.text().strip()
        self.cargar_proveedores(filtro)
    
    def seleccion_cambiada(self):
        """Se activan/desactivan botones según la selección"""
        hay_seleccion = len(self.tabla.selectedItems()) > 0
        self.btn_editar.setEnabled(hay_seleccion)
        self.btn_eliminar.setEnabled(hay_seleccion)
    
    def nuevo_proveedor(self):
        """Abre el diálogo para crear un nuevo proveedor"""
        dialogo = DialogoProveedor(self)
        if dialogo.exec():
            self.cargar_proveedores()
    
    def editar_proveedor(self):
        """Abre el diálogo para editar el proveedor seleccionado"""
        seleccion = self.tabla.currentRow()
        if seleccion < 0:
            return
        
        proveedor_id = int(self.tabla.item(seleccion, 0).text())
        dialogo = DialogoProveedor(self, proveedor_id)
        if dialogo.exec():
            self.cargar_proveedores()
    
    def eliminar_proveedor(self):
        """Elimina el proveedor seleccionado"""
        seleccion = self.tabla.currentRow()
        if seleccion < 0:
            return
        
        proveedor_id = int(self.tabla.item(seleccion, 0).text())
        nombre = self.tabla.item(seleccion, 1).text()
        
        # Confirmar eliminación
        respuesta = QMessageBox.question(
            self,
            "⚠️ Confirmar eliminación",
            f"¿Está seguro de eliminar el proveedor '{nombre}'?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if respuesta != QMessageBox.Yes:
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("DELETE FROM proveedores WHERE id=?", (proveedor_id,))
            con.commit()
            con.close()
            
            QMessageBox.information(self, "✅ Éxito", f"Proveedor '{nombre}' eliminado correctamente.")
            self.cargar_proveedores()
            
        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self, 
                "⚠️ No se puede eliminar",
                f"El proveedor '{nombre}' tiene artículos asociados.\n\n"
                "No se puede eliminar un proveedor que está siendo usado."
            )
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al eliminar:\n{e}")