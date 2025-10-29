# app.py - Programa Principal - Sistema Climatot Almacén
import sys
import time
import socket
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGridLayout
)
from PySide6.QtCore import Qt
from src.ventanas.operativas.ventana_recepcion import VentanaRecepcion
from src.ventanas.operativas.ventana_movimientos import VentanaMovimientos
from src.ventanas.operativas.ventana_imputacion import VentanaImputacion
from src.ventanas.maestros.ventana_proveedores import VentanaProveedores
from src.ventanas.maestros.ventana_familias import VentanaFamilias
from src.ventanas.maestros.ventana_ubicaciones import VentanaUbicaciones
from src.ventanas.maestros.ventana_operarios import VentanaOperarios
from src.ventanas.maestros.ventana_articulos import VentanaArticulos
from src.ventanas.maestros.ventana_furgonetas import VentanaFurgonetas  # ← NUEVO: Gestión de Furgonetas/Almacenes
from src.ventanas.consultas.ventana_stock import VentanaStock
from src.ventanas.consultas.ventana_consumos import VentanaConsumos
from src.ventanas.consultas.ventana_pedido_ideal import VentanaPedidoIdeal
from src.ventanas.operativas.ventana_material_perdido import VentanaMaterialPerdido
from src.ventanas.operativas.ventana_devolucion import VentanaDevolucion
from src.ventanas.operativas.ventana_inventario import VentanaInventario
from src.ventanas.consultas.ventana_historico import VentanaHistorico
from src.ui.estilos import ESTILO_LOGIN, ESTILO_VENTANA
from src.core.idle_manager import get_idle_manager

# ========================================
# IMPORTAR FUNCIONES CENTRALIZADAS
# ========================================
from src.core.db_utils import get_con, hash_pwd, DB_PATH

# ========================================
# VENTANA DE LOGIN
# ========================================
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔐 Acceso - Climatot Almacén")
        self.setFixedSize(450, 400)
        self.setStyleSheet(ESTILO_LOGIN)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Título
        self.label = QLabel("🏢 Sistema de Gestión de Almacén")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 5px;")
        
        label_subtitle = QLabel("Inicia sesión para continuar")
        label_subtitle.setAlignment(Qt.AlignCenter)
        label_subtitle.setStyleSheet("color: #64748b; margin-bottom: 20px; font-size: 13px;")
        
        # Campos de entrada
        self.user = QLineEdit()
        self.user.setPlaceholderText("👤 Usuario")
        
        self.passw = QLineEdit()
        self.passw.setPlaceholderText("🔒 Contraseña")
        self.passw.setEchoMode(QLineEdit.Password)
        
        # Botones
        self.btn_login = QPushButton("✅ Entrar")
        self.btn_login.clicked.connect(self.login)
        
        self.btn_salir = QPushButton("❌ Salir")
        self.btn_salir.clicked.connect(self.close)
        
        # Agregar todo al layout principal
        layout.addWidget(self.label)
        layout.addWidget(label_subtitle)
        layout.addWidget(self.user)
        layout.addWidget(self.passw)
        layout.addWidget(self.btn_login)
        layout.addWidget(self.btn_salir)
        layout.addStretch()
        
        # Enter para login
        self.passw.returnPressed.connect(self.login)
        self.user.returnPressed.connect(self.login)
    
    def login(self):
        """Procesa el login del usuario"""
        u = self.user.text().strip()
        p = self.passw.text().strip()
        
        if not u or not p:
            QMessageBox.warning(self, "⚠️ Error", "Usuario y contraseña son obligatorios.")
            return
        
        try:
            con = get_con()
            cur = con.cursor()
            cur.execute("SELECT pass_hash, rol, activo FROM usuarios WHERE usuario=?", (u,))
            row = cur.fetchone()
            con.close()
            
            if not row:
                QMessageBox.warning(self, "❌ Error", "Usuario no encontrado.")
                return
            
            if row[2] == 0:
                QMessageBox.warning(self, "❌ Error", "Usuario desactivado. Contacta al administrador.")
                return
            
            if row[0] != hash_pwd(p):
                QMessageBox.warning(self, "❌ Error", "Contraseña incorrecta.")
                return
            
            # Registrar sesión
            hostname = socket.gethostname()
            t = int(time.time())
            con = get_con()
            cur = con.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO sesiones(usuario, inicio_utc, ultimo_ping_utc, hostname) VALUES(?,?,?,?)",
                (u, t, t, hostname),
            )
            con.commit()
            con.close()
            
            # Abrir menú principal
            self.hide()
            self.main = MainMenuWindow(usuario=u, rol=row[1], login_window=self)
            self.main.show()
            
            # Iniciar el gestor de inactividad
            idle_manager = get_idle_manager()
            idle_manager.start(login_window=self, main_window=self.main)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al conectar con la base de datos:\n{e}")

