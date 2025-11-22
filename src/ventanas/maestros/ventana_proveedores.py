# ventana_proveedores.py - Gestión de Proveedores
from PySide6.QtWidgets import (
    QTableWidgetItem, QLineEdit, QTextEdit, QHeaderView
)
from src.ui.dialogo_maestro_base import DialogoMaestroBase
from src.ui.ventana_maestro_base import VentanaMaestroBase
from src.services import proveedores_service
from src.utils import validaciones

# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR PROVEEDOR
# ========================================
class DialogoProveedor(DialogoMaestroBase):
    def __init__(self, parent=None, proveedor_id=None):
        super().__init__(
            parent=parent,
            item_id=proveedor_id,
            titulo_nuevo="➕ Nuevo Proveedor",
            titulo_editar="✏️ Editar Proveedor",
            service=proveedores_service,
            nombre_item="proveedor"
        )

    def configurar_dimensiones(self):
        """Personaliza dimensiones del diálogo"""
        self.setMinimumSize(450, 350)
        self.resize(500, 400)

    def crear_formulario(self, form_layout):
        """Crea los campos del formulario"""
        self.txt_nombre = QLineEdit()
        self.txt_telefono = QLineEdit()
        self.txt_contacto = QLineEdit()
        self.txt_email = QLineEdit()
        self.txt_notas = QTextEdit()
        self.txt_notas.setMaximumHeight(100)

        form_layout.addRow("📛 Nombre *:", self.txt_nombre)
        form_layout.addRow("📞 Teléfono:", self.txt_telefono)
        form_layout.addRow("👤 Contacto:", self.txt_contacto)
        form_layout.addRow("📧 Email:", self.txt_email)
        form_layout.addRow("📝 Notas:", self.txt_notas)

    def obtener_datos_formulario(self):
        """Obtiene los datos del formulario"""
        return {
            'nombre': self.txt_nombre.text().strip(),
            'telefono': self.txt_telefono.text().strip() or None,
            'contacto': self.txt_contacto.text().strip() or None,
            'email': self.txt_email.text().strip() or None,
            'notas': self.txt_notas.toPlainText().strip() or None
        }

    def validar_datos(self, datos):
        """Valida los datos del formulario usando validaciones centralizadas"""
        # Validar nombre obligatorio
        valido, mensaje = validaciones.validar_campo_obligatorio(datos.get('nombre', ''), 'nombre')
        if not valido:
            return False, mensaje

        # Validar email si se proporcionó
        if datos.get('email'):
            valido, mensaje = validaciones.validar_email(datos['email'])
            if not valido:
                return False, mensaje

        # Validar teléfono si se proporcionó
        if datos.get('telefono'):
            valido, mensaje = validaciones.validar_telefono(datos['telefono'])
            if not valido:
                return False, mensaje

        return True, ""

    def cargar_datos_en_formulario(self, item_data):
        """Personaliza carga de datos para el campo notas (QTextEdit)"""
        super().cargar_datos_en_formulario(item_data)
        # El QTextEdit usa setPlainText en lugar de setText
        if 'notas' in item_data:
            self.txt_notas.setPlainText(item_data['notas'] or "")

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