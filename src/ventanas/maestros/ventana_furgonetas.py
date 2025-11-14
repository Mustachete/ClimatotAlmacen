# ventana_furgonetas.py - Gestión de Furgonetas y Asignaciones
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QTextEdit, QHeaderView, QSpinBox, QCheckBox, QDateEdit, QGroupBox, QComboBox
)
from PySide6.QtCore import Qt, QDate
from datetime import date
from src.ui.estilos import ESTILO_DIALOGO, ESTILO_VENTANA
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
# VENTANA PRINCIPAL: GESTIÓN DE FURGONETAS
# ========================================
class VentanaFurgonetas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Maestros - Furgonetas")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)
        self.setStyleSheet(ESTILO_VENTANA)

        # Asegurar esquema de base de datos
        boot()

        layout = QVBoxLayout(self)

        # ========================================
        # SECCIÓN 1: LISTADO DE FURGONETAS
        # ========================================
        grupo_furgonetas = QGroupBox("Furgonetas Registradas")
        layout_grupo = QVBoxLayout(grupo_furgonetas)

        # Tabla de furgonetas
        self.tabla_furgonetas = QTableWidget()
        self.tabla_furgonetas.setColumnCount(8)
        self.tabla_furgonetas.setHorizontalHeaderLabels([
            "ID", "Nº", "Matrícula", "Marca", "Modelo", "Año", "Activa", "Notas"
        ])
        self.tabla_furgonetas.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla_furgonetas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla_furgonetas.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla_furgonetas.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tabla_furgonetas.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.tabla_furgonetas.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tabla_furgonetas.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.tabla_furgonetas.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        self.tabla_furgonetas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_furgonetas.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_furgonetas.setAlternatingRowColors(True)

        layout_grupo.addWidget(self.tabla_furgonetas)

        # Botones de acciones
        layout_botones = QHBoxLayout()

        self.btn_nueva = QPushButton("Nueva Furgoneta")
        self.btn_nueva.clicked.connect(self.nueva_furgoneta)

        self.btn_editar = QPushButton("Editar")
        self.btn_editar.clicked.connect(self.editar_furgoneta)

        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.clicked.connect(self.eliminar_furgoneta)

        self.btn_volver = QPushButton("Volver")
        self.btn_volver.clicked.connect(self.close)

        layout_botones.addWidget(self.btn_nueva)
        layout_botones.addWidget(self.btn_editar)
        layout_botones.addWidget(self.btn_eliminar)
        layout_botones.addStretch()
        layout_botones.addWidget(self.btn_volver)

        layout_grupo.addLayout(layout_botones)
        layout.addWidget(grupo_furgonetas)

        # Cargar datos iniciales
        self.cargar_furgonetas()

    def cargar_furgonetas(self):
        """Carga todas las furgonetas en la tabla"""
        try:
            furgonetas = list_furgonetas()

            self.tabla_furgonetas.setRowCount(0)

            for furgoneta in furgonetas:
                row = self.tabla_furgonetas.rowCount()
                self.tabla_furgonetas.insertRow(row)

                self.tabla_furgonetas.setItem(row, 0, QTableWidgetItem(str(furgoneta['id'])))

                # Columna Número
                numero_text = str(furgoneta.get('numero', '')) if furgoneta.get('numero') else ''
                self.tabla_furgonetas.setItem(row, 1, QTableWidgetItem(numero_text))

                self.tabla_furgonetas.setItem(row, 2, QTableWidgetItem(furgoneta.get('matricula', '')))
                self.tabla_furgonetas.setItem(row, 3, QTableWidgetItem(furgoneta.get('marca', '') or ''))
                self.tabla_furgonetas.setItem(row, 4, QTableWidgetItem(furgoneta.get('modelo', '') or ''))
                self.tabla_furgonetas.setItem(row, 5, QTableWidgetItem(str(furgoneta.get('anio', '')) if furgoneta.get('anio') else ''))

                activa_text = "Sí" if furgoneta.get('activa') else "No"
                item_activa = QTableWidgetItem(activa_text)
                if not furgoneta.get('activa'):
                    item_activa.setForeground(Qt.red)
                self.tabla_furgonetas.setItem(row, 6, item_activa)

                self.tabla_furgonetas.setItem(row, 7, QTableWidgetItem(furgoneta.get('notas', '') or ''))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar furgonetas:\n{e}")

    def nueva_furgoneta(self):
        """Abre el diálogo para crear una nueva furgoneta"""
        dialogo = DialogoFurgoneta(self)
        if dialogo.exec() == QDialog.Accepted:
            self.cargar_furgonetas()

    def editar_furgoneta(self):
        """Edita la furgoneta seleccionada"""
        seleccion = self.tabla_furgonetas.selectedItems()
        if not seleccion:
            QMessageBox.information(self, "Información", "Selecciona una furgoneta para editar")
            return

        row = seleccion[0].row()
        furgoneta_id = int(self.tabla_furgonetas.item(row, 0).text())

        dialogo = DialogoFurgoneta(self, furgoneta_id)
        if dialogo.exec() == QDialog.Accepted:
            self.cargar_furgonetas()

    def eliminar_furgoneta(self):
        """Elimina la furgoneta seleccionada"""
        seleccion = self.tabla_furgonetas.selectedItems()
        if not seleccion:
            QMessageBox.information(self, "Información", "Selecciona una furgoneta para eliminar")
            return

        row = seleccion[0].row()
        furgoneta_id = int(self.tabla_furgonetas.item(row, 0).text())
        matricula = self.tabla_furgonetas.item(row, 2).text()  # Ahora la matrícula está en columna 2

        respuesta = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Estás seguro de que deseas eliminar la furgoneta '{matricula}'?\n\nEsta acción es irreversible.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta == QMessageBox.Yes:
            try:
                baja_furgoneta(furgoneta_id)
                QMessageBox.information(self, "Éxito", "Furgoneta eliminada correctamente")
                self.cargar_furgonetas()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar:\n{e}")

