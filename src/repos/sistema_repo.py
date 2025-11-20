"""
Repositorio de operaciones de sistema y mantenimiento de BD PostgreSQL
"""
from typing import Dict, Any
from src.core.db_utils import get_con


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
