# ventana_operarios.py - Gestión de Operarios
from PySide6.QtWidgets import (
    QTableWidgetItem, QLineEdit, QLabel, QHeaderView, QComboBox, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from src.ui.dialogo_maestro_base import DialogoMaestroBase
from src.ui.ventana_maestro_base import VentanaMaestroBase
from src.services import operarios_service
from src.utils import validaciones

# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR OPERARIO
# ========================================
class DialogoOperario(DialogoMaestroBase):
    def __init__(self, parent=None, operario_id=None):
        super().__init__(
            parent=parent,
            item_id=operario_id,
            titulo_nuevo="➕ Nuevo Operario",
            titulo_editar="✏️ Editar Operario",
            service=operarios_service,
            nombre_item="operario",
            mostrar_nota_obligatorios=False  # Usamos nota personalizada
        )

    def configurar_dimensiones(self):
        """Personaliza dimensiones del diálogo"""
        self.setMinimumSize(450, 300)
        self.resize(500, 350)

    def crear_formulario(self, form_layout):
        """Crea los campos del formulario"""
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: José Martínez")

        self.cmb_rol = QComboBox()
        self.cmb_rol.addItems(["oficial", "ayudante"])

        self.chk_activo = QCheckBox("Operario activo")
        self.chk_activo.setChecked(True)

        form_layout.addRow("👤 Nombre completo *:", self.txt_nombre)
        form_layout.addRow("🔧 Rol *:", self.cmb_rol)
        form_layout.addRow("", self.chk_activo)

        # Nota personalizada explicativa
        nota = QLabel("* Campos obligatorios\n\n"
                     "👷 Oficial: Responsable de la furgoneta y trabajos\n"
                     "🔨 Ayudante: Asiste al oficial")
        nota.setStyleSheet("color: gray; font-size: 11px;")
        form_layout.addRow("", nota)

    def obtener_datos_formulario(self):
        """Obtiene los datos del formulario"""
        return {
            'nombre': self.txt_nombre.text().strip(),
            'rol_operario': self.cmb_rol.currentText(),
            'activo': self.chk_activo.isChecked()
        }

    def validar_datos(self, datos):
        """Valida los datos del formulario"""
        return validaciones.validar_campo_obligatorio(datos.get('nombre', ''), 'nombre')

    def cargar_datos_en_formulario(self, item_data):
        """Personaliza carga de datos para combo y checkbox"""
        super().cargar_datos_en_formulario(item_data)

        # Cargar rol en combo
        if 'rol_operario' in item_data:
            idx = self.cmb_rol.findText(item_data['rol_operario'])
            if idx >= 0:
                self.cmb_rol.setCurrentIndex(idx)

        # Cargar estado activo
        if 'activo' in item_data:
            self.chk_activo.setChecked(item_data['activo'] == 1)

# ========================================
# VENTANA PRINCIPAL DE OPERARIOS
# ========================================
class VentanaOperarios(VentanaMaestroBase):
    def __init__(self, parent=None):
        # Crear ComboBox de filtros antes de llamar a super()
        self.cmb_filtro = None

        super().__init__(
            titulo="👷 Gestión de Operarios",
            descripcion="Gestiona los técnicos que trabajan en campo (oficiales y ayudantes)",
            icono_nuevo="➕",
            texto_nuevo="Nuevo Operario",
            parent=parent
        )

    def configurar_dimensiones(self):
        """Configura las dimensiones específicas para esta ventana"""
        self.resize(850, 600)
        self.setMinimumSize(750, 500)

    def _crear_interfaz(self):
        """Crea la interfaz con filtros adicionales"""
        # Primero llamamos al método padre para crear la estructura base
        super()._crear_interfaz()

        # Ahora agregamos el filtro adicional en la barra superior
        # Necesitamos acceder al layout superior que ya creó el padre
        # Lo insertamos antes de los botones

        # Obtener el layout principal
        layout_principal = self.layout()

        # El top_layout es el segundo widget (después del título y descripción)
        # Usamos itemAt para acceder a los layouts
        top_layout = layout_principal.itemAt(2).layout()  # Índice 2 = barra superior

        # Insertar el combo de filtros antes del botón "Nuevo"
        lbl_filtro = QLabel("Filtrar:")
        self.cmb_filtro = QComboBox()
        self.cmb_filtro.addItems(["Todos", "Solo Oficiales", "Solo Ayudantes", "Solo Activos", "Solo Inactivos"])
        self.cmb_filtro.currentTextChanged.connect(self.buscar)

        # Insertar en la posición 2 (después de lbl_buscar y txt_buscar)
        top_layout.insertWidget(2, lbl_filtro)
        top_layout.insertWidget(3, self.cmb_filtro)

    def configurar_tabla(self):
        """Configura las columnas de la tabla de operarios"""
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Rol", "Estado"])
        self.tabla.setColumnHidden(0, True)

        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Nombre
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Rol
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Estado

    def get_service(self):
        """Retorna el service de operarios"""
        return operarios_service

    def crear_dialogo(self, item_id=None):
        """Crea el diálogo para crear/editar un operario"""
        return DialogoOperario(self, item_id)

    def cargar_datos(self, filtro=""):
        """Sobrescribe para manejar filtros adicionales"""
        filtro_tipo = self.cmb_filtro.currentText() if self.cmb_filtro else "Todos"

        # Preparar filtros
        filtro_texto_param = filtro if filtro else None

        solo_rol = None
        if filtro_tipo == "Solo Oficiales":
            solo_rol = "oficial"
        elif filtro_tipo == "Solo Ayudantes":
            solo_rol = "ayudante"

        solo_activos = None
        if filtro_tipo == "Solo Activos":
            solo_activos = True
        elif filtro_tipo == "Solo Inactivos":
            solo_activos = False

        # Obtener operarios con filtros
        try:
            operarios = operarios_service.obtener_operarios(
                filtro_texto=filtro_texto_param,
                solo_rol=solo_rol,
                solo_activos=solo_activos,
                limit=1000
            )
            self.cargar_datos_en_tabla(operarios)
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar operarios:\n{e}")

    def cargar_datos_en_tabla(self, datos):
        """Carga los operarios en la tabla con formato especial"""
        self.tabla.setRowCount(len(datos))

        for i, oper in enumerate(datos):
            # ID
            self.tabla.setItem(i, 0, QTableWidgetItem(str(oper['id'])))
            # Nombre
            self.tabla.setItem(i, 1, QTableWidgetItem(oper['nombre']))
            # Rol con emoji
            rol_texto = "👷 Oficial" if oper['rol_operario'] == "oficial" else "🔨 Ayudante"
            item_rol = QTableWidgetItem(rol_texto)
            self.tabla.setItem(i, 2, item_rol)
            # Estado
            estado_texto = "✅ Activo" if oper['activo'] == 1 else "❌ Inactivo"
            item_estado = QTableWidgetItem(estado_texto)
            if oper['activo'] == 0:
                item_estado.setForeground(Qt.gray)
            self.tabla.setItem(i, 3, item_estado)