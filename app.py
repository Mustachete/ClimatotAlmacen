# app.py - Programa Principal - Sistema Climatot Almacén
import socket
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# ========================================
# IMPORTAR FUNCIONES CENTRALIZADAS
# ========================================
from src.core.db_utils import get_con
from src.core.idle_manager import get_idle_manager
from src.core.logger import log_fin_sesion, log_inicio_sesion, logger
from src.core.session_manager import session_manager
from src.repos import sesiones_repo
from src.ui.estilos import ESTILO_VENTANA
from src.ventanas.consultas.ventana_consumos import VentanaConsumos
from src.ventanas.consultas.ventana_historico import VentanaHistorico
from src.ventanas.consultas.ventana_informe_furgonetas import VentanaInformeFurgonetas
from src.ventanas.consultas.ventana_pedido_ideal import VentanaPedidoIdeal
from src.ventanas.consultas.ventana_stock import VentanaStock
from src.ventanas.dialogo_cambiar_password import DialogoCambiarPassword
from src.ventanas.maestros.ventana_articulos import VentanaArticulos
from src.ventanas.maestros.ventana_familias import VentanaFamilias
from src.ventanas.maestros.ventana_furgonetas import VentanaFurgonetas
from src.ventanas.maestros.ventana_operarios import VentanaOperarios
from src.ventanas.maestros.ventana_proveedores import VentanaProveedores
from src.ventanas.maestros.ventana_ubicaciones import VentanaUbicaciones
from src.ventanas.maestros.ventana_usuarios import VentanaUsuarios
from src.ventanas.operativas.ventana_devolucion import VentanaDevolucion
from src.ventanas.operativas.ventana_imputacion import VentanaImputacion
from src.ventanas.operativas.ventana_inventario import VentanaInventario
from src.ventanas.operativas.ventana_material_perdido import VentanaMaterialPerdido
from src.ventanas.operativas.ventana_movimientos import VentanaMovimientos
from src.ventanas.operativas.ventana_recepcion import VentanaRecepcion
from src.ventanas.ventana_login import VentanaLogin


