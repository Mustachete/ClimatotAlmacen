# ventana_informe_furgonetas.py - Generación de informes semanales de furgonetas
"""
Ventana para generar informes semanales de consumo por furgoneta.
Permite seleccionar semana, furgoneta(s) y exportar a PDF.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QMessageBox, QComboBox, QDateEdit,
    QGroupBox, QHeaderView, QProgressDialog, QFileDialog
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QBrush, QFont
from datetime import datetime, timedelta

from src.ui.estilos import ESTILO_VENTANA
from src.core.logger import logger
from src.services import informes_furgonetas_service
from src.repos.furgonetas_repo import list_furgonetas


class VentanaInformeFurgonetas(QWidget):
    """Ventana para generar informes semanales de consumo de furgonetas"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Informe Semanal de Furgonetas")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)
        self.setStyleSheet(ESTILO_VENTANA)

        self.datos_informe = None  # Almacena los datos generados

        layout = QVBoxLayout(self)

        # ========== TÍTULO ==========
        titulo = QLabel("📊 Informe Semanal de Consumo por Furgoneta")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        desc = QLabel(
            "Genera informes detallados de stock y movimientos (entregas, devoluciones, gastos) por furgoneta y semana"
        )
        desc.setStyleSheet("color: #64748b; font-size: 12px; margin-bottom: 10px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # ========== GRUPO: FILTROS ==========
        grupo_filtros = QGroupBox("Filtros de Generación")
        filtros_layout = QHBoxLayout()

        # Selector de semana (lunes)
        lbl_semana = QLabel("Semana (Lunes):")
        self.date_semana = QDateEdit()
        self.date_semana.setCalendarPopup(True)
        self.date_semana.setDisplayFormat("dd/MM/yyyy")
        # Por defecto: lunes de la semana pasada
        hoy = QDate.currentDate()
        lunes_actual = hoy.addDays(-(hoy.dayOfWeek() - 1))  # dayOfWeek: 1=Lunes, 7=Domingo
        lunes_pasado = lunes_actual.addDays(-7)
        self.date_semana.setDate(lunes_pasado)

        filtros_layout.addWidget(lbl_semana)
        filtros_layout.addWidget(self.date_semana)

        # Selector de furgoneta
        lbl_furgoneta = QLabel("Furgoneta:")
        self.cmb_furgoneta = QComboBox()
        self.cmb_furgoneta.setMinimumWidth(250)
        self.cargar_furgonetas()

        filtros_layout.addWidget(lbl_furgoneta)
        filtros_layout.addWidget(self.cmb_furgoneta)

        # Botón generar
        self.btn_generar = QPushButton("🔍 Generar Informe")
        self.btn_generar.setMinimumHeight(40)
        self.btn_generar.clicked.connect(self.generar_informe)

        filtros_layout.addWidget(self.btn_generar)
        filtros_layout.addStretch()

        grupo_filtros.setLayout(filtros_layout)
        layout.addWidget(grupo_filtros)

        # ========== GRUPO: VISTA PREVIA ==========
        grupo_preview = QGroupBox("Vista Previa del Informe")
        preview_layout = QVBoxLayout()

        # Info de la furgoneta y semana
        self.lbl_info = QLabel("Selecciona una furgoneta y semana, luego genera el informe")
        self.lbl_info.setStyleSheet("font-size: 13px; font-weight: bold; margin: 5px;")
        preview_layout.addWidget(self.lbl_info)

        # Tabla de preview
        self.tabla_preview = QTableWidget()
        self.tabla_preview.setAlternatingRowColors(True)
        self.tabla_preview.setSelectionBehavior(QTableWidget.SelectRows)
        preview_layout.addWidget(self.tabla_preview)

        grupo_preview.setLayout(preview_layout)
        layout.addWidget(grupo_preview)

        # ========== BOTONES INFERIORES ==========
        botones_layout = QHBoxLayout()

        self.btn_exportar_pdf = QPushButton("📄 Exportar a PDF")
        self.btn_exportar_pdf.setMinimumHeight(40)
        self.btn_exportar_pdf.setEnabled(False)
        self.btn_exportar_pdf.clicked.connect(self.exportar_pdf)

        self.btn_volver = QPushButton("❌ Volver")
        self.btn_volver.setMinimumHeight(40)
        self.btn_volver.clicked.connect(self.close)

        botones_layout.addWidget(self.btn_exportar_pdf)
        botones_layout.addStretch()
        botones_layout.addWidget(self.btn_volver)

        layout.addLayout(botones_layout)

    def cargar_furgonetas(self):
        """Carga las furgonetas activas en el combobox"""
        try:
            furgonetas = list_furgonetas(include_inactive=False)

            self.cmb_furgoneta.clear()
            self.cmb_furgoneta.addItem("-- Selecciona una furgoneta --", None)

            for furgoneta in furgonetas:
                nombre = furgoneta.get('nombre', 'Sin nombre')
                matricula = furgoneta.get('matricula', '')
                # Si list_furgonetas devuelve matricula y nombre distintos, mostrar ambos
                if matricula and matricula != nombre:
                    texto = f"{nombre} ({matricula})"
                else:
                    texto = nombre
                self.cmb_furgoneta.addItem(texto, furgoneta['id'])

        except Exception as e:
            logger.exception(f"Error al cargar furgonetas: {e}")
            QMessageBox.critical(self, "Error", f"Error al cargar furgonetas:\n{e}")

    def generar_informe(self):
        """Genera los datos del informe y los muestra en la tabla"""
        furgoneta_id = self.cmb_furgoneta.currentData()

        if not furgoneta_id:
            QMessageBox.warning(self, "Aviso", "Selecciona una furgoneta")
            return

        # Obtener fecha del lunes
        fecha_lunes = self.date_semana.date().toString("yyyy-MM-dd")

        # Mostrar diálogo de progreso
        progress = QProgressDialog("Generando informe...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)
        progress.show()

        try:
            exito, mensaje, datos = informes_furgonetas_service.generar_datos_informe(
                furgoneta_id,
                fecha_lunes
            )

            progress.close()

            if not exito:
                QMessageBox.critical(self, "Error", mensaje)
                return

            self.datos_informe = datos
            self.mostrar_datos_en_tabla()
            self.btn_exportar_pdf.setEnabled(True)

            num_articulos = len(datos['articulos'])
            num_operarios = len(datos['operarios'])

            if num_articulos == 0:
                QMessageBox.warning(
                    self,
                    "Informe Vacío",
                    f"El informe se generó pero no contiene artículos.\n\n"
                    f"Esto puede ocurrir si:\n"
                    f"• No hay movimientos en la semana seleccionada\n"
                    f"• La furgoneta no tenía stock al inicio de la semana\n\n"
                    f"Prueba con otra semana o furgoneta."
                )
            else:
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Informe generado correctamente\n\n"
                    f"• Artículos: {num_articulos}\n"
                    f"• Operarios: {num_operarios if num_operarios > 0 else 'Sin operarios asignados'}"
                )

        except Exception as e:
            progress.close()
            logger.exception(f"Error al generar informe: {e}")
            QMessageBox.critical(self, "Error", f"Error al generar informe:\n{e}")

    def mostrar_datos_en_tabla(self):
        """Muestra los datos del informe en la tabla de preview"""
        if not self.datos_informe:
            return

        datos = self.datos_informe

        # Actualizar info del título con formato "Informe Semanal de Consumo - Furgoneta XX"
        operarios_txt = ", ".join(datos['operarios']) if datos['operarios'] else "Sin operarios asignados"
        fecha_ini = datetime.strptime(datos['fecha_inicio'], "%Y-%m-%d").strftime("%d/%m/%Y")
        fecha_fin = datetime.strptime(datos['fecha_fin'], "%Y-%m-%d").strftime("%d/%m/%Y")

        self.lbl_info.setText(
            f"Informe Semanal de Consumo - Furgoneta {datos['furgoneta_nombre']} | "
            f"Semana: {fecha_ini} - {fecha_fin} | "
            f"Operario(s): {operarios_txt}"
        )

        # Configurar columnas de la tabla
        dias = datos['dias_semana']
        num_dias = len(dias)

        # Columnas: FAMILIA | ARTÍCULO | STOCK INICIAL | (E D G) por cada día | TOTAL
        num_columnas = 3 + (num_dias * 3) + 1
        self.tabla_preview.setColumnCount(num_columnas)

        # Crear encabezados - La fecha solo aparece en la columna E de cada día
        headers = ["FAMILIA", "ARTÍCULO", "STOCK\nINICIAL"]

        for dia in dias:
            dia_abrev = dia['dia_nombre']  # L, M, X, J, V, S
            fecha_corta = dia['dia_completo']  # DD/MM
            # Solo la columna E lleva la fecha completa
            headers.extend([
                f"{dia_abrev} {fecha_corta} — E",
                "D",  # Solo la letra, sin repetir fecha
                "G"   # Solo la letra, sin repetir fecha
            ])

        headers.append("TOTAL\nFINAL")

        self.tabla_preview.setHorizontalHeaderLabels(headers)

        # Llenar datos
        articulos = datos['articulos']
        self.tabla_preview.setRowCount(len(articulos))

        for row, art in enumerate(articulos):
            col = 0

            # Familia
            item_familia = QTableWidgetItem(art['familia'])
            item_familia.setBackground(QColor("#f1f5f9"))
            self.tabla_preview.setItem(row, col, item_familia)
            col += 1

            # Artículo
            self.tabla_preview.setItem(row, col, QTableWidgetItem(art['articulo_nombre']))
            col += 1

            # Stock inicial
            item_stock_ini = QTableWidgetItem(f"{art['stock_inicial']:.2f}")
            item_stock_ini.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla_preview.setItem(row, col, item_stock_ini)
            col += 1

            # Movimientos por día
            for dia in dias:
                fecha = dia['fecha']
                movs = art['movimientos_diarios'].get(fecha, {'E': 0, 'D': 0, 'G': 0})

                for tipo in ['E', 'D', 'G']:
                    valor = movs[tipo]
                    item = QTableWidgetItem(f"{valor:.2f}" if valor != 0 else "-")
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                    # Colorear según tipo
                    if valor != 0:
                        if tipo == 'E':
                            item.setBackground(QColor("#dcfce7"))  # Verde claro
                        elif tipo == 'D':
                            item.setBackground(QColor("#fef3c7"))  # Amarillo claro
                        elif tipo == 'G':
                            item.setBackground(QColor("#fee2e2"))  # Rojo claro

                    self.tabla_preview.setItem(row, col, item)
                    col += 1

            # Total (stock final)
            item_total = QTableWidgetItem(f"{art['stock_final']:.2f}")
            item_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_total.setBackground(QColor("#e0e7ff"))  # Azul claro
            item_total.setFont(item_total.font())
            font = item_total.font()
            font.setBold(True)
            item_total.setFont(font)
            self.tabla_preview.setItem(row, col, item_total)

        # Ajustar columnas
        header = self.tabla_preview.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # FAMILIA
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # ARTÍCULO
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # STOCK INICIAL

        # Columnas E/D/G: todas con el mismo ancho fijo (60 pixels)
        ancho_edg = 60
        for i in range(3, num_columnas - 1):  # Desde la primera E hasta antes de TOTAL
            header.setSectionResizeMode(i, QHeaderView.Fixed)
            self.tabla_preview.setColumnWidth(i, ancho_edg)

        # TOTAL FINAL: ajustar al contenido
        header.setSectionResizeMode(num_columnas - 1, QHeaderView.ResizeToContents)

    def exportar_pdf(self):
        """Exporta el informe a PDF"""
        if not self.datos_informe:
            QMessageBox.warning(self, "Aviso", "Genera primero el informe")
            return

        # Diálogo para guardar archivo
        fecha_inicio = datetime.strptime(self.datos_informe['fecha_inicio'], "%Y-%m-%d")
        nombre_sugerido = f"Furgoneta_{self.datos_informe['furgoneta_nombre']}_Semana_{fecha_inicio.strftime('%Y-%m-%d')}.pdf"

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar informe PDF",
            nombre_sugerido,
            "PDF Files (*.pdf)"
        )

        if not ruta:
            return

        # Importar exportador PDF
        try:
            from src.utils.exportador_pdf_furgonetas import exportar_informe_a_pdf

            progress = QProgressDialog("Generando PDF...", None, 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setCancelButton(None)
            progress.show()

            exito = exportar_informe_a_pdf(self.datos_informe, ruta)

            progress.close()

            if exito:
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Informe exportado correctamente:\n{ruta}"
                )
            else:
                QMessageBox.critical(self, "Error", "Error al generar PDF")

        except Exception as e:
            progress.close()
            logger.exception(f"Error al exportar PDF: {e}")
            QMessageBox.critical(self, "Error", f"Error al exportar PDF:\n{e}")
