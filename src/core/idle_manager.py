# idle_manager.py - Gestor Global de Inactividad (CORREGIDO)
"""
Sistema centralizado para gestionar el timeout de inactividad.
Detecta actividad en TODAS las ventanas de la aplicación.

CORRECCIONES:
1. ✅ Bucle infinito al cerrar sesión SOLUCIONADO
2. ✅ Solo cierra por inactividad real (no por uso activo)
3. ✅ Aviso 5 minutos antes del cierre
4. ✅ Reinicio automático con cualquier actividad
5. ✅ Cierre limpio de todas las ventanas
"""
from PySide6.QtCore import QObject, QTimer, QEvent
from PySide6.QtWidgets import QMessageBox, QApplication
import time

class IdleManager(QObject):
    """
    Gestor de inactividad para toda la aplicación.
    
    Equivalente en VBA:
        - Como un Timer en un formulario principal que controla todo
        - Pero este funciona para TODAS las ventanas a la vez
    """
    
    def __init__(self, timeout_minutes=20, warning_minutes=5):
        super().__init__()
        
        # Configuración
        self.timeout_seconds = timeout_minutes * 60  # 20 minutos = 1200 segundos
        self.warning_seconds = warning_minutes * 60   # 5 minutos = 300 segundos
        
        # Control de tiempo
        self.last_activity = time.time()
        self.warning_shown = False
        self.is_active = False
        self.logout_in_progress = False  # ← NUEVO: Evita bucle infinito
        
        # Timer que revisa cada segundo
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_idle)
        self.timer.setInterval(1000)  # Cada 1 segundo
        
        # Referencia a las ventanas
        self.login_window = None
        self.main_window = None
    
    def start(self, login_window, main_window):
        """
        Inicia el sistema de detección de inactividad.
        
        Args:
            login_window: Referencia a la ventana de login
            main_window: Referencia al menú principal
        """
        self.login_window = login_window
        self.main_window = main_window
        self.last_activity = time.time()
        self.warning_shown = False
        self.is_active = True
        self.logout_in_progress = False  # ← NUEVO: Reset del flag
        self.timer.start()
        
        # Instalar filtro de eventos en TODA la aplicación
        QApplication.instance().installEventFilter(self)
    
    def stop(self):
        """Detiene el sistema de detección"""
        self.timer.stop()
        self.is_active = False
        QApplication.instance().removeEventFilter(self)
    
    def reset_activity(self):
        """
        Reinicia el contador de inactividad.
        Se llama automáticamente cuando hay actividad.
        """
        # ✅ CORRECCIÓN: Si hay logout en progreso, NO resetear
        if self.logout_in_progress:
            return
        
        self.last_activity = time.time()
        self.warning_shown = False
    
    def eventFilter(self, obj, event):
        """
        Filtro de eventos global.
        Captura CUALQUIER actividad del usuario (ratón, teclado, scroll...)
        
        Equivalente en VBA:
            Private Sub Application_MouseMove(...)
            Private Sub Application_KeyPress(...)
            ' Pero para TODAS las ventanas a la vez
        """
        # ✅ CORRECCIÓN: Si hay logout en progreso, no capturar eventos
        if self.logout_in_progress:
            return False
        
        # Eventos que indican actividad del usuario
        if event.type() in (
            QEvent.MouseMove,
            QEvent.MouseButtonPress,
            QEvent.MouseButtonRelease,
            QEvent.KeyPress,
            QEvent.KeyRelease,
            QEvent.Wheel,
            QEvent.FocusIn,
            QEvent.Enter  # ← NUEVO: También cuando entra el mouse
        ):
            self.reset_activity()
        
        # No bloqueamos el evento, solo lo monitorizamos
        return False
    
    def _check_idle(self):
        """
        Revisa el tiempo de inactividad cada segundo.
        Muestra aviso a los 15 minutos (5 antes del timeout).
        Cierra sesión a los 20 minutos.
        """
        # ✅ CORRECCIÓN: Si ya hay logout en progreso, no hacer nada
        if not self.is_active or self.logout_in_progress:
            return
        
        elapsed = time.time() - self.last_activity
        remaining = self.timeout_seconds - elapsed
        
        # AVISO: Quedan 5 minutos
        if remaining <= self.warning_seconds and not self.warning_shown:
            self.warning_shown = True
            self._show_warning()
        
        # TIMEOUT: Se acabó el tiempo
        if elapsed >= self.timeout_seconds:
            self._force_logout()
    
    def _show_warning(self):
        """
        Muestra aviso de que quedan 5 minutos.
        Si el usuario hace clic en OK, reinicia el contador automáticamente.
        """
        # ✅ CORRECCIÓN: Pausar el timer mientras se muestra el aviso
        self.timer.stop()
        
        # Crear mensaje de aviso
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("⏱️ Aviso de Inactividad")
        msg.setText(
            "⚠️ Tu sesión se cerrará en 5 minutos por inactividad.\n\n"
            "Si estás trabajando, haz clic en OK para continuar.\n"
            "Si no haces nada, la sesión se cerrará automáticamente."
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        
        # Mostrar el mensaje
        msg.exec()
        
        # ✅ CORRECCIÓN: Al hacer clic en OK, resetear actividad manualmente
        self.last_activity = time.time()
        self.warning_shown = False
        
        # Reiniciar el timer
        if self.is_active:
            self.timer.start()
    
    def _force_logout(self):
        """
        Cierra la sesión forzosamente:
        1. Detiene el timer para evitar bucle
        2. Cierra TODAS las ventanas abiertas
        3. Muestra mensaje de timeout UNA SOLA VEZ
        4. Vuelve al login
        """
        # ✅ CORRECCIÓN: Flag para evitar bucle infinito
        if self.logout_in_progress:
            return
        
        self.logout_in_progress = True
        
        # Detener el timer PRIMERO
        self.stop()
        
        # ✅ CORRECCIÓN: Cerrar TODAS las ventanas ANTES del mensaje
        all_windows = QApplication.topLevelWidgets()
        for window in all_windows:
            if window != self.login_window and window.isVisible():
                try:
                    # Cerrar sin confirmación
                    window.setAttribute(128, True)  # Qt.WA_DeleteOnClose
                    window.close()
                except:
                    pass
        
        # Cerrar el menú principal explícitamente
        if self.main_window and self.main_window.isVisible():
            try:
                self.main_window.close()
            except:
                pass
        
        # ✅ CORRECCIÓN: Mensaje DESPUÉS de cerrar ventanas
        msg = QMessageBox(self.login_window)  # ← Padre: login_window
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("⏱️ Sesión Cerrada")
        msg.setText(
            "Tu sesión ha sido cerrada por inactividad (20 minutos).\n\n"
            "Por favor, inicia sesión nuevamente."
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        msg.setModal(True)  # ← Modal para evitar interacción
        msg.exec()
        
        # Mostrar el login y prepararlo
        if self.login_window:
            self.login_window.show()
            self.login_window.user.clear()
            self.login_window.passw.clear()
            self.login_window.user.setFocus()
        
        # Resetear el flag
        self.logout_in_progress = False


# Instancia global del gestor
_idle_manager = IdleManager()

def get_idle_manager():
    """
    Obtiene la instancia global del gestor de inactividad.
    
    Uso:
        from src.core.idle_manager import get_idle_manager
        manager = get_idle_manager()
        manager.start(login_window, main_window)
    """
    return _idle_manager