# ========================================
# VENTANA MENÚ PRINCIPAL
# ========================================
class MainMenuWindow(QWidget):
    def __init__(self, login_window):
        super().__init__()
        self.login_window = login_window

        # Obtener datos de sesión
        self.usuario = session_manager.get_usuario_actual()
        self.rol = session_manager.get_rol_actual()
        self.hostname = socket.gethostname()

        self.setWindowTitle(f"📋 Menú Principal - {self.usuario} ({self.rol})")
        self.setMinimumSize(700, 550)
        self.resize(700, 550)
        self.setStyleSheet(ESTILO_VENTANA)

        layout = QVBoxLayout(self)

        # Encabezado con notificaciones
        self.crear_encabezado(layout)

        # Generar notificaciones al iniciar sesión
        self.generar_notificaciones_inicio()

        # Actualizar contador
        self.actualizar_contador_notificaciones()

        # Timer para actualizar ping de sesión cada 30 segundos
        self.timer_ping = QTimer(self)
        self.timer_ping.timeout.connect(self._actualizar_ping_sesion)
        self.timer_ping.start(30000)  # 30 segundos

        # Grid de botones
        grid = QGridLayout()
        grid.setSpacing(10)

        # Definir botones según el rol
        botones = [
            ("📦 Recepción", self.abrir_recepcion, True),
            ("🔄 Hacer Movimientos", self.abrir_movimientos, True),
            ("📝 Imputar Material", self.abrir_imputacion, True),
            ("↩️ Devolución a Proveedor", self.abrir_devolucion, True),
            ("⚠️ Material Perdido", self.abrir_material_perdido, self.rol == "admin"),
            ("📊 Inventario Físico", self.abrir_inventario, True),
            ("📊 Informes", self.abrir_info_menu, True),
            ("⚙️ Maestros", self.abrir_maestros, True),
            ("🔧 Configuración", self.abrir_configuracion, self.rol == "admin"),
            ("⚙️ Ajustes", self.abrir_ajustes, True),
            ("🔄 Cambiar Usuario", self.logout, True),
            ("🚪 Salir", self.salir_aplicacion, True),
        ]

        # Crear botones
        row, col = 0, 0
        for texto, func, visible in botones:
            if visible:
                btn = QPushButton(texto)
                btn.setMinimumHeight(55)
                btn.setStyleSheet("font-size: 13px; text-align: left; padding: 10px;")
                btn.clicked.connect(func)
                grid.addWidget(btn, row, col)
                col += 1
                if col > 1:
                    col = 0
                    row += 1

        layout.addLayout(grid)

    def logout(self):
        """Cierra sesión manualmente"""
        # Detener timer de ping
        if hasattr(self, 'timer_ping'):
            self.timer_ping.stop()

        # NO usar gestor de inactividad - deshabilitado por solicitud del usuario
        # idle_manager = get_idle_manager()
        # idle_manager.stop()

        # Registrar cierre de sesión en logs
        log_fin_sesion(self.usuario, self.hostname)

        # Eliminar sesión de la base de datos
        try:
            sesiones_repo.eliminar_sesion(self.usuario, self.hostname)
        except Exception as e:
            logger.error(f"Error al eliminar sesión: {str(e)}")

        # Cerrar sesión en session manager
        session_manager.logout()

        # Cerrar ventanas secundarias si están abiertas
        if hasattr(self, 'ventana_notif') and self.ventana_notif:
            try:
                self.ventana_notif.close()
            except:
                pass

        # Cerrar esta ventana
        self.close()

        # Bucle de login: seguir intentando hasta que el usuario se autentique o quiera salir
        while True:
            # Resetear el flag de salir antes de mostrar el login
            self.login_window.quiere_salir = False
            resultado = self.login_window.exec()

            if resultado == QDialog.Accepted:
                # Usuario autenticado - registrar sesión en BD
                user_data = self.login_window.get_usuario_autenticado()
                hostname = socket.gethostname()
                t = int(time.time())

                try:
                    sesiones_repo.registrar_sesion(user_data["usuario"], t, hostname)
                    log_inicio_sesion(user_data["usuario"], hostname)

                except Exception as e:
                    logger.error(f"Error al registrar sesión: {str(e)}")
                    # Continuar en el bucle de login en caso de error
                    continue

                # Crear y abrir nuevo menú principal
                new_main_window = MainMenuWindow(login_window=self.login_window)
                new_main_window.show()

                # NO reiniciar el gestor de inactividad - deshabilitado
                # idle_manager.start(
                #     login_window=self.login_window, main_window=new_main_window
                # )

                # Salir del bucle después de un login exitoso
                break
            else:
                # Usuario canceló el login
                # Si presionó "Salir" o cerró la ventana, salir de la aplicación
                if self.login_window.quiere_salir:
                    QApplication.quit()
                    break
                # Si fue un error de autenticación, volver a mostrar el login
                continue

    def _actualizar_ping_sesion(self):
        """Actualiza el último ping de la sesión del usuario en la base de datos"""
        try:
            t = int(time.time())
            sesiones_repo.actualizar_ping(self.usuario, self.hostname, t)
        except Exception as e:
            logger.error(f"Error al actualizar ping de sesión: {str(e)}")

    def salir_aplicacion(self):
        """Cierra la aplicación con confirmación"""
        # Preguntar al usuario si está seguro de salir
        respuesta = QMessageBox.question(
            self,
            "Confirmar salida",
            "¿Está seguro que desea salir de la aplicación?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Por defecto, "No"
        )

        if respuesta == QMessageBox.Yes:
            # Usuario confirmó la salida - cerrar la ventana
            self.close()

    def closeEvent(self, event):
        """Cuando se cierra el menú principal, confirmar y crear backup si está configurado"""
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
            # Detener timer de ping
            if hasattr(self, 'timer_ping'):
                self.timer_ping.stop()

            # Eliminar sesión de la base de datos
            try:
                sesiones_repo.eliminar_sesion(self.usuario, self.hostname)
                log_fin_sesion(self.usuario, self.hostname)
            except Exception as e:
                logger.error(f"Error al eliminar sesión al cerrar: {str(e)}")

            # Crear backup automático al cerrar si está configurado
            try:
                from src.services.backup_config_service import obtener_configuracion
                config = obtener_configuracion()

                if config.backup_auto_cierre:
                    # Importar y ejecutar backup
                    import sys
                    from pathlib import Path
                    ROOT_DIR = Path(__file__).parent
                    sys.path.insert(0, str(ROOT_DIR))

                    from scripts.backup_db import crear_backup
                    crear_backup(mostrar_log=True, forzar=False)
            except Exception as e:
                # No bloquear el cierre si falla el backup
                logger.warning(f"No se pudo crear backup automático al cerrar: {e}")

            # NO usar idle manager - deshabilitado
            # idle_manager = get_idle_manager()
            # idle_manager.stop()
            event.accept()
        else:
            # Usuario canceló el cierre - ignorar el evento
            event.ignore()

    def crear_encabezado(self, layout):
        """Crea el encabezado con bienvenida y notificaciones"""
        # Contenedor para el encabezado
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 10, 10, 10)

        # Label de bienvenida
        self.label_bienvenida = QLabel(f"👤 Bienvenido, {self.usuario}")
        self.label_bienvenida.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.label_bienvenida)

        # Botón de notificaciones (campana)
        self.btn_notificaciones = QPushButton("🔔")
        self.btn_notificaciones.setFixedSize(70, 60)
        self.btn_notificaciones.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                background-color: #f1f5f9;
                border: 2px solid #cbd5e1;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
                border-color: #94a3b8;
            }
        """)
        self.btn_notificaciones.clicked.connect(self.abrir_notificaciones)
        self.btn_notificaciones.setToolTip("Ver notificaciones")
        header_layout.addWidget(self.btn_notificaciones)

        layout.addWidget(header_widget)

    def actualizar_contador_notificaciones(self):
        """Actualiza el contador de notificaciones en la bienvenida"""
        try:
            # Verificar que los widgets aún existen antes de actualizar
            if not hasattr(self, 'label_bienvenida') or not hasattr(self, 'btn_notificaciones'):
                return

            # Verificar que los widgets no han sido destruidos
            try:
                _ = self.label_bienvenida.text()
            except RuntimeError:
                # Widget ya destruido, salir silenciosamente
                return

            from src.services import notificaciones_service

            # Contar notificaciones
            total = notificaciones_service.contar_notificaciones(self.usuario)

            if total > 0:
                # Actualizar texto de bienvenida
                self.label_bienvenida.setText(
                    f"👤 Bienvenido, {self.usuario}. "
                    f"Tienes {total} notificación{'es' if total != 1 else ''} por revisar"
                )

                # Actualizar botón de campana con badge
                self.btn_notificaciones.setText(f"🔔\n{total}")
                self.btn_notificaciones.setStyleSheet("""
                    QPushButton {
                        font-size: 16px;
                        font-weight: bold;
                        background-color: #fef3c7;
                        border: 2px solid #fbbf24;
                        border-radius: 8px;
                        color: #92400e;
                        padding: 4px;
                    }
                    QPushButton:hover {
                        background-color: #fde68a;
                        border-color: #f59e0b;
                    }
                """)
            else:
                self.label_bienvenida.setText(f"👤 Bienvenido, {self.usuario}")
                self.btn_notificaciones.setText("🔔")

        except RuntimeError:
            # Widget ya destruido, salir silenciosamente
            pass
        except Exception as e:
            from src.core.logger import logger
            logger.exception(f"Error al actualizar notificaciones: {e}")

    def generar_notificaciones_inicio(self):
        """Genera notificaciones automáticamente al iniciar sesión"""
        try:
            from src.services import notificaciones_service

            # Generar notificaciones en segundo plano
            notificaciones_service.generar_notificaciones_usuario(self.usuario)

        except Exception as e:
            from src.core.logger import logger
            logger.exception(f"Error al generar notificaciones de inicio: {e}")

    def abrir_notificaciones(self):
        """Abre la ventana de notificaciones"""
        try:
            from src.ventanas.ventana_notificaciones import VentanaNotificaciones

            self.ventana_notif = VentanaNotificaciones()
            self.ventana_notif.show()

            # Cuando se cierre la ventana, actualizar el contador
            # Usamos una lambda con try-catch para evitar errores si MainMenuWindow ya se destruyó
            self.ventana_notif.destroyed.connect(
                lambda: self.actualizar_contador_notificaciones() if hasattr(self, 'label_bienvenida') else None
            )

        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al abrir notificaciones:\n{e}")

    def abrir_recepcion(self):
        """Abrir ventana de recepción (maximizada)"""
        self.ventana_recep = VentanaRecepcion()
        self.ventana_recep.showMaximized()

    def abrir_movimientos(self):
        """Abrir ventana de movimientos (maximizada)"""
        self.ventana_mov = VentanaMovimientos()
        self.ventana_mov.showMaximized()

    def abrir_maestros(self):
        """Abrir ventana de Maestros"""
        self.maestros = MaestrosWindow()
        self.maestros.show()

    def abrir_imputacion(self):
        """Abrir ventana de imputación (maximizada)"""
        self.ventana_imput = VentanaImputacion()
        self.ventana_imput.showMaximized()

    def abrir_info_menu(self):
        """Abrir submenu de informes"""
        self.menu_info = MenuInformes()
        self.menu_info.show()

    def abrir_material_perdido(self):
        """Abrir ventana de material perdido (maximizada)"""
        self.ventana_perdido = VentanaMaterialPerdido()
        self.ventana_perdido.showMaximized()

    def abrir_devolucion(self):
        """Abrir ventana de devolución (maximizada)"""
        self.ventana_devol = VentanaDevolucion()
        self.ventana_devol.showMaximized()

    def abrir_inventario(self):
        """Abrir ventana de inventario físico"""
        self.ventana_inv = VentanaInventario()
        self.ventana_inv.show()

    def abrir_ajustes(self):
        """Abrir menú de ajustes personales"""
        self.menu_ajustes = MenuAjustes()
        self.menu_ajustes.show()

    def abrir_configuracion(self):
        """Abrir menú de configuración del sistema (solo admin)"""
        self.menu_config = MenuConfiguracion()
        self.menu_config.show()

    def no_func(self):
        QMessageBox.information(
            self,
            "ℹ️ Aviso",
            "Esta función aún no está implementada.\n\nEn desarrollo...",
        )


# ========================================
# VENTANA DE SUBMENÚ INFORMES
# ========================================
class MenuInformes(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Informes")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        self.setStyleSheet(ESTILO_VENTANA)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        titulo = QLabel("📊 Informes")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; margin: 15px;")
        layout.addWidget(titulo)

        # Botones con más espaciado
        botones = [
            ("📊 Consulta de Stock", self.abrir_stock),
            ("📋 Histórico de Movimientos", self.abrir_historico),
            ("📦 Ficha Completa de Artículo", self.abrir_ficha),
            ("📈 Análisis de Consumos", self.abrir_consumos),
            ("🛒 Pedido Ideal Sugerido", self.abrir_pedido_ideal),
            ("🚚 Asignaciones de Furgonetas", self.abrir_asignaciones),
            ("📑 Informe Semanal Furgonetas", self.abrir_informe_furgonetas),
        ]

        for texto, func in botones:
            btn = QPushButton(texto)
            btn.setMinimumHeight(55)
            btn.setStyleSheet("font-size: 13px; text-align: left; padding: 10px;")
            btn.clicked.connect(func)
            layout.addWidget(btn)

        # Botón volver
        layout.addStretch()
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.setMinimumHeight(40)
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)

    def abrir_stock(self):
        from src.ventanas.consultas.ventana_stock import VentanaStock

        self.ventana_stock = VentanaStock()
        self.ventana_stock.show()

    def abrir_historico(self):
        from src.ventanas.consultas.ventana_historico import VentanaHistorico

        self.ventana_hist = VentanaHistorico()
        self.ventana_hist.show()

    def abrir_ficha(self):
        from src.ventanas.consultas.ventana_ficha_articulo import VentanaFichaArticulo

        self.ventana_ficha = VentanaFichaArticulo()
        self.ventana_ficha.show()

    def abrir_consumos(self):
        """Abrir ventana consolidada de análisis de consumos"""
        self.ventana_consumos = VentanaConsumos()
        self.ventana_consumos.show()

    def abrir_pedido_ideal(self):
        """Abrir ventana de cálculo de pedido ideal"""
        self.ventana_pedido_ideal = VentanaPedidoIdeal()
        self.ventana_pedido_ideal.show()

    def abrir_asignaciones(self):
        """Abrir ventana de consulta de asignaciones de furgonetas"""
        from src.ventanas.consultas.ventana_asignaciones import VentanaAsignaciones
        self.ventana_asignaciones = VentanaAsignaciones()
        self.ventana_asignaciones.show()

    def abrir_informe_furgonetas(self):
        """Abrir ventana de informe semanal de furgonetas"""
        self.ventana_informe_furg = VentanaInformeFurgonetas()
        self.ventana_informe_furg.show()

    def no_func(self):
        QMessageBox.information(
            self,
            "ℹ️ Aviso",
            "Esta función aún no está implementada.\n\nEn desarrollo...",
        )


# ========================================
# VENTANA DE MAESTROS
# ========================================
class MaestrosWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Gestión de Maestros")
        self.setMinimumSize(500, 500)
        self.resize(600, 650)
        self.setStyleSheet(ESTILO_VENTANA)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        titulo = QLabel("📋 Gestión de Datos Maestros")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; margin: 15px;")
        layout.addWidget(titulo)

        # Botones de maestros
        botones = [
            ("🏭 Proveedores", self.abrir_proveedores),
            ("📦 Artículos", self.abrir_articulos),
            ("👷 Operarios", self.abrir_operarios),
            ("📂 Familias", self.abrir_familias),
            ("📍 Ubicaciones", self.abrir_ubicaciones),
            ("🚚 Furgonetas", self.abrir_furgonetas),
        ]

        for i, (texto, func) in enumerate(botones):
            btn = QPushButton(texto)
            btn.setMinimumHeight(50)
            btn.setStyleSheet("font-size: 13px; text-align: left; padding: 10px;")
            btn.clicked.connect(func)
            layout.addWidget(btn)
            # Agregar espaciado explícito entre botones (excepto después del último)
            if i < len(botones) - 1:
                layout.addSpacing(10)

        # Botón volver
        layout.addStretch()
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.setMinimumHeight(40)
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)

    def abrir_proveedores(self):
        self.ventana_prov = VentanaProveedores()
        self.ventana_prov.show()

    def abrir_familias(self):
        self.ventana_fam = VentanaFamilias()
        self.ventana_fam.show()

    def abrir_ubicaciones(self):
        self.ventana_ubic = VentanaUbicaciones()
        self.ventana_ubic.show()

    def abrir_operarios(self):
        self.ventana_oper = VentanaOperarios()
        self.ventana_oper.show()

    def abrir_articulos(self):
        self.ventana_art = VentanaArticulos()
        self.ventana_art.show()

    def abrir_furgonetas(self):
        """Abrir ventana de gestión de furgonetas/almacenes"""
        self.ventana_furg = VentanaFurgonetas()
        self.ventana_furg.show()


# ========================================
# VENTANA DE AJUSTES PERSONALES
# ========================================
class MenuAjustes(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Ajustes Personales")
        self.setMinimumSize(450, 350)
        self.resize(550, 450)
        self.setStyleSheet(ESTILO_VENTANA)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        titulo = QLabel("⚙️ Ajustes Personales")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; margin: 15px;")
        layout.addWidget(titulo)

        # Descripción
        desc = QLabel(
            f"Usuario: {session_manager.get_usuario_actual()}\n"
            "Configure sus preferencias personales"
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: gray; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Botones con más espaciado
        botones = [
            ("🔑 Cambiar Mi Contraseña", self.cambiar_password),
            ("🎨 Preferencias de Visualización", self.abrir_preferencias_visualizacion),
            ("🔔 Notificaciones", self.abrir_notificaciones),
        ]

        for i, (texto, func) in enumerate(botones):
            btn = QPushButton(texto)
            btn.setMinimumHeight(55)
            btn.setStyleSheet("font-size: 13px; text-align: left; padding: 10px;")
            btn.clicked.connect(func)
            layout.addWidget(btn)
            # Agregar espaciado explícito entre botones (excepto después del último)
            if i < len(botones) - 1:
                layout.addSpacing(10)

        # Botón volver
        layout.addStretch()
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.setMinimumHeight(40)
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)

    def cambiar_password(self):
        """Abrir diálogo para cambiar contraseña propia"""
        dialogo = DialogoCambiarPassword(self)
        dialogo.exec()

    def abrir_preferencias_visualizacion(self):
        """Muestra preferencias de visualización"""
        mensaje = """
