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


def obtener_estadisticas_sistema() -> Dict[str, Any]:
    """
    Obtiene estadísticas completas del sistema.

    Returns:
        dict: Estadísticas completas (artículos, movimientos, usuarios, stock, etc.)
              o None si hay error
    """
    try:
        con = get_con()
        try:
            cur = con.cursor()
            stats = {}

            # Contar artículos activos
            cur.execute("SELECT COUNT(*) as total FROM articulos WHERE activo = 1")
            stats['articulos'] = cur.fetchone()[0]

            # Contar movimientos del último mes (PostgreSQL)
            cur.execute("""
                SELECT COUNT(*) as total
                FROM movimientos
                WHERE fecha >= CURRENT_DATE - INTERVAL '30 days'
            """)
            stats['movimientos_mes'] = cur.fetchone()[0]

            # Contar OTs del último mes (PostgreSQL)
            cur.execute("""
                SELECT COUNT(DISTINCT ot) as total
                FROM movimientos
                WHERE ot IS NOT NULL AND ot != ''
                AND fecha >= CURRENT_DATE - INTERVAL '30 days'
            """)
            stats['ots_mes'] = cur.fetchone()[0]

            # Contar usuarios activos
            cur.execute("SELECT COUNT(*) as total FROM usuarios WHERE activo = 1")
            stats['usuarios'] = cur.fetchone()[0]

            # Contar furgonetas (PostgreSQL: desde 'almacenes')
            cur.execute("SELECT COUNT(*) as total FROM almacenes WHERE tipo = 'furgoneta'")
            stats['furgonetas'] = cur.fetchone()[0]

            # Valor total del stock (usando vista vw_stock_total)
            cur.execute("""
                SELECT SUM(COALESCE(s.stock_total, 0) * COALESCE(a.coste, 0)) as total
                FROM articulos a
                LEFT JOIN vw_stock_total s ON a.id = s.articulo_id
                WHERE a.activo = 1
            """)
            result = cur.fetchone()[0]
            stats['valor_stock'] = float(result) if result else 0.0

            # Artículos con stock bajo (usando vista vw_stock_total y min_alerta)
            cur.execute("""
                SELECT COUNT(*) as total
                FROM articulos a
                LEFT JOIN vw_stock_total s ON a.id = s.articulo_id
                WHERE a.activo = 1
                AND COALESCE(s.stock_total, 0) <= a.min_alerta
                AND a.min_alerta > 0
            """)
            stats['stock_bajo'] = cur.fetchone()[0]

            # Tamaño de la base de datos PostgreSQL
            try:
                cur.execute("SELECT pg_database_size(current_database()) as size")
                db_size = cur.fetchone()[0] / (1024 * 1024)
                stats['db_size'] = f"{db_size:.2f} MB"
            except:
                stats['db_size'] = "N/A"

            return stats
        finally:
            con.close()
    except Exception as e:
        logger.exception(f"Error al obtener estadísticas del sistema: {e}")
        return None


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