# ========================================
# VENTANA MENÚ PRINCIPAL
# ========================================
class MainMenuWindow(QWidget):
    def __init__(self, usuario, rol, login_window):
        super().__init__()
        self.usuario = usuario
        self.rol = rol
        self.login_window = login_window
        self.setWindowTitle(f"📋 Menú Principal - {usuario} ({rol})")
        self.setFixedSize(700, 550)
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)
        
        # Encabezado
        header = QLabel(f"👤 Bienvenido, {usuario}")
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
            ("⚠️ Material Perdido", self.abrir_material_perdido, rol == "admin"),
            ("📊 Inventario Físico", self.abrir_inventario, True),
            ("ℹ️ Info e Informes", self.abrir_info_menu, True),
            ("⚙️ Maestros", self.abrir_maestros, True),
            ("🔧 Configuración", self.no_func, rol == "admin"),
            ("🔄 Cambiar Usuario", self.logout, True),
            ("🚪 Salir", self.close, True),
        ]
        
        # Crear botones
        row, col = 0, 0
        for texto, func, visible in botones:
            if visible:
                btn = QPushButton(texto)
                btn.setMinimumHeight(55)
                btn.setMinimumWidth(200)
                btn.setStyleSheet("font-size: 13px; text-align: left; padding: 10px;")
                btn.clicked.connect(func)
                grid.addWidget(btn, row, col)
                col += 1
                if col > 1:
                    col = 0
                    row += 1
        
        layout.addLayout(grid)
        
        # NOTA: El timer de inactividad ahora se gestiona globalmente
        # No hace falta código aquí, el idle_manager se encarga de todo
    
    def logout(self):
        """Cierra sesión manualmente"""
        # Detener el gestor de inactividad
        idle_manager = get_idle_manager()
        idle_manager.stop()
        
        # Cerrar esta ventana
        self.close()
        
        # Mostrar el login
        self.login_window.show()
        self.login_window.user.clear()
        self.login_window.passw.clear()
        self.login_window.user.setFocus()
    
    def closeEvent(self, event):
        """Cuando se cierra el menú principal, detener el idle manager"""
        idle_manager = get_idle_manager()
        idle_manager.stop()
        event.accept()
    
    def abrir_recepcion(self):
        """Abrir ventana de recepción"""
        self.ventana_recep = VentanaRecepcion()
        self.ventana_recep.show()
    
    def abrir_movimientos(self):
        """Abrir ventana de movimientos"""
        self.ventana_mov = VentanaMovimientos()
        self.ventana_mov.show()
    
    def abrir_maestros(self):
        """Abrir ventana de Maestros"""
        self.maestros = MaestrosWindow()
        self.maestros.show()

    def abrir_imputacion(self):
        """Abrir ventana de imputación"""
        self.ventana_imput = VentanaImputacion()
        self.ventana_imput.show()
    
    def abrir_info_menu(self):
        """Abrir submenu de informes"""
        self.menu_info = MenuInformes()
        self.menu_info.show()
    
    def abrir_material_perdido(self):
        """Abrir ventana de material perdido"""
        self.ventana_perdido = VentanaMaterialPerdido()
        self.ventana_perdido.show()
    
    def abrir_devolucion(self):
        """Abrir ventana de devolución"""
        self.ventana_devol = VentanaDevolucion()
        self.ventana_devol.show()
    
    def abrir_inventario(self):
        """Abrir ventana de inventario físico"""
        self.ventana_inv = VentanaInventario()
        self.ventana_inv.show()
    
    def no_func(self):
        QMessageBox.information(self, "ℹ️ Aviso", "Esta función aún no está implementada.\n\nEn desarrollo...")
    
# ========================================
# VENTANA DE SUBMENÚ INFORMES
# ========================================
class MenuInformes(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ℹ️ Información e Informes")
        self.setFixedSize(600, 480)  # ← Aumentado de 400 a 480
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)  # ← Aumentado de 10 a 12
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        titulo = QLabel("ℹ️ Información e Informes")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; margin: 15px;")
        layout.addWidget(titulo)
        
        # Botones con más espaciado
        botones = [
            ("📊 Consulta de Stock", self.abrir_stock),
            ("📋 Histórico de Movimientos", self.abrir_historico),
            ("📦 Ficha Completa de Artículo", self.abrir_ficha),
            ("📈 Análisis de Consumos", self.abrir_consumos),  # ← NUEVA: Consolidada con tabs
            ("🛒 Pedido Ideal Sugerido", self.abrir_pedido_ideal),  # ← NUEVA: Cálculo de pedidos
        ]
        
        for texto, func in botones:
            btn = QPushButton(texto)
            btn.setMinimumHeight(55)  # ← Aumentado de 50 a 55
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
    
    def no_func(self):
        QMessageBox.information(self, "ℹ️ Aviso", "Esta función aún no está implementada.\n\nEn desarrollo...")
    
# ========================================
# VENTANA DE MAESTROS
# ========================================
class MaestrosWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Gestión de Maestros")
        self.setFixedSize(600, 450)
        self.setStyleSheet(ESTILO_VENTANA)
        
        layout = QVBoxLayout(self)
        
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
            ("🏢 Almacenes/Furgonetas", self.abrir_furgonetas),  # ← ACTUALIZADO
        ]
        
        for texto, func in botones:
            btn = QPushButton(texto)
            btn.setMinimumHeight(50)
            btn.setStyleSheet("font-size: 13px; text-align: left; padding: 10px;")
            btn.clicked.connect(func)
            layout.addWidget(btn)
        
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
    
    def no_func(self):
        QMessageBox.information(self, "ℹ️ Aviso", "Esta función aún no está implementada.\n\nEn desarrollo...")
    
# ========================================
# MAIN - INICIAR APLICACIÓN
# ========================================
def main():
    app = QApplication(sys.argv)
    
    if not DB_PATH.exists():
        QMessageBox.critical(
            None, 
            "❌ Error", 
            f"No se encuentra la base de datos.\n\n"
            f"Ubicación esperada: {DB_PATH}\n\n"
            f"Ejecuta primero: python init_db.py"
        )
        sys.exit(1)
    
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()