# ventana_familias.py - Gestión de Familias de Artículos
from PySide6.QtWidgets import (
    QTableWidgetItem, QLineEdit, QHeaderView
)
from src.ui.dialogo_maestro_base import DialogoMaestroBase
from src.ui.ventana_maestro_base import VentanaMaestroBase
from src.services import familias_service
from src.utils import validaciones

# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR FAMILIA
# ========================================
class DialogoFamilia(DialogoMaestroBase):
    def __init__(self, parent=None, familia_id=None):
        super().__init__(
            parent=parent,
            item_id=familia_id,
            titulo_nuevo="➕ Nueva Familia",
            titulo_editar="✏️ Editar Familia",
            service=familias_service,
            nombre_item="familia"
        )

    def configurar_dimensiones(self):
        """Personaliza dimensiones del diálogo"""
        self.setMinimumSize(400, 180)
        self.resize(450, 200)

    def crear_formulario(self, form_layout):
        """Crea los campos del formulario"""
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Calefacción, Climatización...")
        form_layout.addRow("📂 Nombre de la Familia *:", self.txt_nombre)

    def obtener_datos_formulario(self):
        """Obtiene los datos del formulario"""
        return {'nombre': self.txt_nombre.text().strip()}

    def validar_datos(self, datos):
        """Valida los datos del formulario usando validaciones centralizadas"""
        return validaciones.validar_campo_obligatorio(datos.get('nombre', ''), 'nombre de familia')

# ========================================
# VENTANA PRINCIPAL DE FAMILIAS
# ========================================
class VentanaFamilias(VentanaMaestroBase):
    def __init__(self, parent=None):
        super().__init__(
            titulo="📂 Gestión de Familias de Artículos",
            descripcion="Las familias sirven para categorizar y organizar los artículos del almacén",
            icono_nuevo="➕",
            texto_nuevo="Nueva Familia",
            parent=parent
        )

    def configurar_dimensiones(self):
        """Configura las dimensiones específicas para esta ventana"""
        self.resize(700, 500)
        self.setMinimumSize(600, 400)

    def configurar_tabla(self):
        """Configura las columnas de la tabla de familias"""
        self.tabla.setColumnCount(2)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre"])
        self.tabla.setColumnHidden(0, True)

        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)

    def get_service(self):
        """Retorna el service de familias"""
        return familias_service

    def crear_dialogo(self, item_id=None):
        """Crea el diálogo para crear/editar una familia"""
        return DialogoFamilia(self, item_id)

    def cargar_datos_en_tabla(self, datos):
        """Carga las familias en la tabla"""
        self.tabla.setRowCount(len(datos))
        for i, fam in enumerate(datos):
            self.tabla.setItem(i, 0, QTableWidgetItem(str(fam['id'])))
            self.tabla.setItem(i, 1, QTableWidgetItem(fam['nombre'] or ""))