"""
Repositorio de Sesiones - Gestión de sesiones de usuario
"""
from typing import Optional, Dict, Any
from src.core.db_utils import execute_query, fetch_one, fetch_all


def registrar_sesion(usuario: str, inicio_utc: int, hostname: str) -> bool:
    """
    Registra o actualiza una sesión de usuario.

    Args:
        usuario: Nombre de usuario
        inicio_utc: Timestamp Unix de inicio de sesión
        hostname: Nombre del host/equipo

    Returns:
        True si se registró correctamente
    """
    sql = """
        INSERT INTO sesiones(usuario, inicio_utc, ultimo_ping_utc, hostname)
        VALUES(%s, %s, %s, %s)
        ON CONFLICT (usuario, hostname)
        DO UPDATE SET
            inicio_utc = EXCLUDED.inicio_utc,
            ultimo_ping_utc = EXCLUDED.ultimo_ping_utc
    """
    execute_query(sql, (usuario, inicio_utc, inicio_utc, hostname))
    return True


def actualizar_ping(usuario: str, hostname: str, ultimo_ping_utc: int) -> bool:
    """
    Actualiza el último ping de una sesión activa.

    Args:
        usuario: Nombre de usuario
        hostname: Nombre del host
        ultimo_ping_utc: Timestamp Unix del último ping

    Returns:
        True si se actualizó correctamente
    """
    sql = """
        UPDATE sesiones
        SET ultimo_ping_utc = %s
        WHERE usuario = %s AND hostname = %s
    """
    execute_query(sql, (ultimo_ping_utc, usuario, hostname))
    return True


def obtener_sesion(usuario: str, hostname: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene información de una sesión específica.

    Args:
        usuario: Nombre de usuario
        hostname: Nombre del host

    Returns:
        Diccionario con datos de la sesión o None
    """
    sql = """
        SELECT usuario, inicio_utc, ultimo_ping_utc, hostname
        FROM sesiones
        WHERE usuario = %s AND hostname = %s
    """
    return fetch_one(sql, (usuario, hostname))


def obtener_sesiones_activas() -> list:
    """
    Obtiene todas las sesiones activas en las últimas 24 horas.

    Returns:
        Lista de sesiones activas
    """
    import time
    hace_24h = int(time.time()) - (24 * 3600)

    sql = """
        SELECT usuario, inicio_utc, ultimo_ping_utc, hostname
        FROM sesiones
        WHERE ultimo_ping_utc >= %s
        ORDER BY ultimo_ping_utc DESC
    """
    return fetch_all(sql, (hace_24h,))


def eliminar_sesion(usuario: str, hostname: str) -> bool:
    """
    Elimina una sesión específica.

    Args:
        usuario: Nombre de usuario
        hostname: Nombre del host

    Returns:
        True si se eliminó correctamente
    """
    sql = "DELETE FROM sesiones WHERE usuario = %s AND hostname = %s"
    execute_query(sql, (usuario, hostname))
    return True


def limpiar_sesiones_antiguas(dias: int = 7) -> int:
    """
    Limpia sesiones más antiguas de N días.

    Args:
        dias: Número de días de antigüedad

    Returns:
        Número de sesiones eliminadas
    """
    import time
    limite = int(time.time()) - (dias * 24 * 3600)

    sql = "DELETE FROM sesiones WHERE ultimo_ping_utc < %s"
    return execute_query(sql, (limite,))
