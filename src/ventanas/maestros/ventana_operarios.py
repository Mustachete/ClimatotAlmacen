# ventana_operarios.py - Gestión de Operarios
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QHeaderView, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt
from pathlib import Path
import sqlite3
from src.ui.estilos import ESTILO_DIALOGO, ESTILO_VENTANA
from src.core.db_utils import get_con

# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR OPERARIO
# ========================================
class DialogoOperario(QDialog):
    def __init__(self, parent=None, operario_id=None):
        super().__init__(parent)
        self.operario_id = operario_id
        self.setWindowTitle("✏️ Editar Operario" if operario_id else "➕ Nuevo Operario")
        self.setFixedSize(500, 280)
        self.setStyleSheet(ESTILO_DIALOGO)
        
        layout = QVBoxLayout(self)
        
        # Formulario
        form = QFormLayout()
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: José Martínez")
        
        self.cmb_rol = QComboBox()
        self.cmb_rol.addItems(["oficial", "ayudante"])
        
        self.chk_activo = QCheckBox("Operario activo")
        self.chk_activo.setChecked(True)
        
        form.addRow("👤 Nombre completo *:", self.txt_nombre)
        form.addRow("🔧 Rol *:", self.cmb_rol)
        form.addRow("", self.chk_activo)
        
        layout.addLayout(form)
        
        # Nota
        nota = QLabel("* Campos obligatorios\n\n"
                     "👷 Oficial: Responsable de la furgoneta y trabajos\n"
                     "🔨 Ayudante: Asiste al oficial")
        nota.setStyleSheet("color: gray; font-size: 11px;")
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
        if self.operario_id:
            self.cargar_datos()
        
        # Focus en el campo de texto
        self.txt_nombre.setFocus()
    
    def cargar_datos(self):
        """Carga los datos del operario a editar"""
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute(
                "SELECT nombre, rol_operario, activo FROM operarios WHERE id=?",
                (self.operario_id,)
            )
            row = cur.fetchone()
            con.close()
            
            if row:
                self.txt_nombre.setText(row[0] or "")
                # Buscar el índice del rol
                idx = self.cmb_rol.findText(row[1])
                if idx >= 0:
                    self.cmb_rol.setCurrentIndex(idx)
                self.chk_activo.setChecked(row[2] == 1)
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar datos:\n{e}")
    
    def guardar(self):
        """Guarda el operario (nuevo o editado)"""
        nombre = self.txt_nombre.text().strip()
        rol = self.cmb_rol.currentText()
        activo = 1 if self.chk_activo.isChecked() else 0
        
        if not nombre:
            QMessageBox.warning(self, "⚠️ Aviso", "El nombre del operario es obligatorio.")
            self.txt_nombre.setFocus()
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            
            if self.operario_id:
                # Editar existente
                cur.execute(
                    "UPDATE operarios SET nombre=?, rol_operario=?, activo=? WHERE id=?",
                    (nombre, rol, activo, self.operario_id)
                )
                mensaje = f"✅ Operario '{nombre}' actualizado correctamente."
            else:
                # Crear nuevo
                cur.execute(
                    "INSERT INTO operarios(nombre, rol_operario, activo) VALUES(?,?,?)",
                    (nombre, rol, activo)
                )
                mensaje = f"✅ Operario '{nombre}' creado correctamente."
            
            con.commit()
            con.close()
            
            QMessageBox.information(self, "✅ Éxito", mensaje)
            self.accept()
            
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "⚠️ Aviso", f"Ya existe un operario con el nombre '{nombre}'.")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al guardar:\n{e}")

