"""
Ventana de Login - Autenticación de usuarios
"""

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.core.session_manager import session_manager
from src.repos import sesiones_repo
from src.services import usuarios_service
from src.ui.estilos import COLOR_AZUL_PRINCIPAL, COLOR_TEXTO_OSCURO, ESTILO_LOGIN


class VentanaLogin(QDialog):
    """Ventana de inicio de sesión."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Iniciar Sesión - ClimatotAlmacen")
        self.setFixedSize(750, 650)
        self.setStyleSheet(ESTILO_LOGIN)
        self.setModal(True)

        # Usuario autenticado (None si no se autentica)
        self.usuario_autenticado = None

        # Flag para indicar si el usuario quiere salir de la aplicación
        self.quiere_salir = False

        # Layout principal horizontal
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Panel izquierdo - Login form
        left_panel = QWidget()
        layout = QVBoxLayout(left_panel)
        layout.setSpacing(15)
        layout.setContentsMargins(50, 15, 50, 40)

        # Logo/Título
        titulo_container = QWidget()
        titulo_layout = QVBoxLayout(titulo_container)
        titulo_layout.setSpacing(0)
        titulo_layout.setContentsMargins(0, 0, 0, 0)

        # Cargar y mostrar el logo
        base_dir = Path(__file__).parent.parent.parent
        logo_path = base_dir / "assets" / "images" / "logo_climatot.png"

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setMinimumHeight(120)  # Asegurar altura mínima para evitar corte

        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            # Escalar el logo por ancho (380px) manteniendo proporción
            pixmap = pixmap.scaledToWidth(380, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            # Fallback al texto si no se encuentra el logo
            logo_label.setText("ClimatotAlmacen")
            logo_font = QFont()
            logo_font.setPointSize(24)
            logo_font.setBold(True)
            logo_label.setFont(logo_font)
            logo_label.setStyleSheet(
                f"color: {COLOR_AZUL_PRINCIPAL}; margin-bottom: 5px;"
            )

        titulo_layout.addWidget(logo_label)
        layout.addWidget(titulo_container)

        # Espaciador
        layout.addSpacing(10)

        # Campo Usuario
        lbl_usuario = QLabel("👤 Usuario:")
        lbl_usuario.setStyleSheet(
            f"font-weight: bold; color: {COLOR_TEXTO_OSCURO}; font-size: 14px; margin-bottom: 5px;"
        )
        layout.addWidget(lbl_usuario)

        self.txt_usuario = QLineEdit()
        self.txt_usuario.setPlaceholderText("Ingrese su nombre de usuario")
        self.txt_usuario.returnPressed.connect(self._focus_password)
        layout.addWidget(self.txt_usuario)

        # Espaciador entre campos
        layout.addSpacing(15)

        # Campo Contraseña
        lbl_password = QLabel("🔒 Contraseña:")
        lbl_password.setStyleSheet(
            f"font-weight: bold; color: {COLOR_TEXTO_OSCURO}; font-size: 14px; margin-bottom: 5px;"
        )
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
        self.btn_cancelar.clicked.connect(self.salir_aplicacion)

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

        # Añadir panel izquierdo al layout principal
        main_layout.addWidget(left_panel)

        # Separador vertical
        separador = QFrame()
        separador.setFrameShape(QFrame.VLine)
        separador.setStyleSheet("background-color: #e2e8f0; width: 1px;")
        main_layout.addWidget(separador)

        # Panel derecho - Usuarios conectados
        self._crear_panel_usuarios_conectados(main_layout)

        # Timer para actualizar usuarios conectados cada 5 segundos
        self.timer_usuarios = QTimer()
        self.timer_usuarios.timeout.connect(self._actualizar_usuarios_conectados)
        self.timer_usuarios.start(5000)  # 5 segundos

        # Cargar usuarios conectados inicialmente
        self._actualizar_usuarios_conectados()

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
                self, "Campo vacío", "Por favor, ingrese su nombre de usuario."
            )
            self.txt_usuario.setFocus()
            return

        if not password:
            QMessageBox.warning(
                self, "Campo vacío", "Por favor, ingrese su contraseña."
            )
            self.txt_password.setFocus()
            return

        # Autenticar con el servicio
        exito, mensaje, user_data = usuarios_service.autenticar_usuario(
            usuario, password
        )

        if not exito:
            QMessageBox.critical(self, "Error de autenticación", mensaje)
            self.txt_password.clear()
            self.txt_password.setFocus()
            return

        # Login exitoso - guardar en session manager
        session_manager.login(
            user_data["usuario"], user_data["rol"], user_data.get("id")
        )
        self.usuario_autenticado = user_data

        # Crear backup automático al inicio si está configurado
        try:
            from src.services.backup_config_service import obtener_configuracion

            config = obtener_configuracion()

            if config.backup_auto_inicio:
                # Importar y ejecutar backup en segundo plano
                import sys
                from pathlib import Path

                ROOT_DIR = Path(__file__).parent.parent.parent
                sys.path.insert(0, str(ROOT_DIR))

                from scripts.backup_db import crear_backup

                crear_backup(mostrar_log=True, forzar=False)
        except Exception as e:
            # No mostrar error al usuario, solo registrar en log
            from src.core.logger import logger

            logger.warning(f"No se pudo crear backup automático al inicio: {e}")

        QMessageBox.information(
            self,
            "Bienvenido",
            f"Bienvenido, {user_data['usuario']}!\n\n"
            f"Rol: {user_data['rol'].capitalize()}",
        )

        self.accept()

    def _crear_panel_usuarios_conectados(self, main_layout):
        """Crea el panel lateral con usuarios conectados"""
        panel_derecho = QWidget()
        panel_derecho.setFixedWidth(260)
        panel_derecho.setStyleSheet("background-color: #f8fafc;")

        panel_layout = QVBoxLayout(panel_derecho)
        panel_layout.setSpacing(10)
        panel_layout.setContentsMargins(20, 20, 20, 20)

        # Título del panel
        titulo_usuarios = QLabel("👥 Usuarios Conectados")
        titulo_usuarios.setStyleSheet(
            f"color: {COLOR_AZUL_PRINCIPAL}; "
            "font-weight: bold; "
            "font-size: 14px; "
            "padding-bottom: 10px;"
        )
        panel_layout.addWidget(titulo_usuarios)

        # Área scrollable para la lista de usuarios
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                width: 8px;
                background: #e2e8f0;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #94a3b8;
                border-radius: 4px;
            }
        """)

        self.lista_usuarios_widget = QWidget()
        self.lista_usuarios_layout = QVBoxLayout(self.lista_usuarios_widget)
        self.lista_usuarios_layout.setSpacing(8)
        self.lista_usuarios_layout.setContentsMargins(0, 0, 0, 0)
        self.lista_usuarios_layout.addStretch()

        scroll.setWidget(self.lista_usuarios_widget)
        panel_layout.addWidget(scroll)

        # Indicador de última actualización
        self.lbl_ultima_actualizacion = QLabel("Actualizando...")
        self.lbl_ultima_actualizacion.setStyleSheet(
            "color: #64748b; font-size: 10px; padding-top: 5px;"
        )
        self.lbl_ultima_actualizacion.setAlignment(Qt.AlignCenter)
        panel_layout.addWidget(self.lbl_ultima_actualizacion)

        main_layout.addWidget(panel_derecho)

    def _actualizar_usuarios_conectados(self):
        """Actualiza la lista de usuarios conectados"""
        try:
            # Limpiar layout actual
            while self.lista_usuarios_layout.count() > 1:  # Mantener el stretch
                item = self.lista_usuarios_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Obtener TODOS los usuarios del sistema
            from src.repos import usuarios_repo

            todos_usuarios = usuarios_repo.get_todos(None, True, 100)  # Solo activos

            # Obtener sesiones para cruzar con usuarios
            sesiones = sesiones_repo.obtener_sesiones_activas()

            # Crear un dict para acceso rápido: usuario -> sesion
            import time

            ahora = int(time.time())
            sesiones_dict = {}
            for s in sesiones:
                if s["usuario"] not in sesiones_dict:
                    sesiones_dict[s["usuario"]] = s

            if not todos_usuarios:
                # Mensaje cuando no hay usuarios
                no_usuarios = QLabel("No hay usuarios\nen el sistema")
                no_usuarios.setAlignment(Qt.AlignCenter)
                no_usuarios.setStyleSheet(
                    "color: #94a3b8; font-size: 12px; padding: 20px;"
                )
                self.lista_usuarios_layout.insertWidget(0, no_usuarios)
            else:
                # Crear lista de usuarios con su información de sesión para ordenar
                usuarios_con_info = []
                for usuario in todos_usuarios:
                    usuario_nombre = usuario["usuario"]
                    sesion = sesiones_dict.get(usuario_nombre)

                    # Calcular tiempo de inactividad para ordenar
                    if sesion:
                        tiempo_inactivo = ahora - sesion["ultimo_ping_utc"]
                    else:
                        tiempo_inactivo = float(
                            "inf"
                        )  # Usuarios nunca conectados al final

                    usuarios_con_info.append(
                        {
                            "nombre": usuario_nombre,
                            "sesion": sesion,
                            "tiempo_inactivo": tiempo_inactivo,
                        }
                    )

                # Ordenar por tiempo de inactividad (más recientes primero)
                usuarios_con_info.sort(key=lambda x: x["tiempo_inactivo"])

                # Añadir cada usuario con su estado
                for info in usuarios_con_info:
                    usuario_item = self._crear_item_usuario_con_estado(
                        info["nombre"], info["sesion"], ahora
                    )
                    self.lista_usuarios_layout.insertWidget(
                        self.lista_usuarios_layout.count() - 1, usuario_item
                    )

            # Actualizar timestamp
            ahora_str = datetime.now().strftime("%H:%M:%S")
            self.lbl_ultima_actualizacion.setText(f"Actualizado: {ahora_str}")

        except Exception as e:
            from src.core.logger import logger

            logger.error(f"Error al actualizar usuarios conectados: {e}")

    def _crear_item_usuario_con_estado(self, usuario_nombre, sesion, ahora):
        """Crea un widget para mostrar un usuario con su estado de conexión en una sola línea"""
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 6px;
                padding: 8px 10px;
                border: 1px solid #e2e8f0;
            }
        """)

        item_layout = QHBoxLayout(item)
        item_layout.setSpacing(0)
        item_layout.setContentsMargins(8, 4, 8, 4)

        # Determinar estado del usuario y calcular color con gradiente
        if sesion is None:
            # Usuario nunca conectado o desconectado hace mucho
            icono = "🔴"
            estado = "Desconectado"
            color_rgb = "#94a3b8"  # Gris claro
            font_weight = "normal"
            font_style = "italic"
        else:
            tiempo_inactivo = ahora - sesion["ultimo_ping_utc"]

            if tiempo_inactivo < 90:  # Menos de 90 segundos (3x intervalo de ping de 30s)
                icono = "🟢"
                estado = "Conectado"
                color_rgb = "#1e40af"  # Azul oscuro
                font_weight = "bold"
                font_style = "normal"
            elif tiempo_inactivo < 600:  # Menos de 10 minutos
                mins = tiempo_inactivo // 60
                icono = "🟡"
                estado = f"Hace {mins} min"
                # Gradiente azul medio
                color_rgb = "#3b82f6"
                font_weight = "normal"
                font_style = "normal"
            elif tiempo_inactivo < 3600:  # Menos de 1 hora
                mins = tiempo_inactivo // 60
                icono = "🟠"
                estado = f"Hace {mins} min"
                # Gradiente azul claro
                color_rgb = "#60a5fa"
                font_weight = "normal"
                font_style = "italic"
            elif tiempo_inactivo < 86400:  # Menos de 1 día
                horas = tiempo_inactivo // 3600
                icono = "🟠"
                estado = f"Hace {horas}h"
                # Gradiente gris azulado
                color_rgb = "#94a3b8"
                font_weight = "normal"
                font_style = "italic"
            else:  # Más de 1 día
                dias = tiempo_inactivo // 86400
                icono = "🟤"
                estado = f"Hace +{dias}d"
                # Gris claro
                color_rgb = "#94a3b8"
                font_weight = "normal"
                font_style = "italic"

        # Crear etiqueta única con formato HTML para estilo inline
        # Separar el emoji del nombre para que no se vea afectado por el estilo
        texto_html = f"""
        <span style='font-size: 12px;'>
            {icono}
        </span>
        <span style='color: {color_rgb}; font-weight: {font_weight}; font-style: {font_style}; font-size: 12px;'>
            {usuario_nombre}
        </span>
        <span style='color: #94a3b8; font-size: 11px;'>
            - {estado}
        </span>
        """

        label = QLabel(texto_html)
        label.setTextFormat(Qt.RichText)
        item_layout.addWidget(label)

        return item

    def salir_aplicacion(self):
        """Marca que el usuario quiere salir de la aplicación y cierra el diálogo"""
        # Preguntar al usuario si está seguro de salir
        respuesta = QMessageBox.question(
            self,
            "Confirmar salida",
            "¿Está seguro que desea salir de la aplicación?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Por defecto, "No"
        )

        if respuesta == QMessageBox.Yes:
            # Usuario confirmó la salida
            self.quiere_salir = True
            self.reject()

    def closeEvent(self, event):
        """Detener timer al cerrar y confirmar cierre"""
        # Preguntar al usuario si está seguro de cerrar
        respuesta = QMessageBox.question(
            self,
            "Confirmar cierre",
            "¿Está seguro que desea cerrar la aplicación?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Por defecto, "No"
        )

        if respuesta == QMessageBox.Yes:
            # Usuario confirmó el cierre
            if hasattr(self, "timer_usuarios"):
                self.timer_usuarios.stop()
            self.quiere_salir = True
            super().closeEvent(event)
        else:
            # Usuario canceló el cierre - ignorar el evento
            event.ignore()

    def get_usuario_autenticado(self):
        """Devuelve los datos del usuario autenticado (o None)."""
        return self.usuario_autenticado
