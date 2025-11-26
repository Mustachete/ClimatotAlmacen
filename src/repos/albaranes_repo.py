"""
Repositorio de Albaranes - Consultas SQL para gestión de albaranes de recepción
"""
from typing import List, Dict, Any, Optional
from src.core.db_utils import fetch_all, fetch_one, execute_query


# ========================================
# CONSULTAS DE ALBARANES
# ========================================

def get_by_numero(albaran: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un albarán por su número.

    Args:
        albaran: Número de albarán

    Returns:
        Diccionario con información del albarán o None
    """
    sql = """
        SELECT a.albaran, a.proveedor_id, a.fecha, p.nombre as proveedor_nombre
        FROM albaranes a
        LEFT JOIN proveedores p ON a.proveedor_id = p.id
        WHERE a.albaran = %s
    """
    return fetch_one(sql, (albaran,))


def verificar_duplicado(albaran: str, proveedor_id: Optional[int], fecha: str) -> bool:
    """
    Verifica si ya existe un albarán con el mismo número, proveedor y fecha.

    Args:
        albaran: Número de albarán
        proveedor_id: ID del proveedor (puede ser None)
        fecha: Fecha del albarán (YYYY-MM-DD)

    Returns:
        True si existe, False si no
    """
    sql = """
        SELECT COUNT(*) as count
        FROM albaranes
        WHERE albaran = %s AND proveedor_id = %s AND fecha = %s
    """
    result = fetch_one(sql, (albaran, proveedor_id, fecha))
    return result['count'] > 0 if result else False


def crear_albaran(albaran: str, proveedor_id: Optional[int], fecha: str) -> bool:
    """
    Crea un nuevo albarán.

    Args:
        albaran: Número de albarán (obligatorio, PK)
        proveedor_id: ID del proveedor (opcional)
        fecha: Fecha del albarán (YYYY-MM-DD)

    Returns:
        True si se creó correctamente
    """
    sql = "INSERT INTO albaranes(albaran, proveedor_id, fecha) VALUES(%s,%s,%s)"
    execute_query(sql, (albaran, proveedor_id, fecha))
    return True


def get_todos(filtro_texto: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Obtiene lista de albaranes con información del proveedor y cantidad de artículos.

    Args:
        filtro_texto: Filtro por número de albarán o nombre de proveedor
        limit: Límite de resultados

    Returns:
        Lista de albaranes ordenados por fecha descendente
    """
    if filtro_texto:
        sql = """
            SELECT a.albaran, p.nombre as proveedor_nombre, a.fecha,
                   (SELECT COUNT(DISTINCT articulo_id) FROM movimientos WHERE albaran=a.albaran) as num_articulos
            FROM albaranes a
            LEFT JOIN proveedores p ON a.proveedor_id = p.id
            WHERE a.albaran ILIKE %s OR p.nombre ILIKE %s
            ORDER BY a.fecha DESC, a.albaran
            LIMIT %s
        """
        params = (f"%{filtro_texto}%", f"%{filtro_texto}%", limit)
    else:
        sql = """
            SELECT a.albaran, p.nombre as proveedor_nombre, a.fecha,
                   (SELECT COUNT(DISTINCT articulo_id) FROM movimientos WHERE albaran=a.albaran) as num_articulos
            FROM albaranes a
            LEFT JOIN proveedores p ON a.proveedor_id = p.id
            ORDER BY a.fecha DESC, a.albaran
            LIMIT %s
        """
        params = (limit,)

    return fetch_all(sql, params)


def get_articulos_albaran(albaran: str) -> List[Dict[str, Any]]:
    """
    Obtiene los artículos asociados a un albarán.

    Args:
        albaran: Número de albarán

    Returns:
        Lista de artículos del albarán con sus cantidades
    """
    sql = """
        SELECT a.nombre, m.cantidad, a.u_medida, m.coste_unit
        FROM movimientos m
        JOIN articulos a ON m.articulo_id = a.id
        WHERE m.albaran = %s
        ORDER BY a.nombre
    """
    return fetch_all(sql, (albaran,))
