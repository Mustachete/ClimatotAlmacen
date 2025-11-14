"""
Diálogo para cambiar la contraseña del usuario actual
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFormLayout
)
from PySide6.QtCore import Qt
from src.ui.estilos import ESTILO_DIALOGO, COLOR_TEXTO_OSCURO
from src.services import usuarios_service
from src.core.session_manager import session_manager


class DialogoCambiarPassword(QDialog):
    """Diálogo para que un usuario cambie su propia contraseña."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 Cambiar Mi Contraseña")
        self.setFixedSize(500, 400)
        self.setStyleSheet(ESTILO_DIALOGO)
        self.setModal(True)

        # Obtener usuario actual
        self.usuario_actual = session_manager.get_usuario_actual()
        if not self.usuario_actual:
            QMessageBox.critical(
                self,
                "❌ Error",
                "No hay una sesión activa.\n\nPor favor, inicie sesión."
            )
            self.reject()
            return

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)

        # Título
        titulo = QLabel("🔑 Cambiar Mi Contraseña")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(titulo)

        # Información del usuario
        info = QLabel(f"Usuario: {self.usuario_actual}")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #64748b; font-size: 13px; margin-bottom: 20px;")
        layout.addWidget(info)

        # Formulario
        form = QFormLayout()
        form.setSpacing(15)

        # Contraseña actual
        lbl_actual = QLabel("Contraseña Actual:")
        lbl_actual.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXTO_OSCURO}; font-size: 14px;")

        self.txt_password_actual = QLineEdit()
        self.txt_password_actual.setEchoMode(QLineEdit.Password)
        self.txt_password_actual.setPlaceholderText("Ingrese su contraseña actual")
        self.txt_password_actual.returnPressed.connect(self._focus_nueva)
        form.addRow(lbl_actual, self.txt_password_actual)

        # Nueva contraseña
        lbl_nueva = QLabel("Nueva Contraseña:")
        lbl_nueva.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXTO_OSCURO}; font-size: 14px;")

        self.txt_password_nueva = QLineEdit()
        self.txt_password_nueva.setEchoMode(QLineEdit.Password)
        self.txt_password_nueva.setPlaceholderText("Mínimo 4 caracteres")
        self.txt_password_nueva.returnPressed.connect(self._focus_confirmar)
        form.addRow(lbl_nueva, self.txt_password_nueva)

        # Confirmar nueva contraseña
        lbl_confirmar = QLabel("Confirmar Nueva:")
        lbl_confirmar.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXTO_OSCURO}; font-size: 14px;")

        self.txt_password_confirmar = QLineEdit()
        self.txt_password_confirmar.setEchoMode(QLineEdit.Password)
        self.txt_password_confirmar.setPlaceholderText("Repita la nueva contraseña")
        self.txt_password_confirmar.returnPressed.connect(self.cambiar_password)
        form.addRow(lbl_confirmar, self.txt_password_confirmar)

        layout.addLayout(form)

        # Nota de seguridad
        nota = QLabel(
            "⚠️ Requisitos:\n"
            "• Mínimo 4 caracteres\n"
            "• Debe ser diferente a la actual"
        )
        nota.setStyleSheet("color: #64748b; font-size: 12px; margin: 10px 0;")
        nota.setWordWrap(True)
        layout.addWidget(nota)

        # Espaciador
        layout.addStretch()

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)

        self.btn_cambiar = QPushButton("✅ Cambiar Contraseña")
        self.btn_cambiar.clicked.connect(self.cambiar_password)
        self.btn_cambiar.setDefault(True)

        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addWidget(self.btn_cambiar)

        layout.addLayout(btn_layout)

        # Focus inicial
        self.txt_password_actual.setFocus()

    def _focus_nueva(self):
        """Mueve el foco al campo de nueva contraseña."""
        self.txt_password_nueva.setFocus()

    def _focus_confirmar(self):
        """Mueve el foco al campo de confirmar contraseña."""
        self.txt_password_confirmar.setFocus()

    def cambiar_password(self):
        """Procesa el cambio de contraseña."""
        password_actual = self.txt_password_actual.text()
        password_nueva = self.txt_password_nueva.text()
        password_confirmar = self.txt_password_confirmar.text()

        # Validar que todos los campos estén llenos
        if not password_actual:
            QMessageBox.warning(
                self,
                "⚠️ Campo vacío",
                "Por favor, ingrese su contraseña actual."
            )
            self.txt_password_actual.setFocus()
            return

        if not password_nueva:
            QMessageBox.warning(
                self,
                "⚠️ Campo vacío",
                "Por favor, ingrese su nueva contraseña."
            )
            self.txt_password_nueva.setFocus()
            return

        if not password_confirmar:
            QMessageBox.warning(
                self,
                "⚠️ Campo vacío",
                "Por favor, confirme su nueva contraseña."
            )
            self.txt_password_confirmar.setFocus()
            return

        # Validar que las contraseñas nuevas coincidan
        if password_nueva != password_confirmar:
            QMessageBox.warning(
                self,
                "⚠️ Error",
                "La nueva contraseña y su confirmación no coinciden.\n\n"
                "Por favor, verifique e intente nuevamente."
            )
            self.txt_password_confirmar.clear()
            self.txt_password_confirmar.setFocus()
            return

        # Intentar cambiar la contraseña
        exito, mensaje = usuarios_service.cambiar_password_propia(
            usuario=self.usuario_actual,
            password_actual=password_actual,
            password_nueva=password_nueva
        )

        if not exito:
            QMessageBox.warning(self, "⚠️ Error", mensaje)
            # Si es error de contraseña actual, limpiar ese campo
            if "incorrecta" in mensaje.lower():
                self.txt_password_actual.clear()
                self.txt_password_actual.setFocus()
            return

        # Éxito
        QMessageBox.information(
            self,
            "✅ Éxito",
            f"{mensaje}\n\n"
            "Su contraseña ha sido actualizada correctamente."
        )
        self.accept()
