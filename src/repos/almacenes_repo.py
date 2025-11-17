"""
Repositorio de Almacenes - Consultas SQL para gestión de almacenes y furgonetas
"""
from typing import List, Dict, Any, Optional
from src.core.db_utils import fetch_all, fetch_one, execute_query


def get_todos(filtro_texto: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Obtiene lista de almacenes con filtro opcional.

    Args:
        filtro_texto: Búsqueda por nombre
        limit: Límite de resultados

    Returns:
        Lista de almacenes
    """
    if filtro_texto:
        sql = """
            SELECT id, nombre, tipo
            FROM almacenes
            WHERE nombre LIKE ?
            ORDER BY nombre
            LIMIT ?
        """
        return fetch_all(sql, (f"%{filtro_texto}%", limit))
    else:
        sql = """
            SELECT id, nombre, tipo
            FROM almacenes
            ORDER BY nombre
            LIMIT ?
        """
        return fetch_all(sql, (limit,))


def get_by_id(almacen_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene un almacén por su ID."""
    sql = "SELECT id, nombre, tipo FROM almacenes WHERE id = ?"
    return fetch_one(sql, (almacen_id,))


def get_by_nombre(nombre: str) -> Optional[Dict[str, Any]]:
    """Obtiene un almacén por su nombre exacto."""
    sql = "SELECT id, nombre, tipo FROM almacenes WHERE nombre = ?"
    return fetch_one(sql, (nombre,))


def get_by_tipo(tipo: str) -> List[Dict[str, Any]]:
    """
    Obtiene almacenes por tipo.

    Args:
        tipo: 'almacen' o 'furgoneta'

    Returns:
        Lista de almacenes del tipo especificado
    """
    sql = """
        SELECT id, nombre, tipo
        FROM almacenes
        WHERE tipo = ?
        ORDER BY nombre
    """
    return fetch_all(sql, (tipo,))


def get_almacenes() -> List[Dict[str, Any]]:
    """Obtiene solo los almacenes fijos (tipo='almacen')."""
    return get_by_tipo('almacen')


def get_furgonetas() -> List[Dict[str, Any]]:
    """Obtiene solo las furgonetas (tipo='furgoneta')."""
    return get_by_tipo('furgoneta')


def crear_almacen(nombre: str, tipo: str = 'almacen') -> int:
    """
    Crea un nuevo almacén.

    Args:
        nombre: Nombre del almacén
        tipo: 'almacen' o 'furgoneta'

    Returns:
        ID del almacén creado
    """
    sql = "INSERT INTO almacenes(nombre, tipo) VALUES(?, ?)"
    return execute_query(sql, (nombre, tipo))


def actualizar_almacen(almacen_id: int, nombre: str, tipo: str) -> bool:
    """Actualiza un almacén existente."""
    sql = "UPDATE almacenes SET nombre=?, tipo=? WHERE id=?"
    execute_query(sql, (nombre, tipo, almacen_id))
    return True


def eliminar_almacen(almacen_id: int) -> bool:
    """Elimina un almacén (fallará si tiene movimientos asociados)."""
    sql = "DELETE FROM almacenes WHERE id=?"
    execute_query(sql, (almacen_id,))
    return True


def verificar_movimientos(almacen_id: int) -> bool:
    """Verifica si un almacén tiene movimientos asociados."""
    sql = """
        SELECT COUNT(*) as count
        FROM movimientos
        WHERE origen_id = ? OR destino_id = ?
    """
    result = fetch_one(sql, (almacen_id, almacen_id))
    return result['count'] > 0 if result else False


def get_stock_almacen(almacen_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene el stock actual de un almacén específico.

    Args:
        almacen_id: ID del almacén

    Returns:
        Lista de artículos con su stock en el almacén
    """
    sql = """
        SELECT
            a.id,
            a.nombre,
            a.u_medida,
            COALESCE(SUM(
                CASE
                    WHEN m.destino_id = ? THEN m.cantidad
                    WHEN m.origen_id = ? THEN -m.cantidad
                    ELSE 0
                END
            ), 0) as stock
        FROM articulos a
        LEFT JOIN movimientos m ON a.id = m.articulo_id
        WHERE a.activo = 1
        GROUP BY a.id, a.nombre, a.u_medida
        HAVING stock > 0
        ORDER BY a.nombre
    """
    return fetch_all(sql, (almacen_id, almacen_id))


def get_estadisticas_almacen(almacen_id: int) -> Dict[str, Any]:
    """
    Obtiene estadísticas de un almacén.

    Returns:
        Diccionario con estadísticas del almacén
    """
    sql = """
        SELECT
            COUNT(DISTINCT m.articulo_id) as articulos_diferentes,
            COALESCE(SUM(
                CASE
                    WHEN m.destino_id = ? THEN m.cantidad
                    WHEN m.origen_id = ? THEN -m.cantidad
                    ELSE 0
                END
            ), 0) as cantidad_total
        FROM movimientos m
        WHERE m.origen_id = ? OR m.destino_id = ?
    """
    result = fetch_one(sql, (almacen_id, almacen_id, almacen_id, almacen_id))
    return result if result else {}
