# ventana_furgonetas.py - Gestión de Furgonetas y Asignaciones
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QTextEdit, QHeaderView, QSpinBox, QCheckBox, QDateEdit, QGroupBox, QComboBox
)
from PySide6.QtCore import Qt, QDate
from datetime import date
from src.ui.estilos import ESTILO_DIALOGO
from src.ui.ventana_maestro_base import VentanaMaestroBase
from src.services.furgonetas_service import (
    boot, list_furgonetas, alta_furgoneta, modificar_furgoneta, baja_furgoneta
)
from src.repos.operarios_repo import get_todos as get_todos_operarios
from src.core.session_manager import session_manager

# ========================================
# DIÁLOGO PARA AÑADIR/EDITAR FURGONETA
# ========================================
class DialogoFurgoneta(QDialog):
    def __init__(self, parent=None, furgoneta_id=None):
        super().__init__(parent)
        self.furgoneta_id = furgoneta_id
        self.setWindowTitle("Editar Furgoneta" if furgoneta_id else "Nueva Furgoneta")
        self.setMinimumSize(450, 400)
        self.resize(500, 450)
        self.setStyleSheet(ESTILO_DIALOGO)

        layout = QVBoxLayout(self)

        # Formulario
        form = QFormLayout()

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

        form.addRow("Número:", self.spin_numero)
        form.addRow("Matrícula *:", self.txt_matricula)
        form.addRow("Marca:", self.txt_marca)
        form.addRow("Modelo:", self.txt_modelo)
        form.addRow("Año:", self.spin_anio)
        form.addRow("Estado:", self.chk_activa)
        form.addRow("Notas:", self.txt_notas)

        layout.addLayout(form)

        # Nota obligatorio
        nota = QLabel("* Campos obligatorios")
        nota.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(nota)

        # Botones
        layout.addStretch()
        btn_layout = QHBoxLayout()

        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.clicked.connect(self.guardar)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)

        # Si estamos editando, cargar datos
        if self.furgoneta_id:
            self.cargar_datos()

    def cargar_datos(self):
        """Carga los datos de la furgoneta a editar"""
        try:
            furgonetas = list_furgonetas()
            furgoneta = next((f for f in furgonetas if f['id'] == self.furgoneta_id), None)

            if furgoneta:
                if furgoneta.get('numero'):
                    self.spin_numero.setValue(int(furgoneta['numero']))
                self.txt_matricula.setText(furgoneta.get('matricula', ''))
                self.txt_marca.setText(furgoneta.get('marca', '') or '')
                self.txt_modelo.setText(furgoneta.get('modelo', '') or '')
                if furgoneta.get('anio'):
                    self.spin_anio.setValue(int(furgoneta['anio']))
                self.chk_activa.setChecked(bool(furgoneta.get('activa', True)))
                self.txt_notas.setPlainText(furgoneta.get('notas', '') or '')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar datos:\n{e}")

    def guardar(self):
        """Guarda la furgoneta (nueva o editada)"""
        matricula = self.txt_matricula.text().strip()

        if not matricula:
            QMessageBox.warning(self, "Validación", "La matrícula es obligatoria.")
            return

        numero = self.spin_numero.value() if self.spin_numero.value() > 0 else None
        marca = self.txt_marca.text().strip() or None
        modelo = self.txt_modelo.text().strip() or None
        anio = self.spin_anio.value()
        activa = 1 if self.chk_activa.isChecked() else 0
        notas = self.txt_notas.toPlainText().strip() or None

        # Validar que el número no esté duplicado
        if numero is not None:
            furgonetas = list_furgonetas()
            for f in furgonetas:
                # Si estamos editando, excluir la furgoneta actual
                if f['id'] != self.furgoneta_id and f.get('numero') == numero:
                    QMessageBox.warning(
                        self,
                        "Validación",
                        f"El número {numero} ya está asignado a otra furgoneta.\nPor favor, elige otro número."
                    )
                    return

        try:
            if self.furgoneta_id:
                # Editar existente
                modificar_furgoneta(
                    self.furgoneta_id,
                    numero=numero,
                    matricula=matricula,
                    marca=marca,
                    modelo=modelo,
                    anio=anio,
                    activa=activa,
                    notas=notas
                )
                QMessageBox.information(self, "Éxito", "Furgoneta actualizada correctamente")
            else:
                # Nueva furgoneta
                alta_furgoneta(matricula, marca, modelo, anio, notas, numero)
                QMessageBox.information(self, "Éxito", "Furgoneta creada correctamente")

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar:\n{e}")


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

