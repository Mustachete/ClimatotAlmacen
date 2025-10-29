from __future__ import annotations
from datetime import date
from typing import List, Dict, Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QTextEdit,
    QPushButton, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit,
    QMessageBox, QGroupBox
)

from src.services.furgonetas_service import (
    boot, list_furgonetas, alta_furgoneta, modificar_furgoneta, baja_furgoneta,
    estado_actual, list_asignaciones, reasignar_furgoneta
)


class VentanaFurgonetas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Maestros · Furgonetas/Almacén")
        self.resize(980, 640)

        boot()  # asegura esquema

        layout = QVBoxLayout(self)

        # --- Tabla principal furgonetas
        self.tbl = QTableWidget(0, 7)
        self.tbl.setHorizontalHeaderLabels(["ID", "Matrícula", "Marca", "Modelo", "Año", "Activa", "Notas"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(QLabel("Furgonetas"))
        layout.addWidget(self.tbl)

        # --- Formulario
        form = QGroupBox("Detalle")
        f_l = QHBoxLayout()
        form.setLayout(f_l)

        self.in_matricula = QLineEdit(); self.in_matricula.setPlaceholderText("1234-ABC")
        self.in_marca = QLineEdit(); self.in_marca.setPlaceholderText("Marca")
        self.in_modelo = QLineEdit(); self.in_modelo.setPlaceholderText("Modelo")
        self.in_anio = QSpinBox(); self.in_anio.setRange(1990, 2100); self.in_anio.setValue(date.today().year)
        self.in_activa = QCheckBox("Activa"); self.in_activa.setChecked(True)
        self.in_notas = QLineEdit(); self.in_notas.setPlaceholderText("Notas")

        for w, label in [
            (self.in_matricula, "Matrícula"),
            (self.in_marca, "Marca"),
            (self.in_modelo, "Modelo"),
            (self.in_anio, "Año"),
            (self.in_activa, ""),
            (self.in_notas, "Notas"),
        ]:
            box = QVBoxLayout();
            if label: box.addWidget(QLabel(label))
            box.addWidget(w)
            f_l.addLayout(box)

        layout.addWidget(form)

        # --- Botonera CRUD
        btns = QHBoxLayout()
        self.btn_nuevo = QPushButton("Nuevo")
        self.btn_guardar = QPushButton("Guardar cambios")
        self.btn_borrar = QPushButton("Borrar")
        btns.addWidget(self.btn_nuevo); btns.addWidget(self.btn_guardar); btns.addWidget(self.btn_borrar)
        layout.addLayout(btns)

        # --- Estado actual (vista)
        layout.addWidget(QLabel("Estado actual (asignación vigente)"))
        self.tbl_estado = QTableWidget(0, 5)
        self.tbl_estado.setHorizontalHeaderLabels(["ID", "Matrícula", "Operario actual", "Desde", "Activa"])
        self.tbl_estado.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tbl_estado)

        # --- Panel reasignación rápida
        reas = QGroupBox("Reasignación rápida")
        r_l = QHBoxLayout(); reas.setLayout(r_l)
        self.in_operario = QLineEdit(); self.in_operario.setPlaceholderText("Nombre del operario")
        self.in_fecha = QDateEdit(); self.in_fecha.setCalendarPopup(True); self.in_fecha.setDate(date.today())
        self.btn_reasignar = QPushButton("Asignar a operario")
        for w, label in [
            (self.in_operario, "Operario"),
            (self.in_fecha, "Fecha desde"),
        ]:
            box = QVBoxLayout();
            box.addWidget(QLabel(label)); box.addWidget(w); r_l.addLayout(box)
        r_l.addWidget(self.btn_reasignar)
        layout.addWidget(reas)

        # Eventos
        self.tbl.itemSelectionChanged.connect(self._on_row_selected)
        self.btn_nuevo.clicked.connect(self._nuevo)
        self.btn_guardar.clicked.connect(self._guardar)
        self.btn_borrar.clicked.connect(self._borrar)
        self.btn_reasignar.clicked.connect(self._reasignar)

        # Estado
        self._selected_id: int | None = None
        self._reload()

    # -----------------------------
    # Helpers de UI
    # -----------------------------
    def _reload(self):
        # Furgonetas
        datos = list_furgonetas()
        self.tbl.setRowCount(0)
        for row in datos:
            r = self.tbl.rowCount(); self.tbl.insertRow(r)
            self.tbl.setItem(r, 0, QTableWidgetItem(str(row["id"])) )
            self.tbl.setItem(r, 1, QTableWidgetItem(row.get("matricula") or ""))
            self.tbl.setItem(r, 2, QTableWidgetItem(row.get("marca") or ""))
            self.tbl.setItem(r, 3, QTableWidgetItem(row.get("modelo") or ""))
            self.tbl.setItem(r, 4, QTableWidgetItem(str(row.get("anio") or "")))
            self.tbl.setItem(r, 5, QTableWidgetItem("Sí" if row.get("activa") else "No"))
            self.tbl.setItem(r, 6, QTableWidgetItem(row.get("notas") or ""))

        # Estado actual
        est = estado_actual()
        self.tbl_estado.setRowCount(0)
        for row in est:
            r = self.tbl_estado.rowCount(); self.tbl_estado.insertRow(r)
            self.tbl_estado.setItem(r, 0, QTableWidgetItem(str(row["furgoneta_id"])) )
            self.tbl_estado.setItem(r, 1, QTableWidgetItem(row.get("matricula") or ""))
            self.tbl_estado.setItem(r, 2, QTableWidgetItem(row.get("operario_actual") or "—"))
            self.tbl_estado.setItem(r, 3, QTableWidgetItem(row.get("desde") or "—"))
            self.tbl_estado.setItem(r, 4, QTableWidgetItem("Sí" if row.get("activa") else "No"))

        self._selected_id = None
        self._limpiar_form()

    def _limpiar_form(self):
        self.in_matricula.clear(); self.in_marca.clear(); self.in_modelo.clear(); self.in_anio.setValue(date.today().year)
        self.in_activa.setChecked(True); self.in_notas.clear()

    def _on_row_selected(self):
        items = self.tbl.selectedItems()
        if not items:
            self._selected_id = None; return
        r = items[0].row()
        self._selected_id = int(self.tbl.item(r, 0).text())
        self.in_matricula.setText(self.tbl.item(r, 1).text())
        self.in_marca.setText(self.tbl.item(r, 2).text())
        self.in_modelo.setText(self.tbl.item(r, 3).text())
        try:
            self.in_anio.setValue(int(self.tbl.item(r, 4).text()))
        except ValueError:
            pass
        self.in_activa.setChecked(self.tbl.item(r, 5).text() == "Sí")
        self.in_notas.setText(self.tbl.item(r, 6).text())

    # -----------------------------
    # Acciones
    # -----------------------------
    def _nuevo(self):
        self._selected_id = None
        self._limpiar_form()
        self.in_matricula.setFocus()

    def _guardar(self):
        matricula = self.in_matricula.text().strip()
        if not matricula:
            QMessageBox.warning(self, "Validación", "La matrícula es obligatoria.")
            return
        marca = self.in_marca.text().strip() or None
        modelo = self.in_modelo.text().strip() or None
        anio = int(self.in_anio.value())
        activa = 1 if self.in_activa.isChecked() else 0
        notas = self.in_notas.text().strip() or None

        try:
            if self._selected_id is None:
                alta_furgoneta(matricula, marca, modelo, anio, notas)
            else:
                modificar_furgoneta(self._selected_id, matricula=matricula, marca=marca, modelo=modelo, anio=anio, activa=activa, notas=notas)
            self._reload()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {e}")

    def _borrar(self):
        if self._selected_id is None:
            return
        if QMessageBox.question(self, "Confirmación", "¿Borrar la furgoneta seleccionada? Esta acción es irreversible.") != QMessageBox.Yes:
            return
        try:
            baja_furgoneta(self._selected_id)
            self._reload()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo borrar: {e}")

    def _reasignar(self):
        if self._selected_id is None:
            QMessageBox.information(self, "Selecciona", "Selecciona primero una furgoneta en la tabla superior.")
            return
        operario = self.in_operario.text().strip()
        if not operario:
            QMessageBox.warning(self, "Validación", "Indica el nombre del operario.")
            return
        fecha = self.in_fecha.date().toPython()  # date
        try:
            reasignar_furgoneta(self._selected_id, operario=operario, fecha_desde=fecha)
            self._reload()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo reasignar: {e}")