<h3>🎨 Preferencias de Visualización</h3>

<h4>Configuraciones Disponibles</h4>

<p><b>Tamaños de Fuente:</b> Los tamaños de fuente están definidos en los estilos del sistema.</p>

<p><b>Colores y Tema:</b> El sistema utiliza un esquema de colores definido en src/ui/estilos.py</p>

<h4>Personalización</h4>
<p>Para personalizar la apariencia del sistema:</p>
<ul>
<li>Edite el archivo <code>src/ui/estilos.py</code></li>
<li>Modifique las constantes de color y estilo</li>
<li>Reinicie la aplicación para aplicar los cambios</li>
</ul>

<h4>Ajustes de Ventana</h4>
<ul>
<li>Tamaños de ventana: Se ajustan automáticamente o pueden redimensionarse manualmente</li>
<li>Posición: Las ventanas recuerdan su última posición</li>
</ul>

<h4>Próximas Mejoras</h4>
<p>En futuras versiones se añadirán:</p>
<ul>
<li>Selector de temas (claro/oscuro)</li>
<li>Ajuste de tamaño de fuente desde la interfaz</li>
<li>Personalización de colores</li>
<li>Configuración de idioma</li>
</ul>
        """

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("🎨 Preferencias de Visualización")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(mensaje)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec()

    def abrir_notificaciones(self):
        """Muestra configuración de notificaciones"""
        mensaje = """
