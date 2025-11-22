"""
Ventana de Notificaciones - Gestión de notificaciones del usuario
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QLabel, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import json

from src.services import notificaciones_service
from src.core.session_manager import session_manager
from src.ui.estilos import ESTILO_VENTANA, ESTILO_TITULO_VENTANA


class VentanaNotificaciones(QWidget):
    """Ventana para gestionar las notificaciones del usuario"""

    # Señal para indicar que se ha navegado a un destino
    navegar_a = Signal(str, dict)  # (destino, datos)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window)  # Abre como ventana independiente
        self.usuario = session_manager.get_usuario_actual()
        self.setWindowTitle("🔔 Notificaciones")
        self.resize(900, 600)
        self.setStyleSheet(ESTILO_VENTANA)

        self.configurar_ui()
        self.cargar_notificaciones()

    def configurar_ui(self):
        """Configura la interfaz de usuario"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Título
        titulo = QLabel("🔔 MIS NOTIFICACIONES")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet(ESTILO_TITULO_VENTANA)
        layout.addWidget(titulo)

        # Información
        info = QLabel(
            "💡 Haz doble clic en una notificación para ir al detalle\n"
            "Selecciona las notificaciones que deseas eliminar"
        )
        info.setStyleSheet(
            "color: #64748b; font-size: 11px; padding: 8px; "
            "background-color: #f1f5f9; border-radius: 5px; margin-bottom: 5px;"
        )
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

        # Tabla de notificaciones
        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(['☑️', 'Fecha', 'Tipo', 'Mensaje'])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.doubleClicked.connect(self.al_doble_clic)
        layout.addWidget(self.tabla)

        # Botones de acción
        botones_layout = QHBoxLayout()

        self.btn_seleccionar_todo = QPushButton("☑️ Seleccionar Todo")
        self.btn_seleccionar_todo.clicked.connect(self.seleccionar_todo)

        self.btn_eliminar = QPushButton("🗑️ Eliminar Seleccionadas")
        self.btn_eliminar.clicked.connect(self.eliminar_seleccionadas)
        self.btn_eliminar.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
        """)

        self.btn_actualizar = QPushButton("🔄 Actualizar")
        self.btn_actualizar.clicked.connect(self.cargar_notificaciones)

        btn_cerrar = QPushButton("⬅️ Cerrar")
        btn_cerrar.clicked.connect(self.close)

        botones_layout.addWidget(self.btn_seleccionar_todo)
        botones_layout.addWidget(self.btn_eliminar)
        botones_layout.addStretch()
        botones_layout.addWidget(self.btn_actualizar)
        botones_layout.addWidget(btn_cerrar)

        layout.addLayout(botones_layout)

    def cargar_notificaciones(self):
        """Carga las notificaciones del usuario"""
        try:
            notificaciones = notificaciones_service.obtener_notificaciones(self.usuario)

            self.tabla.setRowCount(0)

            if not notificaciones:
                # Mostrar mensaje de sin notificaciones
                self.tabla.setRowCount(1)
                item = QTableWidgetItem("No tienes notificaciones pendientes ✅")
                item.setTextAlignment(Qt.AlignCenter)
                font = QFont()
                font.setItalic(True)
                item.setFont(font)
                self.tabla.setItem(0, 1, item)
                self.tabla.setSpan(0, 1, 1, 3)
                return

            tipos = notificaciones_service.obtener_todos_tipos()

            for notif in notificaciones:
                fila = self.tabla.rowCount()
                self.tabla.insertRow(fila)

                # Checkbox
                checkbox = QCheckBox()
                checkbox.setStyleSheet("QCheckBox { margin-left: 10px; }")
                self.tabla.setCellWidget(fila, 0, checkbox)

                # Fecha (PostgreSQL retorna datetime objects)
                fecha_creacion = notif['fecha_creacion']
                fecha = fecha_creacion.strftime('%Y-%m-%d %H:%M')
                item_fecha = QTableWidgetItem(fecha)
                item_fecha.setData(Qt.UserRole, notif['id'])  # Guardar ID
                item_fecha.setData(Qt.UserRole + 1, notif['datos_adicionales'])  # Guardar datos
                self.tabla.setItem(fila, 1, item_fecha)

                # Tipo
                tipo_info = tipos.get(notif['tipo'], {})
                tipo_nombre = tipo_info.get('nombre', notif['tipo'])
                self.tabla.setItem(fila, 2, QTableWidgetItem(tipo_nombre))

                # Mensaje
                self.tabla.setItem(fila, 3, QTableWidgetItem(notif['mensaje']))

            # Actualizar título de ventana con contador
            total = len(notificaciones)
            self.setWindowTitle(f"🔔 Notificaciones ({total})")

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al cargar notificaciones:\n{e}")

    def seleccionar_todo(self):
        """Selecciona o deselecciona todas las notificaciones"""
        if self.tabla.rowCount() == 0:
            return

        # Ver si hay alguna seleccionada
        alguna_seleccionada = False
        for fila in range(self.tabla.rowCount()):
            checkbox = self.tabla.cellWidget(fila, 0)
            if checkbox and checkbox.isChecked():
                alguna_seleccionada = True
                break

        # Si alguna está seleccionada, deseleccionar todas; si no, seleccionar todas
        estado = not alguna_seleccionada

        for fila in range(self.tabla.rowCount()):
            checkbox = self.tabla.cellWidget(fila, 0)
            if checkbox:
                checkbox.setChecked(estado)

        self.btn_seleccionar_todo.setText(
            "☐ Deseleccionar Todo" if estado else "☑️ Seleccionar Todo"
        )

    def eliminar_seleccionadas(self):
        """Elimina las notificaciones seleccionadas"""
        try:
            # Obtener IDs seleccionados
            ids_eliminar = []
            for fila in range(self.tabla.rowCount()):
                checkbox = self.tabla.cellWidget(fila, 0)
                if checkbox and checkbox.isChecked():
                    item = self.tabla.item(fila, 1)
                    if item:
                        notif_id = item.data(Qt.UserRole)
                        ids_eliminar.append(notif_id)

            if not ids_eliminar:
                QMessageBox.warning(
                    self,
                    "⚠️ Aviso",
                    "No hay notificaciones seleccionadas.\n\n"
                    "Marca las notificaciones que deseas eliminar."
                )
                return

            # Confirmar eliminación
            respuesta = QMessageBox.question(
                self,
                "❓ Confirmar eliminación",
                f"¿Eliminar {len(ids_eliminar)} notificación(es)?\n\n"
                "Esta acción no se puede deshacer.",
                QMessageBox.Yes | QMessageBox.No
            )

            if respuesta == QMessageBox.Yes:
                exito, mensaje = notificaciones_service.eliminar_notificaciones_multiples(ids_eliminar)

                if exito:
                    QMessageBox.information(self, "✅ Éxito", mensaje)
                    self.cargar_notificaciones()
                else:
                    QMessageBox.critical(self, "❌ Error", mensaje)

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al eliminar:\n{e}")

    def al_doble_clic(self, index):
        """Maneja el doble clic en una notificación para navegar al detalle"""
        try:
            fila = index.row()
            item = self.tabla.item(fila, 1)

            if not item:
                return

            datos_json = item.data(Qt.UserRole + 1)
            if not datos_json:
                QMessageBox.information(
                    self,
                    "ℹ️ Información",
                    "Esta notificación no tiene acción asociada."
                )
                return

            datos = json.loads(datos_json)

            # Determinar destino según el tipo de notificación
            tipo_item = self.tabla.item(fila, 2)
            if not tipo_item:
                return

            tipo_texto = tipo_item.text()

            if '🔴' in tipo_texto or '🟡' in tipo_texto:  # Stock crítico o bajo
                # Navegar a la ficha del artículo
                self.navegar_a_articulo(datos.get('articulo_id'))

            elif '📦' in tipo_texto:  # Inventario pendiente
                # Navegar a inventarios
                self.navegar_a_inventarios()

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al navegar:\n{e}")

    def navegar_a_articulo(self, articulo_id: int):
        """Navega a la ficha de un artículo"""
        try:
            from src.ventanas.consultas.ventana_ficha_articulo import VentanaFichaArticulo

            # Abrir ficha del artículo (parent=None, articulo_id=id)
            self.ventana_ficha = VentanaFichaArticulo(parent=None, articulo_id=articulo_id)
            self.ventana_ficha.show()

            # Cerrar esta ventana
            self.close()

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al abrir ficha de artículo:\n{e}")

    def navegar_a_inventarios(self):
        """Navega a la ventana de inventarios"""
        try:
            from src.ventanas.operativas.ventana_inventario import VentanaInventario

            # Abrir ventana de inventarios
            self.ventana_inv = VentanaInventario()
            self.ventana_inv.showMaximized()

            # Cerrar esta ventana
            self.close()

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al abrir inventarios:\n{e}")