# ========================================
# VENTANA PRINCIPAL DE OPERARIOS
# ========================================
class VentanaOperarios(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("👷 Gestión de Operarios")
        self.resize(850, 600)
        self.setMinimumSize(750, 500)
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("👷 Gestión de Operarios")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        # Descripción
        desc = QLabel("Gestiona los técnicos que trabajan en campo (oficiales y ayudantes)")
        desc.setStyleSheet("color: gray; font-size: 12px; margin-bottom: 10px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # Barra de búsqueda y botones superiores
        top_layout = QHBoxLayout()
        
        lbl_buscar = QLabel("🔍 Buscar:")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre...")
        self.txt_buscar.textChanged.connect(self.buscar)
        
        lbl_filtro = QLabel("Filtrar:")
        self.cmb_filtro = QComboBox()
        self.cmb_filtro.addItems(["Todos", "Solo Oficiales", "Solo Ayudantes", "Solo Activos", "Solo Inactivos"])
        self.cmb_filtro.currentTextChanged.connect(self.buscar)
        
        self.btn_nuevo = QPushButton("➕ Nuevo Operario")
        self.btn_nuevo.clicked.connect(self.nuevo_operario)
        
        self.btn_editar = QPushButton("✏️ Editar")
        self.btn_editar.clicked.connect(self.editar_operario)
        self.btn_editar.setEnabled(False)
        
        self.btn_eliminar = QPushButton("🗑️ Eliminar")
        self.btn_eliminar.clicked.connect(self.eliminar_operario)
        self.btn_eliminar.setEnabled(False)
        
        top_layout.addWidget(lbl_buscar)
        top_layout.addWidget(self.txt_buscar)
        top_layout.addWidget(lbl_filtro)
        top_layout.addWidget(self.cmb_filtro)
        top_layout.addWidget(self.btn_nuevo)
        top_layout.addWidget(self.btn_editar)
        top_layout.addWidget(self.btn_eliminar)
        
        layout.addLayout(top_layout)
        
        # Tabla de operarios
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Rol", "Estado"])
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self.seleccion_cambiada)
        self.tabla.doubleClicked.connect(self.editar_operario)
        
        # Ocultar columna ID
        self.tabla.setColumnHidden(0, True)
        
        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Nombre
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Rol
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Estado
        
        layout.addWidget(self.tabla)
        
        # Botón volver
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)
        
        # Cargar datos iniciales
        self.cargar_operarios()
    
    def cargar_operarios(self, filtro_texto="", filtro_tipo="Todos"):
        """Carga los operarios en la tabla"""
        try:
            con = get_con()
            cur = con.cursor()
            
            # Construir query según filtros
            query = "SELECT id, nombre, rol_operario, activo FROM operarios WHERE 1=1"
            params = []
            
            if filtro_texto:
                query += " AND nombre LIKE ?"
                params.append(f"%{filtro_texto}%")
            
            if filtro_tipo == "Solo Oficiales":
                query += " AND rol_operario='oficial'"
            elif filtro_tipo == "Solo Ayudantes":
                query += " AND rol_operario='ayudante'"
            elif filtro_tipo == "Solo Activos":
                query += " AND activo=1"
            elif filtro_tipo == "Solo Inactivos":
                query += " AND activo=0"
            
            query += " ORDER BY rol_operario DESC, nombre"
            
            cur.execute(query, params)
            rows = cur.fetchall()
            con.close()
            
            self.tabla.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                # ID
                self.tabla.setItem(i, 0, QTableWidgetItem(str(row[0])))
                # Nombre
                self.tabla.setItem(i, 1, QTableWidgetItem(row[1]))
                # Rol con emoji
                rol_texto = "👷 Oficial" if row[2] == "oficial" else "🔨 Ayudante"
                item_rol = QTableWidgetItem(rol_texto)
                self.tabla.setItem(i, 2, item_rol)
                # Estado
                estado_texto = "✅ Activo" if row[3] == 1 else "❌ Inactivo"
                item_estado = QTableWidgetItem(estado_texto)
                if row[3] == 0:
                    item_estado.setForeground(Qt.gray)
                self.tabla.setItem(i, 3, item_estado)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar operarios:\n{e}")
    
    def buscar(self):
        """Filtra la tabla según el texto de búsqueda y filtros"""
        filtro_texto = self.txt_buscar.text().strip()
        filtro_tipo = self.cmb_filtro.currentText()
        self.cargar_operarios(filtro_texto, filtro_tipo)
    
    def seleccion_cambiada(self):
        """Se activan/desactivan botones según la selección"""
        hay_seleccion = len(self.tabla.selectedItems()) > 0
        self.btn_editar.setEnabled(hay_seleccion)
        self.btn_eliminar.setEnabled(hay_seleccion)
    
    def nuevo_operario(self):
        """Abre el diálogo para crear un nuevo operario"""
        dialogo = DialogoOperario(self)
        if dialogo.exec():
            self.cargar_operarios()
    
    def editar_operario(self):
        """Abre el diálogo para editar el operario seleccionado"""
        seleccion = self.tabla.currentRow()
        if seleccion < 0:
            return
        
        operario_id = int(self.tabla.item(seleccion, 0).text())
        dialogo = DialogoOperario(self, operario_id)
        if dialogo.exec():
            self.cargar_operarios()
    
    def eliminar_operario(self):
        """Elimina el operario seleccionado"""
        seleccion = self.tabla.currentRow()
        if seleccion < 0:
            return
        
        operario_id = int(self.tabla.item(seleccion, 0).text())
        nombre = self.tabla.item(seleccion, 1).text()
        
        # Confirmar eliminación
        respuesta = QMessageBox.question(
            self,
            "⚠️ Confirmar eliminación",
            f"¿Está seguro de eliminar el operario '{nombre}'?\n\n"
            "Esta acción no se puede deshacer.\n"
            "Si el operario tiene movimientos registrados, no podrá eliminarse.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if respuesta != QMessageBox.Yes:
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("DELETE FROM operarios WHERE id=?", (operario_id,))
            con.commit()
            con.close()
            
            QMessageBox.information(self, "✅ Éxito", f"Operario '{nombre}' eliminado correctamente.")
            self.cargar_operarios()
            
        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self, 
                "⚠️ No se puede eliminar",
                f"El operario '{nombre}' tiene movimientos o asignaciones asociadas.\n\n"
                "En lugar de eliminarlo, puede marcarlo como 'Inactivo' editándolo."
            )
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al eliminar:\n{e}")