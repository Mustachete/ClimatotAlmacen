# asignaciones_repo.py - Gestión de asignaciones operario-furgoneta
"""
Sistema unificado de asignaciones furgoneta-operario.
Soporta turnos (mañana, tarde, completo) y consultas por fecha.
"""

from typing import Optional, Dict, Any, List
from src.core.db_utils import get_con, fetch_one, fetch_all, execute_query
from src.core.logger import logger


def verificar_asignacion_operario_fecha(
    operario_id: int,
    fecha: str
) -> Optional[Dict[str, Any]]:
    """
    Verifica si un operario ya tiene asignación en una fecha específica.

    Args:
        operario_id: ID del operario
        fecha: Fecha (YYYY-MM-DD)

    Returns:
        Dict con información de la asignación existente, o None si no hay
    """
    try:
        sql = """
            SELECT af.turno, af.furgoneta_id, a.nombre as furgoneta_nombre
            FROM asignaciones_furgoneta af
            JOIN almacenes a ON af.furgoneta_id = a.id
            WHERE af.operario_id = %s AND af.fecha = %s
        """
        return fetch_one(sql, (operario_id, fecha))
    except Exception as e:
        logger.exception(f"Error al verificar asignación: {e}")
        return None


def asignar_furgoneta(
    operario_id: int,
    fecha: str,
    furgoneta_id: int,
    turno: str = 'completo',
    forzar: bool = False
) -> bool:
    """
    Asigna una furgoneta a un operario para una fecha y turno específicos.

    Lógica de conflictos:
    - Si tiene "día completo" y se asigna "tarde": Cambia "completo" a "mañana" automáticamente
    - Si tiene "día completo" y se asigna "mañana": Cambia "completo" a "tarde" automáticamente
    - Si tiene "día completo" y se asigna otro "día completo": Requiere forzar=True
    - Si tiene "mañana" y se asigna "tarde" (o viceversa): OK
    - Si tiene misma asignación: Actualiza

    Args:
        operario_id: ID del operario
        fecha: Fecha (YYYY-MM-DD)
        furgoneta_id: ID de la furgoneta (almacen con tipo='furgoneta')
        turno: 'manana', 'tarde' o 'completo' (default)
        forzar: Si True, permite sobrescribir "día completo" con otro "día completo"

    Returns:
        True si se asignó correctamente

    Raises:
        ValueError: Si hay conflicto de turnos y no se fuerza (formato: "CONFLICTO_DIA_COMPLETO|furgoneta_actual|furgoneta_nueva")
    """
    try:
        # Validar turno
        if turno not in ('manana', 'tarde', 'completo'):
            raise ValueError(f"Turno inválido: {turno}. Debe ser 'manana', 'tarde' o 'completo'")

        # Verificar asignación existente
        asignacion_existente = verificar_asignacion_operario_fecha(operario_id, fecha)

        if asignacion_existente:
            turno_existente = asignacion_existente['turno']
            furgoneta_existente_id = asignacion_existente['furgoneta_id']
            furgoneta_existente_nombre = asignacion_existente['furgoneta_nombre']

            # CASO 1: Tiene "día completo" y se asigna "tarde"
            # → Cambiar "completo" a "mañana" + agregar "tarde"
            if turno_existente == 'completo' and turno == 'tarde':
                # Cambiar el turno completo a mañana
                sql_update = """
                    UPDATE asignaciones_furgoneta
                    SET turno = 'manana'
                    WHERE operario_id = %s AND fecha = %s AND turno = 'completo'
                """
                execute_query(sql_update, (operario_id, fecha))
                logger.info(f"Cambiado turno completo a mañana para operario {operario_id} - {fecha}")

                # Insertar la nueva asignación de tarde
                sql_insert = """
                    INSERT INTO asignaciones_furgoneta(operario_id, fecha, turno, furgoneta_id)
                    VALUES(%s, %s, 'tarde', %s)
                    ON CONFLICT (fecha, turno, furgoneta_id)
                    DO UPDATE SET operario_id = EXCLUDED.operario_id
                """
                execute_query(sql_insert, (operario_id, fecha, furgoneta_id))
                logger.info(f"Furgoneta {furgoneta_id} asignada (tarde) a operario {operario_id} - {fecha}")
                return True

            # CASO 2: Tiene "día completo" y se asigna "mañana"
            # → Cambiar "completo" a "tarde" + agregar "mañana"
            elif turno_existente == 'completo' and turno == 'manana':
                # Cambiar el turno completo a tarde
                sql_update = """
                    UPDATE asignaciones_furgoneta
                    SET turno = 'tarde'
                    WHERE operario_id = %s AND fecha = %s AND turno = 'completo'
                """
                execute_query(sql_update, (operario_id, fecha))
                logger.info(f"Cambiado turno completo a tarde para operario {operario_id} - {fecha}")

                # Insertar la nueva asignación de mañana
                sql_insert = """
                    INSERT INTO asignaciones_furgoneta(operario_id, fecha, turno, furgoneta_id)
                    VALUES(%s, %s, 'manana', %s)
                    ON CONFLICT (fecha, turno, furgoneta_id)
                    DO UPDATE SET operario_id = EXCLUDED.operario_id
                """
                execute_query(sql_insert, (operario_id, fecha, furgoneta_id))
                logger.info(f"Furgoneta {furgoneta_id} asignada (mañana) a operario {operario_id} - {fecha}")
                return True

            # CASO 3: Tiene "día completo" y se asigna otro "día completo"
            # → Requiere confirmación (forzar=True)
            elif turno_existente == 'completo' and turno == 'completo':
                if not forzar:
                    raise ValueError(
                        f"CONFLICTO_DIA_COMPLETO|{furgoneta_existente_nombre}|{furgoneta_id}"
                    )

                # Eliminar asignación anterior y crear nueva
                sql_delete = """
                    DELETE FROM asignaciones_furgoneta
                    WHERE operario_id = %s AND fecha = %s AND turno = 'completo'
                """
                execute_query(sql_delete, (operario_id, fecha))
                logger.info(f"Eliminada asignación anterior (día completo) para operario {operario_id} - {fecha}")

        # Insertar o actualizar asignación normal
        sql = """
            INSERT INTO asignaciones_furgoneta(operario_id, fecha, turno, furgoneta_id)
            VALUES(%s, %s, %s, %s)
            ON CONFLICT (fecha, turno, furgoneta_id)
            DO UPDATE SET operario_id = EXCLUDED.operario_id
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
            WHERE af.operario_id = %s
              AND af.fecha = %s
              AND af.turno = %s
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
            WHERE af.operario_id = %s
        """
        params = [operario_id]

        if fecha_desde:
            sql += " AND af.fecha >= %s"
            params.append(fecha_desde)

        if fecha_hasta:
            sql += " AND af.fecha <= %s"
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
            WHERE operario_id = %s AND fecha = %s AND turno = %s
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
            WHERE af.furgoneta_id = %s
              AND af.fecha = %s
            ORDER BY af.turno, o.nombre
        """
        return fetch_all(sql, (furgoneta_id, fecha))

    except Exception as e:
        logger.exception(f"Error al obtener operarios en furgoneta: {e}")
        return []


def buscar_asignaciones_filtradas(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    operario_id: Optional[int] = None,
    furgoneta_id: Optional[int] = None,
    turno: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Busca asignaciones con múltiples filtros opcionales.

    Args:
        fecha_desde: Fecha inicial (YYYY-MM-DD)
        fecha_hasta: Fecha final (YYYY-MM-DD)
        operario_id: Filtrar por operario
        furgoneta_id: Filtrar por furgoneta
        turno: Filtrar por turno ('manana', 'tarde', 'completo')

    Returns:
        Lista de asignaciones que cumplen los filtros
    """
    try:
        sql = """
            SELECT
                af.fecha,
                af.turno,
                af.operario_id,
                o.nombre as operario_nombre,
                o.rol_operario,
                af.furgoneta_id,
                a.nombre as furgoneta_nombre
            FROM asignaciones_furgoneta af
            JOIN operarios o ON af.operario_id = o.id
            JOIN almacenes a ON af.furgoneta_id = a.id
            WHERE 1=1
        """
        params = []

        if fecha_desde:
            sql += " AND af.fecha >= %s"
            params.append(fecha_desde)

        if fecha_hasta:
            sql += " AND af.fecha <= %s"
            params.append(fecha_hasta)

        if operario_id:
            sql += " AND af.operario_id = %s"
            params.append(operario_id)

        if furgoneta_id:
            sql += " AND af.furgoneta_id = %s"
            params.append(furgoneta_id)

        if turno:
            sql += " AND af.turno = %s"
            params.append(turno)

        sql += " ORDER BY af.fecha DESC, af.turno, o.nombre"

        return fetch_all(sql, tuple(params))

    except Exception as e:
        logger.exception(f"Error al buscar asignaciones filtradas: {e}")
        return []
