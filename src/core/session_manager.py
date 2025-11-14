"""
Session Manager - Gestión de sesión de usuario activa en la aplicación
"""
from typing import Optional, Dict, Any


class SessionManager:
    """Gestiona la sesión del usuario actual en la aplicación."""

    _instance = None
    _usuario_actual: Optional[str] = None
    _usuario_id: Optional[int] = None
    _rol_actual: Optional[str] = None
    _is_authenticated: bool = False

    def __new__(cls):
        """Implementa el patrón Singleton para garantizar una única instancia."""
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance

    def login(self, usuario: str, rol: str, usuario_id: Optional[int] = None) -> None:
        """Inicia sesión con un usuario."""
        self._usuario_actual = usuario
        self._usuario_id = usuario_id
        self._rol_actual = rol
        self._is_authenticated = True

    def logout(self) -> None:
        """Cierra la sesión del usuario actual."""
        self._usuario_actual = None
        self._usuario_id = None
        self._rol_actual = None
        self._is_authenticated = False

    def get_usuario_actual(self) -> Optional[str]:
        """Obtiene el nombre de usuario de la sesión actual."""
        return self._usuario_actual

    def get_usuario_id(self) -> Optional[int]:
        """Obtiene el ID del usuario de la sesión actual."""
        return self._usuario_id

    def get_rol_actual(self) -> Optional[str]:
        """Obtiene el rol del usuario de la sesión actual."""
        return self._rol_actual

    def is_authenticated(self) -> bool:
        """Verifica si hay una sesión activa."""
        return self._is_authenticated

    def is_admin(self) -> bool:
        """Verifica si el usuario actual es administrador."""
        return self._is_authenticated and self._rol_actual == "admin"

    def is_almacen(self) -> bool:
        """Verifica si el usuario actual tiene rol de almacén."""
        return self._is_authenticated and self._rol_actual in ["admin", "almacen"]

    def is_operario(self) -> bool:
        """Verifica si el usuario actual es operario."""
        return self._is_authenticated and self._rol_actual == "operario"

    def get_session_info(self) -> Dict[str, Any]:
        """Obtiene información completa de la sesión."""
        return {
            'usuario': self._usuario_actual,
            'usuario_id': self._usuario_id,
            'rol': self._rol_actual,
            'authenticated': self._is_authenticated
        }

    def __repr__(self) -> str:
        if self._is_authenticated:
            return f"SessionManager(usuario={self._usuario_actual}, id={self._usuario_id}, rol={self._rol_actual})"
        return "SessionManager(no authenticated)"


# Instancia global del gestor de sesiones
session_manager = SessionManager()