<h3>🔔 Notificaciones</h3>

<h4>Sistema de Alertas</h4>
<p>El sistema incluye notificaciones para eventos importantes:</p>

<h4>Alertas Implementadas</h4>
<ul>
<li><b>Stock bajo:</b> Cuando un artículo alcanza el stock mínimo</li>
<li><b>Stock crítico:</b> Cuando el stock es cero o negativo</li>
<li><b>Errores de operación:</b> Mensajes de error en operaciones</li>
<li><b>Confirmaciones:</b> Confirmación de operaciones exitosas</li>
</ul>

<h4>Visualización</h4>
<ul>
<li>Iconos de estado en las tablas (🔴 crítico, 🟡 bajo, 🟢 normal)</li>
<li>Mensajes emergentes (QMessageBox)</li>
<li>Colores de fondo en filas de tablas</li>
</ul>

<h4>Próximas Mejoras</h4>
<p>En desarrollo:</p>
<ul>
<li>Panel de notificaciones centralizado</li>
<li>Notificaciones por email</li>
<li>Alertas configurables por usuario</li>
<li>Historial de notificaciones</li>
<li>Notificaciones de escritorio del sistema operativo</li>
</ul>

<h4>Configuración Actual</h4>
<p>Las notificaciones están activadas por defecto y no se pueden desactivar para garantizar que el usuario esté informado de eventos críticos.</p>
        """

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("🔔 Notificaciones")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(mensaje)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec()

    def no_func(self):
        QMessageBox.information(
            self,
            "ℹ️ Aviso",
            "Esta función aún no está implementada.\n\nEn desarrollo...",
        )


# ========================================
# VENTANA DE CONFIGURACIÓN DEL SISTEMA
# ========================================
class MenuConfiguracion(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔧 Configuración del Sistema")
        self.setMinimumSize(500, 600)
        self.resize(600, 760)
        self.setStyleSheet(ESTILO_VENTANA)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        titulo = QLabel("🔧 Configuración del Sistema")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; margin: 15px;")
        layout.addWidget(titulo)

        # Descripción
        desc = QLabel("Configuración avanzada del sistema\n(Solo administradores)")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: gray; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Botones con más espaciado
        botones = [
            ("👥 Gestión de Usuarios", self.abrir_usuarios),
            ("🗄️ Gestión de Base de Datos", self.abrir_gestion_bd),
            ("💾 Backup y Restauración", self.abrir_backup),
            ("📊 Estadísticas del Sistema", self.abrir_estadisticas_sistema),
            ("🔒 Seguridad y Permisos", self.abrir_seguridad_permisos),
        ]

        for i, (texto, func) in enumerate(botones):
            btn = QPushButton(texto)
            btn.setMinimumHeight(55)
            btn.setStyleSheet("font-size: 13px; text-align: left; padding: 10px;")
            btn.clicked.connect(func)
            layout.addWidget(btn)
            # Agregar espaciado explícito entre botones (excepto después del último)
            if i < len(botones) - 1:
                layout.addSpacing(10)

        # Botón volver
        layout.addStretch()
        btn_volver = QPushButton("⬅️ Volver")
        btn_volver.setMinimumHeight(40)
        btn_volver.clicked.connect(self.close)
        layout.addWidget(btn_volver)

    def abrir_usuarios(self):
        """Abrir ventana de gestión de usuarios (solo admin)"""
        self.ventana_usuarios = VentanaUsuarios()
        self.ventana_usuarios.show()

    def abrir_gestion_bd(self):
        """Abrir diálogo de gestión de base de datos"""
        from src.ventanas.dialogs_configuracion import DialogoGestionBD
        dialogo = DialogoGestionBD(self)
        dialogo.exec()

    def abrir_backup(self):
        """Abrir diálogo de backup y restauración"""
        from src.ventanas.dialogs_configuracion import DialogoBackupRestauracion
        dialogo = DialogoBackupRestauracion(self)
        dialogo.exec()

    def abrir_estadisticas_sistema(self):
        """Muestra estadísticas generales del sistema"""
        try:
            from src.core.db_utils import fetch_all

            # Obtener estadísticas de la base de datos
            stats = {}

            # Contar artículos
            resultado = fetch_all("SELECT COUNT(*) as total FROM articulos WHERE activo = 1")
            stats['articulos'] = resultado[0]['total'] if resultado else 0

            # Contar movimientos del último mes (PostgreSQL)
            resultado = fetch_all("""
                SELECT COUNT(*) as total
                FROM movimientos
                WHERE fecha >= CURRENT_DATE - INTERVAL '30 days'
            """)
            stats['movimientos_mes'] = resultado[0]['total'] if resultado else 0

            # Contar OTs del último mes (PostgreSQL)
            resultado = fetch_all("""
                SELECT COUNT(DISTINCT ot) as total
                FROM movimientos
                WHERE ot IS NOT NULL AND ot != ''
                AND fecha >= CURRENT_DATE - INTERVAL '30 days'
            """)
            stats['ots_mes'] = resultado[0]['total'] if resultado else 0

            # Contar usuarios
            resultado = fetch_all("SELECT COUNT(*) as total FROM usuarios WHERE activo = 1")
            stats['usuarios'] = resultado[0]['total'] if resultado else 0

            # Contar furgonetas (PostgreSQL: desde 'almacenes')
            resultado = fetch_all("SELECT COUNT(*) as total FROM almacenes WHERE tipo = 'furgoneta'")
            stats['furgonetas'] = resultado[0]['total'] if resultado else 0

            # Valor total del stock (usando vista vw_stock_total)
            resultado = fetch_all("""
                SELECT SUM(COALESCE(s.stock_total, 0) * COALESCE(a.coste, 0)) as total
                FROM articulos a
                LEFT JOIN vw_stock_total s ON a.id = s.articulo_id
                WHERE a.activo = 1
            """)
            valor_stock = resultado[0]['total'] if resultado and resultado[0]['total'] else 0
            # Convertir Decimal a float para formato
            valor_stock = float(valor_stock) if valor_stock else 0.0

            # Artículos con stock bajo (usando vista vw_stock_total y min_alerta)
            resultado = fetch_all("""
                SELECT COUNT(*) as total
                FROM articulos a
                LEFT JOIN vw_stock_total s ON a.id = s.articulo_id
                WHERE a.activo = 1
                AND COALESCE(s.stock_total, 0) <= a.min_alerta
                AND a.min_alerta > 0
            """)
            stats['stock_bajo'] = resultado[0]['total'] if resultado else 0

            # Tamaño de la base de datos PostgreSQL
            try:
                resultado = fetch_all("SELECT pg_database_size(current_database()) as size")
                db_size = resultado[0]['size'] / (1024 * 1024) if resultado else 0
                stats['db_size'] = f"{db_size:.2f} MB"
            except:
                stats['db_size'] = "N/A"

            # Mostrar diálogo con estadísticas
            mensaje = f"""
