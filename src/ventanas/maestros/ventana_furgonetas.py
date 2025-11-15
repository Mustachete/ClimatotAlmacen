# ventana_furgonetas.py - Gestión de Furgonetas y Asignaciones
from PySide6.QtWidgets import (
    QTableWidgetItem, QLineEdit, QTextEdit, QHeaderView, QSpinBox, QCheckBox,
    QDateEdit, QGroupBox, QComboBox, QLabel
)
from PySide6.QtCore import Qt, QDate
from datetime import date
from src.ui.dialogo_maestro_base import DialogoMaestroBase
from src.ui.ventana_maestro_base import VentanaMaestroBase
from src.services.furgonetas_service import (
    boot, list_furgonetas, baja_furgoneta, furgonetas_service_wrapper
)
from src.repos.operarios_repo import get_todos as get_todos_operarios
from src.utils import validaciones

# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR FURGONETA
# ========================================
class DialogoFurgoneta(DialogoMaestroBase):
    def __init__(self, parent=None, furgoneta_id=None):
        super().__init__(
            parent=parent,
            item_id=furgoneta_id,
            titulo_nuevo="🚐 Nueva Furgoneta",
            titulo_editar="✏️ Editar Furgoneta",
            service=furgonetas_service_wrapper,
            nombre_item="furgoneta"
        )

    def configurar_dimensiones(self):
        """Personaliza dimensiones del diálogo"""
        self.setMinimumSize(450, 450)
        self.resize(500, 500)

    def crear_formulario(self, form_layout):
        """Crea los campos del formulario"""
        self.spin_numero = QSpinBox()
        self.spin_numero.setRange(0, 999)
        self.spin_numero.setValue(0)
        self.spin_numero.setSpecialValueText("Sin asignar")

        self.txt_matricula = QLineEdit()
        self.txt_matricula.setPlaceholderText("Ej: 1234-ABC")

        self.txt_marca = QLineEdit()
        self.txt_marca.setPlaceholderText("Ej: Ford, Mercedes...")

        self.txt_modelo = QLineEdit()
        self.txt_modelo.setPlaceholderText("Ej: Transit, Sprinter...")

        self.spin_anio = QSpinBox()
        self.spin_anio.setRange(1990, 2100)
        self.spin_anio.setValue(date.today().year)

        self.chk_activa = QCheckBox("Furgoneta activa")
        self.chk_activa.setChecked(True)

        self.txt_notas = QTextEdit()
        self.txt_notas.setMaximumHeight(100)
        self.txt_notas.setPlaceholderText("Observaciones, estado, etc.")

        form_layout.addRow("🔢 Número:", self.spin_numero)
        form_layout.addRow("🚗 Matrícula *:", self.txt_matricula)
        form_layout.addRow("🏭 Marca:", self.txt_marca)
        form_layout.addRow("📋 Modelo:", self.txt_modelo)
        form_layout.addRow("📅 Año:", self.spin_anio)
        form_layout.addRow("", self.chk_activa)
        form_layout.addRow("📝 Notas:", self.txt_notas)

    def obtener_datos_formulario(self):
        """Obtiene los datos del formulario"""
        numero = self.spin_numero.value() if self.spin_numero.value() > 0 else None
        return {
            'numero': numero,
            'matricula': self.txt_matricula.text().strip(),
            'marca': self.txt_marca.text().strip() or None,
            'modelo': self.txt_modelo.text().strip() or None,
            'anio': self.spin_anio.value(),
            'activa': self.chk_activa.isChecked(),
            'notas': self.txt_notas.toPlainText().strip() or None
        }

    def validar_datos(self, datos):
        """Valida los datos del formulario"""
        return validaciones.validar_campo_obligatorio(datos.get('matricula', ''), 'matrícula')

    def cargar_datos_en_formulario(self, item_data):
        """Personaliza carga de datos para spinboxes, checkbox y textarea"""
        super().cargar_datos_en_formulario(item_data)

        # Cargar número
        if 'numero' in item_data and item_data['numero'] is not None:
            self.spin_numero.setValue(int(item_data['numero']))

        # Cargar año
        if 'anio' in item_data and item_data['anio'] is not None:
            self.spin_anio.setValue(int(item_data['anio']))

        # Cargar estado activa
        if 'activa' in item_data:
            self.chk_activa.setChecked(bool(item_data['activa']))

        # Cargar notas
        if 'notas' in item_data:
            self.txt_notas.setPlainText(item_data['notas'] or "")


