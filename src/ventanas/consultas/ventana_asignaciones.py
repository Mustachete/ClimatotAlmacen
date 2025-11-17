# ventana_asignaciones.py - Consulta de Asignaciones de Furgonetas
"""
Consulta para ver el historial de asignaciones de furgonetas a operarios.
Permite filtrar por fecha, operario, furgoneta y turno.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidgetItem, QHeaderView, QDateEdit,
    QComboBox, QMessageBox, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime, timedelta

from src.core.logger import logger
from src.services import furgonetas_service, operarios_service
from src.ui.estilos import ESTILO_VENTANA
from src.ui.widgets_base import (
    TituloVentana, DescripcionVentana, PanelFiltros, TablaEstandar,
    Alerta, BotonPrimario, BotonSecundario
)


class VentanaAsignaciones(QWidget):
    """
    Ventana de consulta de asignaciones de furgonetas.
    Muestra histórico completo con filtros por fecha, operario, furgoneta y turno.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🚚 Consulta de Asignaciones de Furgonetas")
        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)
        self.setStyleSheet(ESTILO_VENTANA)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # ========== TÍTULO ==========
        titulo = TituloVentana("🚚 Historial de Asignaciones de Furgonetas")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        desc = DescripcionVentana("Consulta el historial completo de asignaciones furgoneta-operario")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # ========== GRUPO: FILTROS ==========
        grupo_filtros = PanelFiltros("🔍 Filtros de Búsqueda")
        filtros_layout = QVBoxLayout()

        # Fila 1: Fechas
        fila_fechas = QHBoxLayout()

        lbl_fecha_desde = QLabel("📅 Desde:")
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(QDate.currentDate().addDays(-30))
        self.date_desde.setDisplayFormat("dd/MM/yyyy")

        lbl_fecha_hasta = QLabel("📅 Hasta:")
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(QDate.currentDate())
        self.date_hasta.setDisplayFormat("dd/MM/yyyy")

        fila_fechas.addWidget(lbl_fecha_desde)
        fila_fechas.addWidget(self.date_desde)
        fila_fechas.addSpacing(20)
        fila_fechas.addWidget(lbl_fecha_hasta)
        fila_fechas.addWidget(self.date_hasta)
        fila_fechas.addStretch()

        filtros_layout.addLayout(fila_fechas)

        # Fila 2: Operario y Furgoneta
        fila_filtros = QHBoxLayout()

        lbl_operario = QLabel("👷 Operario:")
        self.cmb_operario = QComboBox()
        self.cmb_operario.setMinimumWidth(200)

        lbl_furgoneta = QLabel("🚚 Furgoneta:")
        self.cmb_furgoneta = QComboBox()
        self.cmb_furgoneta.setMinimumWidth(150)

        fila_filtros.addWidget(lbl_operario)
        fila_filtros.addWidget(self.cmb_operario)
        fila_filtros.addSpacing(20)
        fila_filtros.addWidget(lbl_furgoneta)
        fila_filtros.addWidget(self.cmb_furgoneta)
        fila_filtros.addStretch()

        filtros_layout.addLayout(fila_filtros)

        # Fila 3: Filtro de turno
        fila_turno = QHBoxLayout()
        lbl_turno = QLabel("⏰ Turno:")
        fila_turno.addWidget(lbl_turno)

        self.radio_group_turno = QButtonGroup()
        self.radio_todos = QRadioButton("Todos")
        self.radio_manana = QRadioButton("🌅 Mañana")
        self.radio_tarde = QRadioButton("🌆 Tarde")
        self.radio_completo = QRadioButton("🕐 Día completo")
        self.radio_todos.setChecked(True)

        self.radio_group_turno.addButton(self.radio_todos, 0)
        self.radio_group_turno.addButton(self.radio_manana, 1)
        self.radio_group_turno.addButton(self.radio_tarde, 2)
        self.radio_group_turno.addButton(self.radio_completo, 3)

        fila_turno.addWidget(self.radio_todos)
        fila_turno.addWidget(self.radio_manana)
        fila_turno.addWidget(self.radio_tarde)
        fila_turno.addWidget(self.radio_completo)
        fila_turno.addStretch()

        filtros_layout.addLayout(fila_turno)

        grupo_filtros.setLayout(filtros_layout)
        layout.addWidget(grupo_filtros)

        # ========== BOTONES DE ACCIÓN ==========
        botones_layout = QHBoxLayout()

        self.btn_buscar = BotonPrimario("🔍 Buscar")
        self.btn_buscar.clicked.connect(self.buscar_asignaciones)

        self.btn_exportar = BotonSecundario("📄 Exportar CSV")
        self.btn_exportar.clicked.connect(self.exportar_csv)

        self.btn_limpiar = BotonSecundario("🔄 Limpiar Filtros")
        self.btn_limpiar.clicked.connect(self.limpiar_filtros)

        botones_layout.addWidget(self.btn_buscar, 2)
        botones_layout.addWidget(self.btn_exportar, 1)
        botones_layout.addWidget(self.btn_limpiar, 1)

        layout.addLayout(botones_layout)

        # ========== TABLA DE RESULTADOS ==========
        lbl_resultados = QLabel("📋 Resultados:")
        lbl_resultados.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_resultados)

        self.tabla = TablaEstandar(0, 6)
        self.tabla.setHorizontalHeaderLabels([
            "Fecha", "Turno", "Operario", "Rol", "Furgoneta", "Días"
        ])

        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Fecha
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Turno
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Operario
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Rol
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Furgoneta
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Días

        self.tabla.setMinimumHeight(300)
        layout.addWidget(self.tabla)

        # ========== ESTADÍSTICAS ==========
        self.lbl_estadisticas = Alerta("", tipo='info')
        layout.addWidget(self.lbl_estadisticas)

        # ========== BOTÓN VOLVER ==========
        btn_volver = BotonSecundario("⬅️ Volver")
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)

        # Cargar combos
        self.cargar_combos()

        # Buscar al iniciar (últimos 30 días)
        self.buscar_asignaciones()

    def cargar_combos(self):
        """Carga los combos de operario y furgoneta"""
        try:
            # Cargar operarios usando operarios_service
            operarios = operarios_service.obtener_operarios()

            self.cmb_operario.clear()
            self.cmb_operario.addItem("(Todos los operarios)", None)
            for op in operarios:
                emoji = "👷" if op['rol_operario'] == "oficial" else "🔨"
                texto = f"{emoji} {op['nombre']} ({op['rol_operario']})"
                self.cmb_operario.addItem(texto, op['id'])

            # Cargar furgonetas usando furgonetas_service
            furgonetas = furgonetas_service.list_furgonetas()

            self.cmb_furgoneta.clear()
            self.cmb_furgoneta.addItem("(Todas las furgonetas)", None)
            for furg in furgonetas:
                # furgonetas_service devuelve objetos con 'id' y 'numero', no 'nombre'
                nombre = f"Furgoneta {furg.get('numero', furg['id'])}"
                self.cmb_furgoneta.addItem(f"🚚 {nombre}", furg['id'])

        except Exception as e:
            logger.exception(f"Error al cargar combos: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al cargar filtros:\n{e}")

    def buscar_asignaciones(self):
        """Busca asignaciones según los filtros"""
        try:
            fecha_desde = self.date_desde.date().toString("yyyy-MM-dd")
            fecha_hasta = self.date_hasta.date().toString("yyyy-MM-dd")
            operario_id = self.cmb_operario.currentData()
            furgoneta_id = self.cmb_furgoneta.currentData()

            # Determinar filtro de turno
            turno_filtro = None
            if self.radio_manana.isChecked():
                turno_filtro = 'manana'
            elif self.radio_tarde.isChecked():
                turno_filtro = 'tarde'
            elif self.radio_completo.isChecked():
                turno_filtro = 'completo'

            # Usar furgonetas_service en lugar de SQL directo
            resultados = furgonetas_service.obtener_asignaciones_filtradas(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                operario_id=operario_id,
                furgoneta_id=furgoneta_id,
                turno=turno_filtro
            )

            # Llenar tabla
            self.tabla.setRowCount(len(resultados))

            for i, row in enumerate(resultados):
                # Fecha
                fecha_obj = datetime.strptime(row['fecha'], "%Y-%m-%d")
                fecha_formateada = fecha_obj.strftime("%d/%m/%Y")
                self.tabla.setItem(i, 0, QTableWidgetItem(fecha_formateada))

                # Turno con emoji
                turno_emoji = {
                    'manana': '🌅 Mañana',
                    'tarde': '🌆 Tarde',
                    'completo': '🕐 Completo'
                }
                self.tabla.setItem(i, 1, QTableWidgetItem(turno_emoji.get(row['turno'], row['turno'])))

                # Operario
                self.tabla.setItem(i, 2, QTableWidgetItem(row['operario_nombre']))

                # Rol
                rol_emoji = "👷" if row['rol_operario'] == "oficial" else "🔨"
                self.tabla.setItem(i, 3, QTableWidgetItem(f"{rol_emoji} {row['rol_operario']}"))

                # Furgoneta
                self.tabla.setItem(i, 4, QTableWidgetItem(row['furgoneta_nombre']))

                # Calcular días desde la asignación
                dias_transcurridos = (datetime.now() - fecha_obj).days
                if dias_transcurridos == 0:
                    dias_texto = "Hoy"
                elif dias_transcurridos == 1:
                    dias_texto = "Ayer"
                else:
                    dias_texto = f"Hace {dias_transcurridos} días"
                self.tabla.setItem(i, 5, QTableWidgetItem(dias_texto))

            # Estadísticas
            total = len(resultados)
            if total > 0:
                # Contar operarios únicos
                operarios_unicos = len(set(r[5] for r in resultados))

                # Contar por turno
                turnos_count = {}
                for r in resultados:
                    turno = r[1]
                    turnos_count[turno] = turnos_count.get(turno, 0) + 1

                stats = f"📊 Total: {total} asignaciones | 👷 {operarios_unicos} operarios únicos"
                if turnos_count:
                    stats += " | Turnos: "
                    turno_stats = []
                    if 'completo' in turnos_count:
                        turno_stats.append(f"🕐 {turnos_count['completo']} completos")
                    if 'manana' in turnos_count:
                        turno_stats.append(f"🌅 {turnos_count['manana']} mañanas")
                    if 'tarde' in turnos_count:
                        turno_stats.append(f"🌆 {turnos_count['tarde']} tardes")
                    stats += ", ".join(turno_stats)

                self.lbl_estadisticas.setText(stats)
            else:
                self.lbl_estadisticas.setText("ℹ️ No se encontraron asignaciones con los filtros seleccionados")

        except Exception as e:
            logger.exception(f"Error al buscar asignaciones: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al buscar:\n{e}")

    def exportar_csv(self):
        """Exporta los resultados a CSV"""
        if self.tabla.rowCount() == 0:
            QMessageBox.warning(self, "⚠️ Aviso", "No hay resultados para exportar")
            return

        try:
            from PySide6.QtWidgets import QFileDialog
            import csv

            fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_sugerido = f"asignaciones_furgonetas_{fecha_str}.csv"

            ruta, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar exportación",
                nombre_sugerido,
                "CSV Files (*.csv);;All Files (*)"
            )

            if not ruta:
                return

            with open(ruta, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')

                # Encabezados
                writer.writerow(['Fecha', 'Turno', 'Operario', 'Rol', 'Furgoneta', 'Días'])

                # Datos
                for i in range(self.tabla.rowCount()):
                    row_data = []
                    for j in range(6):
                        item = self.tabla.item(i, j)
                        row_data.append(item.text() if item else '')
                    writer.writerow(row_data)

            QMessageBox.information(
                self,
                "✅ Éxito",
                f"Datos exportados correctamente a:\n\n{ruta}"
            )

        except Exception as e:
            logger.exception(f"Error al exportar: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al exportar:\n{e}")

    def limpiar_filtros(self):
        """Limpia todos los filtros"""
        self.date_desde.setDate(QDate.currentDate().addDays(-30))
        self.date_hasta.setDate(QDate.currentDate())
        self.cmb_operario.setCurrentIndex(0)
        self.cmb_furgoneta.setCurrentIndex(0)
        self.radio_todos.setChecked(True)
        self.buscar_asignaciones()
