# app.py - Programa Principal - Sistema Climatot Almacén
import socket
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import Qt
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
from src.core.db_utils import DB_PATH, get_con
from src.core.idle_manager import get_idle_manager
from src.core.logger import log_fin_sesion, log_inicio_sesion, logger
from src.core.session_manager import session_manager
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

        self.setWindowTitle(f"📋 Menú Principal - {self.usuario} ({self.rol})")
        self.setMinimumSize(700, 550)
        self.resize(700, 550)
        self.setStyleSheet(ESTILO_VENTANA)

        layout = QVBoxLayout(self)

        # Encabezado
        header = QLabel(f"👤 Bienvenido, {self.usuario}")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin: 15px;")
        layout.addWidget(header)

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
            ("🚪 Salir", self.close, True),
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
        # Detener el gestor de inactividad
        idle_manager = get_idle_manager()
        idle_manager.stop()

        # Registrar cierre de sesión en logs
        log_fin_sesion(self.usuario, socket.gethostname())

        # Cerrar sesión en session manager
        session_manager.logout()

        # Cerrar esta ventana
        self.close()

        # Mostrar el login como diálogo modal
        resultado = self.login_window.exec()

        if resultado == QDialog.Accepted:
            # Usuario autenticado - registrar sesión en BD
            user_data = self.login_window.get_usuario_autenticado()
            hostname = socket.gethostname()
            t = int(time.time())

            try:
                con = get_con()
                cur = con.cursor()
                cur.execute(
                    "INSERT OR REPLACE INTO sesiones(usuario, inicio_utc, ultimo_ping_utc, hostname) VALUES(?,?,?,?)",
                    (user_data["usuario"], t, t, hostname),
                )
                con.commit()
                con.close()

                log_inicio_sesion(user_data["usuario"], hostname)

            except Exception as e:
                logger.error(f"Error al registrar sesión: {str(e)}")

            # Crear y abrir nuevo menú principal
            new_main_window = MainMenuWindow(login_window=self.login_window)
            new_main_window.show()

            # Reiniciar el gestor de inactividad
            idle_manager.start(
                login_window=self.login_window, main_window=new_main_window
            )
        else:
            # Usuario canceló el login - salir de la aplicación
            QApplication.quit()

    def closeEvent(self, event):
        """Cuando se cierra el menú principal, detener el idle manager"""
        idle_manager = get_idle_manager()
        idle_manager.stop()
        event.accept()

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
            ("🎨 Preferencias de Visualización", self.no_func),
            ("🔔 Notificaciones", self.no_func),
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
            ("📊 Estadísticas del Sistema", self.no_func),
            ("🔒 Seguridad y Permisos", self.no_func),
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

    # Mostrar el login como diálogo modal
    login = VentanaLogin()
    resultado = login.exec()

    if resultado == QDialog.Accepted:
        # Usuario autenticado - registrar sesión en BD
        user_data = login.get_usuario_autenticado()
        hostname = socket.gethostname()
        t = int(time.time())

        try:
            con = get_con()
            cur = con.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO sesiones(usuario, inicio_utc, ultimo_ping_utc, hostname) VALUES(?,?,?,?)",
                (user_data["usuario"], t, t, hostname),
            )
            con.commit()
            con.close()

            log_inicio_sesion(user_data["usuario"], hostname)

        except Exception as e:
            logger.error(f"Error al registrar sesión: {str(e)}")
            QMessageBox.critical(
                None, "Error", f"Error al iniciar sesión:\n{str(e)}"
            )
            sys.exit(1)

        # Crear y mostrar el menú principal
        main_window = MainMenuWindow(login_window=login)
        main_window.show()

        # Iniciar el gestor de inactividad
        idle_manager = get_idle_manager()
        idle_manager.start(login_window=login, main_window=main_window)

        sys.exit(app.exec())
    else:
        # Usuario canceló el login
        sys.exit(0)


if __name__ == "__main__":
    main()
