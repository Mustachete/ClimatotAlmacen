# dialogo_historial.py - Diálogo para ver y seleccionar del historial
"""
Diálogo que muestra el historial de operaciones recientes y artículos frecuentes.
Permite repetir operaciones con un solo click.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel,
    QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from datetime import datetime

from src.services import historial_service
from src.ui.estilos import ESTILO_DIALOGO


class DialogoHistorial(QDialog):
    """
    Diálogo para mostrar y seleccionar del historial de operaciones.

    Señales:
        articulo_seleccionado(dict): Emite cuando se selecciona un artículo del historial
            dict contiene: {'articulo_id', 'articulo_nombre', 'u_medida', 'cantidad', 'datos_adicionales'}
    """

    articulo_seleccionado = Signal(dict)

    def __init__(self, usuario, tipo_operacion=None, parent=None):
        super().__init__(parent)
        self.usuario = usuario
        self.tipo_operacion = tipo_operacion

        self.setWindowTitle("📜 Historial de Operaciones")
        self.setMinimumSize(800, 600)
        self.resize(900, 650)
        self.setStyleSheet(ESTILO_DIALOGO)

        layout = QVBoxLayout(self)

        # Título
        titulo = QLabel("📜 Historial de Operaciones Recientes")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        desc = QLabel("Haz click en una operación para repetirla rápidamente")
        desc.setStyleSheet("color: #64748b; font-size: 12px; margin-bottom: 15px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # Tabs
        self.tabs = QTabWidget()

        # Tab 1: Historial Reciente
        tab_historial = self.crear_tab_historial()
        self.tabs.addTab(tab_historial, "🕐 Reciente (20 últimas)")

        # Tab 2: Artículos Frecuentes
        tab_frecuentes = self.crear_tab_frecuentes()
        self.tabs.addTab(tab_frecuentes, "⭐ Más Usados")

        layout.addWidget(self.tabs)

        # Botones
        botones_layout = QHBoxLayout()

        btn_actualizar = QPushButton("🔄 Actualizar")
        btn_actualizar.clicked.connect(self.actualizar_datos)

        btn_cerrar = QPushButton("❌ Cerrar")
        btn_cerrar.clicked.connect(self.reject)

        botones_layout.addWidget(btn_actualizar)
        botones_layout.addStretch()
        botones_layout.addWidget(btn_cerrar)

        layout.addLayout(botones_layout)

        # Cargar datos iniciales
        self.cargar_historial_reciente()
        self.cargar_articulos_frecuentes()

    def crear_tab_historial(self):
        """Crea el tab de historial reciente"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Tabla
        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(6)
        self.tabla_historial.setHorizontalHeaderLabels([
            "Fecha/Hora", "Artículo", "Cantidad", "U.Medida", "Tipo", "Info Extra"
        ])

        header = self.tabla_historial.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.tabla_historial.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_historial.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_historial.setAlternatingRowColors(True)
        self.tabla_historial.doubleClicked.connect(self.seleccionar_historial)

        layout.addWidget(self.tabla_historial)

        # Info
        info = QLabel("💡 Doble click en una fila para repetir la operación")
        info.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic; margin-top: 5px;")
        layout.addWidget(info)

        return widget

    def crear_tab_frecuentes(self):
        """Crea el tab de artículos frecuentes"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Descripción
        desc = QLabel("Artículos que has usado más frecuentemente en los últimos 30 días")
        desc.setStyleSheet("color: #64748b; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Tabla
        self.tabla_frecuentes = QTableWidget()
        self.tabla_frecuentes.setColumnCount(5)
        self.tabla_frecuentes.setHorizontalHeaderLabels([
            "Artículo", "Veces Usado", "Cantidad Total", "U.Medida", "Última Vez"
        ])

        header = self.tabla_frecuentes.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.tabla_frecuentes.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_frecuentes.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_frecuentes.setAlternatingRowColors(True)
        self.tabla_frecuentes.doubleClicked.connect(self.seleccionar_frecuente)

        layout.addWidget(self.tabla_frecuentes)

        # Info
        info = QLabel("💡 Doble click en una fila para añadir el artículo")
        info.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic; margin-top: 5px;")
        layout.addWidget(info)

        return widget

    def cargar_historial_reciente(self):
        """Carga el historial reciente en la tabla"""
        historial = historial_service.obtener_historial_reciente(
            self.usuario,
            self.tipo_operacion,
            limite=20
        )

        self.tabla_historial.setRowCount(len(historial))

        for i, item in enumerate(historial):
            # Fecha/Hora (formato legible)
            try:
                dt = datetime.fromisoformat(item['fecha_hora'])
                fecha_str = dt.strftime("%d/%m/%Y %H:%M")
                # Calcular hace cuánto
                diff = datetime.now() - dt
                if diff.days == 0:
                    if diff.seconds < 3600:
                        hace = f"Hace {diff.seconds // 60} min"
                    else:
                        hace = f"Hace {diff.seconds // 3600}h"
                elif diff.days == 1:
                    hace = "Ayer"
                else:
                    hace = f"Hace {diff.days} días"
                fecha_texto = f"{fecha_str}\n({hace})"
            except (ValueError, AttributeError, TypeError):
                fecha_texto = item['fecha_hora']

            item_fecha = QTableWidgetItem(fecha_texto)
            self.tabla_historial.setItem(i, 0, item_fecha)

            # Artículo
            item_articulo = QTableWidgetItem(item['articulo_nombre'])
            self.tabla_historial.setItem(i, 1, item_articulo)

            # Cantidad
            item_cantidad = QTableWidgetItem(f"{item['cantidad']:.2f}")
            item_cantidad.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla_historial.setItem(i, 2, item_cantidad)

            # U.Medida
            item_umedida = QTableWidgetItem(item['u_medida'])
            self.tabla_historial.setItem(i, 3, item_umedida)

            # Tipo
            tipos_iconos = {
                'movimiento': '🔄',
                'imputacion': '📝',
                'material_perdido': '⚠️',
                'devolucion': '↩️'
            }
            icono = tipos_iconos.get(item['tipo_operacion'], '📦')
            item_tipo = QTableWidgetItem(f"{icono} {item['tipo_operacion'].title()}")
            self.tabla_historial.setItem(i, 4, item_tipo)

            # Info Extra
            datos_extra = item['datos_adicionales']
            info_extra = ""
            if datos_extra:
                if 'ot' in datos_extra:
                    info_extra += f"OT: {datos_extra['ot']}"
                if 'modo' in datos_extra:
                    info_extra += f" | {datos_extra['modo'].title()}"
                if 'motivo' in datos_extra:
                    motivo = datos_extra['motivo'][:30] + "..." if len(datos_extra['motivo']) > 30 else datos_extra['motivo']
                    info_extra += f" | {motivo}"
            item_info = QTableWidgetItem(info_extra)
            item_info.setForeground(QColor("#64748b"))
            self.tabla_historial.setItem(i, 5, item_info)

            # Guardar datos completos en la fila
            item_fecha.setData(Qt.UserRole, item)

    def cargar_articulos_frecuentes(self):
        """Carga los artículos frecuentes en la tabla"""
        frecuentes = historial_service.obtener_articulos_frecuentes(
            self.usuario,
            self.tipo_operacion,
            limite=15,
            dias=30
        )

        self.tabla_frecuentes.setRowCount(len(frecuentes))

        for i, item in enumerate(frecuentes):
            # Artículo
            item_articulo = QTableWidgetItem(item['articulo_nombre'])
            self.tabla_frecuentes.setItem(i, 0, item_articulo)

            # Veces usado
            item_veces = QTableWidgetItem(f"{item['veces_usado']} veces")
            item_veces.setTextAlignment(Qt.AlignCenter)
            # Color según frecuencia
            if item['veces_usado'] >= 10:
                item_veces.setBackground(QColor("#dcfce7"))  # Verde claro
            elif item['veces_usado'] >= 5:
                item_veces.setBackground(QColor("#fef3c7"))  # Amarillo claro
            self.tabla_frecuentes.setItem(i, 1, item_veces)

            # Cantidad total
            item_cant_total = QTableWidgetItem(f"{item['cantidad_total']:.2f}")
            item_cant_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabla_frecuentes.setItem(i, 2, item_cant_total)

            # U.Medida
            item_umedida = QTableWidgetItem(item['u_medida'])
            self.tabla_frecuentes.setItem(i, 3, item_umedida)

            # Última vez
            try:
                dt = datetime.fromisoformat(item['ultima_vez'])
                diff = datetime.now() - dt
                if diff.days == 0:
                    ultima = "Hoy"
                elif diff.days == 1:
                    ultima = "Ayer"
                else:
                    ultima = f"Hace {diff.days} días"
            except (ValueError, AttributeError, TypeError):
                ultima = "---"
            item_ultima = QTableWidgetItem(ultima)
            item_ultima.setTextAlignment(Qt.AlignCenter)
            self.tabla_frecuentes.setItem(i, 4, item_ultima)

            # Guardar datos en la fila
            item_articulo.setData(Qt.UserRole, item)

    def seleccionar_historial(self):
        """Selecciona una operación del historial para repetirla"""
        fila = self.tabla_historial.currentRow()
        if fila < 0:
            return

        item_fecha = self.tabla_historial.item(fila, 0)
        datos = item_fecha.data(Qt.UserRole)

        if datos:
            self.articulo_seleccionado.emit({
                'articulo_id': datos['articulo_id'],
                'articulo_nombre': datos['articulo_nombre'],
                'u_medida': datos['u_medida'],
                'cantidad': datos['cantidad'],
                'datos_adicionales': datos['datos_adicionales']
            })
            self.accept()

    def seleccionar_frecuente(self):
        """Selecciona un artículo frecuente"""
        fila = self.tabla_frecuentes.currentRow()
        if fila < 0:
            return

        item_articulo = self.tabla_frecuentes.item(fila, 0)
        datos = item_articulo.data(Qt.UserRole)

        if datos:
            self.articulo_seleccionado.emit({
                'articulo_id': datos['articulo_id'],
                'articulo_nombre': datos['articulo_nombre'],
                'u_medida': datos['u_medida'],
                'cantidad': 1.0,  # Cantidad por defecto
                'datos_adicionales': {}
            })
            self.accept()

    def actualizar_datos(self):
        """Actualiza los datos de ambas tablas"""
        self.cargar_historial_reciente()
        self.cargar_articulos_frecuentes()
        QMessageBox.information(self, "✅ Actualizado", "Datos actualizados correctamente")
