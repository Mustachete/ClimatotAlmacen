# ventana_ubicaciones.py - Gestión de Ubicaciones del Almacén
from PySide6.QtWidgets import (
    QTableWidgetItem, QLineEdit, QHeaderView
)
from src.ui.dialogo_maestro_base import DialogoMaestroBase
from src.ui.ventana_maestro_base import VentanaMaestroBase
from src.services import ubicaciones_service
from src.utils import validaciones

# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR UBICACIÓN
# ========================================
class DialogoUbicacion(DialogoMaestroBase):
    def __init__(self, parent=None, ubicacion_id=None):
        super().__init__(
            parent=parent,
            item_id=ubicacion_id,
            titulo_nuevo="➕ Nueva Ubicación",
            titulo_editar="✏️ Editar Ubicación",
            service=ubicaciones_service,
            nombre_item="ubicacion"
        )

    def configurar_dimensiones(self):
        """Personaliza dimensiones del diálogo"""
        self.setMinimumSize(400, 180)
        self.resize(450, 200)

    def crear_formulario(self, form_layout):
        """Crea los campos del formulario"""
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: A1, B2, Estantería 5...")
        form_layout.addRow("📍 Código/Nombre de Ubicación *:", self.txt_nombre)

    def obtener_datos_formulario(self):
        """Obtiene los datos del formulario"""
        return {'nombre': self.txt_nombre.text().strip()}

    def validar_datos(self, datos):
        """Valida los datos del formulario"""
        return validaciones.validar_campo_obligatorio(datos.get('nombre', ''), 'nombre de ubicación')

# ========================================
# VENTANA PRINCIPAL DE UBICACIONES
# ========================================
class VentanaUbicaciones(VentanaMaestroBase):
    def __init__(self, parent=None):
        super().__init__(
            titulo="📍 Gestión de Ubicaciones del Almacén",
            descripcion="Las ubicaciones sirven para identificar dónde está físicamente cada artículo en el almacén",
            icono_nuevo="➕",
            texto_nuevo="Nueva Ubicación",
            parent=parent
        )

    def configurar_dimensiones(self):
        """Configura las dimensiones específicas para esta ventana"""
        self.resize(700, 500)
        self.setMinimumSize(600, 400)

    def configurar_tabla(self):
        """Configura las columnas de la tabla de ubicaciones"""
        self.tabla.setColumnCount(2)
        self.tabla.setHorizontalHeaderLabels(["ID", "Ubicación"])
        self.tabla.setColumnHidden(0, True)

        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)

    def get_service(self):
        """Retorna el service de ubicaciones"""
        return ubicaciones_service

    def crear_dialogo(self, item_id=None):
        """Crea el diálogo para crear/editar una ubicación"""
        return DialogoUbicacion(self, item_id)

    def cargar_datos_en_tabla(self, datos):
        """Carga las ubicaciones en la tabla"""
        self.tabla.setRowCount(len(datos))
        for i, ubi in enumerate(datos):
            self.tabla.setItem(i, 0, QTableWidgetItem(str(ubi['id'])))
            self.tabla.setItem(i, 1, QTableWidgetItem(ubi['nombre'] or ""))