"""
Repositorio de Stock - Consultas SQL para obtener stock de artículos
"""
from typing import List, Dict, Any, Optional
from src.core.db_utils import fetch_all


def get_stock_completo(
    filtro_texto: Optional[str] = None,
    familia: Optional[str] = None,
    almacen: Optional[str] = None,
    solo_con_stock: bool = False,
    solo_alertas: bool = False
) -> List[Dict[str, Any]]:
    """
    Obtiene el stock completo de todos los artículos con filtros opcionales.

    Args:
        filtro_texto: Búsqueda por nombre, EAN o referencia
        familia: Filtro por nombre de familia
        almacen: Filtro por nombre de almacén
        solo_con_stock: Si True, solo artículos con stock > 0
        solo_alertas: Si True, solo artículos con stock < mínimo

    Returns:
        Lista de artículos con su stock por almacén
    """
    query = """
        SELECT
            a.id,
            a.nombre,
            a.ean,
            f.nombre as familia,
            alm.nombre as almacen,
            COALESCE(SUM(v.delta), 0) as stock,
            a.min_alerta,
            a.u_medida
        FROM articulos a
        LEFT JOIN familias f ON a.familia_id = f.id
        LEFT JOIN vw_stock v ON a.id = v.articulo_id
        LEFT JOIN almacenes alm ON v.almacen_id = alm.id
        WHERE a.activo = 1
    """

    params = []

    # Filtro de búsqueda
    if filtro_texto:
        query += " AND (a.nombre LIKE ? OR a.ean LIKE ? OR a.ref_proveedor LIKE ?)"
        params.extend([f"%{filtro_texto}%"] * 3)

    # Filtro de familia
    if familia:
        query += " AND f.nombre = ?"
        params.append(familia)

    # Filtro de almacén
    if almacen:
        query += " AND alm.nombre = ?"
        params.append(almacen)

    query += " GROUP BY a.id, a.nombre, a.ean, f.nombre, alm.nombre, a.min_alerta, a.u_medida"

    # Filtro de solo con stock
    if solo_con_stock:
        query += " HAVING stock > 0"

    # Filtro de solo alertas
    if solo_alertas:
        if solo_con_stock:
            query += " AND stock < a.min_alerta"
        else:
            query += " HAVING stock < a.min_alerta"

    query += " ORDER BY a.nombre, alm.nombre"

    return fetch_all(query, params)


def get_stock_articulo_por_almacen(articulo_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene el stock de un artículo específico en todos los almacenes.

    Args:
        articulo_id: ID del artículo

    Returns:
        Lista con el stock del artículo por almacén
    """
    query = """
        SELECT
            alm.id as almacen_id,
            alm.nombre as almacen,
            COALESCE(SUM(v.delta), 0) as stock
        FROM almacenes alm
        LEFT JOIN vw_stock v ON alm.id = v.almacen_id AND v.articulo_id = ?
        GROUP BY alm.id, alm.nombre
        HAVING stock > 0
        ORDER BY alm.nombre
    """
    return fetch_all(query, (articulo_id,))


def get_stock_total_articulo(articulo_id: int) -> float:
    """
    Obtiene el stock total de un artículo (sumando todos los almacenes).

    Args:
        articulo_id: ID del artículo

    Returns:
        Stock total del artículo
    """
    query = """
        SELECT COALESCE(SUM(delta), 0) as stock_total
        FROM vw_stock
        WHERE articulo_id = ?
    """
    result = fetch_all(query, (articulo_id,))
    return result[0]['stock_total'] if result else 0.0


def get_articulos_con_stock_bajo() -> List[Dict[str, Any]]:
    """
    Obtiene artículos con stock por debajo del mínimo de alerta.

    Returns:
        Lista de artículos con stock bajo
    """
    query = """
        SELECT
            a.id,
            a.nombre,
            a.ean,
            f.nombre as familia,
            COALESCE(SUM(v.delta), 0) as stock_total,
            a.min_alerta,
            a.u_medida
        FROM articulos a
        LEFT JOIN familias f ON a.familia_id = f.id
        LEFT JOIN vw_stock v ON a.id = v.articulo_id
        WHERE a.activo = 1
        GROUP BY a.id, a.nombre, a.ean, f.nombre, a.min_alerta, a.u_medida
        HAVING stock_total < a.min_alerta
        ORDER BY (stock_total - a.min_alerta), a.nombre
    """
    return fetch_all(query)


def get_articulos_sin_stock() -> List[Dict[str, Any]]:
    """
    Obtiene artículos activos sin stock en ningún almacén.

    Returns:
        Lista de artículos sin stock
    """
    query = """
        SELECT
            a.id,
            a.nombre,
            a.ean,
            f.nombre as familia,
            a.min_alerta,
            a.u_medida
        FROM articulos a
        LEFT JOIN familias f ON a.familia_id = f.id
        LEFT JOIN vw_stock v ON a.id = v.articulo_id
        WHERE a.activo = 1
        GROUP BY a.id, a.nombre, a.ean, f.nombre, a.min_alerta, a.u_medida
        HAVING COALESCE(SUM(v.delta), 0) = 0
        ORDER BY a.nombre
    """
    return fetch_all(query)


def get_estadisticas_stock() -> Dict[str, Any]:
    """
    Obtiene estadísticas generales de stock.

    Returns:
        Diccionario con estadísticas de stock
    """
    query = """
        SELECT
            COUNT(DISTINCT a.id) as total_articulos,
            COUNT(DISTINCT CASE WHEN COALESCE(SUM(v.delta), 0) > 0 THEN a.id END) as articulos_con_stock,
            COUNT(DISTINCT CASE WHEN COALESCE(SUM(v.delta), 0) < a.min_alerta THEN a.id END) as articulos_bajo_minimo,
            COUNT(DISTINCT CASE WHEN COALESCE(SUM(v.delta), 0) = 0 THEN a.id END) as articulos_sin_stock
        FROM articulos a
        LEFT JOIN vw_stock v ON a.id = v.articulo_id
        WHERE a.activo = 1
        GROUP BY a.id, a.min_alerta
    """
    results = fetch_all(query)

    if not results:
        return {
            'total_articulos': 0,
            'articulos_con_stock': 0,
            'articulos_bajo_minimo': 0,
            'articulos_sin_stock': 0
        }

    # Consolidar resultados
    stats = {
        'total_articulos': len(results),
        'articulos_con_stock': sum(1 for r in results if r.get('articulos_con_stock')),
        'articulos_bajo_minimo': sum(1 for r in results if r.get('articulos_bajo_minimo')),
        'articulos_sin_stock': sum(1 for r in results if r.get('articulos_sin_stock'))
    }

    return stats
