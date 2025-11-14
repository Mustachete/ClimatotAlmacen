# asignaciones_repo.py - Gestión de asignaciones operario-furgoneta
"""
Sistema unificado de asignaciones furgoneta-operario.
Soporta turnos (mañana, tarde, completo) y consultas por fecha.
"""

from typing import Optional, Dict, Any, List
from src.core.db_utils import get_con, fetch_one, fetch_all, execute_query
from src.core.logger import logger


def asignar_furgoneta(
    operario_id: int,
    fecha: str,
    furgoneta_id: int,
    turno: str = 'completo'
) -> bool:
    """
    Asigna una furgoneta a un operario para una fecha y turno específicos.

    Args:
        operario_id: ID del operario
        fecha: Fecha (YYYY-MM-DD)
        furgoneta_id: ID de la furgoneta (almacen con tipo='furgoneta')
        turno: 'manana', 'tarde' o 'completo' (default)

    Returns:
        True si se asignó correctamente
    """
    try:
        # Validar turno
        if turno not in ('manana', 'tarde', 'completo'):
            raise ValueError(f"Turno inválido: {turno}. Debe ser 'manana', 'tarde' o 'completo'")

        sql = """
            INSERT OR REPLACE INTO asignaciones_furgoneta(operario_id, fecha, turno, furgoneta_id)
            VALUES(?, ?, ?, ?)
        """
        execute_query(sql, (operario_id, fecha, turno, furgoneta_id))
        logger.info(f"Furgoneta {furgoneta_id} asignada a operario {operario_id} - {fecha} {turno}")
        return True

    except Exception as e:
        logger.exception(f"Error al asignar furgoneta: {e}")
        raise


def get_furgoneta_asignada(
    operario_id: int,
    fecha: str,
    turno: str = 'completo'
) -> Optional[Dict[str, Any]]:
    """
    Obtiene la furgoneta asignada a un operario en una fecha y turno.

    Args:
        operario_id: ID del operario
        fecha: Fecha (YYYY-MM-DD)
        turno: 'manana', 'tarde' o 'completo'

    Returns:
        Dict con furgoneta_id y furgoneta_nombre, o None
    """
    try:
        sql = """
            SELECT af.furgoneta_id, a.nombre as furgoneta_nombre
            FROM asignaciones_furgoneta af
            JOIN almacenes a ON af.furgoneta_id = a.id
            WHERE af.operario_id = ?
              AND af.fecha = ?
              AND af.turno = ?
        """
        return fetch_one(sql, (operario_id, fecha, turno))

    except Exception as e:
        logger.exception(f"Error al obtener furgoneta asignada: {e}")
        return None


def get_asignaciones_operario(
    operario_id: int,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Obtiene todas las asignaciones de un operario en un rango de fechas.

    Args:
        operario_id: ID del operario
        fecha_desde: Fecha inicial (opcional)
        fecha_hasta: Fecha final (opcional)

    Returns:
        Lista de asignaciones
    """
    try:
        sql = """
            SELECT
                af.fecha,
                af.turno,
                af.furgoneta_id,
                a.nombre as furgoneta_nombre,
                o.nombre as operario_nombre
            FROM asignaciones_furgoneta af
            JOIN almacenes a ON af.furgoneta_id = a.id
            JOIN operarios o ON af.operario_id = o.id
            WHERE af.operario_id = ?
        """
        params = [operario_id]

        if fecha_desde:
            sql += " AND af.fecha >= ?"
            params.append(fecha_desde)

        if fecha_hasta:
            sql += " AND af.fecha <= ?"
            params.append(fecha_hasta)

        sql += " ORDER BY af.fecha DESC, af.turno"

        return fetch_all(sql, tuple(params))

    except Exception as e:
        logger.exception(f"Error al obtener asignaciones: {e}")
        return []


def eliminar_asignacion(
    operario_id: int,
    fecha: str,
    turno: str = 'completo'
) -> bool:
    """
    Elimina una asignación específica.

    Args:
        operario_id: ID del operario
        fecha: Fecha (YYYY-MM-DD)
        turno: 'manana', 'tarde' o 'completo'

    Returns:
        True si se eliminó correctamente
    """
    try:
        sql = """
            DELETE FROM asignaciones_furgoneta
            WHERE operario_id = ? AND fecha = ? AND turno = ?
        """
        execute_query(sql, (operario_id, fecha, turno))
        logger.info(f"Asignación eliminada: operario {operario_id} - {fecha} {turno}")
        return True

    except Exception as e:
        logger.exception(f"Error al eliminar asignación: {e}")
        return False


def get_operarios_en_furgoneta(
    furgoneta_id: int,
    fecha: str
) -> List[Dict[str, Any]]:
    """
    Obtiene todos los operarios asignados a una furgoneta en una fecha.

    Args:
        furgoneta_id: ID de la furgoneta
        fecha: Fecha (YYYY-MM-DD)

    Returns:
        Lista de operarios con sus turnos
    """
    try:
        sql = """
            SELECT
                o.id as operario_id,
                o.nombre as operario_nombre,
                af.turno
            FROM asignaciones_furgoneta af
            JOIN operarios o ON af.operario_id = o.id
            WHERE af.furgoneta_id = ?
              AND af.fecha = ?
            ORDER BY af.turno, o.nombre
        """
        return fetch_all(sql, (furgoneta_id, fecha))

    except Exception as e:
        logger.exception(f"Error al obtener operarios en furgoneta: {e}")
        return []
