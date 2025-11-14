# ventana_familias.py - Gestión de Familias de Artículos
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QHeaderView
)
from PySide6.QtCore import Qt
from src.ui.estilos import ESTILO_DIALOGO, ESTILO_VENTANA
from src.services import familias_service
from src.core.session_manager import session_manager

# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR FAMILIA
# ========================================
class DialogoFamilia(QDialog):
    def __init__(self, parent=None, familia_id=None):
        super().__init__(parent)
        self.familia_id = familia_id
        self.setWindowTitle("✏️ Editar Familia" if familia_id else "➕ Nueva Familia")
        self.setMinimumSize(400, 180)
        self.resize(450, 200)
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
            familia = familias_service.obtener_familia(self.familia_id)
            if familia:
                self.txt_nombre.setText(familia['nombre'] or "")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar datos:\n{e}")
    
    def guardar(self):
        """Guarda la familia (nueva o editada)"""
        nombre = self.txt_nombre.text().strip()

        if self.familia_id:
            exito, mensaje = familias_service.actualizar_familia(
                familia_id=self.familia_id,
                nombre=nombre,
                usuario=session_manager.get_usuario_actual() or "admin"
            )
        else:
            exito, mensaje, familia_id = familias_service.crear_familia(
                nombre=nombre,
                usuario=session_manager.get_usuario_actual() or "admin"
            )

        if not exito:
            QMessageBox.warning(self, "⚠️ Error", mensaje)
            return

        QMessageBox.information(self, "✅ Éxito", mensaje)
        self.accept()

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
            filtro_texto = filtro if filtro else None
            familias = familias_service.obtener_familias(filtro_texto=filtro_texto, limit=1000)

            self.tabla.setRowCount(len(familias))

            for i, fam in enumerate(familias):
                self.tabla.setItem(i, 0, QTableWidgetItem(str(fam['id'])))
                self.tabla.setItem(i, 1, QTableWidgetItem(fam['nombre'] or ""))

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

        exito, mensaje = familias_service.eliminar_familia(
            familia_id=familia_id,
            usuario=session_manager.get_usuario_actual() or "admin"
        )

        if not exito:
            QMessageBox.warning(self, "⚠️ No se puede eliminar", mensaje)
            return

        QMessageBox.information(self, "✅ Éxito", mensaje)
        self.cargar_familias()