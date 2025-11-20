"""
Diálogo para configurar las notificaciones de un usuario
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QCheckBox, QMessageBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt

from src.services import notificaciones_service
from src.ui.estilos import ESTILO_DIALOGO


class DialogoConfigNotificaciones(QDialog):
    """Diálogo para configurar las notificaciones de un usuario"""

    def __init__(self, usuario: str, parent=None):
        super().__init__(parent)
        self.usuario = usuario
        self.setWindowTitle(f"🔔 Configurar Notificaciones - {usuario}")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(ESTILO_DIALOGO)

        self.configurar_ui()
        self.cargar_configuracion()

    def configurar_ui(self):
        """Configura la interfaz de usuario"""
        layout = QVBoxLayout(self)

        # Título
        titulo = QLabel(f"🔔 Configuración de Notificaciones\nUsuario: {self.usuario}")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(titulo)

        # Información
        info = QLabel(
            "Selecciona los tipos de notificaciones que deseas recibir.\n"
            "Las notificaciones se generarán automáticamente al iniciar sesión."
        )
        info.setStyleSheet(
            "color: #64748b; font-size: 11px; padding: 8px; "
            "background-color: #f1f5f9; border-radius: 5px; margin-bottom: 10px;"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Grupo de opciones
        grupo = QGroupBox("Tipos de Notificaciones")
        grupo_layout = QVBoxLayout()

        # Obtener tipos disponibles
        self.checkboxes = {}
        tipos = notificaciones_service.obtener_todos_tipos()

        for tipo_id, tipo_info in tipos.items():
            checkbox = QCheckBox(tipo_info['nombre'])
            checkbox.setStyleSheet("font-size: 12px; padding: 5px;")

            # Descripción
            descripcion = QLabel(tipo_info['descripcion'])
            descripcion.setStyleSheet("color: #64748b; font-size: 10px; margin-left: 25px; margin-bottom: 8px;")
            descripcion.setWordWrap(True)

            grupo_layout.addWidget(checkbox)
            grupo_layout.addWidget(descripcion)

            self.checkboxes[tipo_id] = checkbox

        grupo.setLayout(grupo_layout)
        layout.addWidget(grupo)

        # Botones
        layout.addStretch()

        botones_layout = QHBoxLayout()

        btn_guardar = QPushButton("💾 Guardar")
        btn_guardar.setMinimumHeight(35)
        btn_guardar.clicked.connect(self.guardar)
        btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)

        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.setMinimumHeight(35)
        btn_cancelar.clicked.connect(self.reject)

        botones_layout.addWidget(btn_guardar)
        botones_layout.addWidget(btn_cancelar)

        layout.addLayout(botones_layout)

    def cargar_configuracion(self):
        """Carga la configuración actual del usuario"""
        try:
            config = notificaciones_service.obtener_configuracion_usuario(self.usuario)

            for tipo_id, checkbox in self.checkboxes.items():
                activa = config.get(tipo_id, True)
                checkbox.setChecked(activa)

        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Error",
                f"Error al cargar configuración:\n{e}"
            )

    def guardar(self):
        """Guarda la configuración de notificaciones"""
        try:
            # Guardar cada configuración
            for tipo_id, checkbox in self.checkboxes.items():
                activa = checkbox.isChecked()
                exito, mensaje = notificaciones_service.actualizar_configuracion(
                    self.usuario,
                    tipo_id,
                    activa
                )

                if not exito:
                    QMessageBox.critical(
                        self,
                        "❌ Error",
                        f"Error al guardar configuración de {tipo_id}:\n{mensaje}"
                    )
                    return

            QMessageBox.information(
                self,
                "✅ Éxito",
                "Configuración de notificaciones guardada correctamente.\n\n"
                "Los cambios se aplicarán en el próximo inicio de sesión."
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Error",
                f"Error al guardar:\n{e}"
            )
