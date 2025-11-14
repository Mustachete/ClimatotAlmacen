"""
Ventana de Login - Autenticación de usuarios
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from src.ui.estilos import ESTILO_LOGIN, COLOR_AZUL_PRINCIPAL, COLOR_TEXTO_OSCURO
from src.services import usuarios_service
from src.core.session_manager import session_manager


class VentanaLogin(QDialog):
    """Ventana de inicio de sesión."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Iniciar Sesión - ClimatotAlmacen")
        self.setFixedSize(500, 550)
        self.setStyleSheet(ESTILO_LOGIN)
        self.setModal(True)

        # Usuario autenticado (None si no se autentica)
        self.usuario_autenticado = None

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(50, 40, 50, 40)

        # Logo/Título
        titulo_container = QWidget()
        titulo_layout = QVBoxLayout(titulo_container)
        titulo_layout.setSpacing(5)

        titulo = QLabel("ClimatotAlmacen")
        titulo.setAlignment(Qt.AlignCenter)
        titulo_font = QFont()
        titulo_font.setPointSize(24)
        titulo_font.setBold(True)
        titulo.setFont(titulo_font)
        titulo.setStyleSheet(f"color: {COLOR_AZUL_PRINCIPAL}; margin-bottom: 5px;")

        subtitulo = QLabel("Sistema de Gestión de Almacén")
        subtitulo.setAlignment(Qt.AlignCenter)
        subtitulo.setStyleSheet("color: #64748b; font-size: 13px; margin-bottom: 20px;")

        titulo_layout.addWidget(titulo)
        titulo_layout.addWidget(subtitulo)
        layout.addWidget(titulo_container)

        # Espaciador
        layout.addSpacing(25)

        # Campo Usuario
        lbl_usuario = QLabel("👤 Usuario:")
        lbl_usuario.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXTO_OSCURO}; font-size: 14px; margin-bottom: 5px;")
        layout.addWidget(lbl_usuario)

        self.txt_usuario = QLineEdit()
        self.txt_usuario.setPlaceholderText("Ingrese su nombre de usuario")
        self.txt_usuario.returnPressed.connect(self._focus_password)
        layout.addWidget(self.txt_usuario)

        # Espaciador entre campos
        layout.addSpacing(15)

        # Campo Contraseña
        lbl_password = QLabel("🔒 Contraseña:")
        lbl_password.setStyleSheet(f"font-weight: bold; color: {COLOR_TEXTO_OSCURO}; font-size: 14px; margin-bottom: 5px;")
        layout.addWidget(lbl_password)

        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Ingrese su contraseña")
        self.txt_password.setEchoMode(QLineEdit.Password)
        self.txt_password.returnPressed.connect(self.login)
        layout.addWidget(self.txt_password)

        # Espaciador
        layout.addSpacing(25)

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        self.btn_cancelar = QPushButton("Salir")
        self.btn_cancelar.clicked.connect(self.reject)

        self.btn_login = QPushButton("Iniciar Sesión")
        self.btn_login.clicked.connect(self.login)
        self.btn_login.setDefault(True)

        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addWidget(self.btn_login)

        layout.addLayout(btn_layout)

        # Espaciador para empujar todo hacia arriba
        layout.addStretch()

        # Nota sobre primer uso
        nota = QLabel(
            "Nota: Si es la primera vez que usa el sistema,\n"
            "deberá crear un usuario administrador desde la línea de comandos."
        )
        nota.setAlignment(Qt.AlignCenter)
        nota.setStyleSheet("color: #94a3b8; font-size: 11px; margin-top: 10px;")
        layout.addWidget(nota)

        # Focus inicial en usuario
        self.txt_usuario.setFocus()

    def _focus_password(self):
        """Mueve el foco al campo de contraseña."""
        self.txt_password.setFocus()

    def login(self):
        """Procesa el inicio de sesión."""
        usuario = self.txt_usuario.text().strip()
        password = self.txt_password.text()

        if not usuario:
            QMessageBox.warning(
                self,
                "Campo vacío",
                "Por favor, ingrese su nombre de usuario."
            )
            self.txt_usuario.setFocus()
            return

        if not password:
            QMessageBox.warning(
                self,
                "Campo vacío",
                "Por favor, ingrese su contraseña."
            )
            self.txt_password.setFocus()
            return

        # Autenticar con el servicio
        exito, mensaje, user_data = usuarios_service.autenticar_usuario(usuario, password)

        if not exito:
            QMessageBox.critical(
                self,
                "Error de autenticación",
                mensaje
            )
            self.txt_password.clear()
            self.txt_password.setFocus()
            return

        # Login exitoso - guardar en session manager
        session_manager.login(user_data['usuario'], user_data['rol'], user_data.get('id'))
        self.usuario_autenticado = user_data

        QMessageBox.information(
            self,
            "Bienvenido",
            f"Bienvenido, {user_data['usuario']}!\n\n"
            f"Rol: {user_data['rol'].capitalize()}"
        )

        self.accept()

    def get_usuario_autenticado(self):
        """Devuelve los datos del usuario autenticado (o None)."""
        return self.usuario_autenticado