<h3>📊 Estadísticas del Sistema</h3>

<h4>📦 Inventario</h4>
<ul>
<li><b>Artículos activos:</b> {stats['articulos']}</li>
<li><b>Valor total del stock:</b> {valor_stock:.2f}€</li>
<li><b>Artículos con stock bajo:</b> {stats['stock_bajo']}</li>
</ul>

<h4>📋 Actividad (últimos 30 días)</h4>
<ul>
<li><b>Movimientos:</b> {stats['movimientos_mes']}</li>
<li><b>OTs diferentes:</b> {stats['ots_mes']}</li>
</ul>

<h4>👥 Usuarios y Recursos</h4>
<ul>
<li><b>Usuarios activos:</b> {stats['usuarios']}</li>
<li><b>Furgonetas activas:</b> {stats['furgonetas']}</li>
</ul>

<h4>💾 Base de Datos</h4>
<ul>
<li><b>Tamaño:</b> {stats['db_size']}</li>
</ul>
            """

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("📊 Estadísticas del Sistema")
            msg_box.setTextFormat(Qt.RichText)
            msg_box.setText(mensaje)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.exec()

        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Error",
                f"Error al obtener estadísticas:\n{e}"
            )

    def abrir_seguridad_permisos(self):
        """Muestra información sobre seguridad y permisos"""
        mensaje = """
