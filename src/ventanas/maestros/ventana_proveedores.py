# ventana_proveedores.py - Gestión de Proveedores
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QTextEdit, QHeaderView
)
from PySide6.QtCore import Qt
from src.ui.estilos import ESTILO_DIALOGO, ESTILO_VENTANA
from src.services import proveedores_service
from src.core.session_manager import session_manager

# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR PROVEEDOR
# ========================================
class DialogoProveedor(QDialog):
    def __init__(self, parent=None, proveedor_id=None):
        super().__init__(parent)
        self.proveedor_id = proveedor_id
        self.setWindowTitle("✏️ Editar Proveedor" if proveedor_id else "➕ Nuevo Proveedor")
        self.setMinimumSize(450, 350)
        self.resize(500, 400)
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

        # Configurar teclas rápidas
        self.btn_guardar.setDefault(True)  # Return = Guardar
        self.btn_cancelar.setShortcut("Esc")  # Esc = Cancelar

        # Si estamos editando, cargar datos
        if self.proveedor_id:
            self.cargar_datos()

        # Focus inicial
        self.txt_nombre.setFocus()

    def cargar_datos(self):
        """Carga los datos del proveedor a editar"""
        try:
            proveedor = proveedores_service.obtener_proveedor(self.proveedor_id)

            if proveedor:
                self.txt_nombre.setText(proveedor['nombre'] or "")
                self.txt_telefono.setText(proveedor['telefono'] or "")
                self.txt_contacto.setText(proveedor['contacto'] or "")
                self.txt_email.setText(proveedor['email'] or "")
                self.txt_notas.setPlainText(proveedor['notas'] or "")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar datos:\n{e}")
    
    def guardar(self):
        """Guarda el proveedor (nuevo o editado)"""
        nombre = self.txt_nombre.text().strip()
        telefono = self.txt_telefono.text().strip() or None
        contacto = self.txt_contacto.text().strip() or None
        email = self.txt_email.text().strip() or None
        notas = self.txt_notas.toPlainText().strip() or None

        # Llamar al service
        if self.proveedor_id:
            # Editar existente
            exito, mensaje = proveedores_service.actualizar_proveedor(
                proveedor_id=self.proveedor_id,
                nombre=nombre,
                telefono=telefono,
                contacto=contacto,
                email=email,
                notas=notas,
                usuario=session_manager.get_usuario_actual() or "admin"
            )
        else:
            # Crear nuevo
            exito, mensaje, proveedor_id = proveedores_service.crear_proveedor(
                nombre=nombre,
                telefono=telefono,
                contacto=contacto,
                email=email,
                notas=notas,
                usuario=session_manager.get_usuario_actual() or "admin"
            )

        if not exito:
            QMessageBox.warning(self, "⚠️ Error", mensaje)
            return

        QMessageBox.information(self, "✅ Éxito", mensaje)
        self.accept()

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
            filtro_texto = filtro if filtro else None

            proveedores = proveedores_service.obtener_proveedores(
                filtro_texto=filtro_texto,
                limit=1000
            )

            self.tabla.setRowCount(len(proveedores))

            for i, prov in enumerate(proveedores):
                self.tabla.setItem(i, 0, QTableWidgetItem(str(prov['id'])))
                self.tabla.setItem(i, 1, QTableWidgetItem(prov['nombre'] or ""))
                self.tabla.setItem(i, 2, QTableWidgetItem(prov['telefono'] or ""))
                self.tabla.setItem(i, 3, QTableWidgetItem(prov['contacto'] or ""))
                self.tabla.setItem(i, 4, QTableWidgetItem(prov['email'] or ""))
                self.tabla.setItem(i, 5, QTableWidgetItem(prov['notas'] or ""))

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

        # Llamar al service
        exito, mensaje = proveedores_service.eliminar_proveedor(
            proveedor_id=proveedor_id,
            usuario=session_manager.get_usuario_actual() or "admin"
        )

        if not exito:
            QMessageBox.warning(self, "⚠️ No se puede eliminar", mensaje)
            return

        QMessageBox.information(self, "✅ Éxito", mensaje)
        self.cargar_proveedores()