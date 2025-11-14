# ventana_proveedores.py - Gestión de Proveedores
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QTextEdit, QHeaderView
)
from src.ui.estilos import ESTILO_DIALOGO
from src.ui.ventana_maestro_base import VentanaMaestroBase
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
class VentanaProveedores(VentanaMaestroBase):
    def __init__(self, parent=None):
        super().__init__(
            titulo="🏭 Gestión de Proveedores",
            descripcion="Administra los proveedores del almacén",
            icono_nuevo="➕",
            texto_nuevo="Nuevo Proveedor",
            parent=parent
        )

    def configurar_dimensiones(self):
        """Configura las dimensiones específicas para esta ventana"""
        self.setFixedSize(950, 650)

    def configurar_tabla(self):
        """Configura las columnas de la tabla de proveedores"""
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Teléfono", "Contacto", "Email", "Notas"])
        self.tabla.setColumnHidden(0, True)

        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Nombre
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Teléfono
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Contacto
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Email
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Notas

    def get_service(self):
        """Retorna el service de proveedores"""
        return proveedores_service

    def crear_dialogo(self, item_id=None):
        """Crea el diálogo para crear/editar un proveedor"""
        return DialogoProveedor(self, item_id)

    def cargar_datos_en_tabla(self, datos):
        """Carga los proveedores en la tabla"""
        self.tabla.setRowCount(len(datos))
        for i, prov in enumerate(datos):
            self.tabla.setItem(i, 0, QTableWidgetItem(str(prov['id'])))
            self.tabla.setItem(i, 1, QTableWidgetItem(prov['nombre'] or ""))
            self.tabla.setItem(i, 2, QTableWidgetItem(prov['telefono'] or ""))
            self.tabla.setItem(i, 3, QTableWidgetItem(prov['contacto'] or ""))
            self.tabla.setItem(i, 4, QTableWidgetItem(prov['email'] or ""))
            self.tabla.setItem(i, 5, QTableWidgetItem(prov['notas'] or ""))