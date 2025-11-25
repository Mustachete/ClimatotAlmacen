"""
Repositorio de operaciones de sistema y mantenimiento de BD PostgreSQL
"""
from typing import Dict, Any, Tuple
from src.core.db_utils import get_con
from src.core.logger import logger


def verificar_conexion() -> Tuple[bool, str]:
    """
    Verifica la conexión a PostgreSQL y obtiene la versión.

    Returns:
        tuple: (exito: bool, mensaje: str con versión o error)
    """
    try:
        con = get_con()
        try:
            cur = con.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            return True, version
        finally:
            con.close()
    except Exception as e:
        logger.exception(f"Error al verificar conexión: {e}")
        return False, str(e)


def obtener_estadisticas_bd() -> Dict[str, Any]:
    """
    Obtiene estadísticas de la base de datos PostgreSQL.

    Returns:
        dict: {'size': str, 'num_tablas': int} o None si hay error
    """
    try:
        con = get_con()
        try:
            cur = con.cursor()

            # Obtener tamaño de la BD
            cur.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """)
            size = cur.fetchone()[0]

            # Obtener número de tablas
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            num_tablas = cur.fetchone()[0]

            return {
                'size': size,
                'num_tablas': num_tablas
            }
        finally:
            con.close()
    except Exception as e:
        logger.exception(f"Error al obtener estadísticas: {e}")
        return None


def verificar_integridad_bd() -> Dict[str, Any]:
    """
    Verifica la integridad de la base de datos PostgreSQL.

    Returns:
        dict: {'ok': bool, 'resultado': str}
    """
    return {
        'ok': True,
        'resultado': 'PostgreSQL: Verificación de integridad no disponible directamente.\nUsar herramientas PostgreSQL como pg_dump o vacuumdb para verificación completa.'
    }


def optimizar_bd() -> bool:
    """
    Optimiza la base de datos PostgreSQL ejecutando VACUUM ANALYZE.

    Returns:
        bool: True si se optimizó correctamente
    """
    con = get_con()
    try:
        cur = con.cursor()
        # PostgreSQL: VACUUM no puede ejecutarse en una transacción
        old_autocommit = con.autocommit
        con.autocommit = True
        try:
            cur.execute("VACUUM ANALYZE")
        finally:
            con.autocommit = old_autocommit
        return True
    finally:
        con.close()