# ========================================
# WRAPPER DE SERVICE PARA COMPATIBILIDAD
# ========================================
class FurgonetasServiceWrapper:
    """Wrapper para adaptar las funciones del service al patrón esperado por VentanaMaestroBase"""

    def obtener_furgonetas(self, filtro_texto=None, limit=1000):
        """Retorna todas las furgonetas (el service no soporta filtros por ahora)"""
        return list_furgonetas()

    def eliminar_furgoneta(self, furgoneta_id, usuario=None):
        """Elimina una furgoneta"""
        try:
            baja_furgoneta(furgoneta_id)
            return True, "Furgoneta eliminada correctamente"
        except Exception as e:
            return False, f"Error al eliminar: {e}"


# Instancia global del wrapper
_furgonetas_service_wrapper = FurgonetasServiceWrapper()


# ========================================
# VENTANA PRINCIPAL: GESTIÓN DE FURGONETAS
# ========================================
class VentanaFurgonetas(VentanaMaestroBase):
    def __init__(self, parent=None):
        # Asegurar esquema de base de datos
        boot()

        super().__init__(
            titulo="🚐 Gestión de Furgonetas",
            descripcion="Administra las furgonetas de la empresa",
            icono_nuevo="➕",
            texto_nuevo="Nueva Furgoneta",
            parent=parent
        )

    def configurar_dimensiones(self):
        """Configura las dimensiones específicas para esta ventana"""
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)

    def configurar_tabla(self):
        """Configura las columnas de la tabla de furgonetas"""
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Nº", "Matrícula", "Marca", "Modelo", "Año", "Activa", "Notas"
        ])
        self.tabla.setColumnHidden(0, True)

        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Nº
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Matrícula
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Marca
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Modelo
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Año
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Activa
        header.setSectionResizeMode(7, QHeaderView.Stretch)  # Notas

    def get_service(self):
        """Retorna el wrapper del service de furgonetas"""
        return _furgonetas_service_wrapper

    def crear_dialogo(self, item_id=None):
        """Crea el diálogo para crear/editar una furgoneta"""
        return DialogoFurgoneta(self, item_id)

    def get_nombre_item(self, fila):
        """Retorna la matrícula para mostrar en mensajes"""
        return self.tabla.item(fila, 2).text()  # Columna 2 = Matrícula

    def cargar_datos_en_tabla(self, datos):
        """Carga las furgonetas en la tabla con formato especial"""
        self.tabla.setRowCount(len(datos))

        for i, furgoneta in enumerate(datos):
            # ID
            self.tabla.setItem(i, 0, QTableWidgetItem(str(furgoneta['id'])))

            # Número
            numero_text = str(furgoneta.get('numero', '')) if furgoneta.get('numero') else ''
            self.tabla.setItem(i, 1, QTableWidgetItem(numero_text))

            # Matrícula
            self.tabla.setItem(i, 2, QTableWidgetItem(furgoneta.get('matricula', '')))

            # Marca
            self.tabla.setItem(i, 3, QTableWidgetItem(furgoneta.get('marca', '') or ''))

            # Modelo
            self.tabla.setItem(i, 4, QTableWidgetItem(furgoneta.get('modelo', '') or ''))

            # Año
            anio_text = str(furgoneta.get('anio', '')) if furgoneta.get('anio') else ''
            self.tabla.setItem(i, 5, QTableWidgetItem(anio_text))

            # Activa (con color)
            activa_text = "✅ Sí" if furgoneta.get('activa') else "❌ No"
            item_activa = QTableWidgetItem(activa_text)
            if not furgoneta.get('activa'):
                item_activa.setForeground(Qt.red)
            self.tabla.setItem(i, 6, item_activa)

            # Notas
            self.tabla.setItem(i, 7, QTableWidgetItem(furgoneta.get('notas', '') or ''))