<h3>🔒 Seguridad y Permisos</h3>

<h4>Sistema de Usuarios</h4>
<p>El sistema cuenta con gestión de usuarios con contraseñas cifradas.</p>

<h4>Niveles de Acceso</h4>
<ul>
<li><b>Administrador:</b> Acceso completo al sistema, incluyendo configuración y gestión de usuarios</li>
<li><b>Usuario estándar:</b> Acceso a operaciones del almacén y consultas</li>
</ul>

<h4>Auditoría</h4>
<p>Todas las operaciones quedan registradas en el historial con:</p>
<ul>
<li>Usuario que realizó la operación</li>
<li>Fecha y hora</li>
<li>Tipo de operación</li>
<li>Detalles de la operación</li>
</ul>

<h4>Backup y Recuperación</h4>
<p>El sistema incluye funcionalidades de backup y restauración de la base de datos para proteger los datos.</p>

<h4>Configuración Adicional</h4>
<p>Para configuraciones avanzadas de permisos por rol o restricciones específicas, contacte con el administrador del sistema.</p>
        """

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("🔒 Seguridad y Permisos")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(mensaje)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec()

    def no_func(self):
        QMessageBox.information(
            self,
            "ℹ️ Aviso",
            "Esta función aún no está implementada.\n\nEn desarrollo...",
        )


# ========================================
# PUNTO DE ENTRADA DE LA APLICACIÓN
# ========================================
def main():
    app = QApplication(sys.argv)

    # Configurar icono de la aplicación
    base_dir = Path(__file__).parent
    icon_path = base_dir / "assets" / "images" / "icono_climatot.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Bucle de login: seguir intentando hasta que el usuario se autentique o quiera salir
    while True:
        login = VentanaLogin()
        resultado = login.exec()

        if resultado == QDialog.Accepted:
            # Usuario autenticado - registrar sesión en BD
            user_data = login.get_usuario_autenticado()
            hostname = socket.gethostname()
            t = int(time.time())

            try:
                sesiones_repo.registrar_sesion(user_data["usuario"], t, hostname)
                log_inicio_sesion(user_data["usuario"], hostname)

            except Exception as e:
                logger.error(f"Error al registrar sesión: {str(e)}")
                QMessageBox.critical(
                    None, "Error", f"Error al iniciar sesión:\n{str(e)}"
                )
                # No cerrar, volver a intentar el login
                continue

            # Crear y mostrar el menú principal
            main_window = MainMenuWindow(login_window=login)
            main_window.show()

            # NO iniciar el gestor de inactividad - deshabilitado por solicitud del usuario
            # idle_manager = get_idle_manager()
            # idle_manager.start(login_window=login, main_window=main_window)

            sys.exit(app.exec())
        else:
            # Usuario canceló el login
            # Si presionó "Salir" o cerró la ventana, salir de la aplicación
            if login.quiere_salir:
                sys.exit(0)
            # Si fue un error de autenticación u otro, volver a mostrar el login
            continue


if __name__ == "__main__":
    main()
